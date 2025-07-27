import streamlit as st
import pandas as pd
import os
import hashlib
import json
from datetime import datetime

# File paths
USER_FILE = "user.csv"
INVENTORY_FILE = "inventory.csv"
CATEGORY_FILE = "categories.json"

st.set_page_config(page_title="Inventory Manager", layout="wide")

# ---------------- Utility Functions ----------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    else:
        return pd.DataFrame(columns=["email", "password"])

def save_users(users_df):
    users_df.to_csv(USER_FILE, index=False)

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    else:
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

# ---------------- Authentication ----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None

users = load_users()

if not st.session_state.authenticated:
    auth_option = st.selectbox("Choose Action", ["Login", "Signup", "Change Password"])

    if auth_option == "Signup":
        st.subheader("Create Account")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Sign Up"):
            if email and password:
                if email in users["email"].values:
                    st.error("Email already exists.")
                else:
                    new_user = pd.DataFrame([[email, hash_password(password)]], columns=["email", "password"])
                    users = pd.concat([users, new_user], ignore_index=True)
                    save_users(users)
                    st.success("Signup successful. Please log in.")
            else:
                st.error("All fields required.")

    elif auth_option == "Login":
        st.subheader("Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            hashed_pwd = hash_password(password)
            user_row = users[users["email"] == email]
            if not user_row.empty and user_row.iloc[0]["password"] == hashed_pwd:
                st.session_state.authenticated = True
                st.session_state.current_user = email
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

    elif auth_option == "Change Password":
        st.subheader("Change Password")
        email = st.text_input("Email")
        old_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        if st.button("Update Password"):
            hashed_old = hash_password(old_password)
            user_index = users[users["email"] == email].index
            if not user_index.empty and users.loc[user_index[0], "password"] == hashed_old:
                users.loc[user_index[0], "password"] = hash_password(new_password)
                save_users(users)
                st.success("Password updated successfully.")
            else:
                st.error("Invalid credentials")
else:
    st.sidebar.title(f"Welcome, {st.session_state.current_user}")
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.current_user = None
        st.experimental_rerun()

    page = st.sidebar.radio("Navigation", ["View Inventory", "Add Item", "Ask Inventory Agent", "Change Password"])

    inventory = load_inventory()
    categories = load_categories()

    if page == "View Inventory":
        st.subheader("Inventory List")
        if inventory.empty:
            st.info("No items yet.")
        else:
            for idx, row in inventory.iterrows():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
                with col1:
                    st.markdown(f"**Item Name:** {row['Item Name']}")
                with col2:
                    st.markdown(f"**Quantity:** {row['Quantity']}")
                with col3:
                    st.markdown(f"**Price:** {row['Price']}")
                dynamic_cols = list(set(inventory.columns) - set(['Item Name', 'Quantity', 'Price']))
                with col4:
                    for cat in dynamic_cols:
                        st.markdown(f"**{cat}:** {row[cat]}")
                with col5:
                    if st.button("Delete", key=f"delete_{idx}"):
                        inventory.drop(idx, inplace=True)
                        save_inventory(inventory)
                        st.experimental_rerun()

    elif page == "Add Item":
        st.subheader("Add New Inventory Item")
        item_name = st.text_input("Item Name")
        quantity = st.number_input("Quantity", value=0, min_value=0)
        price = st.number_input("Price", value=0.0, min_value=0.0, format="%.2f")

        # Existing category fields
        cat_values = {}
        for cat, dtype in categories.items():
            if dtype == "text":
                cat_values[cat] = st.text_input(cat)
            elif dtype == "number":
                cat_values[cat] = st.number_input(cat, value=0.0)

        # Add new category
        st.markdown("### Add New Category")
        new_cat_name = st.text_input("New Category Name")
        new_cat_type = st.selectbox("Select Type", ["text", "number"])
        if st.button("Add Category"):
            if new_cat_name:
                categories[new_cat_name] = new_cat_type
                save_categories(categories)
                st.success("Category added. Refreshing...")
                st.experimental_rerun()

        if st.button("Add Item"):
            if item_name:
                new_item = {"Item Name": item_name, "Quantity": quantity, "Price": price}
                new_item.update(cat_values)
                inventory = pd.concat([inventory, pd.DataFrame([new_item])], ignore_index=True)
                save_inventory(inventory)
                st.success("Item added successfully.")
            else:
                st.error("Item name required.")

    elif page == "Ask Inventory Agent":
        st.subheader("Ask the Inventory Agent")
        st.write("(Agent logic would be here — integrated with Groq/Gemini/LLM)")

    elif page == "Change Password":
        st.subheader("Change Password")
        old_password = st.text_input("Old Password", type="password")
        new_password = st.text_input("New Password", type="password")
        if st.button("Update Password"):
            hashed_old = hash_password(old_password)
            user_index = users[users["email"] == st.session_state.current_user].index
            if not user_index.empty and users.loc[user_index[0], "password"] == hashed_old:
                users.loc[user_index[0], "password"] = hash_password(new_password)
                save_users(users)
                st.success("Password updated successfully.")
            else:
                st.error("Incorrect old password")
