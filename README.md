# 🧠 KnowledgeHub AI

A Multi-Project Document Intelligence Platform built using Retrieval-Augmented Generation (RAG).

## Overview

KnowledgeHub AI enables users to create multiple independent knowledge bases from PDF documents and interact with them using natural language. The platform supports semantic search, conversational question answering, AI-generated summaries, and automated report generation.

Unlike traditional "Chat with PDF" applications, KnowledgeHub AI organizes documents into separate projects, allowing users to manage multiple domains of knowledge simultaneously.

---

## Problem Statement

Professionals, researchers, and students often work with large collections of documents spread across different topics. Finding relevant information manually is time-consuming and inefficient.

KnowledgeHub AI solves this problem by:

* Converting documents into searchable vector embeddings
* Organizing documents into project-specific workspaces
* Providing conversational access to information
* Generating summaries and reports automatically

---

## Features

### 📂 Multi-Project Workspace

* Create and manage multiple projects
* Independent knowledge bases for each project
* Project metadata and dashboard

### 📄 Multi-PDF Ingestion

* Upload multiple PDF files
* Automatic text extraction
* Intelligent chunking and preprocessing

### 🔍 Conversational RAG

* Retrieval-Augmented Generation pipeline
* Semantic search using vector embeddings
* Context-aware question answering

### 📝 Summary Generation

* Generate concise document summaries
* Extract key findings automatically

### 📊 Report Generation

* AI-generated structured reports
* Executive summaries
* Recommendations and conclusions

### 📚 Source Attribution

* Answers grounded in retrieved document chunks
* Transparent context retrieval

### ⚡ Streaming Responses

* Real-time response generation
* Improved user experience

---

## Tech Stack

### Frontend

* Streamlit

### LLM & AI

* Groq LLM
* LangChain

### Vector Database

* FAISS

### Embeddings

* HuggingFace Sentence Transformers

### Data Processing

* PyPDF2
* LangChain Text Splitters

### Deployment

* Streamlit Community Cloud
* GitHub

---

## Architecture

```text
PDF Documents
      │
      ▼
Text Extraction
      │
      ▼
Document Chunking
      │
      ▼
HuggingFace Embeddings
      │
      ▼
FAISS Vector Store
      │
      ▼
Retriever
      │
      ▼
Groq LLM
      │
      ▼
┌─────────────────────┐
│ Conversational Chat │
│ Summary Generation  │
│ Report Generation   │
└─────────────────────┘
```
---

## Project Structure

```text
projects/
│
├── Project_A/
│   ├── faiss_index/
│   ├── documents.pkl
│   ├── raw_text.txt
│   └── metadata.json
│
├── Project_B/
│   ├── faiss_index/
│   ├── documents.pkl
│   ├── raw_text.txt
│   └── metadata.json
│
└── Project_C/
```

---

## Metadata Tracking

Each project stores:

```json
{
  "project_name": "Research Papers",
  "num_documents": 5,
  "num_chunks": 120,
  "num_characters": 85432,
  "created_at": "...",
  "last_updated": "..."
}
```

---

## Deployment

The application is deployed on Streamlit Community Cloud.

Environment variables:

```text
GROQ_API_KEY
```

Store secrets securely using Streamlit Secrets and never commit API keys to the repository.

---

## Future Improvements

* User authentication
* Project sharing and collaboration
* Chat history persistence
* PostgreSQL metadata storage
* Cloud object storage for documents
* OCR support for scanned PDFs
* Citation-aware answers
* Agentic document workflows

---

## Author

Tavishi Maini

IIT Kanpur

Machine Learning | Data Science | Software Development
