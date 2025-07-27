import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict
import uuid
import litellm

# File constants
USER_FILE = "user.csv"
INVENTORY_FILE = "inventory.csv"
CATEGORY_FILE = "categories.json"

st.set_page_config(page_title="Inventory Manager", layout="wide")

# Load Groq API key
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
litellm.api_key = GROQ_API_KEY
MODEL_NAME = "groq/llama3-70b-8192"

# Utility functions
def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    return pd.DataFrame(columns=["email", "password_hash"])

def save_users(users_df):
    users_df.to_csv(USER_FILE, index=False)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    return pd.DataFrame()

def save_inventory(inventory_df):
    inventory_df.to_csv(INVENTORY_FILE, index=False)

def load_categories():
    if os.path.exists(CATEGORY_FILE):
        with open(CATEGORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_categories(categories):
    with open(CATEGORY_FILE, "w") as f:
        json.dump(categories, f)

# Authentication
def login():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = load_users()
        if "email" not in users.columns:
            st.error("No users found. Please sign up.")
            return None
        user_row = users[users["email"] == email]
        if not user_row.empty and user_row.iloc[0]["password_hash"] == hash_password(password):
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.rerun()
        else:
            st.error("Invalid email or password")

def signup():
    st.title("Sign Up")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Create Account"):
        users = load_users()
        if email in users["email"].values:
            st.error("User already exists")
        else:
            new_user = pd.DataFrame([[email, hash_password(password)]], columns=["email", "password_hash"])
            users = pd.concat([users, new_user], ignore_index=True)
            save_users(users)
            st.success("Account created successfully. Please log in.")

def change_password():
    st.title("Change Password")
    email = st.session_state.get("user_email", "")
    current_password = st.text_input("Current Password", type="password")
    new_password = st.text_input("New Password", type="password")
    if st.button("Change Password"):
        users = load_users()
        user_row = users[users["email"] == email]
        if not user_row.empty and user_row.iloc[0]["password_hash"] == hash_password(current_password):
            users.loc[users["email"] == email, "password_hash"] = hash_password(new_password)
            save_users(users)
            st.success("Password changed successfully")
        else:
            st.error("Current password is incorrect")

# Ask Agent
def ask_agent(query, context_data):
    prompt = f"""
You are an inventory assistant. Here's the inventory data:
{context_data}

Answer this question based on it: "{query}"
If the answer is not found, say 'No relevant data found.'
"""
    response = litellm.completion(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# Main App
if "logged_in" not in st.session_state:
    option = st.sidebar.selectbox("Choose", ["Login", "Sign Up"])
    if option == "Login":
        login()
    else:
        signup()
else:
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("", ["View Inventory", "Add Item", "Update Category", "Ask Inventory Agent", "Change Password", "Logout"])

    if page == "Logout":
        st.session_state.clear()
        st.rerun()

    if page == "Change Password":
        change_password()

    if page == "Add Item":
        st.title("Add New Inventory Item")
        categories = load_categories()

        if not categories:
            st.info("Please add a category first from Update Category")
        else:
            with st.form("add_item_form"):
                item_id = str(uuid.uuid4())[:8]
                item_data = {"ID#": item_id}
                st.write("Enter item details:")
                for cat, ctype in categories.items():
                    if ctype == "text":
                        item_data[cat] = st.text_input(cat)
                    elif ctype == "number":
                        item_data[cat] = st.number_input(cat, step=1)
                    elif ctype == "price":
                        item_data[cat] = st.number_input(cat, step=0.01, format="%.2f")
                submitted = st.form_submit_button("Add Item")
                if submitted:
                    df = load_inventory()
                    new_row = pd.DataFrame([item_data])
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_inventory(df)
                    st.success("Item added successfully")

    if page == "Update Category":
        st.title("Update Categories")
        categories = load_categories()
        with st.form("update_category"):
            cat_name = st.text_input("New Category Name")
            cat_type = st.selectbox("Column Type", ["text", "number", "price"])
            submitted = st.form_submit_button("Add/Update Category")
            if submitted and cat_name:
                categories[cat_name] = cat_type
                save_categories(categories)
                st.success("Category updated")

    if page == "View Inventory":
        st.title("Inventory Table")
        df = load_inventory()
        if not df.empty:
            df_display = df.copy()
            df_display["Action"] = "Delete"
            st.dataframe(df_display)
        else:
            st.info("No inventory data found.")

    if page == "Ask Inventory Agent":
        st.title("Ask Inventory Agent")
        if os.path.exists(INVENTORY_FILE):
            inventory_df = pd.read_csv(INVENTORY_FILE)
            context_data = inventory_df.to_json(orient="records")
        else:
            context_data = "No inventory data available."

        query = st.text_input("Ask a question about your inventory:")
        if st.button("Get Answer") and query:
            answer = ask_agent(query, context_data)
            st.success(answer)
