# Streamlit Inventory Management App
import streamlit as st
import pandas as pd
from typing import Dict, List
import uuid

st.set_page_config(page_title="Inventory Management", layout="wide")

# ------------------ SESSION SETUP ------------------
if "users" not in st.session_state:
    st.session_state.users = {"admin@example.com": {"password": "admin123", "username": "Admin"}}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.current_user = None

if "inventory_data" not in st.session_state:
    st.session_state.inventory_data = []

if "columns_config" not in st.session_state:
    st.session_state.columns_config = [
        {"name": "ID#", "type": "text"},
        {"name": "Action", "type": "text"},
    ]

# ------------------ AUTH ------------------
def login():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = st.session_state.users.get(email)
        if user and user["password"] == password:
            st.session_state.logged_in = True
            st.session_state.current_user = {"email": email, "username": user["username"]}
            st.rerun()
        else:
            st.error("Invalid email or password")

def signup():
    st.title("Signup")
    email = st.text_input("Email")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Signup"):
        if email in st.session_state.users:
            st.warning("User already exists")
        else:
            st.session_state.users[email] = {"password": password, "username": username}
            st.success("Signup successful. Please login.")

def logout():
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()

# ------------------ UTILITIES ------------------
def get_column_names():
    return [col["name"] for col in st.session_state.columns_config if col["name"] not in ["ID#", "Action"]]

def generate_id():
    return str(uuid.uuid4())[:8]

# ------------------ PAGES ------------------
def view_inventory():
    st.subheader("Inventory")
    columns = [col["name"] for col in st.session_state.columns_config]
    df = pd.DataFrame(st.session_state.inventory_data, columns=columns)
    st.dataframe(df, use_container_width=True)

def add_inventory():
    st.subheader("Add Inventory Item")
    item = {}
    item["ID#"] = generate_id()
    for col in get_column_names():
        item[col] = st.text_input(f"Enter {col}")
    item["Action"] = "-"
    if st.button("Add Item"):
        st.session_state.inventory_data.append(item)
        st.success("Item added")


def add_column():
    st.subheader("Add Column")
    new_col_name = st.text_input("Column Name")
    new_col_type = st.selectbox("Column Type", ["text", "number", "date"])
    if st.button("Add Column"):
        if any(col["name"] == new_col_name for col in st.session_state.columns_config):
            st.warning("Column already exists")
        else:
            st.session_state.columns_config.insert(-1, {"name": new_col_name, "type": new_col_type})
            st.success("Column added")

    st.subheader("Update Column")
    all_columns = get_column_names()
    if all_columns:
        selected = st.selectbox("Select column to update", all_columns)
        new_name = st.text_input("New Column Name", value=selected)
        if st.button("Rename Column"):
            for col in st.session_state.columns_config:
                if col["name"] == selected:
                    col["name"] = new_name
            st.success("Column renamed")
        if st.button("Delete Column"):
            st.session_state.columns_config = [col for col in st.session_state.columns_config if col["name"] != selected]
            st.success("Column deleted")


def ask_agent():
    st.subheader("Ask Inventory Agent")
    prompt = st.text_area("Ask something about your inventory")
    if st.button("Send to GroqAI"):
        # Dummy integration - replace this with actual API call
        answer = f"(GroqAI would respond to): {prompt}"
        st.write(answer)

# ------------------ MAIN APP ------------------
if not st.session_state.logged_in:
    menu = st.sidebar.selectbox("Welcome", ["Login", "Signup"])
    if menu == "Login":
        login()
    else:
        signup()
else:
    st.sidebar.markdown(f"### 👤 {st.session_state.current_user['username']}")
    if st.sidebar.button("Logout"):
        logout()

    page = st.sidebar.radio("Navigation", ["View Inventory", "Add Inventory", "Add Column", "Ask Inventory Agent"])
    if page == "View Inventory":
        view_inventory()
    elif page == "Add Inventory":
        add_inventory()
    elif page == "Add Column":
        add_column()
    elif page == "Ask Inventory Agent":
        ask_agent()
