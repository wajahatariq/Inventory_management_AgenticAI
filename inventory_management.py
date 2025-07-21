import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
from litellm import completion

# ---------------------------
# Session State Initialization
# ---------------------------
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame()

if "columns" not in st.session_state:
    st.session_state.columns = []

df = st.session_state.df
columns = st.session_state.columns

# ---------------------------
# Sidebar Menu
# ---------------------------
with st.sidebar:
    st.title("🧠 Inventory Manager")
    selection = st.radio("Go to", ["Add Column", "Add Inventory", "View Inventory", "Ask Inventory Agent"])
    
    # Delete Column Logic
    if len(columns) > 0:
        if st.button("🗑️ Delete Last Column"):
            deleted = columns.pop()
            if deleted["name"] in df.columns:
                df.drop(columns=[deleted["name"]], inplace=True)
            st.success(f"Deleted column: {deleted['name']}")

# ---------------------------
# Add Column
# ---------------------------
if selection == "Add Column":
    st.header("Add New Column to Inventory")
    new_col = st.text_input("Enter new column name")
    new_type = st.selectbox("Select column type", ["text", "number", "date"])
    if st.button("Add Column"):
        if new_col and new_col not in [col["name"] for col in columns]:
            columns.append({"name": new_col, "type": new_type})
            st.success(f"Column '{new_col}' added!")
        else:
            st.warning("Enter unique column name.")

# ---------------------------
# Add Inventory
# ---------------------------
if selection == "Add Inventory":
    st.header("Add Inventory Item")

    if len(columns) == 0:
        st.warning("Add columns first from the sidebar.")
    else:
        item = {}
        item["ID#"] = len(df) + 1
        for col in columns:
            label = col["name"]
            if col["type"] == "text":
                item[label] = st.text_input(label)
            elif col["type"] == "number":
                item[label] = st.number_input(label)
            elif col["type"] == "date":
                item[label] = st.date_input(label)
        if st.button("Add Item"):
            df.loc[len(df)] = item
            st.success("Item added successfully!")

# ---------------------------
# View Inventory (AgGrid)
# ---------------------------
if selection == "View Inventory":
    st.title("📦 Inventory Viewer")

    if len(columns) == 0:
        st.info("No columns configured yet.")
    else:
        assigned_column_names = [col["name"] for col in columns]
        display_columns = ["ID#"] + assigned_column_names

        if not df.empty:
            st.markdown("### Inventory Table")

            # Setup AgGrid
            gb = GridOptionsBuilder.from_dataframe(df[display_columns])
            gb.configure_default_column(editable=False, groupable=True)
            gb.configure_selection(selection_mode="single", use_checkbox=True)
            grid_options = gb.build()

            grid_response = AgGrid(
                df[display_columns],
                gridOptions=grid_options,
                update_mode=GridUpdateMode.SELECTION_CHANGED,
                enable_enterprise_modules=False,
                height=400,
                fit_columns_on_grid_load=True
            )

            selected_rows = grid_response["selected_rows"]
            if selected_rows:
                selected_index = selected_rows[0]["_selectedRowNodeInfo"]["nodeRowIndex"]
                if st.button("Delete Selected Row"):
                    df.drop(index=selected_index, inplace=True)
                    df.reset_index(drop=True, inplace=True)
                    st.success("Row deleted.")
        else:
            st.warning("Inventory is currently empty.")

# ---------------------------
# Ask Inventory Agent (Groq)
# ---------------------------
if selection == "Ask Inventory Agent":
    st.header("🤖 Ask Inventory Agent")
    user_question = st.text_input("What do you want to know about the inventory?")
    if st.button("Ask"):
        try:
            system_prompt = f"You are an inventory management assistant. The current inventory columns are: {', '.join([col['name'] for col in columns])}."
            user_prompt = f"User Question: {user_question}"
            response = completion(
                model="groq/llama3-8b-8192",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            st.write("**Answer:**", response['choices'][0]['message']['content'])
        except Exception as e:
            st.error(f"Error querying Groq AI: {e}")
