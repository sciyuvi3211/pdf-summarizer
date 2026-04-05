import streamlit as st
import PyPDF2
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv("secure.env")

# 🔐 API KEY (put your NEW key here)
API_KEY = os.getenv("GROQ_API_KEY")


# 🎨 Page setup
st.set_page_config(page_title="AI PDF Summarizer")

# 🎨 Styling
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #020617, #0f172a, #1e293b);
    color: #e2e8f0;
    font-family: 'Segoe UI', sans-serif;
}

/* Title */
h1 {
    text-align: center;
    font-size: 40px;
    color: #38bdf8;
}

/* Buttons */
.stButton>button {
    background: linear-gradient(90deg, #22c55e, #4ade80);
    color: black;
    border-radius: 12px;
    height: 3em;
    width: 100%;
    font-weight: bold;
    transition: 0.3s;
}
.stButton>button:hover {
    transform: scale(1.05);
}

/* Upload box */
[data-testid="stFileUploader"] {
    background-color: #1e293b;
    padding: 20px;
    border-radius: 12px;
    border: 2px dashed #38bdf8;
}

/* Info text */
.stAlert {
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# 🧠 Title
st.title("📄 AI PDF Summarizer")

# 📄 Function: Extract text
def extract_text(file):
    reader = PyPDF2.PdfReader(file)
    text = ""

    for page in reader.pages:
        content = page.extract_text()
        if content:
            text += content.strip() + " "

    return text

# 🤖 Function: Summarize
def summarize(text):
    try:
        client = Groq(api_key=API_KEY)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "user", "content": f"Summarize this:\n{text}"}
            ]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"❌ API Error: {str(e)}"

# 📤 Upload
st.markdown("### 📂 Upload Your PDF")
st.info("👉 Click **Browse Files** below to select your PDF")

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type="pdf",
    help="Upload a PDF (1–5 pages recommended)"
)
if uploaded_file:
    st.success(f"✅ File uploaded: {uploaded_file.name}")


# 💾 Store summary (fix duplicate issue)
if "summary" not in st.session_state:
    st.session_state.summary = None

# 🚀 Main logic
if uploaded_file:
    st.success("✅ PDF Uploaded!")

    text = extract_text(uploaded_file)

    if len(text.strip()) == 0:
        st.error("❌ No readable text found")
    else:
        # 👀 Preview
        with st.expander("👀 Preview Text"):
            st.write(text[:500])

        clean_text = text[:800]  # safe limit

        # Generate summary
        if st.button("✨ Generate Summary"):
            with st.spinner("Generating..."):
                st.session_state.summary = summarize(clean_text)

        # Regenerate
        if st.button("🔄 Regenerate"):
            with st.spinner("Regenerating..."):
                st.session_state.summary = summarize(clean_text)

        # Show result
        if st.session_state.summary:
            st.subheader("📌 Summary")
            st.write(st.session_state.summary)

            st.download_button(
                "📥 Download",
                st.session_state.summary,
                file_name="summary.txt"
            )

# Footer
st.markdown("---")
st.markdown("🚀 Built by Yuvraj | Powered by Groq")