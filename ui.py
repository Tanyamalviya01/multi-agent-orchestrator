import streamlit as st
import requests

st.set_page_config(page_title="AI Council Agent")
st.title("AI Council Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "context" in msg and msg["context"]:
            with st.expander("See AI Research Context"):
                st.markdown(msg["context"])

if user_input := st.chat_input("Ask the AI Council..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Researching and Drafting..."):
            try:
                response = requests.post("http://localhost:8000/orchestrate", json={"query": user_input})
                response.raise_for_status()
                data = response.json()
                draft = data.get("draft", "No draft output.")
                context = data.get("context", "No context retrieved.")
            except Exception as e:
                draft = f"Error: {e}"
                context = ""

        st.markdown(draft)
        if context:
            with st.expander("See AI Research Context"):
                st.markdown(context)

    st.session_state.messages.append({"role": "assistant", "content": draft, "context": context})
