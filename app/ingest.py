import os
import glob
from langchain_community.document_loaders import TextLoader, PyPDFLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions
from app.config import DATA_DIR, EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP

def load_documents():
    docs = []
    for ext in ("*.txt", "*.pdf", "*.md"):
        for path in glob.glob(os.path.join(DATA_DIR, ext)):
            print(f"Loading: {path}")
            if ext == ".pdf":
                loader = PyPDFLoader(path)
            elif ext == ".md":
                loader = UnstructuredMarkdownLoader(path)
            else:
                loader = TextLoader(path, encoding="utf-8")
            docs.extend(loader.load())
    print(f"✅ Loaded {len(docs)} raw documents from {DATA_DIR}")
    return docs

def chunk_documents(docs, chunk_size=CHUNK_SIZE):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_splitter.split_documents(docs)
    print(f"✅ Created {len(chunks)} chunks")
    return chunks

def build_or_get_collection(persist_dir="data/chroma_db"):
    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
    client = chromadb.PersistentClient(path=persist_dir)
    collection = client.get_or_create_collection(
        name="northwind_docs",
        embedding_function=embedding_fn
    )
    return collection

def ingest():
    docs = load_documents()
    chunks = chunk_documents(docs)
    collection = build_or_get_collection()
    # Clear existing if any (so we have a clean baseline)
    try:
        all_ids = collection.get()["ids"]
        if all_ids:
            collection.delete(ids=all_ids)
            print("🧹 Cleared existing Chroma collection")
    except:
        pass
    texts = [chunk.page_content for chunk in chunks]
    metadatas = [{"source": chunk.metadata.get("source", "unknown")} for chunk in chunks]
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(documents=texts, metadatas=metadatas, ids=ids)
    print(f"✅ Stored {len(chunks)} chunks in Chroma at data/chroma_db")

if __name__ == "__main__":
    ingest()