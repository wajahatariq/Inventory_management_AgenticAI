import streamlit as st
import pandas as pd
import os
import uuid

# File to store inventory data
INVENTORY_FILE = "inventory.csv"

# Load existing inventory or create an empty DataFrame
if os.path.exists(INVENTORY_FILE):
    df = pd.read_csv(INVENTORY_FILE)
else:
    df = pd.DataFrame(columns=["id", "item", "category", "quantity", "price"])
    df.to_csv(INVENTORY_FILE, index=False)

# Save to CSV
def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

st.set_page_config(page_title="Inventory Manager", layout="centered")
st.title("📦 Inventory Manager")

# Section: Add New Inventory Item
st.header("➕ Add Inventory Item")
with st.form("add_item_form"):
    item = st.text_input("Item Name")
    category = st.text_input("Category")
    quantity = st.number_input("Quantity", min_value=1, step=1)
    price = st.number_input("Price ($)", min_value=0.0, step=0.01, format="%.2f")
    submitted = st.form_submit_button("Add Item")
    if submitted:
        new_id = str(uuid.uuid4())
        new_item = {
            "id": new_id,
            "item": item.strip(),
            "category": category.strip(),
            "quantity": quantity,
            "price": price
        }
        df = pd.concat([df, pd.DataFrame([new_item])], ignore_index=True)
        save_inventory(df)
        st.success(f"{item} added to inventory.")

# Section: View Inventory Table
st.header("📋 View & Manage Inventory")

if df.empty:
    st.info("No items in inventory yet.")
else:
    # Display markdown table
    table_md = "| Item | Category | Quantity | Price ($) | Actions |\n"
    table_md += "|------|----------|----------|------------|---------|\n"

    for index, row in df.iterrows():
        item_name = row["item"]
        category = row["category"]
        quantity = int(row["quantity"])
        price = float(row["price"])
        delete_key = f"delete_{row['id']}"

        table_md += f"| {item_name} | {category} | {quantity} | ${price:.2f} | "

        # Add delete button inline
        delete_col = st.columns([1, 1, 1, 1, 1])[4]
        with delete_col:
            if st.button("Delete", key=delete_key):
                df = df[df["id"] != row["id"]]
                save_inventory(df)
                st.experimental_rerun()

        table_md += "⬅️ Click Button\n"

    st.markdown(table_md)

