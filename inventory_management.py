import streamlit as st
import pandas as pd
import litellm
import os
from uuid import uuid4

# --- Set up LiteLLM with API Key from Streamlit secrets ---
litellm.api_key = st.secrets["GEMINI_API_KEY"]
litellm.model = "gemini/gemini-1.5-flash"

# --- Initialize Session State ---
if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "editing_id" not in st.session_state:
    st.session_state.editing_id = None

# --- Sidebar Navigation ---
st.sidebar.title("📦 Inventory Manager")
selection = st.sidebar.radio("Go to:", ["Add Item", "View Inventory", "Ask Agent"])

# --- Add Item Page ---
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
        st.success("Item added successfully!")

# --- View Inventory Page ---
elif selection == "View Inventory":
    st.header("📋 View & Manage Inventory")
    df = pd.DataFrame(st.session_state.inventory)

    if not df.empty:
        # Table headers
        st.markdown("### Inventory Items")
        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 1, 1])
            with col1:
                st.markdown(f"**{row['name']}**")
            with col2:
                st.markdown(row['category'])
            with col3:
                st.markdown(f"{int(row['quantity'])}")
            with col4:
                st.markdown(f"${row['price']:.2f}")
            with col5:
                if st.button("✏️", key=f"edit_{row['id']}"):
                    st.session_state.editing_id = row['id']
            with col6:
                if st.button("🗑️", key=f"delete_{row['id']}"):
                    st.session_state.inventory = [item for item in st.session_state.inventory if item['id'] != row['id']]
                    st.experimental_rerun()

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
                            st.success("Item updated successfully!")
                            st.experimental_rerun()

        # CSV download button
        st.download_button("📥 Download CSV", df.to_csv(index=False), file_name="inventory.csv", mime="text/csv")
    else:
        st.info("No items in inventory yet.")

# --- Ask Agent Page ---
elif selection == "Ask Agent":
    st.header("🧠 Ask Inventory Agent")
    user_question = st.text_area("What do you want to know about your inventory?")
    ask = st.button("Ask Agent")

    if ask and user_question:
        df = pd.DataFrame(st.session_state.inventory)
        data_csv = df.to_csv(index=False)

        try:
            response = litellm.completion(
                messages=[
                    {"role": "system", "content": "You are an intelligent assistant that helps analyze and answer questions about a user's inventory."},
                    {"role": "user", "content": f"""Here's my inventory data:
{data_csv}

Question: {user_question}"""}
                ]
            )
            reply = response["choices"][0]["message"]["content"]
            st.success(reply)
        except Exception as e:
            st.error(f"Agent error: {str(e)}")
