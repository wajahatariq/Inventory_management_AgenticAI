import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict

USER_FILE = "user.csv"
INVENTORY_FILE = "inventory.csv"
CATEGORY_FILE = "category.json"
st.set_page_config(page_title="Inventory Manager", layout="wide")

# -------------------------- Utility Functions --------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    return pd.read_csv(USER_FILE) if os.path.exists(USER_FILE) else pd.DataFrame(columns=["username", "email", "password"])

def save_users(df):
    df.to_csv(USER_FILE, index=False)

def load_categories():
    if os.path.exists(CATEGORY_FILE):
        with open(CATEGORY_FILE) as f:
            return json.load(f)
    return {}

def save_categories(data):
    with open(CATEGORY_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_inventory():
    return pd.read_csv(INVENTORY_FILE) if os.path.exists(INVENTORY_FILE) else pd.DataFrame()

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

# -------------------------- Login/Signup --------------------------
def login_signup():
    st.title("Inventory Management Login")
    option = st.radio("Choose", ["Login", "Signup"])

    if option == "Login":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            users = load_users()
            if username in users["username"].values:
                user_row = users[users["username"] == username]
                if user_row.iloc[0]["password"] == hash_password(password):
                    st.success(f"Welcome, {username}!")
                    return True, username
                else:
                    st.error("Incorrect password.")
            else:
                st.error("Username not found.")

    elif option == "Signup":
        new_username = st.text_input("Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")

        if st.button("Signup"):
            users = load_users()
            if new_username in users["username"].values:
                st.error("Username already exists.")
            else:
                new_user = pd.DataFrame([[new_username, new_email, hash_password(new_password)]],
                                        columns=["username", "email", "password"])
                users = pd.concat([users, new_user], ignore_index=True)
                save_users(users)
                st.success("Account created! Please log in.")
                st.experimental_rerun()

    return False, None

# -------------------------- Sidebar --------------------------
def sidebar_navigation():
    return st.sidebar.radio("Navigation", ["View Inventory", "Add Item", "Add Category", "Update Column", "Ask the Agent", "Change Password", "Logout"])

# -------------------------- Add Category --------------------------
def add_category():
    st.subheader("Add Category with Custom Columns")
    categories = load_categories()

    category_name = st.text_input("Enter Category Name")
    new_columns = []

    if category_name:
        num_cols = st.number_input("How many columns to add?", min_value=1, step=1)
        for i in range(int(num_cols)):
            col_name = st.text_input(f"Column {i+1} Name")
            col_type = st.selectbox(f"Column {i+1} Type", ["text", "number", "date", "boolean"], key=f"type_{i}")
            if col_name:
                new_columns.append({"name": col_name, "type": col_type})

        if st.button("Save Category"):
            if category_name in categories:
                st.error("Category already exists!")
            else:
                categories[category_name] = new_columns
                save_categories(categories)
                st.success("Category saved!")

# -------------------------- Add Item --------------------------
def add_item():
    st.subheader("Add Inventory Item")
    categories = load_categories()
    if not categories:
        st.warning("No categories found. Please add a category first.")
        return

    category = st.selectbox("Choose Category", list(categories.keys()))
    fields = categories[category]

    item = {"ID#": datetime.now().strftime("%Y%m%d%H%M%S")}
    for field in fields:
        name, field_type = field["name"], field["type"]
        if field_type == "text":
            item[name] = st.text_input(name)
        elif field_type == "number":
            item[name] = st.number_input(name)
        elif field_type == "date":
            item[name] = st.date_input(name)
        elif field_type == "boolean":
            item[name] = st.checkbox(name)

    if st.button("Add Item"):
        inventory = load_inventory()
        for col in item:
            if col not in inventory.columns:
                inventory[col] = ""
        new_row = pd.DataFrame([item])
        inventory = pd.concat([inventory, new_row], ignore_index=True)
        save_inventory(inventory)
        st.success("Item added to inventory.")

# -------------------------- View Inventory --------------------------
def view_inventory():
    st.subheader("Inventory List")
    df = load_inventory()
    if df.empty:
        st.warning("No inventory data found.")
        return

    st.dataframe(df)

    selected_id = st.selectbox("Select ID# to Delete", df["ID#"].unique())
    if st.button("Delete Row"):
        df = df[df["ID#"] != selected_id]
        save_inventory(df)
        st.success("Row deleted.")

# -------------------------- Update Column --------------------------
def update_column():
    st.subheader("Update Column of a Row")
    df = load_inventory()
    if df.empty:
        st.warning("No data found")
        return

    row_id = st.selectbox("Select ID# to update", df["ID#"].unique())
    column = st.selectbox("Select Column", df.columns.drop("ID#"))
    new_value = st.text_input("Enter New Value")

    if st.button("Update"):
        df.loc[df["ID#"] == row_id, column] = new_value
        save_inventory(df)
        st.success("Updated successfully!")

# -------------------------- Change Password --------------------------
def change_password(username):
    st.subheader("Change Password")
    users = load_users()
    old_password = st.text_input("Old Password", type="password")
    new_password = st.text_input("New Password", type="password")

    if st.button("Update Password"):
        user_row = users[users["username"] == username]
        if user_row.iloc[0]["password"] == hash_password(old_password):
            users.loc[users["username"] == username, "password"] = hash_password(new_password)
            save_users(users)
            st.success("Password updated successfully")
        else:
            st.error("Incorrect old password")

# -------------------------- Ask the Agent --------------------------
def ask_inventory_agent():
    st.subheader("Ask the Inventory Agent")
    question = st.text_area("Ask a question about the inventory")
    df = load_inventory()

    if st.button("Ask") and question:
        full_prompt = f"""Answer the following about this inventory data:

Inventory:
{df.to_string(index=False)}

Question:
{question}
"""
        st.info("(Simulated response) This is where the LLM would generate an answer.")
        st.success("Pretend answer: Here's your intelligent response based on the data.")

# -------------------------- Main --------------------------
login_success, current_user = login_signup()
if not login_success:
    st.stop()

page = sidebar_navigation()

if page == "View Inventory":
    view_inventory()
elif page == "Add Item":
    add_item()
elif page == "Add Category":
    add_category()
elif page == "Update Column":
    update_column()
elif page == "Change Password":
    change_password(current_user)
elif page == "Ask the Agent":
    ask_inventory_agent()
elif page == "Logout":
    st.info("You have been logged out. Please refresh to login again.")
    st.stop()
