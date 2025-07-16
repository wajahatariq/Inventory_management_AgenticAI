import streamlit as st
import pandas as pd
import os
import litellm
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini model
litellm.model = "gemini/gemini-1.5-flash"
litellm.api_key = os.getenv("GEMINI_API_KEY")

# Initialize session states
if "inventory" not in st.session_state:
    st.session_state.inventory = []

if "categories" not in st.session_state:
    st.session_state.categories = []

# Sidebar options
st.sidebar.title("Inventory Manager")
page = st.sidebar.radio("Go to", ["Add Inventory", "View Inventory", "View Categories", "Ask Agent"])

st.title("🗂️ Inventory Management System")

# ---------- Add Inventory ----------
if page == "Add Inventory":
    st.subheader("Add Inventory Item")

    name = st.text_input("Item Name")
    category = st.selectbox("Category", options=st.session_state.categories + ["-- Add New Category --"])
    if category == "-- Add New Category --":
        category = st.text_input("Enter New Category")

    quantity = st.number_input("Quantity", min_value=0, step=1)
    price = st.number_input("Price", min_value=0.0, format="%.2f")

    if st.button("Add Item"):
        if name and category:
            # Add new category if not already in list
            if category not in st.session_state.categories:
                st.session_state.categories.append(category)

            item = {"name": name, "category": category, "quantity": quantity, "price": price}
            st.session_state.inventory.append(item)
            st.success(f"Item '{name}' added to inventory.")
        else:
            st.error("Please fill all the fields.")

# ---------- View Inventory ----------
elif page == "View Inventory":
    st.subheader("📋 View & Manage Inventory")

    if st.session_state.inventory:
        df = pd.DataFrame(st.session_state.inventory)
        df.index += 1  # Start row index from 1

        # Show as table with delete button per row
        for i, row in df.iterrows():
            cols = st.columns([3, 3, 2, 2, 2])
            cols[0].markdown(f"**{row['name']}**")
            cols[1].markdown(f"{row['category']}")
            cols[2].markdown(f"{int(row['quantity'])}")
            cols[3].markdown(f"${float(row['price']):.2f}")
            if cols[4].button("Delete", key=f"del_{i}"):
                st.session_state.inventory.pop(i - 1)
                st.rerun()

        # Table headers
        st.markdown("#### Inventory Items")
        st.markdown("| Item | Category | Quantity | Price |")
        st.markdown("|------|----------|----------|--------|")
    else:
        st.info("Inventory is empty.")

# ---------- View Categories ----------
elif page == "View Categories":
    st.subheader("📁 Available Categories")

    if st.session_state.categories:
        df_cat = pd.DataFrame({"Category": st.session_state.categories})
        df_cat.index += 1

        cols = st.columns([6, 1])
        for i, cat in df_cat.iterrows():
            cols = st.columns([10, 2])
            cols[0].markdown(f"**{cat['Category']}**")
            if cols[1].button("Delete", key=f"delcat_{i}"):
                st.session_state.categories.pop(i - 1)
                st.rerun()
    else:
        st.info("No categories added yet.")

# ---------- Ask Agent ----------
elif page == "Ask Agent":
    st.subheader("🤖 Ask the Inventory Agent")

    user_query = st.text_area("Enter your question about the inventory")
    if st.button("Ask Agent"):
        if not st.session_state.inventory:
            st.warning("Inventory is empty.")
        elif user_query.strip() == "":
            st.warning("Please enter a question.")
        else:
            import litellm

            df = pd.DataFrame(st.session_state.inventory)
            data_csv = df.to_csv(index=False)

            try:
                messages = [
                    {"role": "system", "content": "You are an inventory assistant. Answer user questions based on the CSV data provided."},
                    {"role": "user", "content": f"Here's my inventory data:\n{data_csv}"},
                    {"role": "user", "content": user_query}
                ]
                response = litellm.completion(
                    model=litellm.model,
                    messages=messages,
                )
                st.success(response["choices"][0]["message"]["content"])
            except Exception as e:
                st.error(f"Agent error: {e}")
