import streamlit as st
from api_utils import list_models

def display_sidebar():
    options = list_models()
    if st.session_state.get("selected_model") not in options:
        st.session_state.selected_model = options[0] if options else None
    st.sidebar.selectbox("Provider", options, key="selected_model", disabled=not options)
    st.sidebar.caption("Ask about PostgreSQL data, extract API results, or transform local data files.")
    if st.sidebar.button("New chat"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()
