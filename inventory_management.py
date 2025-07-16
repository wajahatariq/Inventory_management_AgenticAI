import streamlit as st
import pandas as pd
import os
import litellm
from io import StringIO

# Set up LiteLLM model and key
litellm.model = "gemini/gemini-1.5-flash"
litellm.api_key = os.getenv("GEMINI_API_KEY") or "your-api-key-here"

# Session State Initialization
if 'inventory' not in st.session_state:
    st.session_state.inventory = []
if 'categories' not in st.session_state:
    st.session_state.categories = set()

# Sidebar Options
st.sidebar.title("📦 Inventory Assistant")
option = st.sidebar.radio("Choose an action:", ["➕ Add Item", "📋 View & Manage Inventory", "🤖 Ask Agent"])

# Page Title
st.title("🎒 Personal Accessories Inventory")

# ➕ Add Inventory Item
if option == "➕ Add Item":
    st.subheader("Add New Item")
    name = st.text_input("Item Name")
    category = st.text_input("Category")
    quantity = st.number_input("Quantity", min_value=0, step=1)
    price = st.number_input("Price", min_value=0.0, step=0.01)

    if st.button("Add to Inventory"):
        if name and category:
            item = {
                "name": name,
                "category": category,
                "quantity": quantity,
                "price": price
            }
            st.session_state.inventory.append(item)
            st.session_state.categories.add(category)
            st.success(f"✅ Added {name} to inventory.")
        else:
            st.error("❌ Please fill all fields.")

# 📋 View & Manage Inventory
elif option == "📋 View & Manage Inventory":
    st.subheader("📋 Inventory Items")
    
    if not st.session_state.inventory:
        st.info("No items in inventory yet.")
    else:
        df = pd.DataFrame(st.session_state.inventory)
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key="inventory_editor"
        )

        st.session_state.inventory = edited_df.to_dict(orient="records")

        if st.button("Download CSV"):
            csv = edited_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Inventory",
                data=csv,
                file_name='inventory.csv',
                mime='text/csv'
            )

# 🤖 Ask Agent About Inventory
elif option == "🤖 Ask Agent":
    st.subheader("Ask Agent About Inventory")

    if not st.session_state.inventory:
        st.info("Please add some inventory items first.")
    else:
        user_question = st.text_input("Ask something about your inventory")

        if user_question:
            df = pd.DataFrame(st.session_state.inventory)
            data_csv = df.to_csv(index=False)

            try:
                response = litellm.completion(
                    model=litellm.model,
                    messages=[
                        {"role": "system", "content": "You are an intelligent assistant that helps analyze and answer questions about a user's inventory."},
                        {"role": "user", "content": f"""Here's my inventory data:

{data_csv}

Question: {user_question}"""}
                    ]
                )
                st.markdown("**🤖 Response:**")
                st.write(response["choices"][0]["message"]["content"])
            except Exception as e:
                st.error(f"Agent Error: {e}")
