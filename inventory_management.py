import streamlit as st
import pandas as pd
import uuid
import litellm
from game.core import Agent, Environment, Tool

# --- LiteLLM Gemini setup ---
litellm.api_key = st.secrets["GEMINI_API_KEY"]
litellm.model = "gemini/gemini-1.5-flash"

# --- Inventory Manager Class ---
class InventoryManager:
    def __init__(self):
        if 'inventory_data' not in st.session_state:
            st.session_state.inventory_data = []

    def add_item(self, category, item_name, quantity, description):
        item_id = str(uuid.uuid4())
        st.session_state.inventory_data.append({
            "ID": item_id,
            "Category": category,
            "Item Name": item_name,
            "Quantity": quantity,
            "Description": description
        })

    def get_items(self):
        return pd.DataFrame(st.session_state.inventory_data)

    def delete_item(self, item_id):
        st.session_state.inventory_data = [item for item in st.session_state.inventory_data if item["ID"] != item_id]

    def edit_item(self, item_id, category, item_name, quantity, description):
        for item in st.session_state.inventory_data:
            if item["ID"] == item_id:
                item["Category"] = category
                item["Item Name"] = item_name
                item["Quantity"] = quantity
                item["Description"] = description


# --- Initialize Manager ---
manager = InventoryManager()

# --- Sidebar Navigation ---
page = st.sidebar.radio("Navigation", ["Add Item", "View Inventory", "Ask Agent"])

st.title("🧳 Personal Accessories Inventory Manager")

# --- Add Item Page ---
if page == "Add Item":
    st.subheader("➕ Add New Item")
    category = st.selectbox("Category", ["Watch", "Shoes", "Wallet", "Perfume", "Other"])
    item_name = st.text_input("Item Name")
    quantity = st.number_input("Quantity", min_value=1, step=1)
    description = st.text_area("Description")
    if st.button("Add Item"):
        manager.add_item(category, item_name, quantity, description)
        st.success("Item added successfully!")

# --- View Inventory Page ---
elif page == "View Inventory":
    st.subheader("📦 Current Inventory")
    df = manager.get_items()
    edited_df = df.copy()

    if not df.empty:
        for index, row in df.iterrows():
            with st.expander(f"{row['Item Name']} - {row['Category']}"):
                new_cat = st.selectbox("Edit Category", ["Watch", "Shoes", "Wallet", "Perfume", "Other"], index=["Watch", "Shoes", "Wallet", "Perfume", "Other"].index(row['Category']), key=f"cat_{row['ID']}")
                new_name = st.text_input("Edit Item Name", row['Item Name'], key=f"name_{row['ID']}")
                new_qty = st.number_input("Edit Quantity", value=int(row['Quantity']), key=f"qty_{row['ID']}")
                new_desc = st.text_area("Edit Description", row['Description'], key=f"desc_{row['ID']}")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Save", key=f"save_{row['ID']}"):
                        manager.edit_item(row['ID'], new_cat, new_name, new_qty, new_desc)
                        st.success("Item updated!")
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{row['ID']}"):
                        manager.delete_item(row['ID'])
                        st.warning("Item deleted.")

        # CSV Download Option
        st.download_button("⬇️ Download CSV", data=manager.get_items().to_csv(index=False), file_name="inventory.csv", mime="text/csv")
    else:
        st.info("No items in your inventory yet.")

# --- Ask Agent Page ---
elif page == "Ask Agent":
    st.subheader("💬 Ask Inventory Assistant")
    user_question = st.text_area("Ask a question about your accessories inventory")
    if st.button("Ask") and user_question:
        df = manager.get_items()
        if df.empty:
            st.warning("Inventory is empty. Add items first.")
        else:
            from litellm import completion
            response = completion(
                messages=[
                    {"role": "system", "content": "You are a personal accessories inventory assistant. Answer questions based on the data provided."},
                    {"role": "user", "content": f"Inventory CSV:\n{df.to_csv(index=False)}\n\nQuestion: {user_question}"},
                ]
            )
            st.success(response['choices'][0]['message']['content'])
