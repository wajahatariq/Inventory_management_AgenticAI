import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from groq import Groq

# Initialize session state for login if not already set
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""

# File paths
USERS_FILE = 'users.json'
COLUMNS_FILE = 'columns.json'
INVENTORY_FILE = 'inventory.csv'

# Load or initialize users
if os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
else:
    users = {}

# Load or initialize columns
if os.path.exists(COLUMNS_FILE):
    with open(COLUMNS_FILE, 'r') as f:
        columns = json.load(f)
else:
    columns = [
        {"name": "ID#", "type": "number"},
        {"name": "Action", "type": "text"}
    ]
    with open(COLUMNS_FILE, 'w') as f:
        json.dump(columns, f)

# Ensure inventory file exists with correct columns
if not os.path.exists(INVENTORY_FILE):
    df = pd.DataFrame(columns=[col['name'] for col in columns])
    df.to_csv(INVENTORY_FILE, index=False)

# Groq Client Setup (replace with your actual key)
client = Groq(api_key="your_groq_api_key")

def save_users():
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def save_columns():
    with open(COLUMNS_FILE, 'w') as f:
        json.dump(columns, f)

def load_inventory():
    return pd.read_csv(INVENTORY_FILE)

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

def login_signup():
    st.title("Inventory Management Login")
    tab1, tab2 = st.tabs(["Login", "Signup"])

    with tab1:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            if username in users and users[username]['password'] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("Logged in successfully!")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

    with tab2:
        new_username = st.text_input("Choose a Username")
        new_password = st.text_input("Choose a Password", type="password")
        if st.button("Signup"):
            if new_username in users:
                st.error("Username already exists")
            else:
                users[new_username] = {"password": new_password}
                save_users()
                st.success("Account created! Please login.")

def add_column():
    st.subheader("Add Column")
    new_column_name = st.text_input("Enter new column name")
    new_column_type = st.selectbox("Select column type", ["text", "number", "date"])
    if st.button("Add Column"):
        if new_column_name.strip():
            if any(col['name'] == new_column_name for col in columns):
                st.warning("Column already exists")
            else:
                columns.insert(-1, {"name": new_column_name, "type": new_column_type})
                save_columns()
                df = load_inventory()
                df[new_column_name] = ""
                save_inventory(df)
                st.success("Column added successfully")
        else:
            st.warning("Column name cannot be empty")

    st.subheader("Update Column")
    column_names = [col['name'] for col in columns if col['name'] not in ["ID#", "Action"]]
    selected_col = st.selectbox("Select column to update", ["None"] + column_names)
    if selected_col != "None":
        new_name = st.text_input("Enter new column name", value=selected_col)
        if st.button("Rename Column"):
            for col in columns:
                if col['name'] == selected_col:
                    col['name'] = new_name
            save_columns()
            df = load_inventory()
            df.rename(columns={selected_col: new_name}, inplace=True)
            save_inventory(df)
            st.success("Column renamed successfully")

        if st.button("Delete Column"):
            columns[:] = [col for col in columns if col['name'] != selected_col]
            save_columns()
            df = load_inventory()
            df.drop(columns=[selected_col], inplace=True)
            save_inventory(df)
            st.success("Column deleted successfully")

def add_inventory():
    st.subheader("Add Inventory Item")
    df = load_inventory()
    new_row = {}
    for col in columns:
        if col['name'] in ["ID#", "Action"]:
            continue
        val = st.text_input(f"Enter {col['name']}")
        new_row[col['name']] = val

    if st.button("Add Item"):
        new_row['ID#'] = len(df) + 1
        new_row['Action'] = "Edit/Delete"
        df = df.append(new_row, ignore_index=True)
        save_inventory(df)
        st.success("Item added to inventory")

def view_inventory():
    st.subheader("Inventory")
    df = load_inventory()
    st.dataframe(df)

def ask_inventory_agent():
    st.subheader("Ask Inventory Agent")
    prompt = st.text_area("Enter your question about the inventory")
    if st.button("Ask"):
        try:
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[
                    {"role": "system", "content": "You are an expert inventory management assistant."},
                    {"role": "user", "content": prompt},
                ]
            )
            st.write(response.choices[0].message.content)
        except Exception as e:
            st.error(f"Error: {e}")

def main():
    if not st.session_state.authenticated:
        login_signup()
        return

    st.sidebar.title(st.session_state.username)
    page = st.sidebar.radio("", ["View Inventory", "Add Inventory", "Add Column", "Ask Inventory Agent"])
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.username = ""
        st.experimental_rerun()

    st.title("Inventory Management System")

    if page == "View Inventory":
        view_inventory()
    elif page == "Add Inventory":
        add_inventory()
    elif page == "Add Column":
        add_column()
    elif page == "Ask Inventory Agent":
        ask_inventory_agent()

if __name__ == '__main__':
    main()
