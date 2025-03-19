from pydantic import BaseModel, Field
from langchain_community.document_loaders import WebBaseLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

from shared import State   
from logger import logging

embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# -----Log Report-----
logger1 = logging.getLogger('TOOL_INFO')
logger1.setLevel(logging.DEBUG) 

# ----------------TOOLS-----------------
def Webloader(state: State):
    try:
        text_contents = []   # For handling mutiple urls
        for url in state['url']:
            data = WebBaseLoader(url)
            web_data = data.load()

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=450, chunk_overlap=100)
            text_splitter_web = text_splitter.split_documents(web_data)

            vector_store = FAISS.from_documents(documents=text_splitter_web, embedding=embedding_function)
            retriever = vector_store.as_retriever()

            # Extract text content from the retriever
            text_content = "\n".join([doc.page_content for doc in retriever.get_all_documents()])
            text_contents.append(text_content)
        logger1.info("Data Extracted - URL")
        combined_text_content = ','.join(text_contents)
        return {'text_content': combined_text_content}
    except Exception as e:
        logger1.error(f'Webloader: {e}')

def document_load(state: State):
    try:
        text_contents = []
        for uploaded_file in state['uploaded_file']:
            with open("temp_resume.pdf", "wb") as f:
                f.write(uploaded_file.getvalue())
            
            loader = PyPDFLoader("temp_resume.pdf")
            docs = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=120)
            docs = text_splitter.split_documents(docs)

            vectorstore = FAISS.from_documents(documents=docs, embedding=embedding_function)
            retriever = vectorstore.as_retriever()

            # Extract text content from the retriever
            text_content = "\n".join([doc.page_content for doc in retriever.get_all_documents()])
            text_contents.append(text_content)
        logger1.info("Data Extracted - URL")
        combined_text_content = ','.join(text_contents)
        return {'text_content': combined_text_content}
    except Exception as e:
        logger1.error(f'Docloader: {e}')