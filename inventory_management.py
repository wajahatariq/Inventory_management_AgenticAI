import streamlit as st
import pandas as pd
import uuid
import requests
from io import StringIO

# --- Gemini API KEY ---
API_KEY = "AIzaSyBviI-5MF2edr6H8KLQ8mO6sPLy-DjTS64"

# --- Page setup ---
st.set_page_config(page_title="Accessory Inventory", page_icon="🎒")

# --- Helper: Generate Unique ID
def generate_id():
    return str(uuid.uuid4())[:8]

# --- Session state init ---
if "inventory" not in st.session_state:
    st.session_state.inventory = []

# --- Sidebar: Add New Accessory ---
with st.sidebar:
    st.header("➕ Add New Accessory")
    name = st.text_input("Accessory Name")
    category = st.text_input("Category")
    quantity = st.number_input("Quantity", min_value=1, step=1)
    location = st.text_input("Location")
    description = st.text_area("Description")
    add_button = st.button("Add Accessory")

    if add_button and name:
        st.session_state.inventory.append({
            "id": generate_id(),
            "Name": name,
            "Category": category,
            "Quantity": quantity,
            "Location": location,
            "Description": description
        })
        st.success(f"'{name}' added!")

# --- Inventory Table Section ---
st.title("🎒 My Accessory Inventory")

df = pd.DataFrame(st.session_state.inventory)

if not df.empty:
    csv = df.drop(columns="id").to_csv(index=False)
    st.download_button("📥 Download CSV", data=csv, file_name="my_accessories.csv", mime="text/csv")

    # --- Editable Data Table ---
    edited_df = st.data_editor(
        df.drop(columns="id"),
        key="data_editor",
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
    )

    # --- Update the inventory list from edited DataFrame ---
    for i, row in edited_df.iterrows():
        st.session_state.inventory[i].update(row.to_dict())

    # --- Delete Buttons for Each Row ---
    st.subheader("🗑️ Delete Accessory")
    for i, item in enumerate(st.session_state.inventory):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.write(f"**{item['Name']}** - {item['Category']}")
        with col2:
            if st.button("❌", key=f"delete_{i}"):
                deleted_item = st.session_state.inventory.pop(i)
                st.warning(f"Deleted {deleted_item['Name']}")
                st.experimental_rerun()
else:
    st.info("No accessories yet. Use the sidebar to add some.")

# --- Ask the Agent Section ---
st.markdown("---")
st.subheader("🤖 Ask the Inventory Agent")

user_question = st.text_input("Ask anything about your accessories...")

if st.button("Ask Agent") and user_question:
    # Send to Gemini API
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
        params={"key": API_KEY},
        json={
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"You are an inventory assistant. Here's the data:\n{df.to_csv(index=False)}\n\nQuestion: {user_question}"
                        }
                    ]
                }
            ]
        }
    )

    if response.status_code == 200:
        result = response.json()
        answer = result['candidates'][0]['content']['parts'][0]['text']
        st.success("Agent Response:")
        st.write(answer)
    else:
        st.error("Failed to get response from the agent. Please check your API key.")
