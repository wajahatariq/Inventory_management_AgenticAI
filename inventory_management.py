import streamlit as st
import pandas as pd
import os
from uuid import uuid4
import litellm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
litellm.model = "gemini/gemini-1.5-flash"
litellm.api_key = os.getenv("GEMINI_API_KEY") or "your-api-key-here"

# Session state initialization
if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "categories" not in st.session_state:
    st.session_state.categories = []

# Sidebar navigation
st.sidebar.title("Inventory Manager")
page = st.sidebar.radio("Navigation", ["Add Category", "View Categories", "View Inventory", "Ask Agent"])

# ---------- Add Category Page ----------
if page == "Add Category":
    st.title("➕ Add New Category")
    name = st.text_input("Category Name")
    type_ = st.text_input("Category Type")
    if st.button("Add Category"):
        st.session_state.categories.append({"id": str(uuid4()), "name": name, "type": type_})
        st.success("Category added!")

# ---------- View Categories Page ----------
elif page == "View Categories":
    st.title("📁 Categories")
    if st.session_state.categories:
        cat_df = pd.DataFrame(st.session_state.categories)
        cat_df = cat_df.drop(columns=["id"], errors="ignore")
        for i, row in cat_df.iterrows():
            col1, col2, col3 = st.columns([4, 4, 2])
            col1.markdown(f"**{row['name']}**")
            col2.markdown(row['type'])
            if col3.button("Delete", key=f"delete_cat_{i}"):
                del st.session_state.categories[i]
                st.experimental_rerun()
    else:
        st.info("No categories added yet.")

# ---------- View Inventory Page ----------
elif page == "View Inventory":
    st.title("📋 View & Manage Inventory")
    if st.session_state.inventory:
        df = pd.DataFrame(st.session_state.inventory)
        display_df = df.drop(columns=["id"], errors="ignore")

        # Table headings
        col_names = st.columns([3, 3, 2, 2, 2])
        headers = ["Name", "Category", "Quantity", "Price", ""]
        for i, header in enumerate(headers):
            col_names[i].markdown(f"**{header}**")

        # Table rows with delete button
        for i, row in display_df.iterrows():
            cols = st.columns([3, 3, 2, 2, 2])
            cols[0].markdown(row['name'])
            cols[1].markdown(row['category'])
            cols[2].markdown(str(row['quantity']))
            cols[3].markdown(f"${row['price']:.2f}")
            if cols[4].button("Delete", key=f"delete_item_{i}"):
                del st.session_state.inventory[i]
                st.experimental_rerun()

        # CSV Download
        df_csv = df.drop(columns=["id"], errors="ignore")
        data_csv = df_csv.to_csv(index=False)
        st.download_button("Download CSV", data=data_csv, file_name="inventory.csv", mime="text/csv")
    else:
        st.info("No inventory items yet.")

    st.divider()
    st.subheader("➕ Add New Inventory Item")
    name = st.text_input("Item Name")
    category = st.selectbox("Category", [cat['name'] for cat in st.session_state.categories])
    quantity = st.number_input("Quantity", min_value=0)
    price = st.number_input("Price", min_value=0.0)
    if st.button("Add Item"):
        st.session_state.inventory.append({
            "id": str(uuid4()),
            "name": name,
            "category": category,
            "quantity": quantity,
            "price": price
        })
        st.success("Item added!")

# ---------- Ask Agent Page ----------
elif page == "Ask Agent":
    st.title("🧠 Ask Inventory Agent")
    question = st.text_area("Ask a question about your inventory:")
    if st.button("Ask Agent"):
        df = pd.DataFrame(st.session_state.inventory)
        df = df.drop(columns=["id"], errors="ignore")
        inventory_text = df.to_string(index=False) if not df.empty else "No items."

        messages = [
            {"role": "system", "content": "You are an inventory assistant. Analyze the inventory and answer questions."},
            {"role": "user", "content": f"Here's my inventory data:\n{inventory_text}\n\nQuestion: {question}"}
        ]

        try:
            response = litellm.completion(model=litellm.model, messages=messages)
            st.write(response["choices"][0]["message"]["content"])
        except Exception as e:
            st.error(f"Error from agent: {e}")
