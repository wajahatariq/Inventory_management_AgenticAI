import streamlit as st
import pandas as pd
import os
import litellm
from litellm import completion
from io import StringIO

# LiteLLM config
litellm.model = "gemini/gemini-1.5-flash"
litellm.api_key = os.getenv("GEMINI_API_KEY") or "your-api-key-here"

st.set_page_config(page_title="Personal Accessories Inventory", layout="wide")

# Session state initialization
if "categories" not in st.session_state:
    st.session_state.categories = []

if "inventory" not in st.session_state:
    st.session_state.inventory = []

# Sidebar
st.sidebar.title("Inventory App")
page = st.sidebar.radio("Menu", ["Add Category", "View Inventory", "Ask Agent"])

# Add Category Page
if page == "Add Category":
    st.title("➕ Add New Category")
    with st.form("category_form"):
        name = st.text_input("Category Name")
        type_ = st.text_input("Type")
        submitted = st.form_submit_button("Add Category")
        if submitted:
            st.session_state.categories.append({"name": name, "type": type_})
            st.success(f"Category '{name}' added!")

# View Inventory Page
elif page == "View Inventory":
    st.title("📋 View & Manage Inventory")

    # Add Inventory Form
    with st.form("add_inventory"):
        name = st.text_input("Item Name")
        category = st.selectbox("Category", [cat["name"] for cat in st.session_state.categories])
        quantity = st.number_input("Quantity", min_value=0)
        price = st.number_input("Price ($)", min_value=0.0)
        add_item = st.form_submit_button("Add Item")
        if add_item:
            st.session_state.inventory.append({
                "name": name, "category": category,
                "quantity": quantity, "price": price
            })
            st.success(f"Added '{name}' to inventory.")

    st.markdown("---")
    st.subheader("Inventory Items")
    if st.session_state.inventory:
        df = pd.DataFrame(st.session_state.inventory)
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
        col1.markdown("**Name**")
        col2.markdown("**Category**")
        col3.markdown("**Qty**")
        col4.markdown("**Price ($)**")
        col5.markdown("**Delete**")

        for i, row in df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
            col1.markdown(row["name"])
            col2.markdown(row["category"])
            col3.markdown(str(row["quantity"]))
            col4.markdown(f"${row['price']:.2f}")
            if col5.button("Delete", key=f"del_inventory_{i}"):
                st.session_state.inventory.pop(i)
                st.experimental_rerun()

        # CSV Download
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Download Inventory CSV", csv, "inventory.csv", "text/csv")
    else:
        st.info("No items in inventory yet.")

    st.markdown("---")
    st.subheader("Categories")
    if st.session_state.categories:
        df_cat = pd.DataFrame(st.session_state.categories)
        col1, col2, col3 = st.columns([4, 4, 2])
        col1.markdown("**Name**")
        col2.markdown("**Type**")
        col3.markdown("**Delete**")

        for i, row in df_cat.iterrows():
            col1, col2, col3 = st.columns([4, 4, 2])
            col1.markdown(row["name"])
            col2.markdown(row["type"])
            if col3.button("Delete", key=f"del_category_{i}"):
                st.session_state.categories.pop(i)
                st.experimental_rerun()
    else:
        st.info("No categories found.")

# Ask Agent Page
elif page == "Ask Agent":
    st.title("🤖 Ask Inventory Agent")

    user_query = st.text_input("Ask a question about your inventory:")
    ask = st.button("Ask Agent")

    if ask and user_query:
        df = pd.DataFrame(st.session_state.inventory)
        if df.empty:
            st.warning("No inventory data to analyze.")
        else:
            inventory_data = df.to_string(index=False)
            try:
                response = completion(
                    model=litellm.model,
                    messages=[
                        {"role": "system", "content": "You're a helpful assistant that answers questions about inventory."},
                        {"role": "user", "content": f"Here's my inventory data:\n\n{inventory_data}\n\nNow answer this: {user_query}"}
                    ]
                )
                answer = response["choices"][0]["message"]["content"]
                st.markdown("### 💡 Agent Response")
                st.write(answer)
            except Exception as e:
                st.error(f"Agent failed: {e}")
