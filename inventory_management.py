import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime
from litellm import completion

# === File Constants ===
USER_FILE = "user.csv"
INVENTORY_FILE = "inventory.csv"

# === App Setup ===
st.set_page_config(page_title="Inventory Manager", layout="wide")

# === Utility Functions ===
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_users():
    if os.path.exists(USER_FILE):
        return pd.read_csv(USER_FILE)
    return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    users = load_users()
    users = users.append({"username": username, "password": hash_password(password)}, ignore_index=True)
    users.to_csv(USER_FILE, index=False)

def verify_user(username, password):
    users = load_users()
    hashed = hash_password(password)
    return not users[(users["username"] == username) & (users["password"] == hashed)].empty

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
            api_key=os.getenv("LITELLM_API_KEY")  # or use st.secrets if set in UI
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {str(e)}"

# === Login/Signup ===
auth_mode = st.sidebar.selectbox("Login/Signup", ["Login", "Signup"])
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

if auth_mode == "Signup":
    if st.sidebar.button("Create Account"):
        save_user(username, password)
        st.sidebar.success("Account created. Please log in.")
    st.stop()

if not verify_user(username, password):
    st.sidebar.warning("Please log in to access the app.")
    st.stop()

# === Logged-in Interface ===
st.title("📦 Inventory Management Dashboard")

# --- Load Inventory ---
df = load_inventory()

# === Tabs ===
tab1, tab2, tab3, tab4 = st.tabs(["📋 View Inventory", "➕ Add Item", "🧠 Ask Inventory Agent", "⚙️ Settings"])

# === View Inventory ===
with tab1:
    st.subheader("Current Inventory")
    st.dataframe(df, use_container_width=True)

# === Add Item ===
with tab2:
    st.subheader("Add New Item")
    item_name = st.text_input("Item Name")
    category = st.text_input("Category")
    quantity = st.number_input("Quantity", min_value=0, step=1)
    price = st.number_input("Price", min_value=0.0, step=0.1)

    if st.button("Add Item"):
        new_row = {
            "item_name": item_name,
            "category": category,
            "quantity": quantity,
            "price": price,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        df = df.append(new_row, ignore_index=True)
        save_inventory(df)
        st.success("Item added successfully!")

# === Ask Inventory Agent ===
with tab3:
    st.subheader("Ask Inventory Agent")
    user_query = st.text_area("Enter your question (e.g., 'Which category has the most items?')")

    if st.button("Ask"):
        inventory_text = df.to_string(index=False)
        final_prompt = f"""
You are an Inventory Agent. Answer the question based on this inventory data below:

{inventory_text}

Question: {user_query}
"""
        result = ask_inventory_agent(final_prompt)
        st.markdown("#### 🤖 Agent Response:")
        st.info(result)

# === Settings (Dynamic Column Support) ===
with tab4:
    st.subheader("Modify Inventory Structure")

    if st.checkbox("Add New Column"):
        new_col = st.text_input("New Column Name")
        default_val = st.text_input("Default Value", "")
        if st.button("Add Column"):
            if new_col not in df.columns:
                df[new_col] = default_val
                save_inventory(df)
                st.success(f"Column '{new_col}' added.")
            else:
                st.warning("Column already exists.")

    if st.checkbox("Delete a Column"):
        col_to_delete = st.selectbox("Select Column", df.columns)
        if st.button("Delete Column"):
            df = df.drop(columns=[col_to_delete])
            save_inventory(df)
            st.success(f"Deleted column '{col_to_delete}'")

