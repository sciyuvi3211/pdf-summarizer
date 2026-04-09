import streamlit as st
import pdfplumber
from groq import Groq
from dotenv import load_dotenv
import os
import re

# 🔐 Load API key
load_dotenv("secure.env")
API_KEY = os.getenv("GROQ_API_KEY")

# 🎨 Page config
st.set_page_config(page_title="AI PDF Summarizer")

# 🎨 Styling
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #020617, #0f172a, #1e293b);
    color: #e2e8f0;
    font-family: 'Segoe UI', sans-serif;
}
h1 {
    text-align: center;
    font-size: 40px;
    color: #38bdf8;
}
.stButton>button {
    background: linear-gradient(90deg, #22c55e, #4ade80);
    color: black;
    border-radius: 12px;
    height: 3em;
    width: 100%;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("📄 AI PDF Summarizer")

# 📄 Extract text using pdfplumber
def extract_text(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                content = page.extract_text()
                if content:
                    text += content + "\n"
    except Exception as e:
        return f"ERROR: {str(e)}"
    return text

# 🧹 Clean text
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# 🤖 Summarize function
def summarize(text):
    try:
        client = Groq(api_key=API_KEY)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": f"""
Summarize the following PDF content clearly and accurately.

Only use the given text.
If the content is unclear or incomplete, say "Content unclear".

Text:
{text}
"""
                }
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ API Error: {str(e)}"

# 📤 Upload
st.markdown("### 📂 Upload Your PDF")
uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

# 💾 Session state
if "summary" not in st.session_state:
    st.session_state.summary = None

# 🚀 Main logic
if uploaded_file:
    st.success(f"✅ File uploaded: {uploaded_file.name}")

    text = extract_text(uploaded_file)

    # ❌ Handle extraction error
    if text.startswith("ERROR"):
        st.error(text)

    # ❌ Handle empty text
    elif len(text.strip()) == 0:
        st.error("❌ No readable text found in PDF")

    else:
        # 🧹 Clean + optimize text
        processed_text = clean_text(text)
        processed_text = processed_text[:3000]

        # 👀 Preview cleaned text
        with st.expander("👀 Preview Extracted Text"):
            st.write(processed_text[:500])

        # ✨ Generate
        if st.button("✨ Generate Summary"):
            with st.spinner("Generating summary..."):
                st.session_state.summary = summarize(processed_text)

        # 🔄 Regenerate
        if st.button("🔄 Regenerate Summary"):
            with st.spinner("Regenerating..."):
                st.session_state.summary = summarize(processed_text)

        # 📌 Show summary
        if st.session_state.summary:
            st.subheader("📌 Summary")
            st.write(st.session_state.summary)

            # 📊 Word count
            st.info(f"📊 Words: {len(st.session_state.summary.split())}")

            # 📥 Download
            st.download_button(
                "📥 Download Summary",
                st.session_state.summary,
                file_name="summary.txt"
            )

# Footer
st.markdown("---")
st.markdown("🚀 Built by Yuvraj | Powered by Groq")
