import streamlit as st
from streamlit_chat import message
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
#from langchain_openai import OpenAIEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
#from langchain.chat_models import ChatOpenAI
from htmlTemplates import css, bot_template, user_template
import os
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from langchain.schema import Document
import pickle, shutil
import json
from datetime import datetime
from vector_store import (
    create_vectorstore,
    save_vectorstore,
    load_vectorstore
)

PROJECTS_DIR = "projects"

os.makedirs(
    PROJECTS_DIR,
    exist_ok=True
)

def get_projects():
    return [
        p for p in os.listdir(PROJECTS_DIR)
        if os.path.isdir(
            os.path.join(PROJECTS_DIR, p)
        )
    ]
    
def get_project_path(project_name):
    return os.path.join(
        PROJECTS_DIR,
        project_name
    )

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader= PdfReader(pdf)
            for page in pdf_reader.pages:
                page_text=page.extract_text()
                if page_text:
                    text += page_text
                    
        except Exception as e:
            st.warning(f"Could not read {pdf.name}")
            print(e)
    return text


def get_relevant_context(query):
    project_folder = get_project_path(
        st.session_state.project_name
    )
    retriever = load_vectorstore(
        f"{project_folder}/faiss_index"
    ).as_retriever(
        search_kwargs={"k":5}
    )

    docs = retriever.invoke(query)

    ...

    retriever = load_vectorstore(f"{project_folder}/faiss_index").as_retriever(
        search_type="similarity",
        search_kwargs={"k": 8}
    )
    docs = retriever.invoke(query)

    context = "\n\n".join(
        [doc.page_content for doc in docs]
    )

    return context

def save_metadata(project_folder, project_name, num_docs, num_chunks, num_characters):
    metadata_file = (f"{project_folder}/metadata.json")
    created_at = datetime.now().isoformat()
    if os.path.exists(metadata_file):
        with open(metadata_file, "r") as f:
            old = json.load(f)
            created_at = old.get("created_at", created_at)
    metadata = {
        "project_name": project_name,
        "num_documents": num_docs,
        "num_chunks": num_chunks,
        "num_characters": num_characters,
        "created_at": created_at,
        "last_updated": datetime.now().isoformat()
    }
    with open(
        metadata_file,
        "w"
    ) as f:
        json.dump(
            metadata,
            f,
            indent=4
        )
        
def load_metadata(project_folder):
    metadata_file = (
        f"{project_folder}/metadata.json"
    )
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
                return json.load(f)
        except Exception as e:
            print(e)
            return None
        
def get_document_chunks(pdf_docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            ""
        ]
    )
    documents = []
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf)

        except Exception:
            continue

        for page_num, page in enumerate(pdf_reader.pages):

            try:
                page_text = page.extract_text()

            except Exception:
                continue

            if not page_text:
                continue

            chunks = text_splitter.split_text(
                page_text
            )

            for chunk in chunks:

                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={
                            "source": pdf.name,
                            "page": page_num + 1
                        }
                    )
                )

    return documents

    
    
def format_documents_for_llm():
    formatted_text = ""

    for doc in st.session_state.documents:

        formatted_text += (
            f"[Source: {doc.metadata['source']} | "
            f"Page {doc.metadata['page']}]\n\n"
            f"{doc.page_content}\n\n"
        )

    return formatted_text

def get_conversation_chain(vectorstore):
    memory= ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="answer")
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name= "llama-3.1-8b-instant",
        streaming=True
    )
    #llm= HuggingFaceHub(repo_id="tencent/KaLM-Chat-Gemma3-12B-2511", model_kwargs={"temperature": 0.7, "max_length": 2048})
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever= vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 10}
        ),
        memory=memory,
        return_source_documents=True
    )
    return conversation_chain

def generate_document(prompt):
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant",
        streaming=True
    )
    placeholder = st.empty()
    full_response = ""

    for chunk in llm.stream(prompt):

        if hasattr(chunk, "content") and chunk.content:
            full_response += chunk.content

            placeholder.markdown(
                full_response + "▌"
            )

    #placeholder.markdown(full_response)

    return full_response

def generate_document_stream(prompt):

    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant"
    )

    placeholder = st.empty()
    full_response = ""

    for chunk in llm.stream(prompt):
        full_response += chunk.content
        placeholder.markdown(full_response + "▌")

    placeholder.empty()

    return full_response

def create_pdf(text, filename):
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    story = []
    for line in text.split("\n"):
        if line.strip():
            story.append(Paragraph(line, styles["BodyText"]))
            story.append(Spacer(1, 6))
    doc.build(story)
    return filename

def handle_userinput(user_question):
    if st.session_state.conversation is None:
        st.error("Please upload and process a PDF first.")
        return
    response = st.session_state.conversation.invoke(
        {"question": user_question}
    ) 
    answer = response["answer"]
    sources = response["source_documents"]   
    st.session_state.chat_history = response["chat_history"]
    
    for i, message in enumerate(st.session_state.chat_history):
        if i % 2 == 0:
            with st.chat_message("user"):
                st.write(message.content)
        else:
            with st.chat_message("assistant"):
                st.write(message.content)

    if "source_documents" in response:

        st.markdown("### Sources")
        seen=set()

        for doc in response["source_documents"]:
            source=(
                doc.metadata["source"],
                doc.metadata["page"]
            )
            if source not in seen:
                seen.add(source)
                st.write(
                    f"📄 {doc.metadata['source']} | Page {doc.metadata['page']}"
                )
def generate_report_raw(prompt):
    llm = ChatGroq(
        groq_api_key=os.getenv("GROQ_API_KEY"),
        model_name="llama-3.1-8b-instant",
        streaming=False
    )

    return llm.invoke(prompt).content

def generate_summary():

    context = format_documents_for_llm()[:8000]

    prompt = f"""
    You are an expert document analyst.

    Create a detailed summary of the provided documents.

    Requirements:
    - Use only the provided content.
    - Do not invent information.
    - Clearly explain the main ideas.
    - Mention important findings and conclusions.
    - If multiple documents are present, summarize each separately when necessary.

    Documents:

    {context}
    """

    return generate_document(prompt)

def generate_report():

    context = format_documents_for_llm()
    prompt = """
    Return ONLY a JSON object.

    Do not explain.
    Do not add markdown.
    Do not add text before or after JSON.
    The first character must be '{'
    The last character must be '}'
    
    For every finding include:

    - source file name
    - page number

    Use ONLY sources explicitly present in the provided document context.

    Format:

    {
        "title":"",
        "introduction":"",
        "executive_summary":"",
        "key_findings":[
            {
                "topic":"",
                "description":"",
                "source":"",
                "page":""
            }
        ],
        "analysis":"",
        "recommendations":[""],
        "conclusion":""
    }

    Document:
    """ + context[:12000]

    response = generate_report_raw(prompt)

    response = response.replace("```json", "").replace("```", "")
    response = response.replace("```", "")
    start = response.find("{")
    end = response.rfind("}") + 1

    response = response[start:end]
    response = response.strip()

    try:
        report_data = json.loads(response)
        return report_data
    
    except json.JSONDecodeError:
        st.error("AI generated invalid JSON.")       
        st.code(response)
        return None

    except Exception as e:
        st.error(f"JSON Parsing Error: {e}")
        st.write(response)
        return None

def get_recent_projects():
    projects = []
    for project in get_projects():
        project_folder = get_project_path(
            project
        )
        metadata = load_metadata(
            project_folder
        )
        if metadata:

            projects.append(metadata)

    projects.sort(
        key=lambda x: x["last_updated"],
        reverse=True
    )

    return projects[:5]

def main():
    load_dotenv()
    st.set_page_config(page_title="Multi-Project RAG Platform", page_icon="📁", layout="centered")
    st.write(css, unsafe_allow_html=True)
    
    if "summary" not in st.session_state:
        st.session_state.summary = None

    if "report" not in st.session_state:
        st.session_state.report = None

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    
    if "ready" not in st.session_state:
        st.session_state.ready = False
        
    if "project_name" not in st.session_state:
        st.session_state.project_name = ""
            
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
        
    if "generated_document" not in st.session_state:
        st.session_state.generated_document = None
        
    if "raw_text" not in st.session_state:
        st.session_state.raw_text = ""
        
    if "report_pdf" not in st.session_state:
        st.session_state.report_pdf = None
    
    if "pdf_name" not in st.session_state:
        st.session_state.pdf_name = ""
    
    disabled = st.session_state.conversation is None
       
    if os.path.exists("raw_text.txt"):
        with open("raw_text.txt", "r", encoding="utf-8") as f:
            st.session_state.raw_text = f.read()
    if (os.path.exists("documents.pkl")):
        with open("documents.pkl", "rb") as f:
            st.session_state.documents = pickle.load(f)
    
           
    if "documents" not in st.session_state:
        st.session_state.documents = []

    if (
        "project_name" in st.session_state
        and st.session_state.project_name
        and st.session_state.conversation is None
    ):
        project_folder = get_project_path(
            st.session_state.project_name
        )
        faiss_path = f"{project_folder}/faiss_index"
        if os.path.exists(faiss_path):

            try:
                vectorstore = load_vectorstore(
                    faiss_path
                )
                st.session_state.conversation = (
                    get_conversation_chain(
                        vectorstore
                    )
                )

            except Exception as e:
                st.warning("Knowledge base missing. Please reprocess PDFs.")
                print(e)

    st.header("Chat with multiple PDFs :books:")
    if st.session_state.ready:
        st.success("🤖 AI Assistant Ready")
    if "pdf_name" in st.session_state:
        st.info(f"📄 Loaded: {st.session_state.pdf_name}")
        
    if "num_docs" in st.session_state:
        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Documents",
            st.session_state.num_docs
        )

        col2.metric(
            "Chunks",
            st.session_state.num_chunks
        )

        col3.metric(
            "Characters",
            f"{st.session_state.num_chars:,}"
        )
    mode = st.sidebar.selectbox(
        "AI Mode",
        [
            "Chat",
            "Summary",
            "Report",
            "Q&A",
            "Simplify Document",
            "Expand Section",
            "Bullet Points"
        ]
    )
    if mode == "Chat":
        chat_container = st.container(height=400)
        
        with chat_container:
            if st.session_state.chat_history:
                for i, message in enumerate(st.session_state.chat_history):

                    if i % 2 == 0:
                        with st.chat_message("user"):
                            st.write(message.content)

                    else:
                        with st.chat_message("assistant"):
                            st.write(message.content)
                            
        with st.form("chat_form", clear_on_submit=True):
            user_question = st.text_input(
                "Ask a question about your documents:",
                disabled=disabled
            )
            submitted = st.form_submit_button("Send")

        if submitted and user_question:
            # with st.chat_message("assistant"):
            #     with st.spinner("Thinking..."):
            handle_userinput(user_question)
            st.rerun()
        
    elif mode == "Summary":
        if not st.session_state.raw_text:
            st.warning("Please upload and process a PDF first.")
        elif st.button("Generate Summary", disabled=disabled):
            st.markdown("---")
            st.subheader("Summary")
            summary = generate_summary()
            #st.session_state.summary = summary
            # if st.session_state.summary:
            #     st.subheader("Summary")
            #     st.markdown(st.session_state.summary)
            base_name = (
                st.session_state.get("pdf_name")
                or st.session_state.get("project_name")
                or "document"
            )
            pdf_name = f"{base_name}_summary.pdf"
            create_pdf(summary, pdf_name)
            st.session_state.summary_pdf = pdf_name
            with open(st.session_state.summary_pdf, "rb") as f:
                st.download_button(
                    label="Download Summary PDF",
                    data=f,
                    file_name=st.session_state.summary_pdf,
                    mime="application/pdf",
                    key="summary_download"
                )
           
        # if st.session_state.summary:
        #     st.markdown("---")
        #     st.subheader("Summary")
        #     st.markdown(st.session_state.summary)
            
        #     with open(st.session_state.summary_pdf, "rb") as f:
        #         st.download_button(
        #             label="Download Summary PDF",
        #             data=f,
        #             file_name=st.session_state.summary_pdf,
        #             mime="application/pdf",
        #             key="summary_download"
        #         )
        
    elif mode == "Report":
        if not st.session_state.raw_text:
            st.warning("Please upload and process a PDF first.")
        #st.write("Raw text length:", len(st.session_state.raw_text))
        elif st.button("Generate Report", disabled=disabled):
            with st.spinner("Generating report"):
                report_data = generate_report()
                
            if report_data:
                st.session_state.report=report_data
                st.rerun()
                
            if report_data is None:
                st.stop()
            st.session_state.report = report_data
            findings_text = "\n\n".join(
                [
                    f"{f['topic']}\n"
                    f"{f['description']}\n"
                    f"Source: {f['source']} | Page {f['page']}"
                    for f in report_data["key_findings"]
                ]
            )
            recommendations_text = "\n".join(
                [f"- {r}" for r in report_data["recommendations"]]
            )
            # if st.session_state.report:
            #     #st.subheader("Report")
            #     st.markdown(st.session_state.report)
            base_name = (
                st.session_state.get("pdf_name")
                or st.session_state.get("project_name")
                or "document"
            )
            pdf_name = f"{base_name}_report.pdf"
            report_text = f"""
            {report_data['title']}

            Introduction
            {report_data['introduction']}

            Key Findings
            {findings_text}

            Analysis
            {report_data['analysis']}

            Recommendations
            {recommendations_text}

            Conclusion
            {report_data['conclusion']}
            """
            create_pdf(report_text, pdf_name)
            
            st.session_state.report_pdf = pdf_name
            # with open(pdf_name, "rb") as pdf_file:
            #     st.download_button(
            #         label="Download Report PDF",
            #         data=pdf_file,
            #         file_name=pdf_name,
            #         mime="application/pdf"
            #     )
        if st.session_state.report:
            st.markdown("---")
            st.subheader("Report")
            report = st.session_state.report

            st.title(report["title"])

            st.header("Introduction")
            st.write(report["introduction"])

            st.header("Key Findings")
            for finding in report["key_findings"]:
                st.subheader(finding["topic"])
                st.write(finding["description"])
                st.caption(
                    f"📄 {finding['source']} | Page {finding['page']}"
                )

            st.header("Analysis")
            st.write(report["analysis"])

            st.header("Recommendations")
            for rec in report["recommendations"]:
                st.markdown(f"- {rec}")

            st.header("Conclusion")
            st.write(report["conclusion"])

            if st.session_state.report_pdf and os.path.exists(st.session_state.report_pdf):
                with open(st.session_state.report_pdf, "rb") as f:
                    st.download_button(
                        label="Download Report PDF",
                        data=f,
                        file_name=st.session_state.report_pdf,
                        mime="application/pdf",
                        key="report_download"
                    )
    
    elif mode == "Q&A":
        question = st.text_input(
            "Ask a question about the document"
        )
        project_folder = get_project_path(st.session_state.project_name)
        if st.button("Answer Question"):
            docs = load_vectorstore(
                f"{project_folder}/faiss_index").similarity_search(
                    question,
                    k=6
                )
            context = "\n\n".join(
                [doc.page_content for doc in docs]
            )
            prompt = f"""
            Use only the document content.
            Question:
            {question}
            Context:
            {context}
            Answer:
            """
            answer = generate_document_stream(prompt)
            st.write(answer)
            
            
    elif mode == "Simplify Document":
        
        if st.button("Simplify Document", disabled=disabled):
            context = get_relevant_context(
                "Summarize the most important information"
            )
            prompt = f"""
            Rewrite this document in simple language.

            Document:
            
            {context}
            """
            result = generate_document_stream(prompt)
            st.markdown(result)
            
    elif mode == "Expand Section":
        if st.button("Expand Content", disabled=disabled):
            context = get_relevant_context(
                "Main concepts discussed"
            )
            prompt = f"""
            Expand the following content.

            Add examples,
            explanations,
            details.

            Content:

            {context}
            """
            result = generate_document_stream(prompt)
            st.markdown(result)
        
    elif mode == "Bullet Points":
        if st.button("Generate Bullet Points", disabled=disabled):
            context = get_relevant_context(
                "Most important points in the document"
            )
            prompt = f"""
            Convert this doument into concise bullet points.

            Document:

            {context}
            """
            result = generate_document_stream(prompt)
            st.markdown(result)
        
    # st.write(type(st.session_state.generated_document))
    # st.write(st.session_state.generated_document) 
    if st.session_state.generated_document:
        st.markdown("---")
        st.subheader("Generated Document")
        st.markdown(st.session_state.generated_document)         
    if (
        st.session_state.generated_document is not None
        and st.session_state.generated_document != ""
    ):
        st.download_button(
            label="Download Document",
            data=st.session_state.generated_document,
            file_name="generated_document.md",
            mime="text/markdown"
        )

    with st.sidebar:
        st.title("🚀 AI Workspace")
        st.caption(
            "Manage multiple knowledge bases"
        )
        st.divider()
        # --------- Create Project ---------
        new_project = st.text_input(
            "Create New Project"
        )
        if st.button("➕ Create Project"):
            if new_project.strip():
                project_path = get_project_path(
                    new_project
                )
                os.makedirs(
                    project_path,
                    exist_ok=True
                )
                st.session_state.project_name = (
                    new_project
                )
                st.success(
                    f"Created project: {new_project}"
                )
                st.rerun()


        # ---------------------------
        # Open Existing Project
        # ---------------------------
        project_folder=None
        projects = get_projects()
        st.markdown("### 📂 Open Project")
        selected_project = st.selectbox(
            "Select Project",
            [""] + projects, label_visibility="collapsed",
            index=(
                projects.index(
                    st.session_state.project_name
                ) + 1
                if (
                    "project_name"
                    in st.session_state
                    and st.session_state.project_name
                    in projects
                )
                else 0
            )
        )
        if selected_project:
            st.session_state.project_name = selected_project
            if "pdf_name" not in st.session_state or not st.session_state.pdf_name:
                st.session_state.pdf_name = selected_project
            project_folder = get_project_path(
                selected_project
            )
            
            metadata = load_metadata(project_folder) 
            if metadata:
                st.markdown("---")
                st.markdown("## 📂 Active Project")
                st.markdown(f"### {metadata['project_name']}")
                c1, c2 = st.columns(2)
                c1.metric(
                    "Docs",
                    metadata["num_documents"]
                )
                c2.metric(
                    "Chunks",
                    metadata["num_chunks"]
                )
                st.metric(
                    "Characters",
                    f"{metadata.get('num_characters'):,}"
                )
                st.caption(
                    f"Created: {metadata['created_at'][:10]}"
                )
                st.caption(
                    f"Last Updated: {metadata['last_updated'][:19]}"
                )
                st.markdown("---")

            st.success(
            f"📁 Active Project: {selected_project}"
            )
            
            st.markdown("### 🕒 Recent Projects")
            recent_projects = get_recent_projects()
            for project in recent_projects:
                if st.button(
                    project["project_name"],
                    key=f"recent_{project['project_name']}",
                    use_container_width=True
                ):
                    st.session_state.project_name = (
                        project["project_name"]
                    )
                    st.rerun()
                    
            # Load project files
            raw_text_file = (
                f"{project_folder}/raw_text.txt"
            )
            documents_file = (
                f"{project_folder}/documents.pkl"
            )
            faiss_path = (
                f"{project_folder}/faiss_index"
            )
            if os.path.exists(raw_text_file):
                with open(
                    raw_text_file,
                    "r",
                    encoding="utf-8"
                ) as f:
                    st.session_state.raw_text = (
                        f.read()
                    )

            if os.path.exists(documents_file):
                try:
                    with open(
                        documents_file,
                        "rb"
                    ) as f:
                        st.session_state.documents = (
                            pickle.load(f)
                        )
                except Exception:

                    st.warning(
                        "Could not load saved documents."
                   )
            if (
                os.path.exists(faiss_path)
                and st.session_state.conversation
                is None
            ):
                vectorstore = load_vectorstore(
                    faiss_path
                )
                st.session_state.conversation = (
                    get_conversation_chain(
                        vectorstore
                    )
                )
                st.session_state.ready = True


        # ---------------------------
        # Upload PDFs
        # ---------------------------
        pdf_docs = st.file_uploader(
            "Upload PDFs",
            accept_multiple_files=True
        )
        if pdf_docs:
            st.write("### Uploaded Files")
            for pdf in pdf_docs:
                st.write(
                    f"📄 {pdf.name}"
                )

        if st.button(
         "🚀 Process Documents",
            use_container_width=True
        ):
            if not project_folder:
                st.warning(
                    "Please create or select a project first."
                )
            elif not pdf_docs:
                st.warning(
                    "Please upload PDFs first."
                )
            else:
                status = st.status(
                    "Processing...",
                    expanded=True
                )
                status.write(
                    "📄 Extracting text..."
                )
                raw_text = get_pdf_text(pdf_docs)
                if not raw_text.strip():
                    st.error("No readable text found in PDF.")
                    st.stop()
                    
                st.session_state.raw_text = (
                    raw_text
                )
                with open(
                    f"{project_folder}/raw_text.txt",
                    "w",
                    encoding="utf-8"
                ) as f:
                    f.write(raw_text)
                status.write(
                    "✂️ Creating chunks..."
                )
                documents = (
                    get_document_chunks(
                        pdf_docs
                    )
                )
                st.session_state.documents = (
                    documents
                )
                st.session_state.num_docs = (
                    len(pdf_docs)
                )
                st.session_state.num_chunks = (
                    len(documents)
                )
                st.session_state.num_chars = (
                    len(raw_text)
                )
                save_metadata(project_folder, st.session_state.project_name, len(pdf_docs), len(documents), st.session_state.num_chars)

                with open(
                    f"{project_folder}/documents.pkl",
                    "wb"
                ) as f:
                    pickle.dump(
                        documents,
                        f
                    )
                status.write(
                    "🧠 Creating embeddings..."
                )
                vectorstore = (
                    create_vectorstore(
                        documents
                    )
                )
                status.write(
                    "💾 Saving FAISS..."
                )
                save_vectorstore(
                    vectorstore,
                    f"{project_folder}/faiss_index"
                )
                status.write(
                    "🔗 Building retriever..."
                )
                st.session_state.conversation = (
                    get_conversation_chain(
                        vectorstore
                    )
                )
                st.session_state.ready = True
                status.update(
                    label="Ready ✔",
                    state="complete"
                )
                st.success(
                "    Documents processed successfully."
                )

        # ---------------------------
        # Delete Project
        # ---------------------------
        if st.button(
            "🗑 Delete Project",
            disabled=(
                "project_name"
                not in st.session_state
            ),
            use_container_width=True
        ):
            project_folder = get_project_path(
                st.session_state.project_name
            )

            shutil.rmtree(
                project_folder,
                ignore_errors=True
            )
            st.session_state.clear()
            st.rerun()

        # ---------------------------
        # Clear Session
        # ---------------------------
        if st.button(
            "🔄 Clear Session",
            use_container_width=True
        ):
            st.session_state.clear()
            st.rerun()

if __name__ == '__main__':
    main()