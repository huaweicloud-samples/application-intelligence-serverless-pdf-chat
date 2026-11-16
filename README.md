# Serverless PDF Chat - Huawei Cloud Best Practice
[中文版](README.cn.md)

[中文](README.md) | English

## Overview

Serverless PDF Chat is a serverless application that allows users to upload PDF documents and ask questions about their content using a conversational AI interface. Documents are processed with embeddings and stored for retrieval, providing accurate answers using RAG (Retrieval-Augmented Generation) technology.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Huawei Cloud                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────┐    ┌─────────┐    ┌─────────────────────────────────────┐ │
│  │ Client  │───▶│  APIG   │───▶│         FunctionGraph (8)          │ │
│  │(Browser)│    │ Gateway │    │                                     │ │
│  └────┬────┘    └────┬────┘    │  ┌────────────┐ ┌────────────┐   │ │
│       │               │           │  │ presigned  │ │  upload_   │   │ │
│       │               │           │  │   _url     │ │  trigger   │   │ │
│       │               │           │  └────────────┘ └────────────┘   │ │
│       │               │           │  ┌────────────┐ ┌────────────┐   │ │
│       │               │           │  │generate_em │ │generate_  │   │ │
│       │               │           │  │ beddings   │ │ response  │   │ │
│       │               │           │  └────────────┘ └────────────┘   │ │
│       │               │           │  ┌────────────┐ ┌────────────┐   │ │
│       │               │           │  │add_conver- │ │get_all_   │   │ │
│       │               │           │  │  sation    │ │documents  │   │ │
│       │               │           │  └────────────┘ └────────────┘   │ │
│       │               │           │  ┌────────────┐ ┌────────────┐   │ │
│       │               │           │  │get_docu-   │ │delete_    │   │ │
│       │               │           │  │   ment     │ │document   │   │ │
│       │               │           │  └────────────┘ └────────────┘   │ │
│       │               │           └─────────────────────┬─────────────┘ │
│       │               │                                 │               │
│       │               │           ┌─────────────────────┴─────────────┐ │
│       │               │           │            OBS Bucket            │ │
│       │               │           │   (pdf-chat-documents)          │ │
│       │               │           │   /functions/*.zip               │ │
│       │               │           │   /documents/*.pdf               │ │
│       │               │           │   /embeddings/*.json             │ │
│       │               │           └───────────────────────────────────┘ │
│       │               │                                                 │
│       │               │           ┌───────────────────────────────────┐ │
│       │               │           │      GeminiDB (Cassandra)        │ │
│       │               │           │   (DynamoDB-compatible)          │ │
│       │               │           │                                   │ │
│       │               │           │  conversations  messages  documents│ │
│       │               │           └───────────────────────────────────┘ │
│       │               │                                                 │
│       │               │           ┌───────────────────────────────────┐ │
│       │               │           │           MaaS LLM                │ │
│       │               │           │   (ModelArts Model As a Service) │ │
│       │               │           │                                   │ │
│       │               │           │  text-embedding-v3  deepseek-v3  │ │
│       │               │           └───────────────────────────────────┘ │
│       │               │                                                 │
│       └───────────────┴─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                    VPC (192.168.0.0/16)                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌───────────────────────────────────────────────────────────────────┐ │
│   │              Private Subnet (192.168.1.0/24)                     │ │
│   │                                                                    │ │
│   │   ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐  │ │
│   │   │  Functions  │   │  GeminiDB   │   │   NAT Gateway      │  │ │
│   │   │ (VPC-attached)│   │ (Private LB)│   │   + EIP            │  │ │
│   │   └─────────────┘   └─────────────┘   └─────────────────────┘  │ │
│   │                                                                    │ │
│   └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

- **PDF Upload**: Direct upload to OBS via pre-signed URLs
- **Automatic Embedding**: Text extraction and vector embedding generation upon upload
- **Conversational Q&A**: Multi-turn dialogue based on document content
- **Serverless Architecture**: Auto-scaling based on FunctionGraph
- **Enterprise Security**: VPC isolation, API key authentication, end-to-end encryption

## Architecture

The following Huawei Cloud services implement the required capabilities:

| Capability | Huawei Cloud Service |
|------------|----------------------|
| Object storage | OBS (Object Storage Service) |
| NoSQL document storage | GeminiDB (DynamoDB-compatible interface) |
| Serverless functions | FunctionGraph |
| API gateway | APIG |
| Large language model inference | MaaS (ModelArts Model as a Service) |
| End-user authentication | APIG application authentication |
| Static web hosting | OBS static website hosting |

## Quick Start

### Prerequisites

- Huawei Cloud account
- Terraform >= 1.5.0
- Python 3.9+

### Deployment

```bash
# 1. Clone the repository
git clone <repo-https-url> application-intelligence-serverless-pdf-chat
cd application-intelligence-serverless-pdf-chat

# 2. Configure credentials
cp infra/terraform.tfvars.example infra/terraform.tfvars
# Edit terraform.tfvars with your values

# 3. Deploy infrastructure
cd infra
terraform init
terraform apply -var-file=terraform.tfvars

# 4. Build function packages
cd ../src
pip install -r requirements.txt -t ./package
python build.py
```

See [Deployment Guide](docs/deployment-guide.md) for detailed instructions.

## Project Structure

```
application-intelligence-serverless-pdf-chat/
├── docs/                    # Architecture and deployment docs
│   ├── architecture.md
│   └── deployment-guide.md
├── src/frontend/             # Frontend application
├── infra/                   # Terraform infrastructure
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── provider.tf
│   └── terraform.tfvars.example
├── src/                     # Function source code
│   ├── common/              # Shared modules
│   ├── add_conversation/
│   ├── delete_document/
│   ├── generate_embeddings/
│   ├── generate_presigned_url/
│   ├── generate_response/
│   ├── get_all_documents/
│   ├── get_document/
│   └── upload_trigger/
├── README.md
└── README-en.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | /documents/presigned | Get PDF upload pre-signed URL |
| POST | /documents | Create document record |
| GET | /documents | List all documents |
| GET | /documents/{id} | Get single document |
| DELETE | /documents/{id} | Delete document |
| POST | /chat | Send chat message |
| GET | /conversations | List all conversations |
| POST | /conversations | Create new conversation |

## License

This project is licensed under MIT-0 License.
