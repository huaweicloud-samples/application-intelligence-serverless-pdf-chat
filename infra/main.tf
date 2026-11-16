# ===========================================================================
# serverless-pdf-chat on Huawei Cloud
# Services: OBS + GeminiDB(DynamoDB-compatible)(x2 tables) + FunctionGraph(x8)
#           + APIG + MaaS(OpenAI-compat) + APIG App auth + OBS static hosting + CDN
#
# Design notes:
#  * Message-queue fan-out is implemented with OBS upload events fanning out to TWO
#    FunctionGraph triggers (upload_trigger + generate_embeddings). A deterministic
#    documentid (uuid5 of the object key) keeps the two triggers consistent.
#  * Cognito is replaced by APIG App authentication; browser identity is a
#    per-browser UUID sent as X-User-Id (see src/frontend/src/common/api.ts).
#  * Functions join the VPC so they can reach the private GeminiDB load balancer;
#    a NAT gateway gives them public egress for MaaS and OBS.
#  * Function packages are uploaded to OBS and referenced via code_url (stable,
#    validate-friendly). Rebuild with `python src/build.py` before apply.
# ===========================================================================

data "huaweicloud_account" "current" {}

# ---------------------------------------------------------------------------
# Networking: VPC + subnet + security group + NAT (public egress for FGS)
# ---------------------------------------------------------------------------
resource "huaweicloud_vpc" "main" {
  name = "pdf-chat-vpc"
  cidr = var.vpc_cidr
}

resource "huaweicloud_vpc_subnet" "main" {
  name       = "pdf-chat-subnet"
  cidr       = var.subnet_cidr
  gateway_ip = cidrhost(var.subnet_cidr, 1)
  vpc_id     = huaweicloud_vpc.main.id
}

resource "huaweicloud_networking_secgroup" "main" {
  name        = "pdf-chat-sg"
  description = "Allow intra-VPC traffic for GeminiDB + FGS."
}

# EIP + NAT gateway so VPC-attached functions can reach the public internet
# (MaaS endpoint, OBS public endpoint).
resource "huaweicloud_vpc_bandwidth" "nat" {
  name = "pdf-chat-nat-bw"
  size = 5
}

resource "huaweicloud_vpc_eip" "nat" {
  name = "pdf-chat-nat-eip"

  publicip {
    type = "5_bgp"
  }

  bandwidth {
    name        = "pdf-chat-nat-bw"
    size        = 5
    share_type  = "PER"
    charge_mode = "bandwidth"
  }
}

resource "huaweicloud_nat_gateway" "main" {
  name        = "pdf-chat-nat"
  spec        = "1"
  vpc_id      = huaweicloud_vpc.main.id
  subnet_id   = huaweicloud_vpc_subnet.main.id
  description = "Public egress for FunctionGraph."
}

# ---------------------------------------------------------------------------
# IAM agency: execution role assumed by every FunctionGraph function
# ---------------------------------------------------------------------------
resource "huaweicloud_identity_agency" "fgs" {
  name                     = var.agency_name
  delegated_service_name   = "op_svc_cff"
  description              = "Execution agency for serverless-pdf-chat functions."
  domain_roles            = ["OBS Administrator", "LTS Administrator", "VPC Administrator"]
}

# ---------------------------------------------------------------------------
# OBS bucket: PDF storage, generated index files and function packages
# ---------------------------------------------------------------------------
resource "huaweicloud_obs_bucket" "main" {
  bucket = var.obs_bucket_name
  acl    = "private"

  cors_rule {
    allowed_origins = ["*"]
    allowed_methods = ["PUT", "GET", "POST", "DELETE", "HEAD"]
    allowed_headers = ["*"]
    max_age_seconds = 3000
  }

  force_destroy = true
}

# Data-plane policy: OBS does NOT honour the agency's IAM role directly, so we
# grant the agency principal the required object actions explicitly.
# OBS bucket policy removed - agency has OBS Administrator role which grants access
# Bucket remains private; functions access via agency credentials

# ---------------------------------------------------------------------------
# GeminiDB (DynamoDB-compatible interface) — two tables created at runtime
# (DocumentTable, MemoryTable) by the functions' common/dynamodb.py.
# ---------------------------------------------------------------------------
resource "huaweicloud_geminidb_instance" "main" {
  name              = var.geminidb_instance_name
  region            = var.region
  password          = var.geminidb_password
  mode              = "Cluster"
  availability_zone = var.geminidb_az
  vpc_id            = huaweicloud_vpc.main.id
  subnet_id         = huaweicloud_vpc_subnet.main.id
  security_group_id = huaweicloud_networking_secgroup.main.id

  datastore {
    type           = "cassandra"
    version        = "3.11"
    storage_engine = "rocksDB"
  }

  flavor {
    num         = var.geminidb_node_num
    size        = var.geminidb_storage_size
    spec_code   = "geminidb.cassandra.large.4"
    storage     = var.geminidb_storage_type
  }

  backup_strategy {
    start_time = "03:00-04:00"
  }

  # Force 3 nodes for Cluster mode (required)
}

# ---------------------------------------------------------------------------
# APIG dedicated instance (public ingress optional)
# ---------------------------------------------------------------------------
resource "huaweicloud_apig_instance" "main" {
  name               = var.apig_instance_name
  edition            = var.apig_edition
  available_zones    = var.apig_available_zones
  vpc_id             = huaweicloud_vpc.main.id
  subnet_id          = huaweicloud_vpc_subnet.main.id
  security_group_id  = huaweicloud_networking_secgroup.main.id

  # Public ingress so the browser SPA can reach the API directly.
  ingress_bandwidth_size            = var.apig_public ? var.apig_ingress_bandwidth_size : null
  ingress_bandwidth_charging_mode   = var.apig_public ? var.apig_ingress_bandwidth_charging_mode : null
}

resource "huaweicloud_apig_group" "main" {
  name        = "pdf-chat-group"
  instance_id = huaweicloud_apig_instance.main.id
}

# ---------------------------------------------------------------------------
# APIG App authentication
# ---------------------------------------------------------------------------
resource "huaweicloud_apig_application" "main" {
  name        = "pdfchatapp"
  instance_id = huaweicloud_apig_instance.main.id
}

resource "huaweicloud_apig_appcode" "main" {
  application_id = huaweicloud_apig_application.main.id
  instance_id    = huaweicloud_apig_instance.main.id
}

# ---------------------------------------------------------------------------
# FunctionGraph functions (8) — deployed from OBS-hosted zips
# ---------------------------------------------------------------------------
locals {
  # api=false  → OBS-event triggered (no APIG route)
  functions = {
    generate_presigned_url = { api = true,  method = "GET",    path = "/generate_presigned_url",                    memory = 128, timeout = 30 }
    get_document          = { api = true,  method = "GET",    path = "/doc/{documentid}/{conversationid}",        memory = 128, timeout = 30 }
    get_all_documents     = { api = true,  method = "GET",    path = "/doc",                                       memory = 128, timeout = 30 }
    add_conversation     = { api = true,  method = "POST",   path = "/doc/{documentid}",                          memory = 128, timeout = 30 }
    generate_response    = { api = true,  method = "POST",   path = "/doc/{documentid}/{conversationid}",         memory = 256, timeout = 60 }
    delete_document      = { api = true,  method = "DELETE", path = "/doc/{documentid}",                          memory = 128, timeout = 30 }
    upload_trigger       = { api = false, method = "",       path = "",                                            memory = 256, timeout = 60 }
    generate_embeddings  = { api = false, method = "",       path = "",                                            memory = 512, timeout = 300 }
  }

  function_env = jsonencode({
    OBS_BUCKET        = var.obs_bucket_name
    OBS_ENDPOINT      = "https://obs.${var.region}.myhuaweicloud.com"
    OBS_REGION        = var.region
    GEMINIDB_ENDPOINT = "http://${huaweicloud_geminidb_instance.main.lb_ip_address}:${huaweicloud_geminidb_instance.main.lb_port}"
    GEMINIDB_USER     = "rwuser"
    GEMINIDB_PASSWORD = var.geminidb_password
    MAAS_ENDPOINT     = var.maas_endpoint
    MAAS_API_KEY      = var.maas_api_key
    MAAS_EMBED_MODEL  = var.maas_embed_model
    MAAS_CHAT_MODEL   = var.maas_chat_model
    HW_REGION         = var.region
  })
}

resource "huaweicloud_obs_bucket_object" "fn" {
  for_each = local.functions
  bucket   = huaweicloud_obs_bucket.main.bucket
  key      = "functions/${each.key}.zip"
  source   = "${path.module}/../src/dist/${each.key}.zip"
  etag     = fileexists("${path.module}/../src/dist/${each.key}.zip") ? filemd5("${path.module}/../src/dist/${each.key}.zip") : null
}

resource "huaweicloud_fgs_function" "fn" {
  for_each = local.functions

  name        = each.key
  app         = "default"
  handler     = "main.handler"
  runtime     = "Python3.9"
  memory_size = each.value.memory
  timeout     = each.value.timeout
  agency      = huaweicloud_identity_agency.fgs.name
  vpc_id      = huaweicloud_vpc.main.id
  network_id  = huaweicloud_vpc_subnet.main.id
  user_data   = local.function_env
  code_url    = "obs://${huaweicloud_obs_bucket.main.bucket}/${huaweicloud_obs_bucket_object.fn[each.key].key}"

  lifecycle {
    replace_triggered_by = [huaweicloud_obs_bucket_object.fn[each.key]]
  }
}

# ---------------------------------------------------------------------------
# APIG APIs (6) + publishment to the instance's default RELEASE environment
# ---------------------------------------------------------------------------
resource "huaweicloud_apig_api" "fn" {
  for_each = { for k, v in local.functions : k => v if v.api }

  group_id              = huaweicloud_apig_group.main.id
  instance_id           = huaweicloud_apig_instance.main.id
  name                  = each.key
  type                  = "FunctionGraph"
  request_method        = each.value.method
  request_path          = each.value.path
  request_protocol      = "HTTPS"
  security_authentication = "App"
  cors                  = true

  func_graph {
    function_urn    = huaweicloud_fgs_function.fn[each.key].urn
    invocation_type = "sync"
    network_type    = "V1"
    request_protocol = "HTTPS"
    timeout         = each.value.timeout * 1000
  }

  lifecycle {
    ignore_changes = [func_graph]
  }
}

resource "huaweicloud_apig_api_publishment" "fn" {
  for_each = { for k, v in local.functions : k => v if v.api }

  instance_id = huaweicloud_apig_instance.main.id
  api_id      = huaweicloud_apig_api.fn[each.key].id
  env_id      = "DEFAULT_ENVIRONMENT_RELEASE_ID"
}

# Authorise the application to call every API in the RELEASE environment.
resource "huaweicloud_apig_application_authorization" "main" {
  instance_id     = huaweicloud_apig_instance.main.id
  application_id  = huaweicloud_apig_application.main.id
  env_id          = "DEFAULT_ENVIRONMENT_RELEASE_ID"
  api_ids         = [for k, v in local.functions : huaweicloud_apig_api.fn[k].id if v.api]
}

# ---------------------------------------------------------------------------
# OBS upload triggers → two FunctionGraph functions (replaces SQS fan-out)
# ---------------------------------------------------------------------------
resource "huaweicloud_fgs_function_trigger" "pdf" {
  for_each = { for k, v in local.functions : k => v if !v.api }

  function_urn = huaweicloud_fgs_function.fn[each.key].urn
  type         = "OBS"
  status       = "ACTIVE"
  event_data   = jsonencode({
    bucket_name = huaweicloud_obs_bucket.main.bucket
    events     = ["ObjectCreated"]
    prefix     = ""
    suffix     = ".pdf"
  })
}
