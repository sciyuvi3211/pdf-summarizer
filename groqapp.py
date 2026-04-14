import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os
import re
import fitz  # PyMuPDF

# 🔥 Firebase
import firebase_admin
from firebase_admin import credentials, firestore

# 🍪 Cookies
from streamlit_cookies_manager import EncryptedCookieManager
import uuid

# 🔐 Load API key
load_dotenv("secure.env")
API_KEY = os.getenv("GROQ_API_KEY")

# 🔥 Firebase init
if not firebase_admin._apps:
    cred = credentials.Certificate(dict(st.secrets["firebase"]))
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 🍪 Cookie setup
cookies = EncryptedCookieManager(password="super-secret-key")

if not cookies.ready():
    st.stop()

# 🆔 Unique user ID
if "user_id" not in cookies:
    cookies["user_id"] = str(uuid.uuid4())
    cookies.save()

user_id = cookies["user_id"]

# 👤 Get user data
def get_user_data(user_id):
    doc_ref = db.collection("users").document(user_id)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    else:
        data = {"usage": 0, "plan": "free"}
        doc_ref.set(data)
        return data

user = get_user_data(user_id)

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

# 📄 Extract text
def extract_text(file):
    text = ""
    try:
        pdf = fitz.open(stream=file.read(), filetype="pdf")
        for page in pdf:
            text += page.get_text()
    except Exception as e:
        return f"ERROR: {str(e)}"
    return text

# 🧹 Clean text
def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# 🤖 Summarize
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

# 💬 Talk to PDF
def answer_question(text, question):
    try:
        client = Groq(api_key=API_KEY)

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": f"""
Answer the question ONLY using the text below.

If the answer is not in the text, say "Not found in document".

Text:
{text}

Question:
{question}
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

# 🚀 MAIN LOGIC
if uploaded_file:

    # 🚫 LIMIT CHECK
    if user["usage"] >= 3 and user["plan"] == "free":
        st.error("🚫 Free limit reached. Upgrade to continue.")

        st.markdown("### 🚀 Upgrade to Pro")
        st.markdown("📩 Contact: **your-email@gmail.com**")
        st.markdown("Send your login email to get Pro access.")

        st.stop()

    st.success(f"✅ File uploaded: {uploaded_file.name}")

    text = extract_text(uploaded_file)

    if text.startswith("ERROR"):
        st.error(text)

    elif len(text.strip()) == 0:
        st.error("❌ No readable text found in PDF")

    else:
        processed_text = clean_text(text)
        processed_text = processed_text[:6000]

        # 👀 Preview
        with st.expander("👀 Preview Extracted Text"):
            st.write(processed_text[:500])

        # ✨ Generate Summary
        if st.button("✨ Generate Summary", key="gen_btn"):
            with st.spinner("Generating summary..."):
                st.session_state.summary = summarize(processed_text)

                # 📊 UPDATE USAGE
                db.collection("users").document(user_id).update({
                    "usage": user["usage"] + 1
                })

                # Refresh user data
                user = get_user_data(user_id)

        # 🔄 Regenerate
        if st.button("🔄 Regenerate Summary", key="regen_btn"):
            with st.spinner("Regenerating..."):
                st.session_state.summary = summarize(processed_text)

        # 📌 SHOW SUMMARY + CHAT
        if st.session_state.summary:

            st.subheader("📌 Summary")
            st.write(st.session_state.summary)

            st.info(f"📊 Words: {len(st.session_state.summary.split())}")

            st.download_button(
                "📥 Download Summary",
                st.session_state.summary,
                file_name="summary.txt"
            )

            # 💬 TALK TO PDF
            st.markdown("### 💬 Talk to your PDF")

            question = st.text_input("Ask something about the PDF")

            if st.button("🤖 Get Answer", key="chat_btn"):
                if question.strip() != "":
                    with st.spinner("Thinking..."):
                        answer = answer_question(processed_text, question)
                        st.subheader("💡 Answer")
                        st.write(answer)
                else:
                    st.warning("Please enter a question")

            # 🚀 UPGRADE SECTION
            st.markdown("### 🚀 Upgrade to Pro")
            st.markdown("📩 Contact: **yuvrajwork0032@gmail.com**")
            st.markdown("Send your email to unlock unlimited access.")

# Footer
st.markdown("---")
st.markdown("🚀 Built by Yuvraj | Powered by Groq")
