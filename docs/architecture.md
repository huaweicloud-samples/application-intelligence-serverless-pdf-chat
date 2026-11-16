# Architecture

## Overview

Serverless PDF Chat is a multi-function RAG (Retrieval-Augmented Generation) application that enables users to upload PDF documents, have them automatically processed with embeddings generated, and then query the documents using a conversational AI interface.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Huawei Cloud                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────────────────────────┐  │
│  │   Client    │───▶│    APIG     │───▶│     FunctionGraph (FGS)      │  │
│  │  (Browser)  │    │  Gateway    │    │                              │  │
│  └─────────────┘    └──────┬──────┘    │  ┌────────────────────────┐ │  │
│                             │           │  │ generate_presigned_url │ │  │
│                             │           │  │ upload_trigger         │ │  │
│                             │           │  │ generate_embeddings    │ │  │
│                             │           │  │ generate_response      │ │  │
│                             │           │  │ add_conversation       │ │  │
│                             │           │  │ get_all_documents      │ │  │
│                             │           │  │ get_document          │ │  │
│                             │           │  │ delete_document        │ │  │
│                             │           │  └────────────────────────┘ │  │
│                             │           └──────────────┬───────────────┘  │
│                             │                          │                   │
│                             │           ┌──────────────┴───────────────┐  │
│                             │           │         OBS Bucket           │  │
│                             │           │   (pdf-chat-documents)       │  │
│                             │           │   /functions/*.zip          │  │
│                             │           │   /documents/*.pdf          │  │
│                             │           │   /embeddings/*.json        │  │
│                             │           └────────────────────────────┘  │
│                             │                                              │
│                             │    ┌────────────────────────────┐         │
│                             │    │      GeminiDB (Cassandra)  │         │
│                             │    │   (DynamoDB-compatible)    │         │
│                             │    │                            │         │
│                             │    │  conversations:            │         │
│                             │    │    - id, user_id, title,  │         │
│                             │    │      created_at            │         │
│                             │    │  messages:                │         │
│                             │    │    - id, conversation_id, │         │
│                             │    │      role, content,        │         │
│                             │    │      document_id, created_at │
│                             │    │  documents:               │         │
│                             │    │    - id, key, name,       │         │
│                             │    │      status, created_at    │         │
│                             │    └────────────────────────────┘         │
│                             │                                              │
│                             │    ┌────────────────────────────┐         │
│                             │    │         MaaS LLM           │         │
│                             │    │  (ModelArts Model As a     │         │
│                             │    │   Service)                │         │
│                             │    │                            │         │
│                             │    │  - text-embedding-v3      │         │
│                             │    │  - deepseek-v3            │         │
│                             │    └────────────────────────────┘         │
│                             │                                              │
└─────────────────────────────┴──────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                           VPC (192.168.0.0/16)                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Private Subnet (192.168.1.0/24)                  │   │
│  │                                                                       │   │
│  │   ┌─────────────┐   ┌────────────────┐   ┌────────────────────┐    │   │
│  │   │  Functions  │   │   GeminiDB     │   │    NAT Gateway     │    │   │
│  │   │  (VPC-attached)│   │   (Private LB) │   │    + EIP          │    │   │
│  │   └─────────────┘   └────────────────┘   └────────────────────┘    │   │
│  │                                                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Mapping

| Capability | Huawei Cloud Component | Notes |
|--------------|---------------------|-------|
| Object storage | OBS | Object storage for PDFs and function code |
| NoSQL document storage | GeminiDB (DynamoDB-compatible) | NoSQL document/message storage |
| Serverless compute | FunctionGraph (8 functions) | Serverless compute |
| API gateway | APIG | REST API with App authentication |
| LLM and embedding | MaaS (ModelArts) | LLM and embedding endpoints |
| App authentication | APIG Application + AppCode | API authentication |
| Frontend hosting | OBS Static Website + CDN | Frontend hosting |

## Data Flow

### 1. Document Upload
1. Client calls `POST /documents/presigned` → APIG → `generate_presigned_url`
2. Client uploads PDF directly to OBS using presigned URL
3. OBS triggers `upload_trigger` function (OBS Event)
4. `upload_trigger` stores document metadata to GeminiDB (status: processing)

### 2. Embedding Generation
1. `upload_trigger` invokes `generate_embeddings` asynchronously
2. `generate_embeddings` downloads PDF from OBS, extracts text
3. Chunks text, calls MaaS `text-embedding-v3` for each chunk
4. Stores embeddings to OBS as JSON files

### 3. Question Answering
1. Client calls `POST /chat` → APIG → `generate_response`
2. `generate_response` retrieves conversation history from GeminiDB
3. Queries embeddings from OBS, finds relevant chunks using cosine similarity
4. Calls MaaS `deepseek-v3` with context + question
5. Stores response to GeminiDB, returns to client

## Security

- **API Authentication**: APIG Application + AppCode (X-App-Key header)
- **Data at Rest**: OBS private bucket + bucket policy limiting access
- **Data in Transit**: All endpoints use HTTPS
- **Function Access**: Functions use agency (op_svc_cff) with OBS/LTS/VPC roles
- **VPC Isolation**: Functions in private subnet, only NAT gateway provides egress

## Scaling

- **FunctionGraph**: Auto-scales to 0, scales up based on invocation
- **GeminiDB**: 3-node cluster (configurable), auto scaling storage
- **OBS**: Infinite scaling, pay per use
- **APIG**: Dedicated instance with auto-scaling
