import streamlit as st
import pandas as pd
import uuid
import os
from litellm import completion

# --- File Paths ---
USER_FILE = "users.csv"
INVENTORY_FILE = "inventory.csv"

# --- Initialize Storage Files ---
if not os.path.exists(USER_FILE):
    pd.DataFrame(columns=["username", "password"]).to_csv(USER_FILE, index=False)

if not os.path.exists(INVENTORY_FILE):
    pd.DataFrame(columns=["item", "category", "quantity", "price"]).to_csv(INVENTORY_FILE, index=False)

# --- Load User Data ---
def load_users():
    return pd.read_csv(USER_FILE)

def save_users(users):
    users.to_csv(USER_FILE, index=False)

def create_user(username, password):
    users = load_users()
    if username in users["username"].values:
        return False
    users.loc[len(users.index)] = [username, password]
    save_users(users)
    return True

def authenticate_user(username, password):
    users = load_users()
    return not users[(users["username"] == username) & (users["password"] == password)].empty

# --- Load Inventory Data ---
def load_data():
    return pd.read_csv(INVENTORY_FILE)

def save_data(df):
    df.to_csv(INVENTORY_FILE, index=False)

# --- Sidebar: Column Configuration ---
st.sidebar.title("Column Settings")
df = load_data()

# Always ensure these 4 base columns are present and in order
base_columns = ["item", "category", "quantity", "price"]
for col in base_columns:
    if col not in df.columns:
        df[col] = ""
        save_data(df)

# Let user rename and reorder custom columns
custom_columns = [col for col in df.columns if col not in base_columns]
new_order = base_columns + custom_columns

st.sidebar.subheader("Reorder Columns")
reordered_custom = st.sidebar.multiselect(
    "Drag to reorder additional columns:",
    options=custom_columns,
    default=custom_columns,
    key="reorder_custom_columns"
)
new_order = base_columns + reordered_custom

# Rename columns
st.sidebar.subheader("Rename Columns")
renamed_columns = {}
for col in new_order:
    new_name = st.sidebar.text_input(f"Rename '{col}'", value=col)
    renamed_columns[col] = new_name

# Update column names in df
df = df.rename(columns=renamed_columns)
save_data(df)

# Add new column
st.sidebar.subheader("Add New Column")
new_col_name = st.sidebar.text_input("New Column Name")
new_col_type = st.sidebar.selectbox("Column Type", ["text", "number", "date", "dropdown"])
if st.sidebar.button("➕ Add Column"):
    final_col_name = renamed_columns.get(new_col_name, new_col_name)
    if final_col_name not in df.columns:
        if new_col_type == "number":
            df[final_col_name] = 0
        elif new_col_type == "date":
            df[final_col_name] = pd.NaT
        else:
            df[final_col_name] = ""
        save_data(df)
        st.success(f"Added column: {final_col_name}")
        st.rerun()

# Delete columns
st.sidebar.subheader("Delete Custom Columns")
for col in custom_columns:
    if st.sidebar.button(f"❌ Delete '{col}'"):
        df.drop(columns=[col], inplace=True)
        save_data(df)
        st.success(f"Deleted column: {col}")
        st.rerun()

# --- Main App ---
page = st.sidebar.radio("Navigation", ["Add Item", "View Inventory", "Ask AI"])
df = load_data()

if page == "Add Item":
    st.title("Add Inventory Item")
    with st.form("add_item"):
        inputs = {}
        for col in df.columns:
            if df[col].dtype == 'int64' or df[col].dtype == 'float64':
                inputs[col] = st.number_input(f"Enter {col.title()}", value=0)
            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                inputs[col] = st.date_input(f"Select {col.title()}")
            else:
                inputs[col] = st.text_input(f"Enter {col.title()}")
        if st.form_submit_button("Add Item"):
            df.loc[len(df.index)] = inputs
            save_data(df)
            st.success("Item added to inventory!")
            st.rerun()

elif page == "View Inventory":
    st.title("Inventory Table")
    st.dataframe(df[new_order], use_container_width=True)

elif page == "Ask AI":
    st.title("Inventory Assistant 🤖")
    question = st.text_input("Ask a question about your inventory:")
    if question:
        context = df.head(100).to_string(index=False)
        prompt = f"You are an inventory assistant. Answer the question using this data:\n\n{context}\n\nQ: {question}\nA:"
        response = completion(model="groq/llama3-8b-8192", messages=[{"role": "user", "content": prompt}])
        st.info(response.choices[0].message.content)
