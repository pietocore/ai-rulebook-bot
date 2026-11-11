import streamlit as st
from pypdf import PdfReader
import re

# YOUR GROQ KEY
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

from groq import Groq
client = Groq(api_key=GROQ_API_KEY)

st.set_page_config(page_title="AI Rulebook Bot", page_icon="📚")
st.title("📚 AI Rulebook Bot - Ask from PDF")
st.write("Upload your school rules PDF and ask questions!")

# Upload PDF
uploaded_file = st.file_uploader("rules.pdf", type="pdf")

if uploaded_file:
    reader = PdfReader(uploaded_file)
    full_text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            full_text += t + "\n"
    
    st.success(f"Loaded {len(reader.pages)} pages, {len(full_text)} characters")
    
    # Chunking
    chunk_size = 800
    chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
    st.info(f"Made {len(chunks)} chunks for Vector Search")

    def simple_search(query, chunks, top_k=3):
        query_words = set(re.findall(r'\w+', query.lower()))
        scores = []
        for i, chunk in enumerate(chunks):
            chunk_words = set(re.findall(r'\w+', chunk.lower()))
            overlap = len(query_words & chunk_words)
            scores.append((overlap, i))
        scores.sort(reverse=True)
        top_chunks = [chunks[idx] for score, idx in scores[:top_k] if score > 0]
        return top_chunks if top_chunks else chunks[:top_k]

    # Chat
    question = st.text_input("Ask question from PDF:", placeholder="e.g., Use of Scribe?")

    if question:
        with st.spinner("Searching relevant chunks..."):
            relevant_chunks = simple_search(question, chunks, top_k=3)
            relevant_text = "\n".join(relevant_chunks)
            
            prompt = f"""
Answer ONLY from this relevant part of PDF:

{relevant_text}

Question: {question}
If not found, say "Not found in PDF".
"""

            response = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}]
            )
            
            st.markdown("### Answer (Vector Search)")
            st.write(response.choices[0].message.content)
            
            with st.expander("See 3 relevant chunks used"):
                for i, c in enumerate(relevant_chunks):
                    st.text(f"Chunk {i+1}: {c[:300]}...")
else:
    st.warning("Please upload a PDF to start")

st.markdown("---")
st.caption("Built by you in Shimla - Vector RAG Bot - Day 4")