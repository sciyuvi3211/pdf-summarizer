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

# 🔥 Firebase init (SAFE)
try:
    firebase_admin.get_app()
except ValueError:
    try:
        cred = credentials.Certificate("firebase_key.json")
    except:
        import json

        cred_dict = json.loads(json.dumps(st.secrets["firebase"]))
        cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

        cred = credentials.Certificate(cred_dict)
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
def get_user(email):
    doc_ref = db.collection("users").document(email)
    doc = doc_ref.get()

    if doc.exists:
        return doc.to_dict()
    else:
        user_data = {
            "email": email,
            "plan": "free",
            "usage": 0,
            "ref_rewarded": False
        }
        doc_ref.set(user_data)
        return user_data

user = get_user(user_id)

# 🎯 REFERRAL SYSTEM (ONE-TIME)
query_params = st.query_params
ref_id = query_params.get("ref", None)

if ref_id and ref_id != user_id:
    ref_doc = db.collection("users").document(ref_id).get()
    current_user_doc = db.collection("users").document(user_id).get()

    if ref_doc.exists and current_user_doc.exists:
        ref_data = ref_doc.to_dict()
        current_user_data = current_user_doc.to_dict()

        if (
            not ref_data.get("ref_rewarded", False)
            and current_user_data.get("usage", 0) == 0
        ):
            db.collection("users").document(ref_id).update({
                "usage": max(ref_data["usage"] - 2, 0),
                "ref_rewarded": True
            })

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
            messages=[{
                "role": "user",
                "content": f"""
Summarize the following PDF content clearly and accurately.

Only use the given text.
If the content is unclear or incomplete, say "Content unclear".

Text:
{text}
"""
            }]
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
            messages=[{
                "role": "user",
                "content": f"""
Answer the question ONLY using the text below.

If the answer is not in the text, say "Not found in document".

Text:
{text}

Question:
{question}
"""
            }]
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

    # 🚫 USAGE LIMIT
    if user["plan"] == "free" and user["usage"] >= 3:
        st.error("🚫 Free limit reached. Upgrade to continue.")

        referral_link = f"https://your-app-url.streamlit.app/?ref={user_id}"

        st.markdown("### 🎁 Get 2 Extra Uses")
        st.code(referral_link)
        st.markdown("📤 Share this link with a friend to unlock +2 uses!")

        st.markdown(f"""
        <a href="https://wa.me/?text=Check this AI PDF tool: {referral_link}" target="_blank">
        📲 Share on WhatsApp
        </a>
        """, unsafe_allow_html=True)

        st.stop()

    st.success(f"✅ File uploaded: {uploaded_file.name}")

    text = extract_text(uploaded_file)

    if text.startswith("ERROR"):
        st.error(text)

    elif len(text.strip()) == 0:
        st.error("❌ No readable text found in PDF")

    else:
        processed_text = clean_text(text)[:6000]

        with st.expander("👀 Preview Extracted Text"):
            st.write(processed_text[:500])

        if st.button("✨ Generate Summary", key="gen_btn"):
            with st.spinner("Generating summary..."):
                st.session_state.summary = summarize(processed_text)

                db.collection("users").document(user_id).update({
                    "usage": user["usage"] + 1
                })

        if st.button("🔄 Regenerate Summary", key="regen_btn"):
            with st.spinner("Regenerating..."):
                st.session_state.summary = summarize(processed_text)

        if st.session_state.summary:
            st.subheader("📌 Summary")
            st.write(st.session_state.summary)

            st.info(f"📊 Words: {len(st.session_state.summary.split())}")

            st.download_button(
                "📥 Download Summary",
                st.session_state.summary,
                file_name="summary.txt"
            )

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

# 🚀 ALWAYS SHOW UPGRADE (ADDED)
st.markdown("---")
st.markdown("### 🚀 Upgrade to Pro")
st.markdown("""
Want unlimited usage and full access?

📩 Contact: **yuvrajwork0032@gmail.com**
""")

# Footer
st.markdown("---")
st.markdown("🚀 Built by Yuvraj | Powered by Groq")
