# inventory_agent_app.py

import streamlit as st
import pandas as pd
from inventory_management import InventoryManager

# Streamlit page setup
st.set_page_config(
    page_title="Accessories Tracker",
    page_icon="👜",
    layout="centered"
)

# Initialize inventory manager
if "inventory_manager" not in st.session_state:
    st.session_state.inventory_manager = InventoryManager()

inventory = st.session_state.inventory_manager

# Title
st.title("👜 Personal Accessories Tracker")

# Add Accessory Form
st.header("➕ Add New Accessory")
with st.form("add_form"):
    name = st.text_input("Item Name")
    quantity = st.number_input("Quantity", min_value=0, step=1)
    category = st.text_input("Category (e.g., Ring, Watch, Sunglasses)")
    location = st.text_input("Location (e.g., Drawer, Closet)")
    price = st.number_input("Estimated Price (PKR)", min_value=0.0, step=0.1)

    submitted = st.form_submit_button("Add Accessory")

    if submitted:
        if name:
            item = {
                "name": name,
                "quantity": quantity,
                "category": category,
                "location": location,
                "price": price
            }
            inventory.add_item(item)
            st.success(f"✅ '{name}' added to inventory!")
        else:
            st.error("Item Name is required!")

# Show Inventory
st.header("📋 My Accessories")
items = inventory.get_inventory()

if not items:
    st.info("No accessories in your inventory yet.")
else:
    for idx, item in enumerate(items):
        with st.expander(f"🧾 {item['name']}"):
            st.markdown(f"""
            - **Quantity**: {item['quantity']}
            - **Category**: {item['category']}
            - **Location**: {item['location']}
            - **Price**: PKR {item['price']:.2f}
            """)

            # Edit form
            with st.form(f"edit_form_{idx}"):
                new_name = st.text_input("Edit Name", item["name"], key=f"name_{idx}")
                new_quantity = st.number_input("Edit Quantity", value=item["quantity"], min_value=0, key=f"qty_{idx}")
                new_category = st.text_input("Edit Category", item["category"], key=f"cat_{idx}")
                new_location = st.text_input("Edit Location", item["location"], key=f"loc_{idx}")
                new_price = st.number_input("Edit Price", value=float(item["price"]), min_value=0.0, key=f"price_{idx}")

                update = st.form_submit_button("Update Accessory")
                if update:
                    updated_item = {
                        "name": new_name,
                        "quantity": new_quantity,
                        "category": new_category,
                        "location": new_location,
                        "price": new_price
                    }
                    inventory.update_item(idx, updated_item)
                    st.success("✅ Updated successfully!")
                    st.experimental_rerun()

            # Delete button
            if st.button(f"🗑️ Delete '{item['name']}'", key=f"delete_{idx}"):
                inventory.delete_item(idx)
                st.warning(f"'{item['name']}' deleted from inventory.")
                st.experimental_rerun()

# CSV Download
st.header("📤 Export Inventory")

if items:
    df = pd.DataFrame(items)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️ Download as CSV",
        data=csv,
        file_name="accessories_inventory.csv",
        mime="text/csv"
    )
