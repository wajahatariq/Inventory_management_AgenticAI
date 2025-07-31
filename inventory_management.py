import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime

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
    df = pd.read_csv(INVENTORY_FILE) if os.path.exists(INVENTORY_FILE) else pd.DataFrame()
    categories = load_categories()
    valid_columns = ["ID#"] + list(categories.keys())
    df = df[[col for col in df.columns if col in valid_columns or col == "ID#"]]
    return df

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
                new_user = pd.DataFrame([{
                "username": new_username,
                "email": new_email,
                "password": hash_password(new_password)}])
                users = pd.concat([users, new_user], ignore_index=True)
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
            st.success("Password updated successfully")
        else:
            st.error("Current password incorrect")

# --- Manage Columns ---
def manage_columns():
    st.subheader("Manage Columns")
    categories = load_categories()

    tab1, tab2 = st.tabs(["Add Column", "Edit Column"])

    # Add Column Tab
    with tab1:
        st.markdown("#### Add Column")
        col_name = st.text_input("Column Name")
        col_type = st.selectbox("Column Type", ["text", "number", "date"])
        if st.button("Add Column"):
            if col_name in categories or col_name in ["ID#", "Action"]:
                st.warning("Column name is reserved or already exists.")
            else:
                categories[col_name] = col_type
                save_categories(categories)
                st.success(f"Column '{col_name}' added successfully")
                st.rerun()

    # Edit Column Tab
    with tab2:
        if not categories:
            st.info("No columns to edit.")
            return

        st.markdown("#### Edit Column")
        selected_col = st.selectbox("Select Column", list(categories.keys()), key="edit_select")
        subtab1, subtab2 = st.tabs(["Rename", "Delete"])

        with subtab1:
            new_col_name = st.text_input("New Column Name", value=selected_col, key="rename_input")
            if st.button("Rename Column"):
                if new_col_name in categories or new_col_name in ["ID#", "Action"]:
                    st.warning("Name is reserved or already exists.")
                else:
                    categories[new_col_name] = categories.pop(selected_col)
                    save_categories(categories)
                    st.success("Column renamed successfully")
                    st.rerun()

        with subtab2:
            st.markdown(f"Are you sure you want to delete column **{selected_col}**?")
            if st.button("Delete Column"):
                categories.pop(selected_col, None)
                save_categories(categories)
                st.success("Column deleted")
                st.rerun()

# --- Manage Inventory ---
def manage_inventory():
    st.subheader("Manage Inventory")
    df = load_inventory()
    categories = load_categories()
    tab1, tab2 = st.tabs(["Add Item", "Edit Existing Item"])

    with tab1:
        st.markdown("#### Add Inventory Item")
        item_data = {"ID#": int(datetime.now().timestamp())}
        for col_name, col_type in categories.items():
            if col_type == "number":
                item_data[col_name] = st.number_input(col_name, value=0.0, key=f"add_{col_name}")
            elif col_type == "date":
                item_data[col_name] = st.date_input(col_name, key=f"add_{col_name}").strftime("%Y-%m-%d")
            else:
                item_data[col_name] = st.text_input(col_name, key=f"add_{col_name}")

        if st.button("Add Item"):
            new_row = pd.DataFrame([item_data])
            updated_df = pd.concat([df, new_row], ignore_index=True)
            save_inventory(updated_df)
            st.success("Item added successfully")
            st.rerun()

    with tab2:
        st.markdown("#### Edit Inventory Row")
        row_id = st.text_input("Enter ID# to Edit")
        if row_id:
            try:
                row_id = int(row_id)
                if row_id in df["ID#"].values:
                    row_data = df[df["ID#"] == row_id].iloc[0].to_dict()
                    updated_data = {}
                    for col in df.columns:
                        if col != "ID#":
                            updated_data[col] = st.text_input(f"{col}", value=row_data.get(col, ""), key=f"edit_{col}")
                    if st.button("Update Row"):
                        for col in updated_data:
                            df.loc[df["ID#"] == row_id, col] = updated_data[col]
                        save_inventory(df)
                        st.success("Row updated successfully")
                        st.rerun()
                else:
                    st.warning("ID# not found")
            except:
                st.error("Invalid ID# format")

# --- View Inventory ---
def view_inventory():
    st.subheader("View Inventory")
    df = load_inventory()
    if df.empty:
        st.info("No items found")
        return

    if st.button("Export as CSV"):
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name="inventory.csv", mime="text/csv")

    columns = ["ID#"] + [col for col in df.columns if col != "ID#"] + ["Action"]
    col_count = len(columns)
    header = st.columns(col_count)
    for i, col in enumerate(columns):
        header[i].markdown(f"**{col}**")

    for idx, row in df.iterrows():
        cols = st.columns(col_count)
        for i, col in enumerate(columns):
            if col == "Action":
                if cols[i].button("Delete", key=f"del_{row['ID#']}_{idx}"):
                    df = delete_row_by_id(df, row["ID#"])
                    st.success(f"Deleted item with ID# {row['ID#']}")
                    st.rerun()
            else:
                cols[i].write(row.get(col, ""))

# --- Ask Inventory Agent ---
def ask_inventory_agent():
    import litellm
    st.subheader("Ask Inventory Agent")
    query = st.text_input("Ask your question about the inventory")
    if st.button("Get Answer"):
        df = load_inventory()
        full_prompt = f"""Answer the following question about this inventory data:\n{df.to_string(index=False)}\n\nQuestion: {query}"""
        try:
            response = litellm.completion(
                model="groq/llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are an inventory expert."},
                    {"role": "user", "content": full_prompt}
                ]
            )
            st.success(response['choices'][0]['message']['content'])
        except Exception as e:
            st.error(f"Error: {e}")

# --- Main App ---
if not st.session_state.logged_in:
    login_signup()
else:
    # Sidebar Navigation
    st.sidebar.markdown(f"Logged in as: **{st.session_state.username}**")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    page = st.sidebar.radio("Navigation", [
        "Manage Inventory", "Manage Columns", "View Inventory", 
        "Ask Agent", "Change Password"
    ])

    if page == "Manage Inventory":
        manage_inventory()
    elif page == "Manage Columns":
        manage_columns()
    elif page == "View Inventory":
        view_inventory()
    elif page == "Ask Agent":
        ask_inventory_agent()
    elif page == "Change Password":
        change_password()
