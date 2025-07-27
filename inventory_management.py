# --- Updated Streamlit Inventory App with All Requested Features ---

import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
from typing import List
import requests

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
        if category_name not in categories:
            if "new_columns" not in st.session_state:
                st.session_state.new_columns = []

            with st.form("Add Columns"):
                col1, col2 = st.columns(2)
                col_name = col1.text_input("Column Name")
                col_type = col2.selectbox("Column Type", ["text", "number", "date"])
                add_col = st.form_submit_button("Add Column")

                if add_col and col_name:
                    st.session_state.new_columns.append({"name": col_name, "type": col_type})

            if st.session_state.new_columns:
                st.write("### Preview Columns")
                for col in st.session_state.new_columns:
                    st.write(f"{col['name']} ({col['type']})")

                if st.button("Save Category"):
                    categories[category_name] = st.session_state.new_columns
                    save_categories(categories)
                    st.success(f"Category '{category_name}' saved!")
                    del st.session_state.new_columns
        else:
            st.warning("Category already exists")

# --- Add Inventory Item ---
def add_inventory():
    st.subheader("Add New Inventory Item")
    df = load_inventory()
    categories = load_categories()

    selected_category = st.selectbox("Select Category", list(categories.keys()))
    if selected_category:
        item_data = {"ID#": int(datetime.now().timestamp()), "Category": selected_category}

        for col in categories[selected_category]:
            col_name = col["name"]
            col_type = col["type"]
            if col_type == "number":
                item_data[col_name] = st.number_input(col_name, value=0.0)
            elif col_type == "date":
                item_data[col_name] = st.date_input(col_name).strftime('%Y-%m-%d')
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

    if "Action" not in df.columns:
        df["Action"] = ""

    display_columns = ["ID#"] + [col for col in df.columns if col not in ["ID#", "Action"] and col != "Category"] + ["Action"]

    col_count = len(display_columns)
    header = st.columns(col_count)
    for i, col in enumerate(display_columns):
        header[i].markdown(f"**{col}**")

    for idx, row in df.iterrows():
        cols = st.columns(col_count)
        for i, col in enumerate(display_columns):
            if col == "Action":
                if cols[i].button("Delete", key=f"del_{row['ID#']}_{idx}"):
                    df = delete_row_by_id(df, row["ID#"])
                    st.success(f"Deleted item with ID# {row['ID#']}")
                    st.rerun()
            else:
                cols[i].write(row.get(col, ""))

# --- Update Category ---
def update_column():
    st.subheader("Update Inventory Row / Category")

    mode = st.radio("Choose Mode", ["Update Row", "Update Category"])
    df = load_inventory()
    categories = load_categories()

    if mode == "Update Row":
        row_id = st.text_input("Enter ID# of row to update")
        if row_id:
            row_id = int(row_id)
            if row_id in df["ID#"].values:
                row_data = df[df["ID#"] == row_id].iloc[0].to_dict()
                updated_data = {}
                for col in df.columns:
                    if col not in ["ID#", "Category"]:
                        updated_data[col] = st.text_input(f"{col}", value=str(row_data[col]))
                if st.button("Update Row"):
                    for col in updated_data:
                        df.loc[df["ID#"] == row_id, col] = updated_data[col]
                    save_inventory(df)
                    st.success("Row updated successfully")
                    st.rerun()
            else:
                st.warning("ID# not found")

    elif mode == "Update Category":
        category_name = st.selectbox("Select Category to Update", list(categories.keys()))
        if category_name:
            col_names = [col["name"] for col in categories[category_name]]
            col_to_edit = st.selectbox("Select Column to Edit", col_names)

            if col_to_edit not in ["ID#", "Action"]:
                new_name = st.text_input("Rename Column To", value=col_to_edit)
                if st.button("Rename Column"):
                    for col in categories[category_name]:
                        if col["name"] == col_to_edit:
                            col["name"] = new_name
                    save_categories(categories)
                    st.success("Column renamed successfully")

                if st.button("Delete Column"):
                    categories[category_name] = [col for col in categories[category_name] if col["name"] != col_to_edit]
                    save_categories(categories)
                    st.success("Column deleted successfully")

# --- Ask Inventory Agent ---
def ask_inventory_agent():
    st.subheader("Ask Inventory Agent")
    query = st.text_input("Ask your question about the inventory")
    if st.button("Get Answer"):
        df = load_inventory()
        full_prompt = f"Answer the following question about this inventory data:\n{df.to_string(index=False)}\n\nQuestion: {query}"

        try:
            response = requests.post(
                "https://api.groq.com/v1/chat/completions",
                headers={"Authorization": f"Bearer YOUR_GROQ_API_KEY"},
                json={
                    "model": "mixtral-8x7b-32768",
                    "messages": [
                        {"role": "user", "content": full_prompt}
                    ]
                }
            )
            result = response.json()
            st.success(result['choices'][0]['message']['content'])
        except Exception as e:
            st.error(f"Failed to get response from Groq API: {e}")

# --- Main App ---
if not st.session_state.logged_in:
    login_signup()
else:
    st.sidebar.title(st.session_state.username)
    page = st.sidebar.radio("Go to", ["Add Inventory", "Add Category", "View Inventory", "Update Column", "Ask Agent", "Change Password"])
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

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
