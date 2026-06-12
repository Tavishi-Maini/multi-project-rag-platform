from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )


def create_vectorstore(documents):
    embeddings = get_embeddings()
    return FAISS.from_documents(
        documents=documents,
        embedding=embeddings
    )


def save_vectorstore(vectorstore, path):
    vectorstore.save_local(path)


def load_vectorstore(path):
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    return FAISS.load_local(
        path,
        embeddings,
        allow_dangerous_deserialization=True
    )