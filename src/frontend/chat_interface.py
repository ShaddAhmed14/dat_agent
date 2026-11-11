import streamlit as st
from api_utils import get_api_response

def display_chat_interface():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                st.caption(f"Provider: {message.get('model')} | Route: {message.get('route')}")

    if prompt := st.chat_input("Select a model to begin...", disabled=not st.session_state.get("selected_model")):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.spinner("Working on your request..."):
            response = get_api_response(prompt, st.session_state.session_id, st.session_state.selected_model)
        if response:
            st.session_state.session_id = response["session_id"]
            st.session_state.messages.append({"role": "assistant", **response, "content": response["answer"]})
            st.rerun()
