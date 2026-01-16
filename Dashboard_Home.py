import streamlit as st

st.set_page_config(
    page_title="Locust Performance Dashboard",
    page_icon="🏠",
    layout="wide"
)

import streamlit as st
import pandas as pd
import os

st.title("🏠 Performance Control Center & History")

st.markdown("""
**👈 Use the sidebar to navigate:**
- **Locust Runner**: Run new performance tests.
- **Database Performance**: Monitor live CloudWatch metrics.
""")

st.divider()

st.header("📜 Test Run History")

history_file = "test_history.csv"

if os.path.exists(history_file):
    try:
        history_df = pd.read_csv(history_file)
        
        if not history_df.empty:
            # Display summary metrics
            st.subheader("Key Performance Indicators (Overall)")
            col1, col2, col3, col4 = st.columns(4)
            
            avg_resp = history_df['Avg Response Time'].mean()
            last_resp = history_df['Avg Response Time'].iloc[-1]
            resp_delta = last_resp - avg_resp

            col1.metric("Total Tests Run", len(history_df))
            col2.metric("Avg Response Time", f"{last_resp:.2f} ms", delta=f"{resp_delta:.2f} ms", delta_color="inverse")
            col3.metric("Max Response Time", f"{history_df['Max Response Time'].max():.2f} ms")
            col4.metric("Total Failures", history_df['Total Failures'].sum(), delta=int(history_df['Total Failures'].iloc[-1]), delta_color="inverse")

            # Charts
            st.subheader("Performance Trends Across Runs")
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.caption("Average Response Time over Runs")
                st.line_chart(history_df.set_index("Timestamp")["Avg Response Time"])
                
            with chart_col2:
                st.caption("Requests per Second over Runs")
                st.line_chart(history_df.set_index("Timestamp")["Requests/s"])

            # Clean up Data Table
            
            # 1. Count queries instead of listing string string
            def count_queries(query_str):
                if pd.isna(query_str): return 0
                return len(str(query_str).split(","))

            history_df['Queries'] = history_df['Queries'].apply(count_queries)
            history_df.rename(columns={'Queries': 'Query Count'}, inplace=True)

            # Data Table
            st.subheader("Detailed Logs")
            st.dataframe(history_df.sort_index(ascending=False), use_container_width=True)
            
            # Download button
            csv = history_df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "Download History CSV",
                csv,
                "test_history.csv",
                "text/csv",
                key='download-csv'
            )
        else:
            st.info("History file exists but is empty.")
            
    except Exception as e:
        st.error(f"Error reading history file: {e}")
else:
    st.info("No test history found yet. Run a test in the 'Locust Runner' page to generate data.")
