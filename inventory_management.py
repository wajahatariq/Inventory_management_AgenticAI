import streamlit as st
import pandas as pd
import json
import os
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# File paths
COLUMN_CONFIG_FILE = "column_config.json"
INVENTORY_FILE = "inventory_data.csv"

# Load column configuration
def load_columns():
    if os.path.exists(COLUMN_CONFIG_FILE):
        with open(COLUMN_CONFIG_FILE, "r") as f:
            return json.load(f)
    return []

# Save column configuration
def save_columns(columns):
    with open(COLUMN_CONFIG_FILE, "w") as f:
        json.dump(columns, f)

# Load inventory
def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        return pd.read_csv(INVENTORY_FILE)
    return pd.DataFrame()

# Save inventory
def save_inventory(df):
    df.to_csv(INVENTORY_FILE, index=False)

# Streamlit App
st.set_page_config(page_title="Inventory Manager", layout="wide")
st.sidebar.title("Inventory Menu")
selection = st.sidebar.radio("Go to", ["Column Manager", "Add Item", "View Inventory"])

# Global State
columns = load_columns()
df = load_inventory()

# --- Column Manager ---
if selection == "Column Manager":
    st.title("Column Manager")
    col1, col2 = st.columns(2)
    with col1:
        new_col_name = st.text_input("Column Name")
    with col2:
        new_col_type = st.selectbox("Column Type", ["text", "number", "date"])

    if st.button("Add Column"):
        if new_col_name.strip() == "":
            st.error("Column name cannot be empty")
        else:
            columns.append({"name": new_col_name.strip(), "type": new_col_type})
            save_columns(columns)
            st.success(f"Column '{new_col_name}' added successfully.")

# --- Add Item ---
if selection == "Add Item":
    st.title("Add Inventory Item")
    if not columns:
        st.warning("No columns defined. Please add columns in Column Manager.")
    else:
        form_data = {}
        for col in columns:
            if col["type"] == "text":
                form_data[col["name"]] = st.text_input(col["name"])
            elif col["type"] == "number":
                form_data[col["name"]] = st.number_input(col["name"], value=0.0)
            elif col["type"] == "date":
                form_data[col["name"]] = st.date_input(col["name"])

        if st.button("Add Item"):
            new_row = {"ID#": len(df) + 1}
            new_row.update(form_data)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_inventory(df)
            st.success("Item added successfully.")

# --- View Inventory ---
if selection == "View Inventory":
    st.title("Inventory Viewer")

    if len(columns) == 0:
        st.info("No columns configured yet.")
    elif df.empty:
        st.warning("Inventory is currently empty")
    else:
        assigned_column_names = [col["name"] for col in columns]
        display_columns = ["ID#"] + assigned_column_names

        # Add Delete button column
        df_display = df.copy()
        df_display["🗑️ Delete"] = "Click"

        st.markdown("### Inventory Table (Click a row's Delete cell to remove it)")
        gb = GridOptionsBuilder.from_dataframe(df_display[display_columns + ["🗑️ Delete"]])
        gb.configure_column("🗑️ Delete", editable=False, cellRenderer="""
            function(params) {
                return `<button style="padding:2px 5px;color:white;background-color:red;border:none;border-radius:4px;cursor:pointer;">🗑️ Delete</button>`;
            }
        """)
        gb.configure_selection("single", use_checkbox=False)
        grid_options = gb.build()

        grid_response = AgGrid(
            df_display[display_columns + ["🗑️ Delete"]],
            gridOptions=grid_options,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            allow_unsafe_jscode=True,
            height=400,
            theme="streamlit"
        )

        # Detect click on delete button
        selected = grid_response["selected_rows"]
        if selected:
            row_id = selected[0]["ID#"]
            df = df[df["ID#"] != row_id].reset_index(drop=True)
            save_inventory(df)
            st.success(f"Item with ID {row_id} deleted successfully.")
            st.rerun()
