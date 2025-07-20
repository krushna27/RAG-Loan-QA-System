# RAG-Loan-QA-System
# Bank of Maharashtra Loan RAG QA System

This project implements a Retrieval-Augmented Generation (RAG) pipeline for answering loan-related questions using data scraped from the Bank of Maharashtra website. It combines web scraping, data cleaning, semantic search (FAISS), and Google's Gemini LLM for accurate, context-grounded answers.

---

## Project Setup

1. **Clone the Repository**  
   Download or clone this repository to your local machine.

2. **Install Required Packages**  
   Install all dependencies using pip:
   ```sh
   pip install google-generativeai faiss-cpu beautifulsoup4 nltk numpy selenium streamlit





3. Download NLTK Data
In your Python environment, run:

 ```sh
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
```

4. Set Up ChromeDriver
Download ChromeDriver and update the path in BankOfMaharashtraLoanScraper if needed.

5. Run the Scraper
Execute the scraper to generate the knowledge base:
python Scraping_Step1.py

This will create scraped_data_mahaloan2.txt.

6. Clean and Preprocess Data
Use the notebook Cleaning_Step2.ipynb to clean and lemmatize the scraped data, saving the result as cleaned_data2.txt.

7. Run the RAG QA Pipeline
You can use either:
```sh
python RAG_Pipeline_Step3.py # for a command-line QA demo.
python app.py # for a Streamlit web interface.
```

# Architectural Decisions
Libraries

1. Scraping: selenium for robust browser automation and scraping dynamic content. BeautifulSoup for HTML parsing and text extraction.

2. Data Processing: nltk for sentence tokenization, stopword removal, and lemmatization. re for regex-based cleaning.

3. RAG Pipeline:
faiss for fast vector similarity search.
google-generativeai for Gemini embeddings and LLM responses.
numpy for efficient array handling.
streamlit for the interactive web UI.

# Why these choices?
Selenium and BeautifulSoup together handle both static and dynamic web content. NLTK is reliable for text processing. FAISS is industry-standard for vector search. Google's Gemini API provides state-of-the-art embeddings and LLM capabilities.

# Data Strategy
Chunking: Text is split into ~1000-character chunks with ~200-character overlap using sentence boundaries.

# Why?
Maintains semantic context across sentences.
Overlap ensures important info isn't lost at chunk borders.
Keeps chunks within token limits for embedding and LLM use.

# Model Selection

1. Embedding Model: models/embedding-001 from Gemini, optimized for retrieval tasks.
2. LLM: gemini-1.5-flash for fast, cost-effective answer generation.
3. Rationale: Gemini models are well-integrated, high-quality, and support both embedding and LLM tasks with a single API.

# AI Tools Used
1. Google Gemini API: For both embeddings and LLM-based answer generation.
2. FAISS: For scalable, efficient nearest-neighbor search.
3. NLTK: For robust text preprocessing.

# Challenges Faced

One major challenge was that the Bank of Maharashtra website actively blocks scraping and disables automated access. As a workaround, I manually downloaded the relevant loan-related pages and used browser developer tools (e.g., Inspect Element) to analyze the HTML structure. I then leveraged GPT-based assistance to generate targeted scraping scripts, which extracted the necessary content from static HTML files by focusing on specific tags and class attributes


Dynamic Web Pages:
Some loan pages load content dynamically. Selenium was used to render JavaScript and ensure complete data extraction.

Messy Data Formats:
Scraped data contained inconsistent formatting and noise. Multiple regex and NLTK-based cleaning steps were applied.

Chunking Trade-offs:
Balancing chunk size for semantic coherence vs. LLM/embedding limits required experimentation.

# Potential Improvements

Add Multi-File or Multi-Format Document Support

Move to LangChain for Modularity & Ecosystem Integration:

Use a Persistent Vector Store (e.g., Chroma or Pinecone)

Use semantic chunking (e.g., split by topic or paragraph).

Use LangChain’s RecursiveCharacterTextSplitter which respects structure.

Using a local model for your RAG pipeline (instead of Gemini API) can greatly reduce costs, improve privacy, and allow offline functionality



# File Overview
Scraping_Step1.py: Web scraper for Bank of Maharashtra loan data.
Cleaning_Step2.ipynb: Data cleaning and preprocessing notebook.
RAG_Pipeline_Step3.py: Command-line RAG QA pipeline.

app.py : Streamlit web app for interactive QA  
app1.py: Streamlit web app for interactive QA Using Langchain.

<img width="1919" height="812" alt="Screenshot 2025-07-20 231256" src="https://github.com/user-attachments/assets/71aa4eba-c16b-498f-95d9-4faaac36a286" />



