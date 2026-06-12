# AI Document Generator

A multi-project AI-powered document analysis platform built with Streamlit, LangChain, FAISS, and Groq.

## Features

* Multi-project workspace
* PDF ingestion and processing
* FAISS vector search
* Conversational document Q&A
* AI-generated summaries
* AI-generated reports
* Project dashboard
* Source attribution
* PDF export

## Tech Stack

* Python
* Streamlit
* LangChain
* FAISS
* HuggingFace Embeddings
* Groq LLM

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
GROQ_API_KEY=your_key_here
```

Run:

```bash
streamlit run app.py
```

## Architecture

projects/
├── Project_A/
│ ├── faiss_index/
│ ├── documents.pkl
│ ├── raw_text.txt
│ └── metadata.json
├── Project_B/
└── Project_C/
