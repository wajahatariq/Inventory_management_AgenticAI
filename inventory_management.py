import streamlit as st
import pandas as pd
import os
import json
import hashlib
from datetime import datetime

# Load or initialize data
INVENTORY_FILE = "inventory.json"
CATEGORY_FILE = "categories.json"

# Load inventory data
def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_json(INVENTORY_FILE)
    else:
        return pd.DataFrame(columns=["ID#"])

# Save inventory data
def save_inventory(df):
    df.to_json(INVENTORY_FILE, indent=4)

# Load categories
def load_categories():
    if os.path.exists(CATEGORY_FILE):
        with open(CATEGORY_FILE, "r") as f:
            return json.load(f)
    else:
        return []

# Save categories
def save_categories(categories):
    with open(CATEGORY_FILE, "w") as f:
        json.dump(categories, f, indent=4)

# App logic
st.set_page_config(page_title="Inventory Manager", layout="wide")

if "inventory" not in st.session_state:
    st.session_state.inventory = load_inventory()
if "categories" not in st.session_state:
    st.session_state.categories = load_categories()

columns = st.session_state.categories

menu = ["Add Item", "View Inventory"]
selection = st.sidebar.selectbox("Menu", menu)

df = st.session_state.inventory

# --- View Inventory ---
if selection == "View Inventory":
    st.title("Inventory Viewer")

    if len(columns) == 0:
        st.info("No columns configured yet.")
    elif df.empty:
        st.warning("Inventory is currently empty")
    else:
        user_columns = [col["name"] for col in columns]
        display_columns = ["ID#"] + user_columns

        # Pagination setup
        page_size = 10
        total_rows = len(df)
        total_pages = (total_rows + page_size - 1) // page_size
        current_page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)

        start = (current_page - 1) * page_size
        end = start + page_size
        paged_df = df.iloc[start:end].copy()

        # Generate Action buttons (Edit placeholder + Delete with confirmation)
        def generate_action_buttons(row_id):
            return f"""
            <div style='display:flex; gap:10px'>
                <button onclick=\"alert('Edit feature coming soon!')\" style='color:white;background:#007bff;border:none;padding:4px 8px;border-radius:4px;'>Edit</button>
                <form method=\"post\" onsubmit=\"return confirm('Are you sure you want to delete this item?')\">
                    <input type=\"hidden\" name=\"delete_id\" value=\"{row_id}\" />
                    <button type=\"submit\" style='color:white;background:#dc3545;border:none;padding:4px 8px;border-radius:4px;'>Delete</button>
                </form>
            </div>
            """

        paged_df["Action"] = [generate_action_buttons(i) for i in paged_df.index]

        # Render table using HTML
        table_html = "<table style='width:100%;border-collapse:collapse;'>"
        table_html += "<thead><tr>" + "".join(
            f"<th style='border:1px solid #ccc;padding:6px;background:#eee'>{col}</th>" for col in display_columns + ["Action"]
        ) + "</tr></thead><tbody>"

        for idx, row in paged_df.iterrows():
            table_html += "<tr>"
            for col in display_columns:
                table_html += f"<td style='border:1px solid #ccc;padding:6px'>{row.get(col, '')}</td>"
            table_html += f"<td style='border:1px solid #ccc;padding:6px'>{row['Action']}</td>"
            table_html += "</tr>"

        table_html += "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)

        # Handle delete ID using query param
        delete_id = st.experimental_get_query_params().get("delete_id", [None])[0]
        if delete_id and delete_id.isdigit():
            delete_idx = int(delete_id)
            if 0 <= delete_idx < len(df):
                df.drop(index=delete_idx, inplace=True)
                df.reset_index(drop=True, inplace=True)
                save_inventory(df)
                st.success("Item deleted successfully.")
                st.rerun()
