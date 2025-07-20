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
        item = st.text_input("Item Name")
        category = st.text_input("Category")
        quantity = st.number_input("Quantity", min_value=0, step=1)
        price = st.number_input("Price ($)", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("Add Item")

    if submitted:
        if item and category:
            new_item = {
                "id": str(uuid.uuid4()),
                cols["item"]: item,
                cols["category"]: category,
                cols["quantity"]: quantity,
                cols["price"]: price
            }
            df = pd.concat([df, pd.DataFrame([new_item])], ignore_index=True)
            save_data(df)
            st.success(f"Added {item} to inventory.")
        else:
            st.error("Please fill all the fields.")

# ===== View Inventory Page =====
elif page == "View Inventory":
    st.header("View & Manage Inventory")
    st.markdown("### Inventory Items")

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Inventory as CSV", data=csv, file_name='inventory.csv', mime='text/csv')

    headers = st.columns([2, 2, 1, 1, 1])
    headers[0].markdown(f"**{cols['item'].capitalize()}**")
    headers[1].markdown(f"**{cols['category'].capitalize()}**")
    headers[2].markdown(f"**{cols['quantity'].capitalize()}**")
    headers[3].markdown(f"**{cols['price'].capitalize()}**")
    headers[4].markdown("**Action**")

    for idx, row in df.iterrows():
        cols_ui = st.columns([2, 2, 1, 1, 1])
        cols_ui[0].markdown(row[cols['item']])
        cols_ui[1].markdown(row[cols['category']])
        cols_ui[2].markdown(str(row[cols['quantity']]))
        cols_ui[3].markdown(f"${row[cols['price']]:.2f}")
        delete_button = cols_ui[4].button("Delete", key=row['id'])
        if delete_button:
            df = df[df['id'] != row['id']]
            save_data(df)
            st.success(f"Deleted {row[cols['item']]} from inventory.")
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
                inventory_summary += f"- {row[cols['item']]} ({row[cols['category']]}): {row[cols['quantity']]} units at ${row[cols['price']]:.2f}\n"

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
    with st.form("column_config"):
        item_col = st.text_input("1st Column (Item)", value=st.session_state.column_names["item"])
        cat_col = st.text_input("2nd Column (Category)", value=st.session_state.column_names["category"])
        qty_col = st.text_input("3rd Column (Quantity)", value=st.session_state.column_names["quantity"])
        price_col = st.text_input("4th Column (Price)", value=st.session_state.column_names["price"])

        st.markdown("### 🗑️ Delete a Column")
        col_to_delete = st.selectbox("Choose a column to delete (optional):", options=["None"] + list(st.session_state.column_names.values()))

        st.markdown("### ➕ Add New Column")
        new_col_name = st.text_input("Add New Column (e.g. 'supplier')")
        add_col_btn = st.form_submit_button("Save")

        if add_col_btn:
            if col_to_delete and col_to_delete != "None":
                st.session_state.column_names = {k: v for k, v in st.session_state.column_names.items() if v != col_to_delete}
                st.success(f"Deleted column: {col_to_delete}")
            if new_col_name:
                key = new_col_name.lower().replace(" ", "_")
                st.session_state.column_names[key] = new_col_name
                st.success(f"Added new column: {new_col_name}")
