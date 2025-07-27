# inventory_management.py

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
from litellm import completion

USER_FILE = "user.csv"
CATEGORY_FILE = "categories.json"
INVENTORY_FILE = "inventory.csv"

st.set_page_config(page_title="Inventory Manager", layout="wide")

# --- Helper Functions ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if not os.path.exists(USER_FILE):
        return pd.DataFrame(columns=["email", "password"])
    return pd.read_csv(USER_FILE)

def save_users(df):
    df.to_csv(USER_FILE, index=False)

def load_categories():
    if not os.path.exists(CATEGORY_FILE):
        return {}
    with open(CATEGORY_FILE, "r") as f:
        return json.load(f)

def save_categories(categories):
    with open(CATEGORY_FILE, "w") as f:
        json.dump(categories, f)

def load_inventory():
    if not os.path.exists(INVENTORY_FILE):
        return pd.DataFrame(columns=["ID"])
    return pd.read_csv(INVENTORY_FILE)

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

# --- Authentication ---
def login_signup():
    st.title("Login / Signup")
    auth_action = st.radio("Select Action", ["Login", "Signup"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    users = load_users()

    if auth_action == "Signup":
        if st.button("Signup"):
            if email in users.email.values:
                st.warning("Email already exists")
            else:
                new_user = pd.DataFrame([[email, hash_password(password)]], columns=["email", "password"])
                users = pd.concat([users, new_user], ignore_index=True)
                save_users(users)
                st.success("Signup successful. Please login.")

    elif auth_action == "Login":
        if st.button("Login"):
            if email in users.email.values:
                user_row = users[users["email"] == email]
                if hash_password(password) == user_row.iloc[0]["password"]:
                    st.session_state["user"] = email
                    st.rerun()
                else:
                    st.error("Incorrect password")
            else:
                st.error("User not found")

# --- Sidebar ---
def sidebar():
    st.sidebar.title("Inventory Navigation")
    choice = st.sidebar.radio("Select Page", [
        "View Inventory",
        "Add Inventory",
        "Add Category",
        "Update Column",
        "Ask Agent",
        "Change Password",
        "Logout"
    ])
    return choice

# --- Add/Update Category ---
def add_category():
    st.title("Add or Update Category")
    categories = load_categories()

    category_name = st.text_input("Category Name")

    if category_name:
        if category_name in categories:
            st.info("Updating existing category")
            fields = categories[category_name]
        else:
            st.info("Creating new category")
            fields = []

        with st.form("add_fields_form"):
            num_fields = st.number_input("How many fields to add?", min_value=1, step=1)
            new_fields = []
            for i in range(int(num_fields)):
                col_name = st.text_input(f"Column {i+1} Name")
                col_type = st.selectbox(f"Column {i+1} Type", ["text", "number", "date", "boolean", "dropdown"], key=f"type_{i}")
                new_fields.append({"name": col_name, "type": col_type})

            submitted = st.form_submit_button("Save Category")
            if submitted:
                categories[category_name] = new_fields
                save_categories(categories)
                st.success(f"Category '{category_name}' saved successfully.")

# --- Add Inventory ---
def add_inventory():
    st.title("Add Inventory")
    categories = load_categories()
    inventory = load_inventory()

    category_name = st.selectbox("Select Category", list(categories.keys()))
    if category_name:
        fields = categories[category_name]
        record = {"Category": category_name}

        for field in fields:
            field_name = field["name"]
            field_type = field["type"]
            if field_type == "number":
                record[field_name] = st.number_input(field_name)
            elif field_type == "text":
                record[field_name] = st.text_input(field_name)
            elif field_type == "date":
                record[field_name] = st.date_input(field_name)
            elif field_type == "boolean":
                record[field_name] = st.checkbox(field_name)
            elif field_type == "dropdown":
                record[field_name] = st.selectbox(field_name, ["Option 1", "Option 2"])  # customize

        if st.button("Add Item"):
            new_id = inventory["ID"].max() + 1 if not inventory.empty else 1
            record["ID"] = new_id
            inventory = pd.concat([inventory, pd.DataFrame([record])], ignore_index=True)
            save_inventory(inventory)
            st.success("Inventory item added.")

# --- View Inventory ---
def view_inventory():
    st.title("Inventory Records")
    inventory = load_inventory()
    if inventory.empty:
        st.info("No inventory available.")
        return

    def delete_row(index):
        inventory.drop(index, inplace=True)
        save_inventory(inventory)
        st.experimental_rerun()

    for i, row in inventory.iterrows():
        with st.expander(f"ID# {row['ID']}"):
            st.write(row.drop(labels=['ID']))
            if st.button(f"Delete ID# {row['ID']}", key=f"del_{i}"):
                delete_row(i)

# --- Update Column (by ID) ---
def update_column():
    st.title("Update Inventory Item by ID")
    inventory = load_inventory()
    categories = load_categories()

    if inventory.empty:
        st.info("No inventory available.")
        return

    id_ = st.number_input("Enter ID# to update", min_value=1, step=1)
    if id_ not in inventory["ID"].values:
        st.warning("ID not found")
        return

    row = inventory[inventory["ID"] == id_].iloc[0]
    category_name = row.get("Category")
    fields = categories.get(category_name, [])

    record = {"ID": id_, "Category": category_name}

    for field in fields:
        field_name = field["name"]
        field_type = field["type"]
        if field_type == "number":
            record[field_name] = st.number_input(field_name, value=row.get(field_name, 0))
        elif field_type == "text":
            record[field_name] = st.text_input(field_name, value=row.get(field_name, ""))
        elif field_type == "date":
            record[field_name] = st.date_input(field_name, value=pd.to_datetime(row.get(field_name)))
        elif field_type == "boolean":
            record[field_name] = st.checkbox(field_name, value=row.get(field_name, False))
        elif field_type == "dropdown":
            record[field_name] = st.selectbox(field_name, ["Option 1", "Option 2"], index=0)

    if st.button("Update Row"):
        inventory.loc[inventory["ID"] == id_, list(record.keys())] = list(record.values())
        save_inventory(inventory)
        st.success("Inventory updated successfully.")

# --- Change Password ---
def change_password():
    st.title("Change Password")
    users = load_users()
    email = st.session_state.get("user")
    old_pwd = st.text_input("Old Password", type="password")
    new_pwd = st.text_input("New Password", type="password")

    if st.button("Change Password"):
        user_row = users[users["email"] == email]
        if hash_password(old_pwd) == user_row.iloc[0]["password"]:
            users.loc[users["email"] == email, "password"] = hash_password(new_pwd)
            save_users(users)
            st.success("Password changed successfully")
        else:
            st.error("Old password incorrect")

# --- Ask Agent ---
def ask_agent():
    st.title("Ask Inventory Agent")
    query = st.text_input("What do you want to ask?")
    inventory = load_inventory()
    if st.button("Ask") and query:
        df_str = inventory.to_string()
        full_prompt = f"""Answer the following about this inventory data:
        Data:
        {df_str}

        Question: {query}
        Answer: """
        res = completion(model="groq/llama3-8b-8192", messages=[{"role": "user", "content": full_prompt}])
        st.write(res["choices"][0]["message"]["content"])

# --- Main App ---
if "user" not in st.session_state:
    login_signup()
else:
    page = sidebar()
    if page == "View Inventory":
        view_inventory()
    elif page == "Add Inventory":
        add_inventory()
    elif page == "Add Category":
        add_category()
    elif page == "Update Column":
        update_column()
    elif page == "Change Password":
        change_password()
    elif page == "Ask Agent":
        ask_agent()
    elif page == "Logout":
        st.session_state.pop("user")
        st.rerun()
