import streamlit as st
import pandas as pd
import litellm
import os
from uuid import uuid4

# Set up LiteLLM with API Key
litellm.api_key = st.secrets["GEMINI_API_KEY"]
litellm.model = "gemini/gemini-1.5-flash"

# ---------- Session State Initialization ----------
if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "delete_id" not in st.session_state:
    st.session_state.delete_id = None

# ---------- Sidebar Navigation ----------
st.sidebar.title("Inventory Manager")
selection = st.sidebar.radio("Go to:", ["Add Item", "View Inventory", "Ask Agent"])

# ---------- Add Item Page ----------
if selection == "Add Item":
    st.header("Add New Inventory Item")
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

# ---------- View Inventory Page ----------
elif selection == "View Inventory":
    st.header("📋 View & Manage Inventory")
    df = pd.DataFrame(st.session_state.inventory)

    if not df.empty:
        st.write("### Inventory Items")
        columns = st.columns([3, 3, 2, 2, 2])  # Name, Category, Qty, Price, Delete

        columns[0].markdown("**Name**")
        columns[1].markdown("**Category**")
        columns[2].markdown("**Quantity**")
        columns[3].markdown("**Price**")
        columns[4].markdown("**Action**")

        for idx, row in df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([3, 3, 2, 2, 2])
            col1.markdown(row["name"])
            col2.markdown(row["category"])
            col3.markdown(f"{int(row['quantity'])}")
            col4.markdown(f"${float(row['price']):.2f}")
            if col5.button("Delete", key=f"del_{row['id']}"):
                st.session_state.delete_id = row["id"]

        # Handle Deletion After Loop
        if st.session_state.delete_id:
            st.session_state.inventory = [
                i for i in st.session_state.inventory if i["id"] != st.session_state.delete_id
            ]
            st.session_state.delete_id = None
            st.experimental_rerun()

        # Download CSV
        df_display = df.drop(columns=["id"])
        st.download_button("Download CSV", df_display.to_csv(index=False), file_name="inventory.csv", mime="text/csv")

    else:
        st.info("No items in inventory.")

# ---------- Ask Agent Page ----------
elif selection == "Ask Agent":
    st.header("Ask Inventory Agent")
    user_question = st.text_area("What do you want to know about your inventory?")
    ask = st.button("Ask Agent")

    if ask and user_question:
        df = pd.DataFrame(st.session_state.inventory)
        data_csv = df.drop(columns=["id"]).to_csv(index=False)

        try:
            response = litellm.completion(
                model=litellm.model,
                messages=[
                    {"role": "system", "content": "You are an intelligent assistant that helps analyze and answer questions about a user's inventory."},
                    {"role": "user", "content": f"Here's my inventory data:\n{data_csv}\n\nQuestion: {user_question}"}
                ]
            )
            agent_reply = response["choices"][0]["message"]["content"]
            st.success(agent_reply)
        except Exception as e:
            st.error(f"Agent error: {str(e)}")
