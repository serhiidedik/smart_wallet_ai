import streamlit as st
import httpx
import pandas as pd

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="SmartWallet AI", page_icon="💳")
st.title("💳 SmartWallet AI")

# --- Session State Management ---
# We need to store the draft data between clicks
if 'draft_data' not in st.session_state:
    st.session_state['draft_data'] = None

# --- Sidebar: Input ---
st.sidebar.header("New Expense Input")
tab1, tab2 = st.sidebar.tabs(["📝 Text", "📸 Receipt"])

# 1. Text Logic
with tab1:
    with st.form("text_form"):
        text_input = st.text_area("Description")
        if st.form_submit_button("Analyze Text"):
            with st.spinner("AI is thinking..."):
                try:
                    resp = httpx.post(f"{API_URL}/analyze/text", json={"text": text_input},
                                      timeout=60.0)
                    if resp.status_code == 200:
                        st.session_state['draft_data'] = resp.json()  # Save draft
                        st.success("Analysis complete! Review below.")
                    else:
                        st.error(f"Error: {resp.text}")
                except Exception as e:
                    st.error(f"Connection failed: {e}")

# 2. Image Logic
with tab2:
    uploaded_file = st.file_uploader("Upload Receipt", type=["jpg", "png", "jpeg"])
    if uploaded_file and st.button("Analyze Receipt"):
        with st.spinner("Scanning receipt..."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                resp = httpx.post(f"{API_URL}/analyze/image", files=files, timeout=120.0)
                if resp.status_code == 200:
                    st.session_state['draft_data'] = resp.json()  # Save draft
                    st.success("Scan complete! Review below.")
                else:
                    st.error(f"Error: {resp.text}")
            except Exception as e:
                st.error(f"Connection failed: {e}")

# --- Main Area: Human-in-the-Loop Review ---

if st.session_state['draft_data']:
    st.divider()
    st.subheader("🧐 Review & Edit")

    draft = st.session_state['draft_data']

    # Edit Form
    with st.form("edit_and_save"):
        col1, col2 = st.columns(2)

        # Pre-fill fields with AI data
        amount = col1.number_input("Amount", value=float(draft.get('amount', 0.0)))
        currency = col2.text_input("Currency", value=draft.get('currency', 'UAH'))

        merchant = st.text_input("Merchant", value=draft.get('merchant') or "")

        # Category Select
        categories = ["food", "transport", "shopping", "entertainment", "bills", "other"]
        current_cat = draft.get('category', 'other')
        cat_index = categories.index(current_cat) if current_cat in categories else 5

        category = st.selectbox("Category", categories, index=cat_index)
        description = st.text_area("Description", value=draft.get('description') or "")

        # Final Save Button
        if st.form_submit_button("💾 Confirm & Save to Database"):
            # Prepare final payload
            final_data = {
                "amount": amount,
                "currency": currency,
                "category": category,
                "merchant": merchant,
                "description": description
            }

            try:
                # Send to SAVE endpoint
                resp = httpx.post(f"{API_URL}/transactions/", json=final_data)
                if resp.status_code == 200:
                    st.success("✅ Saved successfully!")
                    st.session_state['draft_data'] = None  # Clear draft
                    st.rerun()  # Refresh page to show new history
                else:
                    st.error(f"Save failed: {resp.text}")
            except Exception as e:
                st.error(f"Connection error: {e}")

st.divider()
st.subheader("🧠 AI Analyst (Chat with Data)")

question = st.text_input("Ask a question about your finances",
                         placeholder="Сколько я потратил на еду? / Show top 3 expensive items")

# --- Ask ---
if st.button("Ask AI"):
    with st.spinner("Generating SQL..."):
        try:
            resp = httpx.post(f"{API_URL}/analytics/ask", json={"question": question}, timeout=30.0)

            if resp.status_code == 200:
                data = resp.json()

                st.info(f"Generated SQL: `{data['sql']}`")  # Показываем SQL для отладки

                results = data['result']
                if results:
                    st.dataframe(results)
                    # Если результат - это агрегация (например, сумма), покажем крупно
                    if len(results) == 1 and len(results[0]) == 1:
                        key = list(results[0].keys())[0]
                        st.metric(label="Result", value=results[0][key])
                else:
                    st.warning("No data found for this query.")
            else:
                st.error(f"Error: {resp.text}")

        except Exception as e:
            st.error(f"Connection error: {e}")

# --- History ---
st.divider()
st.subheader("📚 History")
try:
    resp = httpx.get(f"{API_URL}/transactions/")
    if resp.status_code == 200:
        transactions = resp.json()
        if transactions:
            df = pd.DataFrame(transactions)
            st.dataframe(
                df[['id', 'created_at', 'category', 'amount', 'currency', 'merchant',
                    'description']],
                use_container_width=True
            )
        else:
            st.info("Database is empty.")
except:
    st.warning("Backend is offline.")