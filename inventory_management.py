import streamlit as st
import pandas as pd
import os
import uuid

# Load or create inventory file
INVENTORY_FILE = "inventory.csv"
if os.path.exists(INVENTORY_FILE):
    df = pd.read_csv(INVENTORY_FILE)
else:
    df = pd.DataFrame(columns=["id", "item", "category", "quantity", "price"])
    df.to_csv(INVENTORY_FILE, index=False)

def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

# Page config
st.set_page_config(page_title="Inventory Manager", layout="wide")
st.sidebar.title("📚 Inventory App")

page = st.sidebar.radio("Go to", ["Add Item", "View Inventory", "Ask the Agent"])
st.title("📦 Inventory Management System")

# --- Add Item Page ---
if page == "Add Item":
    st.header("➕ Add Inventory Item")
    with st.form("add_form"):
        item = st.text_input("Item Name")
        category = st.text_input("Category")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        price = st.number_input("Price ($)", min_value=0.0, step=0.01, format="%.2f")
        submit = st.form_submit_button("Add Item")
        if submit:
            new_id = str(uuid.uuid4())
            new_row = {
                "id": new_id,
                "item": item.strip(),
                "category": category.strip(),
                "quantity": quantity,
                "price": price
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_inventory(df)
            st.success(f"{item} added successfully!")
            st.experimental_rerun()

# --- View Inventory Page ---
elif page == "View Inventory":
    st.header("📋 Current Inventory")
    if df.empty:
        st.info("No items in inventory.")
    else:
        # Table layout
        st.markdown("#### Inventory Items")
        header_cols = st.columns([2, 2, 1, 1, 1])
        header_cols[0].markdown("**Item**")
        header_cols[1].markdown("**Category**")
        header_cols[2].markdown("**Quantity**")
        header_cols[3].markdown("**Price**")
        header_cols[4].markdown("**Actions**")

        for i, row in df.iterrows():
            cols = st.columns([2, 2, 1, 1, 1])
            cols[0].markdown(row["item"])
            cols[1].markdown(row["category"])
            cols[2].markdown(str(int(row["quantity"])))
            cols[3].markdown(f"${float(row['price']):.2f}")
            if cols[4].button("Delete", key=f"del_{row['id']}"):
                df = df[df["id"] != row["id"]]
                save_inventory(df)
                st.experimental_rerun()

# --- Ask the Agent Page ---
elif page == "Ask the Agent":
    st.header("🤖 Ask the Inventory Agent")

    user_input = st.text_input("Ask anything about the inventory...")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if user_input:
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": user_input})

        # Prepare context as text (you can make this more structured)
        inventory_summary = ""
        for i, row in df.iterrows():
            inventory_summary += f"- {row['item']} ({row['category']}): {row['quantity']} units at ${row['price']}\n"

        prompt = f"""You are an inventory assistant. The current inventory is:
{inventory_summary}

User question: {user_input}
Answer briefly and accurately."""

        # Use LLM (replace with your API call)
        try:
            import openai
            openai.api_key = st.secrets.get("OPENAI_API_KEY", "")  # replace with your key logic

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an inventory expert assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            reply = response.choices[0].message.content.strip()
        except Exception as e:
            reply = f"Error: {str(e)}"

        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    # Display chat
    for message in st.session_state.chat_history:
        role = "🧑" if message["role"] == "user" else "🤖"
        st.markdown(f"**{role} {message['role'].capitalize()}:** {message['content']}")
