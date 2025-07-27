import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
from typing import List
from litellm import completion

# -------------------- Constants -------------------- #
USER_FILE = "user.csv"
INVENTORY_FILE = "inventory.csv"
CATEGORY_FILE = "category.json"
st.set_page_config(page_title="Inventory Manager", layout="wide")

# -------------------- Utils -------------------- #
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    return pd.DataFrame(columns=["email", "password"])

def save_users(users):
    users.to_csv(USER_FILE, index=False)

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    return pd.DataFrame()

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

def load_categories():
    if os.path.exists(CATEGORY_FILE):
        with open(CATEGORY_FILE, 'r') as f:
            return json.load(f)
    return []

def save_categories(categories):
    with open(CATEGORY_FILE, 'w') as f:
        json.dump(categories, f)

# -------------------- Auth Pages -------------------- #
def login_page():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        users = load_users()
        if not users.empty and email in users['email'].values:
            stored_password = users[users['email'] == email]['password'].values[0]
            if verify_password(password, stored_password):
                st.session_state['authenticated'] = True
                st.session_state['user'] = email
                st.rerun()
            else:
                st.error("Incorrect password")
        else:
            st.error("User not found")

def signup_page():
    st.title("Signup")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Signup"):
        users = load_users()
        if email in users['email'].values:
            st.error("Email already exists")
        else:
            new_user = pd.DataFrame([[email, hash_password(password)]], columns=["email", "password"])
            users = pd.concat([users, new_user], ignore_index=True)
            save_users(users)
            st.success("Signup successful. Please login.")

def change_password():
    st.subheader("Change Password")
    current_pwd = st.text_input("Current Password", type="password")
    new_pwd = st.text_input("New Password", type="password")
    if st.button("Update Password"):
        users = load_users()
        user = st.session_state['user']
        if user in users['email'].values:
            stored_pwd = users[users['email'] == user]['password'].values[0]
            if verify_password(current_pwd, stored_pwd):
                users.loc[users['email'] == user, 'password'] = hash_password(new_pwd)
                save_users(users)
                st.success("Password updated successfully")
            else:
                st.error("Incorrect current password")

# -------------------- Inventory Pages -------------------- #
def view_inventory():
    st.subheader("Inventory Table")
    df = load_inventory()
    if not df.empty:
        df['Action'] = df.index.map(lambda i: f"Delete_{i}")
        edited_rows = []
        for i, row in df.iterrows():
            cols = st.columns(len(row))
            for j, key in enumerate(df.columns):
                if key == 'Action':
                    if cols[j].button("Delete", key=row['Action']):
                        df.drop(i, inplace=True)
                        save_inventory(df)
                        st.rerun()
                else:
                    cols[j].write(row[key])
    else:
        st.info("No inventory items yet.")

def add_inventory():
    st.subheader("Add Inventory Item")
    categories = load_categories()
    df = load_inventory()
    new_row = {}
    new_row['ID#'] = int(datetime.now().timestamp())
    for cat in categories:
        if cat['type'] == 'number':
            new_row[cat['name']] = st.number_input(cat['name'], value=0.0, key=cat['name'])
        else:
            new_row[cat['name']] = st.text_input(cat['name'], key=cat['name'])

    if st.button("Add Item"):
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_inventory(df)
        st.success("Item added successfully")

    st.markdown("---")
    st.subheader("Add New Category")
    cat_name = st.text_input("Category Name")
    cat_type = st.selectbox("Data Type", ["text", "number"])
    if st.button("Add Category"):
        categories.append({"name": cat_name, "type": cat_type})
        save_categories(categories)
        st.success("Category added. Refreshing page...")
        st.rerun()

def update_column():
    st.subheader("Update Columns by ID#")
    df = load_inventory()
    id_to_edit = st.text_input("Enter ID# to edit")
    if id_to_edit and id_to_edit.isdigit():
        id_to_edit = int(id_to_edit)
        row = df[df['ID#'] == id_to_edit]
        if not row.empty:
            idx = row.index[0]
            for col in df.columns:
                if col not in ['ID#']:
                    new_val = st.text_input(f"{col}", value=str(df.at[idx, col]))
                    df.at[idx, col] = new_val
            if st.button("Update Row"):
                save_inventory(df)
                st.success("Row updated.")
        else:
            st.warning("No row found with that ID#")

def add_category_page():
    st.subheader("Add New Category (Customize Columns)")
    categories = load_categories()
    name = st.text_input("New Column Name")
    dtype = st.selectbox("Column Type", ["text", "number"])
    if st.button("Add Column"):
        categories.append({"name": name, "type": dtype})
        save_categories(categories)
        st.success("New column added.")

def ask_inventory_agent():
    st.subheader("Ask Inventory Agent")
    prompt = st.text_area("Ask a question about your inventory")
    if st.button("Ask") and prompt:
        df = load_inventory()
        data_preview = df.head(10).to_string()
        full_prompt = f"Answer the following about this inventory data:
{data_preview}

Q: {prompt}\nA:"
        response = completion(
            model="groq/llama3-8b-8192",
            messages=[{"role": "user", "content": full_prompt}]
        )
        st.markdown("**Response:**")
        st.write(response.choices[0].message.content)

# -------------------- Main -------------------- #
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    tab1, tab2 = st.tabs(["Login", "Signup"])
    with tab1:
        login_page()
    with tab2:
        signup_page()
else:
    menu = st.sidebar.radio("Navigation", ["View Inventory", "Add Item", "Update Column", "Add Category", "Ask Inventory Agent", "Change Password", "Logout"])

    if menu == "View Inventory":
        view_inventory()
    elif menu == "Add Item":
        add_inventory()
    elif menu == "Update Column":
        update_column()
    elif menu == "Add Category":
        add_category_page()
    elif menu == "Ask Inventory Agent":
        ask_inventory_agent()
    elif menu == "Change Password":
        change_password()
    elif menu == "Logout":
        st.session_state['authenticated'] = False
        st.session_state['user'] = None
        st.rerun()
