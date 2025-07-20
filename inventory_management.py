import streamlit as st
import pandas as pd
import os

# --- Utility Functions ---
@st.cache_data

def load_inventory():
    if os.path.exists("inventory.csv"):
        return pd.read_csv("inventory.csv")
    return pd.DataFrame()

def save_inventory(df):
    df.to_csv("inventory.csv", index=False)

def load_columns():
    if os.path.exists("columns.csv"):
        return pd.read_csv("columns.csv")
    return pd.DataFrame(columns=["column", "type"])

def save_columns(df):
    df.to_csv("columns.csv", index=False)

def login_user(username, password):
    if os.path.exists("users.csv"):
        users = pd.read_csv("users.csv")
        user = users[(users["username"] == username) & (users["password"] == password)]
        return not user.empty
    return False

def create_user(username, password):
    users = pd.read_csv("users.csv") if os.path.exists("users.csv") else pd.DataFrame(columns=["username", "password"])
    if username in users['username'].values:
        return False
    new_user = pd.DataFrame([{"username": username, "password": password}])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv("users.csv", index=False)
    return True

# --- Sidebar Login/Signup ---
st.title("Inventory Manager")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    auth_mode = st.sidebar.radio("Login or Signup", ["Login", "Signup"])
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if auth_mode == "Login":
        if st.sidebar.button("Login"):
            if login_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.sidebar.error("Invalid credentials.")
    else:
        if st.sidebar.button("Signup"):
            if create_user(username, password):
                st.sidebar.success("User created. Please login.")
            else:
                st.sidebar.error("Username already exists.")
    st.stop()

# --- Logout Option ---
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --- Load Columns ---
columns_df = load_columns()
inventory_df = load_inventory()

# --- Sidebar Column Manager ---
st.sidebar.subheader("Manage Columns")

for i, row in columns_df.iterrows():
    col_name = row['column']
    st.sidebar.text(col_name)

with st.sidebar.expander("Add New Column"):
    new_col = st.text_input("Column Name")
    new_type = st.selectbox("Column Type", ["text", "number", "date", "dropdown"])
    if st.button("Add Column"):
        if new_col and new_col not in columns_df['column'].values:
            columns_df = pd.concat([columns_df, pd.DataFrame([[new_col, new_type]], columns=["column", "type"])]).reset_index(drop=True)
            save_columns(columns_df)
            if new_col not in inventory_df.columns:
                inventory_df[new_col] = ""
                save_inventory(inventory_df)
            st.rerun()

# --- Main Window ---
st.header("Inventory")

if columns_df.empty:
    st.warning("No columns to add.")
    st.stop()

# --- Add Item Form ---
with st.form("add_item_form"):
    st.subheader("Add Item")
    new_item = {}
    for _, row in columns_df.iterrows():
        col, col_type = row['column'], row['type']
        if col_type == "number":
            new_item[col] = st.number_input(col, step=1)
        elif col_type == "date":
            new_item[col] = st.date_input(col)
        elif col_type == "dropdown":
            options = st.text_input(f"Options for {col} (comma separated)")
            if options:
                new_item[col] = st.selectbox(col, options.split(","))
            else:
                new_item[col] = ""
        else:
            new_item[col] = st.text_input(col)
    submitted = st.form_submit_button("Add Item")
    if submitted:
        inventory_df = pd.concat([inventory_df, pd.DataFrame([new_item])], ignore_index=True)
        save_inventory(inventory_df)
        st.success("Item added.")

# --- View Inventory ---
st.subheader("Current Inventory")

if inventory_df.empty:
    st.info("No inventory data.")
else:
    st.dataframe(inventory_df)
    for i in range(len(inventory_df)):
        if st.button(f"Delete Row {i+1}", key=f"delete_{i}"):
            inventory_df = inventory_df.drop(index=i).reset_index(drop=True)
            save_inventory(inventory_df)
            st.rerun()
