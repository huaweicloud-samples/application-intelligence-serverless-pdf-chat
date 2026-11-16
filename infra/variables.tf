# ---------------------------------------------------------------------------
# Region & naming
# ---------------------------------------------------------------------------
variable "region" {
  description = "Huawei Cloud region. MaaS (ModelArts) is only available in cn-southwest-2, but the rest of the stack can live in any region; the MaaS endpoint is a public URL so cross-region HTTPS is fine."
  type        = string
  default     = "cn-north-4"
}

variable "obs_bucket_name" {
  description = "Globally unique OBS bucket name used for PDF storage, generated index files and function deployment packages."
  type        = string
  default     = "app-intel-serverless-pdf-chat"
}

# ---------------------------------------------------------------------------
# Secrets (provide via terraform.tfvars — gitignored, never commit)
# ---------------------------------------------------------------------------
variable "geminidb_password" {
  description = "Admin password for the GeminiDB (DynamoDB-compatible) instance. The data plane uses user 'rwuser' + this password."
  type        = string
  sensitive   = true
}

variable "maas_api_key" {
  description = "API key for Huawei Cloud ModelArts MaaS (OpenAI-compatible embeddings + chat)."
  type        = string
  sensitive   = true
}

# ---------------------------------------------------------------------------
# MaaS model endpoints
# ---------------------------------------------------------------------------
variable "maas_endpoint" {
  description = "Base URL of the MaaS OpenAI-compatible API."
  type        = string
  default     = "https://api.modelarts-maas.com/openai/v1"
}

variable "maas_embed_model" {
  description = "MaaS embedding model name used to vectorise PDF chunks."
  type        = string
  default     = "text-embedding-v3"
}

variable "maas_chat_model" {
  description = "MaaS chat-completions model used to answer questions."
  type        = string
  default     = "deepseek-v3"
}

# ---------------------------------------------------------------------------
# GeminiDB (DynamoDB-compatible) instance
# ---------------------------------------------------------------------------
variable "geminidb_instance_name" {
  type    = string
  default = "pdf-chat-geminidb"
}

# NOTE: spec_code depends on region availability. The default below is the
# DynamoDB-compatible flavour analogous to geminidb.cassandra.large.4
# (2 vCPU / 8 GB). Adjust via -var or terraform.tfvars if your region lists a
# different code (ListFlavors on the GeminiDB DynamoDB-compatible interface).
variable "geminidb_spec_code" {
  type    = string
  default = "geminidb.dynamodb.large.4"
}

variable "geminidb_node_num" {
  description = "Cluster mode requires >= 3 nodes."
  type        = number
  default     = 3
}

variable "geminidb_storage_type" {
  type    = string
  default = "ULTRAHIGH"
}

variable "geminidb_storage_size" {
  description = "Storage (GB) per node."
  type        = number
  default     = 100
}

variable "geminidb_az" {
  description = "Single availability zone for the GeminiDB instance (Cluster mode spreads nodes internally)."
  type        = string
  default     = "cn-north-4a"
}

# ---------------------------------------------------------------------------
# APIG dedicated instance
# ---------------------------------------------------------------------------
variable "apig_instance_name" {
  type    = string
  default = "pdf-chat-apig"
}

variable "apig_edition" {
  description = "APIG dedicated instance edition."
  type        = string
  default     = "BASIC"
}

variable "apig_available_zones" {
  description = "MUST be provided; omitting it surfaces a misleading APIC.9999. Make it a variable so you can switch AZ without code changes."
  type        = list(string)
  default     = ["cn-north-4a"]
}

variable "apig_public" {
  description = "Enable a public ingress on the APIG instance so the browser SPA can call the API directly. If false the API is internal-only (verify via invoke_function)."
  type        = bool
  default     = true
}

variable "apig_ingress_bandwidth_size" {
  description = "Public ingress bandwidth (Mbps) when apig_public = true."
  type        = number
  default     = 100
}

variable "apig_ingress_bandwidth_charging_mode" {
  description = "Billing mode for public ingress bandwidth: 'bandwidth' or 'traffic'."
  type        = string
  default     = "traffic"
}

# ---------------------------------------------------------------------------
# IAM agency (FunctionGraph execution role)
# ---------------------------------------------------------------------------
variable "agency_name" {
  description = "Name of the IAM agency that the functions assume for temporary credentials."
  type        = string
  default     = "pdf-chat-fgs-agency"
}

# ---------------------------------------------------------------------------
# Networking
# ---------------------------------------------------------------------------
variable "vpc_cidr" {
  type    = string
  default = "192.168.0.0/16"
}

variable "subnet_cidr" {
  type    = string
  default = "192.168.1.0/24"
}
