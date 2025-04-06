import streamlit as st
import os
import json
import re
from datetime import datetime

DATA_DIR = "tab_data"

def get_all_tabs_data():
    """Return a list of tab data from the latest JSON file."""
    latest_file_path = os.path.join(DATA_DIR, "latest.json")
    if not os.path.exists(latest_file_path):
        return []
    try:
        with open(latest_file_path, "r", encoding="utf-8") as f:
            latest_info = json.load(f)
        data_file_path = os.path.join(DATA_DIR, latest_info["filename"])
        if not os.path.exists(data_file_path):
            return []
        with open(data_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "tabsData" in data:
            return data["tabsData"]
        elif "tabData" in data:
            return [data["tabData"]]
        else:
            return []
    except Exception as e:
        st.error(f"Error reading tab data: {str(e)}")
        return []

def format_timestamp(timestamp_str):
    """Convert an ISO timestamp to a readable format."""
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        return timestamp.strftime("%B %d, %Y at %I:%M %p")
    except Exception:
        return timestamp_str

def match_question_to_tab(question, tabs_data):
    """Simple matching: check if the tab title or URL appears in the question."""
    question_lower = question.lower()
    for tab in tabs_data:
        title = tab.get('title', '').lower()
        url = tab.get('url', '').lower()
        if title and title in question_lower:
            return tab
        if url and url in question_lower:
            return tab
    # Fallback: return the first tab if no clear match is found
    return tabs_data[0] if tabs_data else None

st.set_page_config(
    page_title="Active Tab Reader",
    page_icon="🌐",
    layout="wide"
)

st.title("🌐 Active Tab Reader")

# Sidebar instructions and connection checker
with st.sidebar:
    st.header("Chrome Extension Setup")
    st.write("""
    1. Install and load the Chrome extension from the `extension` folder.
    2. Enable "Auto-share all tabs".
    3. Browse any webpages.
    """)
    st.header("How To Use")
    st.write("""
    1. Navigate to any webpages in Chrome.
    2. The extension will automatically share content from all open tabs.
    3. Return here to ask questions about the pages.
    """)
    if st.button("Check Extension Connection"):
        tabs_data = get_all_tabs_data()
        if tabs_data:
            st.success(f"Connected! {len(tabs_data)} tab(s) received. Last update: {format_timestamp(tabs_data[0].get('timestamp', ''))}")
        else:
            st.error("No data received from extension yet.")

col1, col2 = st.columns([2, 3])

with col1:
    st.header("List of Active Tabs")
    tabs_data = get_all_tabs_data()
    if tabs_data:
        for tab in tabs_data:
            st.subheader(tab.get('title', 'Unknown Tab'))
            st.write(f"URL: {tab.get('url', 'Unknown URL')}")
            with st.expander("Page Content Preview"):
                # Try to get content text from either the main content object or directly
                content = (tab.get('textContent') or 
                           (tab.get('content', {}).get('textContent') if isinstance(tab.get('content'), dict) else "No content available"))
                st.write((content[:1000] + "...") if content else "No content available")
    else:
        st.info("No active tab data available. Ensure the Chrome extension is installed and enabled.")

with col2:
    st.header("Ask About a Website")
    question = st.text_input("Enter your question about one of the websites:")
    if tabs_data and question:
        relevant_tab = match_question_to_tab(question, tabs_data)
        if relevant_tab:
            st.subheader(f"Answer Based on: {relevant_tab.get('title', 'Unknown')}")
            # Replace this with actual analysis logic as needed.
            answer = f"Simulated answer for your question '{question}' based on {relevant_tab.get('url', 'Unknown URL')}."
            st.write(answer)
        else:
            st.info("No matching website found.")

# Maintain a simple chat history in session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if tabs_data and question:
    st.session_state.chat_history.append({"question": question, "answer": answer})
    
if st.session_state.get("chat_history"):
    st.header("Recent Questions & Answers")
    for chat in st.session_state.chat_history[-5:]:
        with st.expander(f"Q: {chat.get('question', '')}"):
            st.write(f"A: {chat.get('answer', '')}")
