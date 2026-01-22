import streamlit as st
import utils  
import time
from datetime import datetime   

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SmartDoc AI",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS STYLING ---
st.markdown("""
    <style>
    /* Main container styling */
    .main {
        background-color: #f8f9fa;
    }
    /* Custom Title */
    .title-text {
        font-family: 'Helvetica', sans-serif;
        color: #2E86C1;
        font-weight: 700;
        text-align: center;
        padding-bottom: 20px;
    }
    /* Summary Card Styling */
    .summary-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
    /* Button Styling */
    .stButton>button {
        background-color: #2E86C1;
        color: white;
        border-radius: 8px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1B4F72;
    }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "setup_pending" not in st.session_state:
    st.session_state["setup_pending"] = False

# --- GOOGLE LOGIN LISTENER ---
# This checks if Google just sent us back a user
if "code" in st.query_params:
    auth_code = st.query_params["code"]
    try:
        user_info = utils.get_google_user_info(auth_code)
        email = user_info["email"]
        
        # Unpack the tuple: (User Object, Is New User?)
        # Make sure you updated utils.py to return this tuple!
        firebase_user, is_new_user = utils.login_with_google_email(email)
        
        # Set Session State
        st.session_state["logged_in"] = True
        st.session_state["user_id"] = firebase_user.uid
        st.session_state["username"] = firebase_user.display_name or email.split("@")[0]
        
        # ✅ FLAG: If new user, trigger the setup screen
        if is_new_user:
            st.session_state["setup_pending"] = True
        else:
            st.session_state["setup_pending"] = False
            # Ideally load username from DB here if needed
        
        # Clear the "code" from URL so it looks clean
        st.query_params.clear()
        st.success(f"✅ Login Successful!")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Google Login Failed: {e}")

# --- LOGIN & REGISTER FUNCTIONS ---
def login_ui():
    st.markdown("<h2 class='title-text'>🔐 Access Your Workspace</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        tab_login, tab_register = st.tabs(["Login", "Register"])
        
        with tab_login:
            email = st.text_input("Email Address", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Log In", use_container_width=True):
                user = utils.verify_login(email, password)
                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["user_id"] = user.uid
                    st.session_state["username"] = user.display_name or "User"
                    st.success("✅ Welcome back!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ User not found or invalid credentials.")
            
            # --- Google Login Section (Inside the Tab) ---
            st.markdown("---")
            st.markdown("<p style='text-align: center;'>OR</p>", unsafe_allow_html=True)
            
            google_url = utils.get_google_login_url()
            st.markdown(f'''
                <a href="{google_url}" target="_self" style="text-decoration: none;">
                    <button style="
                        width: 100%;
                        background-color: white;
                        color: #333;
                        border: 1px solid #ccc;
                        padding: 10px;
                        border-radius: 5px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        cursor: pointer;
                        font-weight: bold;
                        font-family: inherit;">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/5/53/Google_%22G%22_Logo.svg" 
                             style="width: 20px; margin-right: 10px;">
                        Sign in with Google
                    </button>
                </a>
            ''', unsafe_allow_html=True)

        with tab_register:
            new_user = st.text_input("Username")
            new_email = st.text_input("Email Address", key="reg_email")
            new_pass = st.text_input("Password", type="password", key="reg_pass")
            if st.button("Create Account", use_container_width=True):
                if utils.register_user(new_email, new_pass, new_user):
                    st.success("✅ Account created! Please log in.")
                else:
                    st.error("❌ Registration failed.")

# --- USERNAME SETUP UI (NEW) ---
def username_setup_ui():
    """Displays a simple form for new users to pick a username."""
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Using a generic user icon
        st.markdown("<h2 style='text-align:center;'>👋 Welcome!</h2>", unsafe_allow_html=True)
        st.info("Since this is your first time here, please choose a display name.")
        
        with st.form("setup_form"):
            new_username = st.text_input("Choose a Username", placeholder="e.g. CodeMaster99")
            submitted = st.form_submit_button("Save & Continue", use_container_width=True)
            
            if submitted:
                if len(new_username) < 3:
                    st.error("Username must be at least 3 characters.")
                else:
                    # Save to DB
                    utils.update_username(st.session_state["user_id"], new_username)
                    
                    # Update Session State
                    st.session_state["username"] = new_username
                    st.session_state["setup_pending"] = False # ✅ Turn off the flag
                    st.rerun()

# --- MAIN APPLICATION UI ---
def main_app():
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3022/3022209.png", width=50)
        st.markdown(f"### 👋 Hi, {st.session_state['username']}")
        st.markdown("---")
        nav = st.radio("Navigation", ["🏠 Home", "📂 My History", "⚙️ Settings"])
        st.markdown("---")
        if st.button("🚪 Logout"):
            st.session_state["logged_in"] = False
            st.session_state["setup_pending"] = False
            st.rerun()

    # Home Tab
    if nav == "🏠 Home":
        st.markdown("<h1 class='title-text'>📄 SmartDoc Summarizer</h1>", unsafe_allow_html=True)
        
        # Input Method Selection
        input_method = st.radio("Choose Input Method:", ["Upload File", "Paste Text", "Web URL"], horizontal=True)
        
        text_to_summarize = ""
        doc_title = "Untitled Document"

        if input_method == "Upload File":
            uploaded_file = st.file_uploader("Drop your PDF, DOCX, or TXT here", type=['pdf', 'docx', 'txt'])
            if uploaded_file:
                doc_title = uploaded_file.name
                if uploaded_file.name.endswith(".pdf"):
                    text_to_summarize = utils.extract_from_pdf(uploaded_file)
                elif uploaded_file.name.endswith(".docx"):
                    text_to_summarize = utils.extract_from_docx(uploaded_file)
                else:
                    text_to_summarize = uploaded_file.read().decode("utf-8")
        
        elif input_method == "Paste Text":
            text_to_summarize = st.text_area("Paste your content here...", height=200)
            doc_title = "Pasted Text " + str(datetime.now().strftime("%H:%M"))
            
        elif input_method == "Web URL":
            url = st.text_input("Enter Article URL")
            if url:
                with st.spinner("🕷️ Scraping content..."):
                    text_to_summarize = utils.extract_from_url(url)
                    doc_title = "Web Article"

        # Settings Expander
        with st.expander("🛠️ Advanced Settings"):
            col_set1, col_set2 = st.columns(2)
            min_L = col_set1.slider("Min Summary Length", 30, 100, 50)
            max_L = col_set2.slider("Max Summary Length", 100, 500, 150)

        # Summarize Action
        if st.button("✨ Generate Summary", use_container_width=True):
            if text_to_summarize:
                with st.spinner("🤖 AI is reading and summarizing..."):
                    summary = utils.generate_summary(text_to_summarize, min_L, max_L)
                    
                    # Store in session state to persist after reload
                    st.session_state['current_summary'] = summary
                    st.session_state['current_text'] = text_to_summarize
                    st.session_state['current_title'] = doc_title
                    
                    # Auto-save
                    utils.save_summary_to_db(st.session_state["user_id"], doc_title, text_to_summarize, summary)
            else:
                st.warning("⚠️ Please provide some text to summarize.")

        # Display Results
        if 'current_summary' in st.session_state:
            st.markdown("---")
            col_orig, col_sum = st.columns(2)
            
            with col_orig:
                st.info("📄 Original Text")
                st.markdown(f"<div style='height: 400px; overflow-y: scroll; background: white; padding: 10px; border-radius:5px;'>{st.session_state['current_text']}</div>", unsafe_allow_html=True)
            
            with col_sum:
                st.success("📝 AI Summary")
                st.markdown(f"<div style='height: 400px; overflow-y: scroll; background: white; padding: 10px; border-radius:5px;'>{st.session_state['current_summary']}</div>", unsafe_allow_html=True)
                
            st.download_button("📥 Download Summary", st.session_state['current_summary'], file_name="summary.txt")

    # History Tab
    elif nav == "📂 My History":
        st.markdown("<h2 class='title-text'>📜 Your Document History</h2>", unsafe_allow_html=True)
        history = utils.get_user_history(st.session_state["user_id"])
        
        if not history:
            st.info("No summaries found. Go generate some!")
        
        for item in history:
            with st.container():
                st.markdown(f"""
                <div class='summary-card'>
                    <h4>{item.get('title', 'Untitled')}</h4>
                    <small>📅 {item['timestamp'].strftime('%Y-%m-%d %H:%M')}</small>
                    <hr>
                    <p>{item['summary']}</p>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️ Delete", key=item['id']):
                    utils.delete_summary_from_db(st.session_state["user_id"], item['id'])
                    st.rerun()

    elif nav == "⚙️ Settings":
        st.write("User Profile Settings (Coming Soon)")

# --- APP FLOW ---
if st.session_state["logged_in"]:
    # Check if they still need to set up their username
    if st.session_state.get("setup_pending", False):
        username_setup_ui()
    else:
        main_app()
else:
    login_ui()