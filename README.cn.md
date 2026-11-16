# Serverless PDF Chat - 华为云最佳实践
[English](README.md)

[English](README-en.md) | 中文

## 项目简介

Serverless PDF Chat 是一个基于大语言模型的无服务器应用，允许用户上传 PDF 文档，通过对话方式询问关于文档内容的问题。文档经过向量化处理后存储，系统使用 RAG（检索增强生成）技术提供准确的问答服务。

## 架构图

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
│   │   ┌─────────────┐   ┌─────────────┐   ┌─────────────────────┐    │ │
│   │   │  Functions  │   │  GeminiDB   │   │   NAT Gateway      │    │ │
│   │   │ (VPC-attached)│   │ (Private LB)│   │   + EIP            │    │ │
│   │   └─────────────┘   └─────────────┘   └─────────────────────┘    │ │
│   │                                                                    │ │
│   └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## 功能特性

- **PDF 文档上传**：通过预签名 URL 直接上传到 OBS
- **自动向量化**：文档上传后自动提取文本并生成向量嵌入
- **对话式问答**：基于文档内容进行问答，支持多轮对话
- **无服务器架构**：基于 FunctionGraph，按需自动扩缩容
- **企业级安全**：VPC 隔离、API 密钥认证、端到端加密

## 架构概览

本实践由以下华为云服务实现所需能力：

| 能力 | 华为云服务 |
|---------|-----------|
| 对象存储 | OBS 对象存储 |
| NoSQL 文档存储 | GeminiDB 数据库（DynamoDB 兼容协议接口） |
| 无服务器函数 | FunctionGraph 函数计算 |
| API 网关 | APIG API 网关 |
| 大模型推理 | MaaS 模型服务 |
| 终端用户认证 | APIG App 认证 |
| 静态站点托管 | OBS 静态网站托管 |

## 快速开始

### 前置要求

- 华为云账号
- Terraform >= 1.5.0
- Python 3.9+

### 部署步骤

```bash
# 1. 克隆仓库
git clone <repo-https-url> application-intelligence-serverless-pdf-chat
cd application-intelligence-serverless-pdf-chat

# 2. 配置凭据
cp infra/terraform.tfvars.example infra/terraform.tfvars
# 编辑 terraform.tfvars 填入您的配置

# 3. 部署基础设施
cd infra
terraform init
terraform apply -var-file=terraform.tfvars

# 4. 构建函数包
cd ../src
pip install -r requirements.txt -t ./package
python build.py
```

详细部署说明请参考 [部署指南](docs/deployment-guide.md)。

## 项目结构

```
application-intelligence-serverless-pdf-chat/
├── docs/                    # 架构和部署文档
│   ├── architecture.md       # 架构文档
│   └── deployment-guide.md   # 部署指南
├── src/frontend/             # 前端应用
│   ├── index.html
│   ├── app.js
│   └── styles.css
├── infra/                   # Terraform 基础设施
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── provider.tf
│   └── terraform.tfvars.example
├── src/                     # 函数源代码
│   ├── common/              # 共享模块
│   │   ├── config.py
│   │   ├── obs.py
│   │   ├── dynamodb.py
│   │   ├── maas.py
│   │   └── response.py
│   ├── add_conversation/    # 添加对话
│   ├── delete_document/     # 删除文档
│   ├── generate_embeddings/ # 生成向量
│   ├── generate_presigned_url/ # 生成上传URL
│   ├── generate_response/  # 生成回答
│   ├── get_all_documents/  # 获取文档列表
│   ├── get_document/       # 获取文档
│   └── upload_trigger/     # 上传触发器
├── README.md
└── README-en.md
```

## API 接口

| 方法 | 路径 | 描述 |
|-----|------|------|
| POST | /documents/presigned | 获取 PDF 上传预签名 URL |
| POST | /documents | 创建文档记录 |
| GET | /documents | 获取所有文档 |
| GET | /documents/{id} | 获取单个文档 |
| DELETE | /documents/{id} | 删除文档 |
| POST | /chat | 发送聊天消息 |
| GET | /conversations | 获取所有对话 |
| POST | /conversations | 创建新对话 |

## 许可证

本项目基于 MIT-0 许可证开源。
