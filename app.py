# streamlit_app.py

import streamlit as st
import nltk
import numpy as np
import faiss
from bs4 import BeautifulSoup
import google.generativeai as genai

nltk.download("punkt")
from nltk.tokenize import sent_tokenize

# --- Gemini API Key ---
GEMINI_API_KEY = "AIzaSyBhq6qGeBhGpYdE1kNeXE7wGZj2Sz4S30A"  # Replace with your real key
genai.configure(api_key=GEMINI_API_KEY)

# === Load and Clean Text ===
def load_and_clean_text(text):
    return BeautifulSoup(text, "html.parser").get_text()

# === Chunk Text ===
def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    sentences = sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        if current_len + len(sentence) > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-(chunk_overlap // 2):]
            current_len = sum(len(s) for s in current_chunk)
        current_chunk.append(sentence)
        current_len += len(sentence)

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

# === Embed Text ===
def get_google_embeddings(chunks):
    embeddings = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        response = genai.embed_content(
            model="models/embedding-001",
            content=chunk,
            task_type="retrieval_document"
        )
        embeddings.append(response["embedding"])
    return np.array(embeddings).astype("float32")

# === Build FAISS Index ===
def build_faiss_index(embeddings):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

# === Embed Query ===
def embed_query(query):
    response = genai.embed_content(
        model="models/embedding-001",
        content=query,
        task_type="retrieval_query"
    )
    return np.array([response["embedding"]]).astype("float32")

# === Retrieve Chunks ===
def retrieve_chunks(query_embedding, faiss_index, chunks, top_k=5):
    distances, indices = faiss_index.search(query_embedding, top_k)
    return [chunks[i] for i in indices[0] if i < len(chunks)]

# === Ask Gemini ===
def ask_gemini(question, context_chunks):
    model = genai.GenerativeModel("gemini-1.5-flash")
    context = "\n\n".join(context_chunks)
    prompt = f"""
You are an assistant for question-answering tasks.
Use the following retrieved context to answer the question.

Context:
{context}

Question:
{question}

Answer in 3 sentences or fewer.
"""
    response = model.generate_content(prompt)
    return response.text.strip()

# === Streamlit UI ===
st.set_page_config(page_title="Loan RAG QA App", page_icon="💬")
st.title("🔍 Loan Q&A Assistant (Gemini + FAISS)")

uploaded_file = st.file_uploader("Upload a cleaned `.txt` file", type="txt")
question = st.text_input("Ask your loan-related question:")

if uploaded_file and question.strip():
    with st.spinner("Processing..."):
        raw_text = uploaded_file.read().decode("utf-8")
        clean_text = load_and_clean_text(raw_text)
        chunks = chunk_text(clean_text)
        
        if not chunks:
            st.error("No valid chunks could be created from this document.")
        else:
            embeddings = get_google_embeddings(chunks)
            index = build_faiss_index(embeddings)
            query_embedding = embed_query(question)
            relevant_chunks = retrieve_chunks(query_embedding, index, chunks)

            if not relevant_chunks:
                st.warning("No relevant information found.")
            else:
                answer = ask_gemini(question, relevant_chunks)
                st.success("✅ Answer:")
                st.write(answer)
else:
    st.info("Please upload a file and enter a question to begin.")
