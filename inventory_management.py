import os
import streamlit as st
import pandas as pd
import uuid
import litellm

# Set up LiteLLM with Gemini
litellm.model = "gemini/gemini-1.5-flash"
litellm.api_key = os.getenv("GEMINI_API_KEY") or "your-api-key-here"

def ask_agent_with_data(df):
    if df.empty:
        st.warning("No inventory data to send to the agent.")
        return

    try:
        prompt = (
            "You are an inventory analysis assistant. Given the inventory data in a table, "
            "analyze any interesting patterns, low stock items, or inventory value insights."
        )

        # Prepare table content for prompt
        table_text = "\n".join(
            [
                f"{row['name']} ({row['category']}) - Qty: {row['quantity']} - ${row['price']:.2f}"
                for _, row in df.iterrows()
            ]
        )

        messages = [
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"Here's my inventory data:\n{table_text}"},
        ]

        response = litellm.completion(model=litellm.model, messages=messages)
        reply = response["choices"][0]["message"]["content"]
        st.markdown("### 🤖 Agent Response:")
        st.info(reply)

    except Exception as e:
        st.error(f"Agent error: {str(e)}")
