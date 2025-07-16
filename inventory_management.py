import streamlit as st
import pandas as pd
import litellm
import os
from uuid import uuid4

# Set up LiteLLM with API Key from Streamlit secrets
litellm.api_key = st.secrets["GEMINI_API_KEY"]
litellm.model = "gemini/gemini-1.5-flash"

# ---------- Session State Initialization ----------
if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

# ---------- Sidebar Navigation ----------
st.sidebar.title("📦 Inventory Manager")
selection = st.sidebar.radio("Go to:", ["Add Item", "View Inventory", "Ask Agent"])

# ---------- Add Item Page ----------
if selection == "Add Item":
    st.header("➕ Add New Inventory Item")
    with st.form("add_item_form"):
        name = st.text_input("Item Name")
        category = st.text_input("Category")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        price = st.number_input("Price (per unit)", min_value=0.0, step=0.01)
        submit = st.form_submit_button("Add Item")

    if submit and name and category:
        st.session_state.inventory.append({
            "id": str(uuid4()),
            "name": name,
            "category": category,
            "quantity": quantity,
            "price": price
        })
        st.success("✅ Item added successfully!")

# ---------- View Inventory Page ----------
elif selection == "View Inventory":
    st.header("📋 View & Manage Inventory")
    df = pd.DataFrame(st.session_state.inventory)

    if not df.empty:
        for idx, row in df.iterrows():
            col1, col2, col3 = st.columns([5, 1, 1])
            with col1:
                st.markdown(f"**{row['name']}** ({row['category']}) - Qty: {row['quantity']} - ${row['price']:.2f}")
            with col2:
                if st.button("✏️", key=f"edit_{row['id']}"):
                    st.session_state.editing_id = row['id']
            with col3:
                if st.button("🗑️", key=f"delete_{row['id']}"):
                    st.session_state.inventory = [item for item in st.session_state.inventory if item['id'] != row['id']]
                    st.experimental_rerun()

            # Edit Form
            if st.session_state.editing_id == row['id']:
                with st.form(f"edit_form_{row['id']}"):
                    new_name = st.text_input("Item Name", row['name'])
                    new_category = st.text_input("Category", row['category'])
                    new_quantity = st.number_input("Quantity", value=row['quantity'], min_value=1, step=1)
                    new_price = st.number_input("Price", value=row['price'], min_value=0.0, step=0.01)
                    save = st.form_submit_button("Save")
                if save:
                    for item in st.session_state.inventory:
                        if item['id'] == row['id']:
                            item.update({
                                "name": new_name,
                                "category": new_category,
                                "quantity": new_quantity,
                                "price": new_price
                            })
                            st.session_state.editing_id = None
                            st.success("✅ Item updated!")
                            st.experimental_rerun()

        st.download_button("📥 Download as CSV", df.to_csv(index=False), file_name="inventory.csv", mime="text/csv")
    else:
        st.info("No items in inventory yet. Add some first!")

# ---------- Ask Agent Page ----------
elif selection == "Ask Agent":
    st.header("🧠 Ask Inventory Agent")

    if not st.session_state.inventory:
        st.info("No inventory data available. Add items first.")
    else:
        df = pd.DataFrame(st.session_state.inventory)
        st.dataframe(df, use_container_width=True)

        user_question = st.text_area("💬 What do you want to know about your inventory?")
        ask = st.button("Ask Agent")

        if ask and user_question:
            try:
                inventory_text = df.to_string(index=False)
                messages = [
                    {
                        "role": "system",
                        "content": "You're an inventory assistant that analyzes and answers inventory-related questions clearly and intelligently."
                    },
                    {
                        "role": "user",
                        "content": f"""Here's my inventory data:

{inventory_text}

Question: {user_question}"""
                    }
                ]
                response = litellm.completion(model=litellm.model, messages=messages)
                answer = response["choices"][0]["message"]["content"]
                st.success(answer)
            except Exception as e:
                st.error(f"⚠️ Agent error: {str(e)}")
