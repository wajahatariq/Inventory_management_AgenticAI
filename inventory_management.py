import streamlit as st
import pandas as pd
import os
import uuid
import json
import hashlib

# Constants
DATA_FILE = "inventory.csv"
USERS_FILE = "users.json"
DEFAULT_COLUMNS = []

# Utility Functions
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username, password):
    users = load_users()
    return username in users and users[username] == hash_password(password)

def create_user(username, password):
    users = load_users()
    if username not in users:
        users[username] = hash_password(password)
        save_users(users)
        return True
    return False

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame()

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# App Config
st.set_page_config(page_title="Inventory Manager", layout="wide")

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Authentication Page
def login_page():
    st.title("🔐 Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate_user(username, password):
            st.session_state.authenticated = True
            st.session_state.username = username
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials.")
    st.markdown("---")
    st.subheader("Create New Account")
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    if st.button("Create Account"):
        if create_user(new_username, new_password):
            st.success("Account created successfully!")
        else:
            st.error("Username already exists.")

# Main Application
if not st.session_state.authenticated:
    login_page()
else:
    st.sidebar.title("📋 Inventory Manager")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

    df = load_data()

    # Column Management
    st.sidebar.subheader("🔧 Columns")
    if df.empty:
        columns = []
    else:
        columns = list(df.columns)

    for col in columns:
        st.sidebar.markdown(f"- {col}")

    with st.expander("Add New Column"):
        new_col_name = st.text_input("Column Name")
        new_col_type = st.selectbox("Column Type", ["Text", "Number", "Date", "Dropdown"])
        options = ""
        if new_col_type == "Dropdown":
            options = st.text_input("Options (comma separated)")
        if st.button("Add Column"):
            if new_col_name and new_col_name not in columns:
                default_value = ""
                if new_col_type == "Number":
                    default_value = 0
                elif new_col_type == "Date":
                    default_value = "2025-01-01"
                elif new_col_type == "Dropdown":
                    default_value = options.split(",")[0].strip() if options else "Option1"
                df[new_col_name] = default_value
                save_data(df)
                st.success(f"Added column '{new_col_name}'")
                st.rerun()

    st.title("🧾 Inventory Items")
    st.subheader("Add New Item")

    with st.form("add_item_form"):
        item_data = {}
        for col in df.columns:
            if df[col].dtype == 'int64' or df[col].dtype == 'float64':
                item_data[col] = st.number_input(f"{col}", step=1, key=f"input_{col}")
            elif 'date' in col.lower():
                item_data[col] = st.date_input(f"{col}", key=f"input_{col}").strftime("%Y-%m-%d")
            elif isinstance(df[col][0], str) and "," in df[col][0]:
                options = [opt.strip() for opt in df[col][0].split(",")]
                item_data[col] = st.selectbox(f"{col}", options, key=f"input_{col}")
            else:
                item_data[col] = st.text_input(f"{col}", key=f"input_{col}")
        submitted = st.form_submit_button("Add Item")

    if submitted:
        item_data["id"] = str(uuid.uuid4())
        df = pd.concat([df, pd.DataFrame([item_data])], ignore_index=True)
        save_data(df)
        st.success("Item added successfully!")
        st.rerun()

    st.subheader("📦 Current Inventory")

    # Inventory Table with Delete Option
    for i, row in df.iterrows():
        cols = st.columns([1 for _ in df.columns] + [1])
        for j, col in enumerate(df.columns):
            cols[j].markdown(f"**{col}**: {row[col]}")
        delete_button = cols[-1].button("❌", key=f"del_{row['id']}")
        if delete_button:
            df = df[df['id'] != row['id']]
            save_data(df)
            st.success(f"Deleted item {row.get('item', 'Unnamed')}")
            st.rerun()

    # Download CSV
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Inventory as CSV",
        data=csv_data,
        file_name='inventory.csv',
        mime='text/csv'
    )
