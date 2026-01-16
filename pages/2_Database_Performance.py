import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from utils import get_aws_client

# --- CloudWatch Metric Functions ---

def get_rds_metrics(instance_id):
    """Fetches key RDS metrics from CloudWatch."""
    client = get_aws_client('cloudwatch')
    
    end_time = datetime.utcnow()
    # Expand start_time to 60 minutes to ensure we capture the simulated data
    start_time = end_time - timedelta(minutes=60)
    
    # Define metrics to fetch
    metrics = [
        ('CPUUtilization', 'Percent'),
        ('DatabaseConnections', 'Count'),
        ('FreeStorageSpace', 'Bytes'),
        ('ReadIOPS', 'Count/Second'),
        ('WriteIOPS', 'Count/Second')
    ]
    
    queries = []
    for i, (metric_name, unit) in enumerate(metrics):
        queries.append({
            'Id': f'm{i}',
            'MetricStat': {
                'Metric': {
                    'Namespace': 'AWS/RDS',
                    'MetricName': metric_name,
                    'Dimensions': [{'Name': 'DBInstanceIdentifier', 'Value': instance_id}]
                },
                'Period': 60,
                'Stat': 'Average',
                'Unit': unit
            },
            'ReturnData': True
        })

    try:
        response = client.get_metric_data(
            MetricDataQueries=queries,
            StartTime=start_time,
            EndTime=end_time,
            ScanBy='TimestampAscending'
        )
        
        # Process results into a DataFrame
        data = {}
        all_timestamps = set()
        
        # First pass: collect all timestamps to create a master index
        for results in response['MetricDataResults']:
            for ts in results['Timestamps']:
                all_timestamps.add(ts)
        
        if not all_timestamps:
            return pd.DataFrame()
            
        sorted_timestamps = sorted(list(all_timestamps))
        df = pd.DataFrame(index=sorted_timestamps)
        df.index.name = 'Time'
        
        # Second pass: map values to timestamps
        for i, (metric_name, _) in enumerate(metrics):
            results = response['MetricDataResults'][i]
            metric_vals = pd.Series(results['Values'], index=results['Timestamps'])
            df[metric_name] = metric_vals
            
        return df.fillna(0) # Fill missing points with 0
        
    except Exception as e:
        st.error(f"Error fetching CloudWatch metrics: {e}")
        return pd.DataFrame()

# --- CloudWatch Logs Functions ---

def get_rds_logs(instance_id, log_type='error'):
    """Queries RDS logs using CloudWatch Logs Insights."""
    client = get_aws_client('logs')
    log_group = f"/aws/rds/instance/{instance_id}/{log_type}"
    
    # This might fail in LocalStack if the log group doesn't exist,
    # so we'll wrap it in a try-except.
    try:
        query = "fields @timestamp, @message | sort @timestamp desc | limit 20"
        
        start_query_response = client.start_query(
            logGroupName=log_group,
            startTime=int((datetime.utcnow() - timedelta(hours=24)).timestamp()),
            endTime=int(datetime.utcnow().timestamp()),
            queryString=query,
        )
        
        query_id = start_query_response['queryId']
        
        # Simple polling for results
        response = None
        for _ in range(5):
            response = client.get_query_results(queryId=query_id)
            if response['status'] == 'Complete':
                break
            time.sleep(1)
            
        if response and 'results' in response:
            logs = []
            for row in response['results']:
                entry = {item['field']: item['value'] for item in row}
                logs.append(entry)
            return pd.DataFrame(logs)
        return pd.DataFrame()
        
    except Exception as e:
        # Silently fail or show info if group doesn't exist (common in local simulation)
        return pd.DataFrame(columns=['@timestamp', '@message'])

def main():
    st.set_page_config(layout="wide")
    st.title("📊 AWS RDS Performance Dashboard")

    instance_id = os.environ.get("DB_INSTANCE_IDENTIFIER", "locust-rds-instance")
    
    st.info(f"Monitoring RDS Instance: **{instance_id}**")

    # --- Metrics Section ---
    st.header("CloudWatch Metrics (Last 60 Minutes)")
    
    # Auto-refresh logic
    if "auto_refresh" not in st.session_state:
        st.session_state.auto_refresh = True
    
    st.sidebar.divider()
    st.session_state.auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=st.session_state.auto_refresh)
    
    metrics_df = get_rds_metrics(instance_id)
    
    if not metrics_df.empty:
        # Summary metrics
        m1, m2, m3, m4 = st.columns(4)
        latest = metrics_df.iloc[-1]
        m1.metric("CPU Utilization", f"{latest['CPUUtilization']:.1f}%")
        m2.metric("Connections", int(latest['DatabaseConnections']))
        m3.metric("Read IOPS", f"{latest['ReadIOPS']:.1f}")
        m4.metric("Write IOPS", f"{latest['WriteIOPS']:.1f}")

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("CPU Utilization (%)")
            st.line_chart(metrics_df['CPUUtilization'])
            
            st.subheader("Database Connections")
            st.line_chart(metrics_df['DatabaseConnections'])
            
        with col2:
            st.subheader("IOPS (Read/Write)")
            st.line_chart(metrics_df[['ReadIOPS', 'WriteIOPS']])
            
            st.subheader("Free Storage Space (GB)")
            metrics_df['FreeStorage_GB'] = metrics_df['FreeStorageSpace'] / (1024**3)
            st.line_chart(metrics_df['FreeStorage_GB'])
    else:
        st.warning("No metrics found in CloudWatch. Ensure the RDS instance is active and reporting.")

    if st.session_state.auto_refresh:
        time.sleep(30)
        st.rerun()

    # --- Logs Section ---
    st.divider()
    st.header("RDS Logs Analysis (CloudWatch Logs Insights)")
    
    log_type = st.selectbox("Select Log Group", ["error", "slowquery", "general"])
    
    if st.button("Query Logs"):
        logs_df = get_rds_logs(instance_id, log_type)
        if not logs_df.empty:
            st.dataframe(logs_df, use_container_width=True)
        else:
            st.info(f"No logs found for log group: /aws/rds/instance/{instance_id}/{log_type}")

    if st.button("Refresh Dashboard"):
        st.rerun()

if __name__ == "__main__":
    main()
