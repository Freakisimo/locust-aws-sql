import streamlit as st
import pandas as pd
import os
import subprocess
import time
import requests
import psycopg2
from utils import get_secret

import csv
from datetime import datetime

def save_test_history(queries, num_users, spawn_rate, run_time):
    """Parses the generated stats_stats.csv and appends a summary to test_history.csv."""
    history_file = "test_history.csv"
    stats_file = "stats_stats.csv"

    if not os.path.exists(stats_file):
        return

    try:
        df = pd.read_csv(stats_file)
        if df.empty:
            return

        # Get the 'Aggregated' row (usually the last one or explicitly named)
        agg_row = df[df["Name"] == "Aggregated"]
        
        if not agg_row.empty:
            agg_data = agg_row.iloc[0]
            
            new_record = {
                "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Queries": queries,
                "Users": num_users,
                "Spawn Rate": spawn_rate,
                "Run Time": run_time,
                "Total Requests": agg_data.get("Request Count", 0),
                "Total Failures": agg_data.get("Failure Count", 0),
                "Avg Response Time": round(agg_data.get("Average Response Time", 0), 2),
                "Max Response Time": agg_data.get("Max Response Time", 0),
                "Requests/s": round(agg_data.get("Requests/s", 0), 2)
            }

            file_exists = os.path.exists(history_file)
            
            with open(history_file, mode='a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=new_record.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(new_record)
                
    except Exception as e:
        st.error(f"Error saving test history: {e}")

def parse_run_time(time_str):
    """Parses time string (e.g. '1h', '30m', '10s') to seconds."""
    try:
        total_seconds = 0
        current_val = ""
        for char in time_str.lower():
            if char.isdigit():
                current_val += char
            elif char == 'h':
                total_seconds += int(current_val) * 3600
                current_val = ""
            elif char == 'm':
                total_seconds += int(current_val) * 60
                current_val = ""
            elif char == 's':
                total_seconds += int(current_val)
                current_val = ""
        if current_val: # If no suffix, assume seconds
            total_seconds += int(current_val)
        return total_seconds
    except:
        return 0

def send_process(selected_queries, num_users, spawn_rate, run_time):
    st.session_state.test_running = True
    
    # Calculate duration for timer
    duration_seconds = parse_run_time(run_time)
    st.session_state.start_time = time.time()
    st.session_state.run_duration = duration_seconds
    
    # Store config for history saving
    st.session_state.last_config = {
        "queries": ",".join(selected_queries), 
        "num_users": num_users, 
        "spawn_rate": spawn_rate, 
        "run_time": run_time
    }
    env = os.environ.copy()

    if not selected_queries:
        st.sidebar.warning("No queries selected. Please select at least one query.")
        st.session_state.test_running = False # Reset state
        return

    env["QUERIES_TO_RUN"] = ",".join(selected_queries)

    locust_command = [
        "locust",
        "-f", "locustfile.py",
        "--headless",
        "-u", str(num_users),
        "-r", str(spawn_rate),
        "--run-time", run_time,
        "--csv", "stats",
    ]

    # Use files for logs to avoid PIPE buffer deadlock
    stdout_file = open("locust_stdout.log", "w")
    stderr_file = open("locust_stderr.log", "w")
    
    st.session_state.locust_process = subprocess.Popen(
        locust_command, 
        env=env,
        stdout=stdout_file,
        stderr=stderr_file,
        text=True
    )
    # Store file handles in session state to close them later (or rely on OS closing on termination, but explicit is better)
    # Actually, we can close them in the main process right after Popen if we don't need to write to them. 
    # But Popen needs them open. Wait, Popen accepts file descriptors. 
    # Python Popen with file objects: "If you pass a file object... Popen uses the file descriptor... and the file object remains open"
    # We should let Popen manage inheritance but we need to ensure they stay open? 
    # Actually, once Popen is created, we can close the python file objects if we passed descriptors?
    # Safer to just keep paths and read later. Let's just pass the open files.
    # We don't need to keep the file objects in session state for reading, we can read the files from disk later.
    # But we might need to close them in this process?
    # Popen docs: "If file objects are passed... they are kept open".
    # We should close them after Popen returns if we don't need to write to them from parent.
    # "If you wish to capture output... use PIPE... Be careful... deadlock"
    # To avoid deadlock use files.
    
    # We will close the python handles immediately; Popen has its own handles now (via dup2 usually) or we can leave them for GC.
    # Actually, safe practice:
    # st.session_state.log_files = (stdout_file, stderr_file) 
    # But files are not picklable for session state?
    # Simple approach: Open, Popen, Close in Python (Popen keeps its own fd if valid). 
    # Wait, if we close in Python, does output stop?
    # No, Popen uses the OS file descriptor.
    pass # valid python indentation placeholder
    st.sidebar.success("Locust test started!")
    st.rerun()


def stop_process():
    if st.session_state.locust_process is not None:
        st.session_state.locust_process.terminate()
        # Wait for termination
        st.session_state.locust_process.wait()
        
        # Read logs from files
        try:
            with open("locust_stdout.log", "r") as f:
                st.session_state.locust_stdout = f.read()
            with open("locust_stderr.log", "r") as f:
                st.session_state.locust_stderr = f.read()
        except Exception as e:
            st.session_state.locust_stderr = f"Error reading logs: {e}"
            
        st.session_state.locust_process = None
        st.session_state.test_running = False
        
        # Save history on stop
        if 'last_config' in st.session_state:
            save_test_history(**st.session_state.last_config)
            
        st.sidebar.success("Locust test stopped.")
        st.rerun()
    else:
        st.sidebar.warning("No test is currently running.")


def get_stats():
    # Try to load and display results
    stats_files_exist = os.path.exists("stats_stats.csv") and os.path.exists("stats_stats_history.csv")

    if stats_files_exist:
        try:
            stats_df = pd.read_csv("stats_stats.csv")
            stats_history_df = pd.read_csv("stats_stats_history.csv")
            
            st.subheader("Current Statistics")
            st.dataframe(stats_df)
            
            if not stats_history_df.empty:
                st.subheader("Test Statistics History")

                # --- FINAL DEBUG: Show unique values in the 'Name' column ---
                with st.expander("Debug: Unique values in 'Name' column"):
                    st.write(stats_history_df["Name"].unique())

                # Locust's history CSV logs stats for each endpoint AND an aggregated total.
                # We only want to plot the aggregated total for these charts.
                agg_df = stats_history_df[stats_history_df["Name"].str.strip() == "Aggregated"]

                # Requests and Failures chart
                if "Requests/s" in agg_df.columns and "Failures/s" in agg_df.columns:
                    st.line_chart(agg_df, x="Timestamp", y=["Requests/s", "Failures/s"], use_container_width=True)
                
                # Response Time chart
                if "Total Average Response Time" in agg_df.columns:
                    st.line_chart(agg_df, x="Timestamp", y=["Total Average Response Time"], use_container_width=True)
                
                # Users chart
                if "User Count" in agg_df.columns:
                    st.line_chart(agg_df, x="Timestamp", y=["User Count"], use_container_width=True)

            else:
                st.info("Waiting for test data to populate...")
                
        except Exception as e:
            st.error(f"Error loading test results: {e}")
    else:
        if st.session_state.test_running:
            st.info("⏳ Test is running... Results will appear here shortly.")
        else:
            st.info("📊 Run a Locust test to generate a report.")    


def main():
    # Set main page 
    st.set_page_config(layout="wide")
    st.title("Locust Performance Control Center")

    # Initialize session state
    if 'locust_process' not in st.session_state:
        st.session_state.locust_process = None
    if 'test_running' not in st.session_state:
        st.session_state.test_running = False
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
        

    # Auto-refresh every 5 seconds when test is running and check if finished
    if st.session_state.test_running:
        # Display timer
        if 'start_time' in st.session_state and 'run_duration' in st.session_state:
            elapsed = time.time() - st.session_state.start_time
            remaining = max(0, st.session_state.run_duration - elapsed)
            mins, secs = divmod(int(remaining), 60)
            
            # Use a container for the status to take full width roughly (metric takes full width of column)
            st.sidebar.divider()
            st.sidebar.info("🔄 Test is Running")
            st.sidebar.metric("Time Remaining", f"{mins:02d}:{secs:02d}")
            
            # Use a progress bar
            progress = min(1.0, elapsed / st.session_state.run_duration) if st.session_state.run_duration > 0 else 0
            st.sidebar.progress(progress)
            
        if st.session_state.locust_process is not None:
            if st.session_state.locust_process.poll() is not None:
                # Process has finished automatically
                
                # We don't need communicate() since we have files, just ensure it's done
                st.session_state.locust_process.wait() 

                try:
                    with open("locust_stdout.log", "r") as f:
                        st.session_state.locust_stdout = f.read()
                    with open("locust_stderr.log", "r") as f:
                        st.session_state.locust_stderr = f.read()
                except Exception as e:
                    st.session_state.locust_stderr = f"Error reading logs: {e}"

                st.session_state.locust_process = None
                st.session_state.test_running = False
                
                # Save history on auto-finish
                if 'last_config' in st.session_state:
                    save_test_history(**st.session_state.last_config)
                    
                st.rerun()
        
        time.sleep(5)  # Small delay to prevent too rapid refreshes
        st.rerun()

    # --- Sidebar for Test Configuration ---
    st.sidebar.header("Test Configuration")

    # Query selection
    queries_path = "queries"
    if os.path.exists(queries_path):
        sql_files = [f for f in os.listdir(queries_path) if f.endswith('.sql')]
        selected_queries = st.sidebar.multiselect(
            "Select Queries to Run", 
            sql_files, 
            default=sql_files,
            disabled=st.session_state.test_running
        )
    else:
        st.sidebar.warning(f'Directory "{queries_path}" not found.')
        selected_queries = []

    # Locust parameters
    num_users = st.sidebar.slider(
        "Number of Users", 
        1, 50, 10,
        disabled=st.session_state.test_running
    )
    spawn_rate = st.sidebar.slider(
        "Spawn Rate", 
        1, 50, 10,
        disabled=st.session_state.test_running
    )
    run_time = st.sidebar.text_input(
        "Run Time (e.g., 1m, 2h)", 
        "1m",
        disabled=st.session_state.test_running
    )

    # Start and Stop buttons side-by-side
    b_col1, b_col2 = st.sidebar.columns(2)
    
    with b_col1:
        st.button(
            "Start Test", 
            on_click=send_process, 
            args=(selected_queries, num_users, spawn_rate, run_time),
            disabled=st.session_state.test_running,
            use_container_width=True
        )
    
    with b_col2:
        st.button(
            "Stop Test", 
            on_click=stop_process, 
            disabled=not st.session_state.test_running,
            use_container_width=True
        )


    # Display test status
    if not st.session_state.test_running: # Only show these messages if NOT running (running status handles above)
        if st.session_state.locust_process is None and os.path.exists("stats_stats.csv"):
            st.success("✅ Test completed! Results are displayed below.")

    # --- Locust Test Results Display ---
    st.header("Locust Test Results")
    get_stats()
if __name__ == "__main__":
    main()