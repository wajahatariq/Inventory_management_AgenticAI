import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime

USER_FILE = "user.csv"
INVENTORY_FILE = "inventory.csv"

st.set_page_config(page_title="Inventory Manager", layout="wide")

# --- CUSTOM RED-BLACK STYLING ---
def add_custom_style():
    st.markdown("""
    <style>
        .stApp {
            background-color: #121212;
            color: #f0f0f0;
            font-family: 'Segoe UI', sans-serif;
        }

        section[data-testid="stSidebar"] {
            background-color: #1a1a1a;
            color: white;
        }

        section[data-testid="stSidebar"] .css-1d391kg, .css-1v3fvcr {
            color: white;
        }

        h1, h2, h3, h4 {
            color: #e50914;
        }

        .stButton>button {
            background-color: #e50914;
            color: white;
            border-radius: 5px;
            padding: 8px 16px;
            border: none;
        }

        .stButton>button:hover {
            background-color: #b00610;
            color: white;
        }

        input, textarea {
            background-color: #1f1f1f !important;
            color: white !important;
            border: 1px solid #e50914 !important;
        }

        .stTextInput>div>div>input {
            color: white;
        }

        .stAlert {
            border-radius: 5px;
            padding: 10px;
        }

        .stDataFrame {
            background-color: #1e1e1e;
            color: white;
        }

        .css-1v0mbdj {
            color: white !important;
        }
    </style>
    """, unsafe_allow_html=True)

add_custom_style()

# --- PASSWORD HASHING ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Load or initialize user data
def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    else:
        return pd.DataFrame(columns=["username", "password"])

def save_users(users_df):
    users_df.to_csv(USER_FILE, index=False)

# Load or initialize inventory data
def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    else:
        return pd.DataFrame()

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

# Column config: [{"name": "item", "type": "text"}, ...]
def save_columns(columns):
    with open("columns.json", "w") as f:
        json.dump(columns, f)

def load_columns():
    if os.path.exists("columns.json"):
        with open("columns.json", "r") as f:
            return json.load(f)
    return []

# --- SESSION INIT ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title("Login")
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            users = load_users()
            hashed = hash_password(password)
            user_match = users[
                (users["username"].str.strip() == username.strip()) &
                (users["password"] == hashed)
            ]
            if not user_match.empty:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Incorrect username or password")

    with signup_tab:
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            users = load_users()
            if new_username in users.username.values:
                st.warning("Username already exists")
            else:
                hashed = hash_password(new_password)
                users.loc[len(users)] = [new_username, hashed]
                save_users(users)
                st.success("Account created! Please log in.")

# --- LOGGED IN VIEW ---
else:
    st.sidebar.title("Navigation")
    st.sidebar.markdown(f"**Welcome, {st.session_state.username.title()}**")
    selection = st.sidebar.radio("Go to", ["View Inventory", "Add Item", "Ask the Agent", "Column Manager", "Change Password"])

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    columns = load_columns()

    if columns and isinstance(columns[0], str):
        columns = [{"name": col, "type": "text"} for col in columns]
        save_columns(columns)

    df = load_inventory()

    for col in columns:
        if col["name"] not in df.columns:
            df[col["name"]] = ""
    save_inventory(df)

    # ✏️ and 🗑️ emojis are kept in Column Manager (sidebar)

    # ... (The rest of your code remains unchanged and continues as before)
