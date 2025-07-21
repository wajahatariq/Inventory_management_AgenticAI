import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime

USER_FILE = "user.csv"
INVENTORY_FILE = "inventory.csv"

st.set_page_config(page_title="Inventory Manager", layout="wide")

# --- CUSTOM CSS STYLING ---
def add_custom_style():
    st.markdown("""
    <style>
        /* Background and font */
        .stApp {
            background: linear-gradient(to right, #e0f7fa, #ffffff);
            font-family: 'Segoe UI', sans-serif;
            color: #333333;
        }

        /* Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #d0f0ff;
        }

        /* Buttons */
        .stButton>button {
            background-color: #007BFF;
            color: white;
            border-radius: 8px;
            padding: 8px 16px;
            border: none;
            font-size: 16px;
        }

        .stButton>button:hover {
            background-color: #0056b3;
            color: white;
        }

        /* Inputs */
        input, textarea {
            background-color: #f0f9ff !important;
            border-radius: 6px;
        }

        /* Headers */
        h1, h2, h3 {
            color: #004466;
        }

        /* Tables */
        .stDataFrame {
            border-radius: 10px;
            background-color: white;
            padding: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

add_custom_style()

# --- PASSWORD HASHING ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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

# Column config: [{"name": "item", "type": "text"}, ...]
def save_columns(columns):
    with open("columns.json", "w") as f:
        json.dump(columns, f)

def load_columns():
    if os.path.exists("columns.json"):
        with open("columns.json", "r") as f:
            return json.load(f)
    return []

# --- SESSION INIT ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# --- LOGIN ---
if not st.session_state.logged_in:
    st.title("🔐 Login")
    login_tab, signup_tab = st.tabs(["🔑 Login", "🆕 Sign Up"])

    with login_tab:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            users = load_users()
            hashed = hash_password(password)
            user_match = users[
                (users["username"].str.strip() == username.strip()) &
                (users["password"] == hashed)
            ]
            if not user_match.empty:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("✅ Login successful")
                st.rerun()
            else:
                st.error("❌ Incorrect username or password")

    with signup_tab:
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")
        if st.button("Sign Up"):
            users = load_users()
            if new_username in users.username.values:
                st.warning("⚠️ Username already exists")
            else:
                hashed = hash_password(new_password)
                users.loc[len(users)] = [new_username, hashed]
                save_users(users)
                st.success("✅ Account created! Please log in.")

# --- LOGGED IN VIEW ---
else:
    st.sidebar.title("📊 Inventory Manager")
    st.sidebar.markdown(f"**👋 Welcome, {st.session_state.username.title()}**")
    selection = st.sidebar.radio("Navigate", ["📦 View Inventory", "➕ Add Item", "🤖 Ask the Agent", "🛠️ Column Manager", "🔑 Change Password"])

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

    columns = load_columns()

    if columns and isinstance(columns[0], str):
        columns = [{"name": col, "type": "text"} for col in columns]
        save_columns(columns)

    df = load_inventory()

    for col in columns:
        if col["name"] not in df.columns:
            df[col["name"]] = ""
    save_inventory(df)

    # --- View Inventory ---
    if selection == "📦 View Inventory":
        st.title("📦 Inventory Viewer")
        if len(columns) == 0:
            st.info("ℹ️ No columns configured yet.")
        else:
            assigned_column_names = [col["name"] for col in columns]
            if not df.empty:
                display_df = df[assigned_column_names + ["ID#"]] if "ID#" in df.columns else df[assigned_column_names]
                st.write("Inventory Table:")
                for i, row in display_df.iterrows():
                    cols = st.columns(len(display_df.columns) + 1)
                    for j, col_name in enumerate(display_df.columns):
                        cols[j].write(row[col_name])
                    delete_button_key = f"delete_{i}"
                    if cols[-1].button("❌ Delete", key=delete_button_key):
                        df.drop(index=i, inplace=True)
                        df.reset_index(drop=True, inplace=True)
                        save_inventory(df)
                        st.success(f"✅ Item '{row.get('ID#', i)}' deleted successfully.")
                        st.rerun()
                st.dataframe(display_df)
            else:
                st.warning("⚠️ Inventory is currently empty")

    # --- Add Item ---
    elif selection == "➕ Add Item":
        st.title("➕ Add or Edit Inventory Item")

        if "ID#" not in df.columns:
            df["ID#"] = ""

        if len(columns) == 0:
            st.info("ℹ️ No columns to add. Please add columns first.")
        else:
            mode = st.radio("Mode", ["Add New Item", "Edit Existing Item"])
            selected_id = None
            existing_data = {}

            if mode == "Edit Existing Item":
                existing_ids = df["ID#"].dropna().unique().tolist()
                if existing_ids:
                    selected_id = st.selectbox("Select ID# to Edit", existing_ids)
                    existing_data = df[df["ID#"] == selected_id].iloc[0].to_dict()
                else:
                    st.warning("⚠️ No items to edit. Add an item first.")
                    st.stop()

            with st.form("item_form"):
                form_data = {}

                if mode == "Add New Item":
                    new_id = f"ID{len(df) + 1:04d}"
                    st.text_input("ID#", value=new_id, disabled=True)
                    form_data["ID#"] = new_id
                else:
                    st.text_input("ID#", value=selected_id, disabled=True)
                    form_data["ID#"] = selected_id

                for col in columns:
                    col_name = col["name"]
                    col_type = col["type"]
                    type_label = col_type.capitalize()

                    default = existing_data.get(col_name, "") if existing_data else ""

                    if col_type == "number":
                        form_data[col_name] = st.number_input(f"{col_name.capitalize()} ({type_label})", value=float(default) if str(default).replace('.', '', 1).isdigit() else 0.0)
                    elif col_type == "date":
                        try:
                            default_date = datetime.strptime(default, "%Y-%m-%d").date() if default else datetime.today().date()
                        except:
                            default_date = datetime.today().date()
                        form_data[col_name] = st.date_input(f"{col_name.capitalize()} ({type_label})", value=default_date).strftime("%Y-%m-%d")
                    else:
                        form_data[col_name] = st.text_input(f"{col_name.capitalize()} ({type_label})", value=default)

                submitted = st.form_submit_button("💾 Save Item")
                if submitted:
                    if mode == "Add New Item":
                        df = pd.concat([df, pd.DataFrame([form_data])], ignore_index=True)
                        st.success("✅ New item added successfully.")
                    else:
                        df.loc[df["ID#"] == selected_id] = form_data
                        st.success("✅ Item updated successfully.")
                    save_inventory(df)

    # --- Ask the Agent ---
    elif selection == "🤖 Ask the Agent":
        st.title("🤖 Ask Inventory Agent")
        if df.empty:
            st.warning("⚠️ Your inventory is currently empty.")
        else:
            query = st.text_input("Ask a question")
            if st.button("Submit") and query:
                from litellm import completion

                inventory_data = df.fillna("").to_dict(orient="records")

                messages = [
                    {"role": "system", "content": "You are an intelligent inventory assistant. Use the data below to answer user questions. Be precise and concise. If something is not in the inventory, say so."},
                    {"role": "user", "content": f"Inventory:\n{json.dumps(inventory_data, indent=2)}"},
                    {"role": "user", "content": f"Question: {query}"},
                ]

                try:
                    response = completion(
                        model="groq/llama3-8b-8192",
                        messages=messages,
                        api_key=st.secrets["GROQ_API_KEY"],
                    )
                    answer = response.choices[0].message.content
                    st.success("💡 Agent Response:")
                    st.write(answer)
                except Exception as e:
                    st.error(f"❌ Error from Groq AI: {e}")

    # --- Change Password ---
    elif selection == "🔑 Change Password":
        st.title("🔑 Change Password")
        users = load_users()
        current_pass = st.text_input("Current Password", type="password")
        new_pass = st.text_input("New Password", type="password")
        confirm_pass = st.text_input("Confirm New Password", type="password")
        if st.button("Update Password"):
            hashed_current = hash_password(current_pass)
            if ((users.username == st.session_state.username) & (users.password == hashed_current)).any():
                if new_pass == confirm_pass:
                    users.loc[users.username == st.session_state.username, "password"] = hash_password(new_pass)
                    save_users(users)
                    st.success("✅ Password updated successfully")
                else:
                    st.error("❌ Passwords do not match")
            else:
                st.error("❌ Incorrect current password")

    # --- Column Manager ---
    elif selection == "🛠️ Column Manager":
        st.sidebar.title("📋 Current Columns")
        updated_columns = []
        edited_column_index = None

        for idx, col in enumerate(columns):
            col_name = col['name']
            col_type = col['type']

            col_container = st.sidebar.container()
            col1, col2, col3 = col_container.columns([2, 1, 1])

            col1.markdown(f"**{col_name} ({col_type})**")
            if col2.button("✏️", key=f"edit_col_{idx}"):
                edited_column_index = idx
            if col3.button("🗑️", key=f"delete_col_{idx}"):
                df.drop(columns=[col_name], inplace=True, errors='ignore')
                save_inventory(df)
                continue

            updated_columns.append(col)

        columns = updated_columns
        save_columns(columns)

        if edited_column_index is not None:
            st.subheader("✏️ Edit Column")
            col_to_edit = columns[edited_column_index]
            new_name = st.text_input("New Column Name", value=col_to_edit["name"])
            new_type = st.selectbox("Column Type", ["text", "number", "date"], index=["text", "number", "date"].index(col_to_edit["type"]))
            if st.button("Update Column"):
                if new_name != col_to_edit["name"]:
                    df.rename(columns={col_to_edit["name"]: new_name}, inplace=True)
                columns[edited_column_index] = {"name": new_name, "type": new_type}
                save_columns(columns)
                save_inventory(df)
                st.success("✅ Column updated successfully")
                st.rerun()

        st.title("➕ Manage Columns")
        with st.form("column_form"):
            new_col = st.text_input("New Column Name")
            col_type = st.selectbox("Select Column Type", ["text", "number", "date"])
            submitted = st.form_submit_button("Add Column")
            if submitted and new_col:
                if not any(c["name"].lower() == new_col.lower() for c in columns):
                    columns.append({"name": new_col, "type": col_type})
                    save_columns(columns)
                    if new_col not in df.columns:
                        df[new_col] = ""
                    save_inventory(df)
                    st.success("✅ Column added successfully")
                    st.rerun()
                else:
                    st.warning("⚠️ Column already exists")
