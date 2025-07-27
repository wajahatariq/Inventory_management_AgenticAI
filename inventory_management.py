import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime
from typing import List
from uuid import uuid4
from litellm import completion

# ---------------------- CONFIGURATION ---------------------- #
st.set_page_config(page_title="Inventory Manager", layout="wide")

USER_FILE = "user.csv"
INVENTORY_FILE = "inventory.csv"
CATEGORY_FILE = "category.json"
PASSWORD_SALT = "inventory_salt"

# ---------------------- UTILITY FUNCTIONS ---------------------- #
def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    return pd.DataFrame(columns=["email", "password"])

def save_users(df):
    df.to_csv(USER_FILE, index=False)

def hash_password(password):
    return hashlib.sha256((PASSWORD_SALT + password).encode()).hexdigest()

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    return pd.DataFrame()

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

def load_category_config():
    if os.path.exists(CATEGORY_FILE):
        with open(CATEGORY_FILE, "r") as f:
            return json.load(f)
    return {}

def save_category_config(config):
    with open(CATEGORY_FILE, "w") as f:
        json.dump(config, f)

def validate_email(email):
    return "@" in email and "." in email

# ---------------------- SESSION SETUP ---------------------- #
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "email" not in st.session_state:
    st.session_state.email = ""

# ---------------------- LOGIN / SIGNUP ---------------------- #
def login_signup():
    st.title("Login or Signup")
    mode = st.selectbox("Select Mode", ["Login", "Signup"])

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button(mode):
        if not validate_email(email):
            st.error("Please enter a valid email address.")
            return

        users = load_users()

        if mode == "Signup":
            if email in users.email.values:
                st.warning("Email already registered. Please login.")
            else:
                new_user = pd.DataFrame([[email, hash_password(password)]], columns=["email", "password"])
                users = pd.concat([users, new_user], ignore_index=True)
                save_users(users)
                st.success("Signup successful. Please login.")

        elif mode == "Login":
            user_row = users[users["email"] == email]
            if not user_row.empty and user_row.iloc[0]["password"] == hash_password(password):
                st.session_state.authenticated = True
                st.session_state.email = email
                st.experimental_rerun()
            else:
                st.error("Invalid login credentials.")

if not st.session_state.authenticated:
    login_signup()
    st.stop()

# ---------------------- SIDEBAR ---------------------- #
page = st.sidebar.radio("Navigation", [
    "View Inventory",
    "Add Item",
    "Ask Inventory Agent",
    "Add Category",
    "Update Column",
    "Change Password",
    "Logout"
])

# ---------------------- LOGOUT ---------------------- #
if page == "Logout":
    st.session_state.authenticated = False
    st.session_state.email = ""
    st.experimental_rerun()

# ---------------------- VIEW INVENTORY ---------------------- #
if page == "View Inventory":
    st.title("Inventory Table")
    inventory_df = load_inventory()

    if not inventory_df.empty:
        for idx, row in inventory_df.iterrows():
            row_data = row.to_dict()
            col1, *_, colN = st.columns(len(row_data))
            with col1:
                st.write(row_data["ID#"])
            for i, (key, value) in enumerate(row_data.items()):
                if key != "ID#" and key != "Action":
                    st.write(value)
            with colN:
                if st.button("DELETE", key=f"delete_{row['ID#']}"):
                    inventory_df = inventory_df[inventory_df["ID#"] != row["ID#"]]
                    save_inventory(inventory_df)
                    st.experimental_rerun()
    else:
        st.info("No inventory data available.")

# ---------------------- ADD ITEM ---------------------- #
elif page == "Add Item":
    st.title("Add New Inventory Item")
    category_config = load_category_config()
    inventory_df = load_inventory()

    with st.form("add_item_form"):
        inputs = {}
        inputs["ID#"] = str(uuid4())[:8]

        for field, ftype in category_config.items():
            if ftype == "Text":
                inputs[field] = st.text_input(field)
            elif ftype == "Number":
                inputs[field] = st.number_input(field, step=1.0)
            elif ftype == "Boolean":
                inputs[field] = st.checkbox(field)
            else:
                inputs[field] = st.text_input(field)

        if st.form_submit_button("Add Item"):
            new_row = pd.DataFrame([inputs])
            updated_df = pd.concat([inventory_df, new_row], ignore_index=True)
            save_inventory(updated_df)
            st.success("Item added successfully.")

# ---------------------- ASK AGENT ---------------------- #
elif page == "Ask Inventory Agent":
    st.title("Ask Inventory Agent")
    inventory_df = load_inventory()
    user_question = st.text_area("Ask your question about inventory:")

    if st.button("Ask"):
        if inventory_df.empty:
            st.warning("No inventory data available.")
        else:
            full_prompt = (
                f"Answer the following about this inventory data:\n"
                f"{inventory_df.to_csv(index=False)}\n\n"
                f"User Question: {user_question}"
            )
            try:
                response = completion(
                    model="groq/llama3-70b-8192",
                    messages=[{"role": "user", "content": full_prompt}],
                    api_key=st.secrets["GROQ_API_KEY"]
                )
                st.write(response["choices"][0]["message"]["content"])
            except Exception as e:
                st.error("Agent failed to respond.")

# ---------------------- ADD CATEGORY ---------------------- #
elif page == "Add Category":
    st.title("Add New Category Column")
    config = load_category_config()
    col_name = st.text_input("Column Name")
    col_type = st.selectbox("Column Type", ["Text", "Number", "Boolean"])

    if st.button("Add Column"):
        if col_name:
            config[col_name] = col_type
            save_category_config(config)
            st.success("Column added successfully.")
        else:
            st.error("Column name cannot be empty.")

# ---------------------- UPDATE COLUMN ---------------------- #
elif page == "Update Column":
    st.title("Update Existing Column by ID#")
    inventory_df = load_inventory()
    config = load_category_config()

    update_id = st.text_input("Enter ID# to Update")

    if update_id:
        row = inventory_df[inventory_df["ID#"] == update_id]
        if not row.empty:
            row = row.iloc[0].to_dict()
            updated_row = {}
            for col, ftype in config.items():
                default_val = row.get(col, "")
                if ftype == "Text":
                    updated_row[col] = st.text_input(col, default_val)
                elif ftype == "Number":
                    updated_row[col] = st.number_input(col, value=float(default_val or 0))
                elif ftype == "Boolean":
                    updated_row[col] = st.checkbox(col, value=bool(default_val))
            if st.button("Update"):
                for key, val in updated_row.items():
                    inventory_df.loc[inventory_df["ID#"] == update_id, key] = val
                save_inventory(inventory_df)
                st.success("Row updated successfully.")
                st.experimental_rerun()
        else:
            st.warning("No row found with given ID#")

# ---------------------- CHANGE PASSWORD ---------------------- #
elif page == "Change Password":
    st.title("Change Your Password")
    current_pw = st.text_input("Current Password", type="password")
    new_pw = st.text_input("New Password", type="password")

    if st.button("Change Password"):
        users = load_users()
        user_row = users[users.email == st.session_state.email]

        if not user_row.empty and user_row.iloc[0]["password"] == hash_password(current_pw):
            users.loc[users.email == st.session_state.email, "password"] = hash_password(new_pw)
            save_users(users)
            st.success("Password updated successfully.")
        else:
            st.error("Incorrect current password.")
