import streamlit as st
import pandas as pd
import os
import uuid
import litellm

# Use Streamlit secrets for Gemini key
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

st.set_page_config(page_title="Inventory Manager", layout="wide")

DATA_FILE = "inventory.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=["id", "item", "category", "quantity", "price"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

# Sidebar Navigation
st.sidebar.title("Inventory Management")
pages = ["Add Item", "View Inventory", "Ask the Agent"]

# Clear chat history when switching pages
if "last_page" not in st.session_state:
    st.session_state.last_page = pages[0]
page = st.sidebar.radio("Go to", pages)
if page != st.session_state.last_page:
    st.session_state.chat_history = []
    st.session_state.last_page = page

# Add Item Page
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
                "item": item,
                "category": category,
                "quantity": quantity,
                "price": price
            }
            df = pd.concat([df, pd.DataFrame([new_item])], ignore_index=True)
            save_data(df)
            st.success(f"Added {item} to inventory.")
        else:
            st.error("Please fill all the fields.")

# View Inventory Page
elif page == "View Inventory":
    st.header("📋 View & Manage Inventory")
    st.markdown("### Inventory Items")

    # 📥 Download Button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Inventory as CSV",
        data=csv,
        file_name='inventory.csv',
        mime='text/csv',
    )

    # Table Headers
    header_cols = st.columns([2, 2, 1, 1, 1])
    header_cols[0].markdown("**Item**")
    header_cols[1].markdown("**Category**")
    header_cols[2].markdown("**Quantity**")
    header_cols[3].markdown("**Price**")
    header_cols[4].markdown("**Action**")

    # Display Inventory Items
    for idx, row in df.iterrows():
        cols = st.columns([2, 2, 1, 1, 1])
        cols[0].markdown(row['item'])
        cols[1].markdown(row['category'])
        cols[2].markdown(str(row['quantity']))
        cols[3].markdown(f"${row['price']:.2f}")
        delete_button = cols[4].button("Delete", key=row['id'])
        if delete_button:
            df = df[df['id'] != row['id']]
            save_data(df)
            st.success(f"Deleted {row['item']} from inventory.")
            st.rerun()
# Ask the Agent Page
elif page == "Ask the Agent":
    st.header("Ask the Inventory Agent")
    user_input = st.text_input("Ask anything about the inventory...")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if user_input:
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # 🔍 Check if inventory is empty
        if df.empty:
            inventory_summary = "The inventory is currently empty."
        else:
            inventory_summary = ""
            for _, row in df.iterrows():
                inventory_summary += f"- {row['item']} ({row['category']}): {row['quantity']} units at ${row['price']:.2f}\n"

        # 🧠 Construct the prompt
        prompt = f"""
You are an expert inventory assistant.

Here is the current inventory:
{inventory_summary}

Now answer the following user query clearly:
"{user_input}"
        """

        # 🧠 Call Gemini
        try:
            litellm.api_key = GEMINI_API_KEY
            response = litellm.completion(
                model="gemini/gemini-1.5-flash",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that analyzes inventory data."},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = response.choices[0].message["content"]
        except Exception as e:
            reply = f"Error: {str(e)}"

        st.markdown(reply)
