import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

USER_FILE = "users.csv"
INVENTORY_FILE = "inventory.csv"

st.set_page_config(page_title="Inventory Manager", layout="wide")

# Load or initialize user data
def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    else:
        return pd.DataFrame(columns=["username", "password"])

def save_users(users_df):
    users_df.to_csv(USER_FILE, index=False)

# Load or initialize inventory data
def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    else:
        return pd.DataFrame()

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

# Create or update column configuration
def save_columns(columns):
    with open("columns.json", "w") as f:
        json.dump(columns, f)

def load_columns():
    if os.path.exists("columns.json"):
        with open("columns.json", "r") as f:
            return json.load(f)
    return []

    return response.choices[0].message.content
# Login logic
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.title("Login")
    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            users = load_users()
            if ((users.username == username) & (users.password == password)).any():
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("Login successful")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with signup_tab:
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            users = load_users()
            if new_username in users.username.values:
                st.warning("Username already exists")
            else:
                users.loc[len(users)] = [new_username, new_password]
                save_users(users)
                st.success("Account created! Please log in.")
else:
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", ["View Inventory", "Add Item", "Ask the Agent", "Column Manager", "Change Password"])
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    columns = load_columns()
    df = load_inventory()

    if selection == "View Inventory":
        st.title("Inventory Viewer")
        if df.empty or len(columns) == 0:
            st.info("No columns to display.")
        else:
            st.dataframe(df)

    elif selection == "Add Item":
        st.title("Add Inventory Item")
        if len(columns) == 0:
            st.info("No columns to add.")
        else:
            with st.form("add_item_form"):
                new_data = {}
                for col in columns:
                    new_data[col] = st.text_input(f"{col.capitalize()}")
                submitted = st.form_submit_button("Add Item")
                if submitted:
                    df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                    save_inventory(df)
                    st.success("Item added successfully")

elif selection == "Ask the Agent":
    st.title("Ask Inventory Agent")

    if inventory_df.empty:
        st.warning("Your inventory is currently empty. Add some items before asking questions.")
    else:
        query = st.text_input("Ask a question")

        if st.button("Submit") and query:
            import json
            from litellm import completion

            # Format inventory for LLM
            inventory_data = inventory_df.fillna("").to_dict(orient="records")

            messages = [
                {
                    "role": "system",
                    "content": "You are an intelligent inventory assistant. Use the data below to answer user questions. Be precise and concise. If something is not in the inventory, say so.",
                },
                {"role": "user", "content": f"Inventory:\n{json.dumps(inventory_data, indent=2)}"},
                {"role": "user", "content": f"Question: {query}"},
            ]

            try:
                response = completion(
                    model="groq/llama3-8b-8192",
                    messages=messages,
                    api_key=st.secrets["GROQ_API_KEY"],  # Make sure this is set in .streamlit/secrets.toml
                )
                answer = response.choices[0].message.content
                st.success("Agent Response:")
                st.write(answer)
            except Exception as e:
                st.error(f"Error from Groq AI: {e}")
    elif selection == "Change Password":
        st.title("Change Password")
        users = load_users()
        current_pass = st.text_input("Current Password", type="password")
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")
        if st.button("Update Password"):
            if ((users.username == st.session_state.username) & (users.password == current_pass)).any():
                if new_pass == confirm_pass:
                    users.loc[users.username == st.session_state.username, "password"] = new_pass
                    save_users(users)
                    st.success("Password updated successfully")
                else:
                    st.error("Passwords do not match")
            else:
                st.error("Incorrect current password")

    elif selection == "Column Manager":
        st.sidebar.title("Current Columns")
        for col in columns:
            st.sidebar.text(col)

        st.title("Manage Columns")
        with st.form("column_form"):
            new_col = st.text_input("New Column Name")
            submitted = st.form_submit_button("Add Column")
            if submitted and new_col:
                if new_col not in columns:
                    columns.append(new_col)
                    save_columns(columns)
                    if new_col not in df.columns:
                        df[new_col] = ""
                        save_inventory(df)
                    st.success("Column added successfully")
                else:
                    st.warning("Column already exists")
