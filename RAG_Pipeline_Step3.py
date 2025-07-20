

import os
import nltk
import faiss
import numpy as np
import google.generativeai as genai
from bs4 import BeautifulSoup

nltk.download('punkt')

# ===  Load and Clean Text ===
def load_and_clean_text(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        raw_text = file.read()
    clean_text = BeautifulSoup(raw_text, "html.parser").get_text()
    return clean_text

# === Chunk the Text ===
#The chunk_text function splits a long text into overlapping chunks of a specified size (default 1000 characters) while preserving sentence boundaries. 
# It ensures that important context isn't lost between chunks by overlapping about 200 characters between them. 
def chunk_text(text, chunk_size=1000, chunk_overlap=200):
    sentences = nltk.sent_tokenize(text)
    chunks = []
    current_chunk = []
    current_len = 0

    for sentence in sentences:
        if current_len + len(sentence) > chunk_size:
            chunks.append(" ".join(current_chunk))
            current_chunk = current_chunk[-(chunk_overlap // 2):]  # overlap
            current_len = sum(len(s) for s in current_chunk)
        current_chunk.append(sentence)
        current_len += len(sentence)

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks

# === Get Embeddings from Gemini ===
#The get_google_embeddings function generates Google Gemini embeddings for each text chunk using the embedding-001 model. 
# It configures the API with the provided key, sends each non-empty chunk for embedding (optimized for retrieval tasks), 
# and collects the resulting vectors into a NumPy array
def get_google_embeddings(chunks, api_key):
    genai.configure(api_key=api_key)
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
    return np.array(embeddings).astype('float32')

# === Build FAISS Index ===
# The build_faiss_index function creates a FAISS vector index using the provided embeddings
def build_faiss_index(embeddings):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index

# === Embed the Query and Retrieve Chunks ===
def embed_query(query, api_key):
    genai.configure(api_key=api_key)
    if not query.strip():
        raise ValueError("Query cannot be empty.")
    response = genai.embed_content(
        model="models/embedding-001",
        content=query,
        task_type="retrieval_query"
    )
    return np.array([response["embedding"]]).astype('float32')


# The retrieve_chunks function performs a semantic search by querying the FAISS index with a 
# given embedding (usually of the user's question). It returns the top_k most relevant text chunks based on similarity.
def retrieve_chunks(query_embedding, faiss_index, chunks, top_k=5):
    distances, indices = faiss_index.search(query_embedding, top_k)
    if indices.shape[1] == 0 or len(indices[0]) == 0:
        return []
    return [chunks[i] for i in indices[0] if i < len(chunks)]

# === Ask Gemini LLM ===
def ask_gemini(question, context_chunks, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    context = "\n\n".join(context_chunks)
    prompt = f"""
"You are an assistant for question-answering tasks. "
    "Use the following pieces of retrieved context to answer "
    "the question. If you don't know the answer, say that you "
    "don't know. Use three sentences maximum and keep the "
    "answer concise."

Context:
{context}

Question:
{question}
"""
    response = model.generate_content(prompt)
    return response.text.strip()

# ===  Full RAG Pipeline ===
def rag_pipeline(question, file_path, api_key):
    text = load_and_clean_text(file_path)
    chunks = chunk_text(text)

    # It loads and cleans text from a file, breaks it into overlapping chunks, 
    # and generates embeddings for those chunks using the Gemini API.
    # t builds a FAISS index for semantic search and embeds the user’s question.
    # It retrieves the most relevant chunks based on the question and finally passes them to Gemini's LLM to generate an answer.

    if not chunks:
        raise ValueError("No valid text chunks found in the document.")

    embeddings = get_google_embeddings(chunks, api_key)
    if embeddings.shape[0] == 0:
        raise ValueError("No embeddings could be created.")

    index = build_faiss_index(embeddings)
    query_embedding = embed_query(question, api_key)
    relevant_chunks = retrieve_chunks(query_embedding, index, chunks)

    if not relevant_chunks:
        return "Sorry, I couldn’t find anything relevant in the document."

    return ask_gemini(question, relevant_chunks, api_key)

# === Step 8: Run ===
if __name__ == "__main__":
    file_path = "cleaned_data1.txt"
    api_key = "AIzaSyBhq6qGeBhGpYdE1kNeXE7wGZj2Sz4S30A"
    question = input("Ask your question: ").strip()

    if not os.path.exists(file_path):
        print("❌ File does not exist.")
    elif not question:
        print("❌ Question cannot be empty.")
    else:
        try:
            answer = rag_pipeline(question, file_path, api_key)
            print("\nAnswer:\n", answer)
        except Exception as e:
            print("❌ Error:", e)


