import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
from typing import List

# --- File Paths ---
USER_FILE = "user.csv"
CATEGORY_FILE = "category.json"
INVENTORY_FILE = "inventory.csv"

st.set_page_config(page_title="Inventory Manager", layout="wide")

# --- Session State Init ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# --- Utility Functions ---
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    else:
        return pd.DataFrame(columns=["username", "email", "password"])

def save_users(users):
    users.to_csv(USER_FILE, index=False)

def load_categories():
    if os.path.exists(CATEGORY_FILE):
        with open(CATEGORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_categories(data):
    with open(CATEGORY_FILE, "w") as f:
        json.dump(data, f)

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    else:
        return pd.DataFrame()

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

def delete_row_by_id(df, id_value):
    df = df[df['ID#'] != id_value]
    save_inventory(df)
    return df

# --- Authentication ---
def login_signup():
    users = load_users()
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        st.subheader("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username in users.username.values:
                user_row = users[users["username"] == username]
                if hash_password(password) == user_row.iloc[0]["password"]:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("Incorrect password")
            else:
                st.error("Username not found")

    with tab2:
        st.subheader("Signup")
        new_username = st.text_input("Choose Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Choose Password", type="password")
        if st.button("Signup"):
            if new_username in users.username.values:
                st.warning("Username already exists")
            else:
                users = users.append({"username": new_username, "email": new_email, "password": hash_password(new_password)}, ignore_index=True)
                save_users(users)
                st.success("Signup successful! Please login.")

# --- Change Password ---
def change_password():
    users = load_users()
    st.subheader("Change Password")
    current_pass = st.text_input("Current Password", type="password")
    new_pass = st.text_input("New Password", type="password")
    if st.button("Update Password"):
        user_row = users[users["username"] == st.session_state.username]
        if hash_password(current_pass) == user_row.iloc[0]["password"]:
            users.loc[users["username"] == st.session_state.username, "password"] = hash_password(new_pass)
            save_users(users)
            st.success("Password updated successfully!")
        else:
            st.error("Current password incorrect")

# --- Add Category ---
def add_category():
    st.subheader("Add Category")
    categories = load_categories()
    category_name = st.text_input("New Category Name")

    if category_name:
        column_count = st.number_input("How many columns in this category?", min_value=1, max_value=20, step=1)
        custom_columns = []
        for i in range(column_count):
            col_name = st.text_input(f"Column {i+1} Name", key=f"col_name_{i}")
            col_type = st.selectbox(f"Column {i+1} Type", ["text", "number"], key=f"col_type_{i}")
            custom_columns.append({"name": col_name, "type": col_type})

        if st.button("Save Category"):
            categories[category_name] = custom_columns
            save_categories(categories)
            st.success(f"Category '{category_name}' added successfully")

# --- Add Inventory Item ---
def add_inventory():
    st.subheader("Add New Inventory Item")
    df = load_inventory()
    categories = load_categories()

    selected_category = st.selectbox("Select Category", list(categories.keys()))
    if selected_category:
        item_data = {}
        item_data["ID#"] = int(datetime.now().timestamp())
        item_data["Category"] = selected_category

        for col in categories[selected_category]:
            col_name = col["name"]
            col_type = col["type"]
            if col_type == "number":
                item_data[col_name] = st.number_input(col_name, value=0.0)
            else:
                item_data[col_name] = st.text_input(col_name)

        if st.button("Add Item"):
            new_row = pd.DataFrame([item_data])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            save_inventory(updated_df)
            st.success("Item added successfully")

# --- View Inventory ---
def view_inventory():
    st.subheader("View Inventory")
    df = load_inventory()
    if df.empty:
        st.info("No items found")
        return

    # Add Delete buttons to each row
    def delete_callback(id_val):
        updated_df = delete_row_by_id(df, id_val)
        st.rerun()

    # Add delete button column
    df["Action"] = df["ID#"].apply(lambda x: f"Delete_{x}")
    for index, row in df.iterrows():
        delete_btn = st.button("DELETE", key=f"del_{row['ID#']}")
        if delete_btn:
            delete_callback(row["ID#"])

    st.dataframe(df.drop(columns=["Action"]))

# --- Update Columns ---
def update_column():
    st.subheader("Update Inventory Row")
    df = load_inventory()
    row_id = st.text_input("Enter ID# of row to update")

    if row_id:
        row_id = int(row_id)
        if row_id in df["ID#"].values:
            row_data = df[df["ID#"] == row_id].iloc[0].to_dict()
            updated_data = {}
            for col in df.columns:
                if col not in ["ID#", "Category"]:
                    updated_data[col] = st.text_input(f"{col}", value=row_data[col])
            if st.button("Update Row"):
                for col in updated_data:
                    df.loc[df["ID#"] == row_id, col] = updated_data[col]
                save_inventory(df)
                st.success("Row updated successfully")
                st.rerun()
        else:
            st.warning("ID# not found")

# --- Ask Inventory Agent ---
def ask_inventory_agent():
    from openai import OpenAI
    st.subheader("Ask Inventory Agent")
    query = st.text_input("Ask your question about the inventory")
    if st.button("Get Answer"):
        df = load_inventory()
        full_prompt = f"""Answer the following question about this inventory data:
{df.to_string(index=False)}

Question: {query}"""
        # Replace with your actual Groq API call logic
        st.info("(This would send the prompt to Groq API and return an answer)")

# --- Main App ---
if not st.session_state.logged_in:
    login_signup()
else:
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Add Inventory", "Add Category", "View Inventory", "Update Column", "Ask Agent", "Change Password", "Logout"])

    if page == "Add Inventory":
        add_inventory()
    elif page == "Add Category":
        add_category()
    elif page == "View Inventory":
        view_inventory()
    elif page == "Update Column":
        update_column()
    elif page == "Ask Agent":
        ask_inventory_agent()
    elif page == "Change Password":
        change_password()
    elif page == "Logout":
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
