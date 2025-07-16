import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from litellm import completion

# Load environment variables
load_dotenv()

# Set LiteLLM Gemini model and API key
from litellm import completion
litellm_model = "gemini/gemini-1.5-flash"
litellm_api_key = os.getenv("GEMINI_API_KEY") or "your-api-key-here"

# Initialize session state
if "inventory" not in st.session_state:
    st.session_state.inventory = []

# Sidebar navigation
st.sidebar.title("Inventory Manager")
page = st.sidebar.radio("Navigation", ["Add Inventory", "View Inventory", "Ask Agent"])

# Add Inventory Page
if page == "Add Inventory":
    st.header("Add Inventory Item")
    item = st.text_input("Item Name")
    category = st.text_input("Category")
    quantity = st.number_input("Quantity", min_value=0, format="%d")
    price = st.number_input("Price", min_value=0.0, format="%0.2f")
    if st.button("Add Item"):
        st.session_state.inventory.append({
            "item": item,
            "category": category,
            "quantity": quantity,
            "price": price
        })
        st.success("Item added successfully!")

# View Inventory Page
elif page == "View Inventory":
    st.header("View & Manage Inventory")
    if not st.session_state.inventory:
        st.info("No items in inventory.")
    else:
        df = pd.DataFrame(st.session_state.inventory)

        st.markdown("## Inventory Items")
        table_md = "| Item | Category | Quantity | Price |
|------|----------|----------|--------|"
        for i, row in df.iterrows():
            table_md += f"\n| {row['item']} | {row['category']} | {int(row['quantity'])} | ${float(row['price']):.2f} |"
        st.markdown(table_md)

        for i, row in df.iterrows():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.write(f"{row['item']} ({row['category']}) - Qty: {int(row['quantity'])} - ${float(row['price']):.2f}")
            with col2:
                if st.button("Delete", key=f"del_{i}"):
                    st.session_state.inventory.pop(i)
                    st.rerun()

# Ask Agent Page
elif page == "Ask Agent":
    st.header("Ask Inventory Agent")
    user_question = st.text_area("Enter your question about the inventory:")

    if st.button("Ask Agent") and user_question:
        df = pd.DataFrame(st.session_state.inventory)
        if df.empty:
            st.warning("Inventory is empty. Please add items first.")
        else:
            data_csv = df.to_csv(index=False)
            prompt = f"""
You are an inventory assistant.
Here's my inventory data:
{data_csv}

Answer the following question based on the data:
{user_question}
"""
            try:
                response = completion(
                    model=litellm_model,
                    messages=[{"role": "user", "content": prompt}],
                    api_key=litellm_api_key
                )
                st.success("Agent Response:")
                st.write(response['choices'][0]['message']['content'])
            except Exception as e:
                st.error(f"Error: {e}")
