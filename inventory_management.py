import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime
from litellm import completion

# === File Constants ===
USER_FILE = "user.csv"
INVENTORY_FILE = "inventory.csv"

st.set_page_config(page_title="Inventory Manager", layout="wide")

# === Utility Functions ===
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    return pd.DataFrame(columns=["username", "password", "email"])

def save_user(username, password, email):
    users = load_users()
    if username in users["username"].values:
        return False
    new_user = pd.DataFrame([[username, hash_password(password), email]], columns=["username", "password", "email"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_FILE, index=False)
    return True

def verify_user(username, password):
    users = load_users()
    hashed = hash_password(password)
    return not users[(users["username"] == username) & (users["password"] == hashed)].empty

def update_password(username, new_password):
    users = load_users()
    if username in users["username"].values:
        users.loc[users["username"] == username, "password"] = hash_password(new_password)
        users.to_csv(USER_FILE, index=False)
        return True
    return False

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    return pd.DataFrame(columns=["item_name", "category", "quantity", "price", "date_added"])

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

def ask_inventory_agent(prompt):
    try:
        response = completion(
            model="groq/llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            api_key=os.getenv("LITELLM_API_KEY")
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# === Authentication Session ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Inventory Manager Login")

    auth_mode = st.radio("Select Mode", ["Login", "Signup", "Update Password"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if auth_mode == "Signup":
        email = st.text_input("Email")
        if st.button("Create Account"):
            if save_user(username, password, email):
                st.success("Account created. You can now log in.")
            else:
                st.error("Username already exists.")

    elif auth_mode == "Login":
        if st.button("Login"):
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials.")

    elif auth_mode == "Update Password":
        if st.button("Update Password"):
            if update_password(username, password):
                st.success("Password updated successfully.")
            else:
                st.error("Username not found.")

    st.stop()

# === Logged-In Interface ===
st.sidebar.title(f"Welcome, {st.session_state.username}")
page = st.sidebar.radio("Navigation", ["View Inventory", "Add Item", "Ask Inventory Agent"])

df = load_inventory()

# === View Inventory ===
if page == "View Inventory":
    st.title("Current Inventory")
    if not df.empty:
        for i in df.index:
            col1, col2 = st.columns([9, 1])
            with col1:
                st.write(df.loc[i].to_dict())
            with col2:
                if st.button("Delete", key=f"delete_{i}"):
                    df = df.drop(index=i).reset_index(drop=True)
                    save_inventory(df)
                    st.rerun()
    else:
        st.info("Inventory is empty.")

# === Add Item ===
elif page == "Add Item":
    st.title("Add New Inventory Item")
    item_name = st.text_input("Item Name")
    quantity = st.number_input("Quantity", min_value=0, step=1)
    price = st.number_input("Price", min_value=0.0, step=0.1)

    categories = df["category"].dropna().unique().tolist()
    category = st.selectbox("Select Category", categories + ["Add New Category"])

    if category == "Add New Category":
        category = st.text_input("Enter New Category")

    if st.button("Add Item"):
        new_row = {
            "item_name": item_name,
            "category": category,
            "quantity": quantity,
            "price": price,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_inventory(df)
        st.success("Item added successfully.")

# === Ask Inventory Agent ===
elif page == "Ask Inventory Agent":
    st.title("Ask Inventory Agent")
    query = st.text_area("Ask a question about your inventory")
    if st.button("Ask"):
        inventory_text = df.to_string(index=False)
        final_prompt = f"""
You are an Inventory Assistant. Based on the inventory table below, answer the question.

Inventory Data:
{inventory_text}

Question:
{query}
"""
        response = ask_inventory_agent(final_prompt)
        st.subheader("Agent Response")
        st.info(response)
import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime
from litellm import completion

# === File Constants ===
USER_FILE = "user.csv"
INVENTORY_FILE = "inventory.csv"

st.set_page_config(page_title="Inventory Manager", layout="wide")

# === Utility Functions ===
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    return pd.DataFrame(columns=["username", "password", "email"])

def save_user(username, password, email):
    users = load_users()
    if username in users["username"].values:
        return False
    new_user = pd.DataFrame([[username, hash_password(password), email]], columns=["username", "password", "email"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USER_FILE, index=False)
    return True

def verify_user(username, password):
    users = load_users()
    hashed = hash_password(password)
    return not users[(users["username"] == username) & (users["password"] == hashed)].empty

def update_password(username, new_password):
    users = load_users()
    if username in users["username"].values:
        users.loc[users["username"] == username, "password"] = hash_password(new_password)
        users.to_csv(USER_FILE, index=False)
        return True
    return False

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    return pd.DataFrame(columns=["item_name", "category", "quantity", "price", "date_added"])

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

def ask_inventory_agent(prompt):
    try:
        response = completion(
            model="groq/llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            api_key=os.getenv("LITELLM_API_KEY")
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {str(e)}"

# === Authentication Session ===
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("Inventory Manager Login")

    auth_mode = st.radio("Select Mode", ["Login", "Signup", "Update Password"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if auth_mode == "Signup":
        email = st.text_input("Email")
        if st.button("Create Account"):
            if save_user(username, password, email):
                st.success("Account created. You can now log in.")
            else:
                st.error("Username already exists.")

    elif auth_mode == "Login":
        if st.button("Login"):
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid credentials.")

    elif auth_mode == "Update Password":
        if st.button("Update Password"):
            if update_password(username, password):
                st.success("Password updated successfully.")
            else:
                st.error("Username not found.")

    st.stop()

# === Logged-In Interface ===
st.sidebar.title(f"Welcome, {st.session_state.username}")
page = st.sidebar.radio("Navigation", ["View Inventory", "Add Item", "Ask Inventory Agent"])

df = load_inventory()

# === View Inventory ===
if page == "View Inventory":
    st.title("Current Inventory")
    if not df.empty:
        for i in df.index:
            col1, col2 = st.columns([9, 1])
            with col1:
                st.write(df.loc[i].to_dict())
            with col2:
                if st.button("Delete", key=f"delete_{i}"):
                    df = df.drop(index=i).reset_index(drop=True)
                    save_inventory(df)
                    st.rerun()
    else:
        st.info("Inventory is empty.")

# === Add Item ===
elif page == "Add Item":
    st.title("Add New Inventory Item")
    item_name = st.text_input("Item Name")
    quantity = st.number_input("Quantity", min_value=0, step=1)
    price = st.number_input("Price", min_value=0.0, step=0.1)

    categories = df["category"].dropna().unique().tolist()
    category = st.selectbox("Select Category", categories + ["Add New Category"])

    if category == "Add New Category":
        category = st.text_input("Enter New Category")

    if st.button("Add Item"):
        new_row = {
            "item_name": item_name,
            "category": category,
            "quantity": quantity,
            "price": price,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_inventory(df)
        st.success("Item added successfully.")

# === Ask Inventory Agent ===
elif page == "Ask Inventory Agent":
    st.title("Ask Inventory Agent")
    query = st.text_area("Ask a question about your inventory")
    if st.button("Ask"):
        inventory_text = df.to_string(index=False)
        final_prompt = f"""
You are an Inventory Assistant. Based on the inventory table below, answer the question.

Inventory Data:
{inventory_text}

Question:
{query}
"""
        response = ask_inventory_agent(final_prompt)
        st.subheader("Agent Response")
        st.info(response)
