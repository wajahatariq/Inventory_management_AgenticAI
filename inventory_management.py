import streamlit as st
import pandas as pd
import os
import hashlib
import uuid

# ---------- File paths ----------
USER_FILE = "user.csv"
INVENTORY_FILE = "inventory.csv"

# ---------- Helper Functions ----------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    return pd.DataFrame(columns=["email", "password"])

def save_users(df):
    df.to_csv(USER_FILE, index=False)

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    return pd.DataFrame(columns=["ID#"])

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

def authenticate(email, password):
    users = load_users()
    if "email" not in users.columns:
        return False
    user_row = users[users["email"] == email]
    if not user_row.empty and user_row.iloc[0]["password"] == hash_password(password):
        return True
    return False

def email_exists(email):
    users = load_users()
    return email in users["email"].values

def register_user(email, password):
    users = load_users()
    new_user = pd.DataFrame([[email, hash_password(password)]], columns=["email", "password"])
    updated_users = pd.concat([users, new_user], ignore_index=True)
    save_users(updated_users)

def update_user_password(email, new_password):
    users = load_users()
    if email in users["email"].values:
        users.loc[users["email"] == email, "password"] = hash_password(new_password)
        save_users(users)
        return True
    return False

# ---------- Session State ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""

# ---------- Auth UI ----------
def login_ui():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(email, password):
            st.session_state.logged_in = True
            st.session_state.user_email = email
        else:
            st.error("Invalid credentials")
    st.markdown("---")
    st.markdown("Don't have an account? Register below:")
    new_email = st.text_input("New Email")
    new_password = st.text_input("New Password", type="password")
    if st.button("Register"):
        if email_exists(new_email):
            st.warning("Email already registered")
        else:
            register_user(new_email, new_password)
            st.success("User registered. Please login.")

# ---------- Main UI ----------
def inventory_ui():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("", ["View Inventory", "Add Item", "Update Category", "Ask Inventory Agent", "Change Password"])
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.experimental_rerun()

    inventory_df = load_inventory()

    if page == "View Inventory":
        if not inventory_df.empty:
            if "ID#" not in inventory_df.columns:
                inventory_df.insert(0, "ID#", [str(uuid.uuid4())[:8] for _ in range(len(inventory_df))])
            display_df = inventory_df.copy()
            for idx in display_df.index:
                st.write(display_df.loc[idx].to_dict())
                if st.button(f"Delete Row {idx}"):
                    inventory_df.drop(index=idx, inplace=True)
                    save_inventory(inventory_df)
                    st.success("Row deleted.")
                    st.experimental_rerun()
        else:
            st.info("No inventory to display.")

    elif page == "Add Item":
        st.subheader("Add New Inventory Item")
        new_item = {}
        item_name = st.text_input("Item Name")
        quantity = st.number_input("Quantity", min_value=0, step=1)
        price = st.number_input("Price", min_value=0.0, step=0.01)
        new_item["Item Name"] = item_name
        new_item["Quantity"] = quantity
        new_item["Price"] = price

        st.markdown("---")
        st.markdown("### Add New Category")
        col_name = st.text_input("New Column Name")
        col_type = st.selectbox("Column Type", ["text", "number"])

        if col_name:
            if col_type == "text":
                value = st.text_input(f"Enter value for {col_name}")
            else:
                value = st.number_input(f"Enter value for {col_name}", step=1)
            new_item[col_name] = value

        if st.button("Add Item"):
            new_row = pd.DataFrame([{**{"ID#": str(uuid.uuid4())[:8]}, **new_item}])
            inventory_df = pd.concat([inventory_df, new_row], ignore_index=True)
            save_inventory(inventory_df)
            st.success("Item added.")

    elif page == "Update Category":
        st.subheader("Edit Inventory Row")
        if not inventory_df.empty:
            selected_id = st.text_input("Enter ID# to Edit")
            row = inventory_df[inventory_df["ID#"] == selected_id]
            if not row.empty:
                idx = row.index[0]
                updated_data = {}
                for col in inventory_df.columns:
                    if col == "ID#":
                        continue
                    val = inventory_df.at[idx, col]
                    if isinstance(val, (int, float)):
                        new_val = st.number_input(f"{col}", value=float(val))
                    else:
                        new_val = st.text_input(f"{col}", value=str(val))
                    updated_data[col] = new_val
                if st.button("Update Row"):
                    for k, v in updated_data.items():
                        inventory_df.at[idx, k] = v
                    save_inventory(inventory_df)
                    st.success("Row updated.")
            else:
                st.warning("ID# not found")
        else:
            st.info("Inventory is empty.")

    elif page == "Change Password":
        st.subheader("Change Password")
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        if st.button("Update Password"):
            if authenticate(st.session_state.user_email, current_password):
                update_user_password(st.session_state.user_email, new_password)
                st.success("Password updated successfully")
            else:
                st.error("Current password incorrect")

    elif page == "Ask Inventory Agent":
        st.subheader("Coming Soon: Inventory Agent AI Assistant")

# ---------- App Launch ----------
if not st.session_state.logged_in:
    login_ui()
else:
    inventory_ui()
