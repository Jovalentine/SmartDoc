SmartDoc AI - Intelligent Document Summarizer

SmartDoc AI is a powerful web application that uses **Artificial Intelligence (Facebook BART Model)** to automatically summarize long documents. It supports PDFs, Word Docs, Text files, and even Web Articles.

Built with **Streamlit**, **Firebase**, and **Google Authentication**.

## 🚀 Features
* **🤖 AI Summarization:** Uses deep learning to generate concise summaries.
* **🔐 Secure Login:** Sign in with your Google Account (OAuth 2.0).
* **☁️ Cloud History:** Automatically saves your summaries to a secure database.
* **📂 Multi-Format Support:** Upload PDF, DOCX, TXT, or paste a URL.
* **🌓 Modern UI:** Features a side-by-side comparison view and clean design.

## 🛠️ Tech Stack
* **Frontend:** Streamlit
* **AI Model:** HuggingFace Transformers (`facebook/bart-large-cnn`)
* **Backend/Auth:** Firebase Firestore & Authentication
* **Lang:** Python 3.10+

## 📦 Installation
1.  **Clone the repo:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/SmartDoc-Summarizer.git]
    cd SmartDoc-Summarizer
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Setup Secrets:**
    Create a `.streamlit/secrets.toml` file with your Google & Firebase keys.

4.  **Run the App:**
    ```bash
    streamlit run app.py
    ```

## ☁️ Deployment
This app is ready for deployment on **Streamlit Community Cloud**.
Ensure you add your `[google]` and `[firebase]` credentials to the Cloud Secrets dashboard.

---
*Created by Johan*
*Co-Created by Abishek*