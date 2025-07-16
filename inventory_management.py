import streamlit as st
import litellm
import os

# Setup your Gemini model here using LiteLLM
litellm.model = "gemini/gemini-1.5-flash"
litellm.api_key = os.getenv("GEMINI_API_KEY") or "your-api-key-here"  # Replace with your Gemini API Key

# ---- Memory store ----
if "inventory" not in st.session_state:
    st.session_state.inventory = []

# ---- LLM Call Function ----
def ask_gemini(message):
    try:
        response = litellm.completion(
            model=litellm.model,
            messages=[
                {"role": "system", "content": "You are a helpful inventory management assistant."},
                {"role": "user", "content": message}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ---- Streamlit App UI ----
st.set_page_config(page_title="Inventory Agent", page_icon="📦")
st.title("📦 Inventory Management Agent")

menu = st.sidebar.radio("Choose action", ["View Inventory", "Add Item", "Search Item", "Ask Agent"])

# View Inventory
if menu == "View Inventory":
    st.subheader("📋 Current Inventory")
    if st.session_state.inventory:
        st.table(st.session_state.inventory)
    else:
        st.info("No items in inventory yet.")

# Add Item
elif menu == "Add Item":
    st.subheader("➕ Add New Item")
    name = st.text_input("Item Name")
    quantity = st.number_input("Quantity", min_value=1, step=1)
    category = st.text_input("Category")

    if st.button("Add to Inventory"):
        new_item = {"Name": name, "Quantity": quantity, "Category": category}
        st.session_state.inventory.append(new_item)
        st.success(f"Item '{name}' added!")

# Search Item
elif menu == "Search Item":
    st.subheader("🔍 Search Inventory")
    search_query = st.text_input("Search by name or category")

    if st.button("Search"):
        result = [item for item in st.session_state.inventory if search_query.lower() in item["Name"].lower() or search_query.lower() in item["Category"].lower()]
        if result:
            st.table(result)
        else:
            st.warning("No matching items found.")

# Ask LLM Agent
elif menu == "Ask Agent":
    st.subheader("🤖 Ask Inventory Assistant")
    user_input = st.text_area("Ask anything about inventory (e.g., 'How many laptops do we have?')")

    if st.button("Get Response"):
        # Format the inventory data for LLM context
        inventory_context = "\n".join([f"{i['Quantity']} x {i['Name']} ({i['Category']})" for i in st.session_state.inventory])
        prompt = f"""Here's our current inventory:\n{inventory_context}\n\nQuestion: {user_input}"""

        answer = ask_gemini(prompt)
        st.success(answer)
