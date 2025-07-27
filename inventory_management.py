import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient, models
from qdrant_client.models import PointStruct

USER_FILE = "user.csv"
INVENTORY_FILE = "inventory.csv"
CATEGORY_FILE = "category.json"
st.set_page_config(page_title="Inventory Manager", layout="wide")

# Ensure user file exists
if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=["email", "username", "password"]).to_csv(USER_FILE, index=False)

# --- Password hashing ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# --- Authentication ---
def login_signup():
    st.title("Login / Signup")
    users = pd.read_csv(USER_FILE)

    choice = st.radio("Choose an option", ["Login", "Signup"])

    if choice == "Signup":
        email = st.text_input("Email")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Create Account"):
            if email in users['email'].values or username in users['username'].values:
                st.error("User with this email or username already exists.")
            else:
                new_user = pd.DataFrame([[email, username, hash_password(password)]], columns=["email", "username", "password"])
                new_user.to_csv(USER_FILE, mode='a', header=False, index=False)
                st.success("Account created successfully. Please login.")

    else:
        login_id = st.text_input("Email or Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            password_hash = hash_password(password)
            user_row = users[(users["email"] == login_id) | (users["username"] == login_id)]
            if not user_row.empty and user_row.iloc[0]["password"] == password_hash:
                st.session_state.logged_in = True
                st.session_state.user_email = user_row.iloc[0]['email']
                st.experimental_rerun()
            else:
                st.error("Invalid credentials.")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_signup()
    st.stop()

# Once logged in, your app continues from here (view inventory, add, etc.)
st.sidebar.title("Navigation")
st.sidebar.write(f"Logged in as: {st.session_state.user_email}")
st.sidebar.page_link("/view_inventory", label="View Inventory")
st.sidebar.page_link("/add_inventory", label="Add Items")
st.sidebar.page_link("/add_category", label="Add Category")
st.sidebar.page_link("/update_column", label="Update Column")
st.sidebar.page_link("/change_password", label="Change Password")
st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False}))
