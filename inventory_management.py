# inventory_manager.py
import streamlit as st
import pandas as pd
import os
import uuid
import litellm

# ===== Configuration =====
DATA_FILE = "inventory.csv"
USER_DB = "users.csv"

# ===== Streamlit Setup =====
st.set_page_config(page_title="Inventory Manager", layout="wide")

# ===== Load/Save Inventory =====
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["id", *st.session_state.column_names.values()])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

# ===== Load/Save Users =====
def load_users():
    if os.path.exists(USER_DB):
        return pd.read_csv(USER_DB)
    else:
        return pd.DataFrame(columns=["username", "password"])

def save_users(df):
    df.to_csv(USER_DB, index=False)

def create_user(username, password):
    users = load_users()
    if username in users['username'].values:
        return False
    new_user = pd.DataFrame([{"username": username, "password": password}])
    users = pd.concat([users, new_user], ignore_index=True)
    save_users(users)
    return True

def authenticate(username, password):
    users = load_users()
    return any((users["username"] == username) & (users["password"] == password))

# ===== Login/Signup Logic =====
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "column_names" not in st.session_state:
    st.session_state.column_names = {
        "item": "item",
        "category": "category",
        "quantity": "quantity",
        "price": "price"
    }

if not st.session_state.logged_in:
    st.title("Admin Login")

    login_tab, signup_tab = st.tabs(["Login", "Signup"])

    with login_tab:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.logged_in = True
                st.success("Logged in successfully")
                st.rerun()
            else:
                st.error("Invalid credentials")

    with signup_tab:
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            if create_user(new_username, new_password):
                st.success("User created. Please login.")
            else:
                st.error("Username already exists.")
    st.stop()

# ===== Load Inventory After Login =====
df = load_data()

# ===== Sidebar Navigation =====
st.sidebar.title("Inventory Management")
pages = ["Add Item", "View Inventory", "Ask the Agent", "Settings"]

if "last_page" not in st.session_state:
    st.session_state.last_page = pages[0]

page = st.sidebar.radio("Go to", pages)
if page != st.session_state.last_page:
    st.session_state.chat_history = []
    st.session_state.last_page = page

cols = st.session_state.column_names  # shorthand

# ===== Add Item Page =====
if page == "Add Item":
    st.header("Add New Inventory Item")
    with st.form("add_form"):
        new_data = {}
        for key, col_name in st.session_state.column_names.items():
            if "quantity" in key:
                new_data[col_name] = st.number_input(col_name.capitalize(), min_value=0, step=1)
            elif "price" in key:
                new_data[col_name] = st.number_input(col_name.capitalize(), min_value=0.0, step=0.01)
            else:
                new_data[col_name] = st.text_input(col_name.capitalize())
        submitted = st.form_submit_button("Add Item")

    if submitted:
        if all(v != '' for v in new_data.values()):
            new_item = {"id": str(uuid.uuid4()), **new_data}
            df = pd.concat([df, pd.DataFrame([new_item])], ignore_index=True)
            save_data(df)
            st.success(f"Added {new_data.get(cols['item'], 'Item')} to inventory.")
        else:
            st.error("Please fill all the fields.")

# ===== View Inventory Page =====
elif page == "View Inventory":
    st.header("View & Manage Inventory")
    st.markdown("### Inventory Items")

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Inventory as CSV", data=csv, file_name='inventory.csv', mime='text/csv')

    widths = [2] * len(cols) + [1]
    headers = st.columns(widths)
    for i, (key, name) in enumerate(cols.items()):
        headers[i].markdown(f"**{name.capitalize()}**")
    headers[-1].markdown("**Action**")

    for idx, row in df.iterrows():
        row_cols = st.columns(widths)
        for i, name in enumerate(cols.values()):
            row_cols[i].markdown(str(row[name]))
        if row_cols[-1].button("Delete", key=row['id']):
            df = df[df['id'] != row['id']]
            save_data(df)
            st.success("Item deleted.")
            st.rerun()

# ===== Ask the Agent Page =====
elif page == "Ask the Agent":
    st.header("Ask the Inventory Agent")
    user_input = st.text_input("Ask anything about the inventory...")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        inventory_summary = ""
        if df.empty:
            inventory_summary = "The inventory is currently empty."
        else:
            for _, row in df.iterrows():
                summary = " - ".join([f"{row[name]}" for name in cols.values()])
                inventory_summary += f"- {summary}\n"

        prompt = f"""
You are an expert inventory assistant.

Here is the current inventory:
{inventory_summary}

Now answer the following user query clearly:
\"{user_input}\"
        """

        try:
            litellm.api_key = st.secrets["GROQ_API_KEY"]
            response = litellm.completion(
                model="groq/llama3-8b-8192",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes inventory data."},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = response.choices[0].message["content"]
        except Exception as e:
            reply = f"Error: {str(e)}"

        st.markdown(reply)

# ===== Settings Page =====
elif page == "Settings":
    st.header("Customize Column Names")
    updated = False

    col_keys = list(st.session_state.column_names.keys())
    with st.form("column_config"):
        new_column_names = {}
        remove_keys = []
        for i, (key, name) in enumerate(st.session_state.column_names.items()):
            col1, col2 = st.columns([4, 1])
            new_name = col1.text_input(f"{i+1} Column", value=name, key=f"col_{key}")
            if col2.button("❌", key=f"del_{key}") and i >= 3:
                remove_keys.append(key)
            else:
                new_column_names[key] = new_name

        if st.form_submit_button("Add New Column"):
            new_key = f"custom_{uuid.uuid4().hex[:4]}"
            new_column_names[new_key] = f"Column {len(new_column_names)+1}"
            updated = True

        if st.form_submit_button("Save") or updated:
            for k in remove_keys:
                new_column_names.pop(k, None)
            fixed_keys = ["item", "category", "quantity", "price"]
            fixed_ordered = {k: new_column_names.pop(k) for k in fixed_keys if k in new_column_names}
            st.session_state.column_names = {**fixed_ordered, **new_column_names}
            if not df.empty:
                for new_col in st.session_state.column_names.values():
                    if new_col not in df.columns:
                        df[new_col] = ""
                save_data(df)
            st.success("Column names updated and inventory structure synced!")
