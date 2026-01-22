import streamlit as st
from transformers import pipeline
from PyPDF2 import PdfReader
from docx import Document
import firebase_admin
from firebase_admin import credentials, firestore, auth
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from google_auth_oauthlib.flow import Flow
import os

# --- FIREBASE SETUP ---
# We initialize this FIRST so 'db' is available for other functions
def initialize_firebase():
    if not firebase_admin._apps:
        # Check if we are on the Cloud (Secrets exist)
        if "firebase" in st.secrets:
            # Create credential from the Secret Dictionary
            cred = credentials.Certificate(dict(st.secrets["firebase"]))
        else:
            # Fallback to local file (for your laptop)
            cred = credentials.Certificate("Assets/Assert.json") 
            
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = initialize_firebase()

# --- GOOGLE AUTHENTICATION LOGIC ---
def get_google_auth_flow():
    """Sets up the configuration for the Google Login handshake."""
    # This requires .streamlit/secrets.toml to exist with [google] data
    return Flow.from_client_config(
        {
            "web": {
                "client_id": st.secrets["google"]["client_id"],
                "client_secret": st.secrets["google"]["client_secret"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email"],
        redirect_uri=st.secrets["google"]["redirect_uri"]
    )

def get_google_login_url():
    """Generates the URL where the user clicks to log in."""
    flow = get_google_auth_flow()
    authorization_url, _ = flow.authorization_url(prompt='consent')
    return authorization_url

def get_google_user_info(auth_code):
    """Exchanges the 'code' from URL for the actual user email."""
    flow = get_google_auth_flow()
    flow.fetch_token(code=auth_code)
    credentials = flow.credentials
    
    # Use the token to ask Google for the user's email
    session = requests.Session()
    response = session.get(
        'https://www.googleapis.com/oauth2/v1/userinfo',
        params={'access_token': credentials.token}
    )
    return response.json()  # Returns {'email': '...', 'id': '...'}

def login_with_google_email(email):
    """Links Google Login to your existing Firebase system."""
    try:
        # 1. Try to find existing user
        user = auth.get_user_by_email(email)
        
        # Check if they have a username set in Firestore (optional but good)
        doc = db.collection("users").document(user.uid).get()
        if doc.exists and doc.to_dict().get("username"):
            return user, False  # False = Not a new user (Setup complete)
        else:
            return user, True   # True = User exists but needs setup (Edge case)

    except:
        # 2. User doesn't exist? Create them!
        print("User not found, creating new Firebase user for Google Email.")
        user = auth.create_user(email=email)
        
        # Create a placeholder document. 
        # We leave 'username' as None so the App knows to ask for it.
        db.collection("users").document(user.uid).set({
            "email": email,
            "username": None 
        })
        
        return user, True  # True = Is a new user

def update_username(user_id, new_username):
    """Updates the username in Firestore."""
    try:
        db.collection("users").document(user_id).update({
            "username": new_username
        })
        return True
    except Exception as e:
        print(f"Error updating username: {e}")
        return False

# --- AI MODEL CACHING ---
@st.cache_resource
def load_summarizer_model():
    return pipeline("summarization", model="facebook/bart-large-cnn")

# --- TEXT EXTRACTION HELPER FUNCTIONS ---
def extract_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def extract_from_url(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        paragraphs = soup.find_all('p')
        text = " ".join([p.get_text() for p in paragraphs])
        return text
    except Exception as e:
        return f"Error fetching URL: {e}"

# --- SMART CHUNKING & SUMMARIZATION ---
def split_text(text, max_chunk_size=1024):
    sentences = text.replace('\n', ' ').split('. ')
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        if current_length + len(sentence) < max_chunk_size:
            current_chunk.append(sentence)
            current_length += len(sentence)
        else:
            chunks.append(". ".join(current_chunk) + ".")
            current_chunk = [sentence]
            current_length = len(sentence)
    
    if current_chunk:
        chunks.append(". ".join(current_chunk) + ".")
    return chunks

def generate_summary(text, min_len, max_len):
    summarizer = load_summarizer_model()
    chunks = split_text(text)
    summary_text = ""
    
    for chunk in chunks:
        if len(chunk.strip()) > 50:
            res = summarizer(chunk, max_length=max_len, min_length=min_len, do_sample=False)
            summary_text += res[0]['summary_text'] + " "
            
    return summary_text.strip()

# --- DATABASE OPERATIONS ---
def save_summary_to_db(user_id, title, original, summary):
    data = {
        "title": title,
        "original_text": original,
        "summary": summary,
        "timestamp": datetime.now()
    }
    db.collection("users").document(user_id).collection("summaries").add(data)

def get_user_history(user_id):
    docs = db.collection("users").document(user_id).collection("summaries").order_by("timestamp", direction=firestore.Query.DESCENDING).stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]

def delete_summary_from_db(user_id, summary_id):
    db.collection("users").document(user_id).collection("summaries").document(summary_id).delete()

# --- AUTHENTICATION ---
def register_user(email, password, username):
    try:
        user = auth.create_user(email=email, password=password, display_name=username)
        db.collection("users").document(user.uid).set({"username": username, "email": email})
        return user
    except Exception as e:
        st.error(f"Registration Error: {e}")
        return None

def verify_login(email, password):
    try:
        # WARNING: This only checks if the user exists, it DOES NOT verify the password.
        user = auth.get_user_by_email(email)
        return user
    except:
        return None