# Deployment Guide

## Prerequisites

- Huawei Cloud account with valid credentials
- Access Key and Secret Key with sufficient permissions
- Terraform >= 1.5.0 installed
- Python 3.9+ for building function packages

## Configuration

### 1. Clone the Repository

```bash
git clone <repo-https-url> application-intelligence-serverless-pdf-chat
cd application-intelligence-serverless-pdf-chat
```

### 2. Configure Credentials

Create `infra/terraform.tfvars` based on the example:

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars
```

Edit `terraform.tfvars` and fill in your values:

```hcl
region               = "cn-north-4"
obs_bucket_name      = "your-unique-bucket-name"
geminidb_password    = "YourSecurePassword123!"
maas_api_key         = "your-maas-api-key"
```

### 3. Deploy Infrastructure

```bash
cd infra
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

### 4. Build and Upload Functions

```bash
cd ../src
pip install -r requirements.txt -t ./package
python build.py
```

The build script will:
- Package each function with its dependencies
- Upload ZIP files to OBS

### 5. Deploy Frontend (Optional)

Deploy the frontend to OBS static website hosting:

```bash
cd ../src/frontend
# Edit config.js with your APIG endpoint and app code
# Upload to OBS website bucket
```

## Configuration Reference

### Variables

| Variable | Description | Default |
|----------|-------------|---------|
| region | Huawei Cloud region | cn-north-4 |
| obs_bucket_name | OBS bucket for documents | (required) |
| geminidb_password | GeminiDB admin password | (required) |
| maas_api_key | MaaS API key for LLM access | (required) |
| maas_endpoint | MaaS API endpoint | https://api.modelarts-maas.com/openai/v1 |
| maas_embed_model | Embedding model name | text-embedding-v3 |
| maas_chat_model | Chat model name | deepseek-v3 |
| geminidb_instance_name | GeminiDB instance name | pdf-chat-geminidb |
| geminidb_spec_code | Instance规格 | geminidb.dynamodb.large.4 |
| geminidb_node_num | 节点数 | 3 |
| geminidb_az | 可用区 | cn-north-4a |
| apig_instance_name | APIG实例名 | pdf-chat-apig |
| agency_name | 委托名 | pdf-chat-agency |
| vpc_cidr | VPC网段 | 192.168.0.0/16 |
| subnet_cidr | 子网网段 | 192.168.1.0/24 |

## Outputs

After deployment, Terraform will output:

- `api_endpoint`: APIG API base URL
- `apig_app_code`: App code for authentication
- `obs_bucket`: OBS bucket name
- `geminidb_endpoint`: GeminiDB connection endpoint
- `function_urns`: List of FunctionGraph URNs

## Testing

### 1. Get API Endpoint and App Code

```bash
terraform output api_endpoint
terraform output apig_app_code
```

### 2. Test Document Upload

```bash
API_ENDPOINT="https://<group_id>.apic.cn-north-4.huaweicloudapis.com/release"
APP_CODE="<your_app_code>"

# Get presigned URL
curl -X POST "$API_ENDPOINT/documents/presigned" \
  -H "X-App-Key: $APP_CODE" \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.pdf"}'
```

### 3. Test Chat

```bash
# Send a question
curl -X POST "$API_ENDPOINT/chat" \
  -H "X-App-Key: $APP_CODE" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is this document about?",
    "conversation_id": "new"
  }'
```

## Cleanup

```bash
cd infra
terraform destroy -var-file=terraform.tfvars
```

**Note**: Some resources (like OBS buckets) may require manual deletion if they contain data.

## Troubleshooting

### Function Invocation Fails

1. Check FunctionGraph logs in LTS
2. Verify agency has correct permissions (OBS, LTS, VPC)
3. Check VPC configuration (functions need to reach GeminiDB)

### APIG Returns 401

1. Verify App Code is correct
2. Check Application is authorized to the API

### GeminiDB Connection Fails

1. Verify VPC and subnet configuration
2. Check security group allows port 8000 (DynamoDB 兼容协议)
3. Verify credentials in function environment

## Deployed Resources

The deployment creates the following cloud resources. Refer to the official
service documentation for the applicable charges.

| Resource | Configuration | Purpose |
|----------|---------------|---------|
| APIG (Dedicated) | Basic edition | Public entry point for upload and chat APIs |
| EIP + Bandwidth | 5 Mbps | Public access for the frontend and API calls |
| OBS | Storage + requests | Document and frontend static hosting |
| GeminiDB | 3 x large.4 + 100 GB | Document metadata and vector storage |
| FunctionGraph | Pay per invocation | Upload, embedding, and chat handlers |
| NAT Gateway | Small | Outbound access from the VPC |

> **Resource management**: The `geminidb_node_num`, `geminidb_spec_code`, and
> `apig_available_zones` variables let you scale the deployment down for
> development or test environments. Check the service documentation before
> changing the configuration.
