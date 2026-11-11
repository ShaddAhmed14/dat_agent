import os
import requests
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

API_URL = os.getenv("DAT_AGENT_API_URL")
if not API_URL:
    st.error("DAT_AGENT_API_URL is not set in the environment variables.")
    st.stop()
else:
    API_URL = API_URL.rstrip("/")

def list_models():
    try:
        response = requests.get(f"{API_URL}/models", timeout=10)
        response.raise_for_status()
        return response.json()
    except (requests.exceptions.RequestException, ValueError):
        st.error("Could not load providers. Start the DAT Agent backend first.")
        return []

def get_api_response(question, session_id, model_name):
    if not model_name:
        st.error("Select an available provider before sending a request.")
        return None
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"question": question, "session_id": session_id, "model": model_name},
            timeout=180,
        )
        if response.status_code != 200:
            st.error(f"Request failed ({response.status_code}): {response.json().get('detail', 'Unknown error')}")
            return None
        return response.json()
    except (requests.exceptions.RequestException, ValueError):
        st.error("Could not reach the backend or the request timed out. A timed-out operation may still complete on the server.")
        return None
