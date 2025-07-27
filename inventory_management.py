import streamlit as st
import pandas as pd
import os
import json

st.set_page_config(page_title="Inventory Manager", layout="wide")

# --- File Paths ---
INVENTORY_FILE = "inventory.csv"
CATEGORY_CONFIG = "category_config.json"

# --- Helpers for Category Configuration ---
def load_category_config():
    if os.path.exists(CATEGORY_CONFIG):
        with open(CATEGORY_CONFIG, "r") as f:
            return json.load(f)
    return {}

def save_category_config(config):
    with open(CATEGORY_CONFIG, "w") as f:
        json.dump(config, f, indent=2)

# --- Initialize Inventory File ---
def initialize_inventory():
    if not os.path.exists(INVENTORY_FILE):
        df = pd.DataFrame(columns=["ID#"])
        df.to_csv(INVENTORY_FILE, index=False)

# --- Add Category (Column) ---
def add_category():
    st.title("➕ Add New Category (Column)")

    column_name = st.text_input("Enter new column name:")
    column_type = st.selectbox("Select column type:", ["Text", "Number", "Date", "Time"])

    if st.button("Add Column"):
        if column_name.strip() == "":
            st.error("Column name cannot be empty.")
            return

        df = pd.read_csv(INVENTORY_FILE)
        if column_name in df.columns:
            st.warning("This column already exists.")
            return

        # Add column to DataFrame
        df[column_name] = ""
        df.to_csv(INVENTORY_FILE, index=False)

        # Save column type in config
        config = load_category_config()
        config[column_name] = column_type
        save_category_config(config)

        st.success(f"Column '{column_name}' of type '{column_type}' added successfully!")

# --- Add Inventory Item ---
def add_inventory():
    st.title("📦 Add Inventory Item")

    df = pd.read_csv(INVENTORY_FILE)
    config = load_category_config()

    if df.empty or len(df.columns) <= 1:
        st.warning("No columns found. Please add categories (columns) first.")
        return

    with st.form("add_inventory_form"):
        new_entry = {}

        for col in df.columns:
            if col == "ID#":
                continue  # ID auto-generated

            col_type = config.get(col, "Text")

            if col_type == "Number":
                value = st.number_input(col)
            elif col_type == "Date":
                value = st.date_input(col)
            elif col_type == "Time":
                value = st.time_input(col)
            else:
                value = st.text_input(col)

            new_entry[col] = value

        submitted = st.form_submit_button("Add Item")

        if submitted:
            new_id = int(df["ID#"].max()) + 1 if not df["ID#"].empty else 1
            new_entry["ID#"] = new_id

            # Reorder to match column order
            new_row = pd.DataFrame([new_entry])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(INVENTORY_FILE, index=False)

            st.success("Inventory item added successfully!")

# --- View Inventory ---
def view_inventory():
    st.title("📋 View Inventory")

    if not os.path.exists(INVENTORY_FILE):
        st.warning("No inventory file found. Please add data first.")
        return

    df = pd.read_csv(INVENTORY_FILE)
    if df.empty:
        st.info("Inventory is currently empty.")
    else:
        st.dataframe(df, use_container_width=True)

# --- Sidebar Navigation ---
def main():
    initialize_inventory()

    st.sidebar.title("📁 Navigation")
    choice = st.sidebar.radio("Go to:", ["View Inventory", "Add Inventory", "Add Category"])

    if choice == "View Inventory":
        view_inventory()
    elif choice == "Add Inventory":
        add_inventory()
    elif choice == "Add Category":
        add_category()

if __name__ == "__main__":
    main()
