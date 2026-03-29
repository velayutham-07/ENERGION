import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import json
from datetime import datetime
import time

# ============================================
# CONFIGURATION
# ============================================
LOCAL_DATA_DIR = 'local_data'

# ============================================
# HELPER FUNCTIONS
# ============================================
def parse_json_cell(cell_value):
    """Parse JSON from a single cell value"""
    if not cell_value or pd.isna(cell_value):
        return []
    
    # If it's already a list/dict
    if isinstance(cell_value, (list, dict)):
        return cell_value if isinstance(cell_value, list) else [cell_value]
    
    # If it's a string, try to parse as JSON
    if isinstance(cell_value, str):
        try:
            parsed = json.loads(cell_value)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            return []
    
    return []

def load_csv_with_json_arrays(csv_path):
    """
    Load CSV where each row's first column contains a JSON array.
    Returns a DataFrame with all parsed observations and run information.
    """
    if not os.path.exists(csv_path):
        return pd.DataFrame(), []
    
    # Read CSV without parsing JSON
    df_raw = pd.read_csv(csv_path)
    
    if df_raw.empty:
        return pd.DataFrame(), []
    
    # Assume the JSON data is in the first column
    first_col = df_raw.columns[0]
    
    all_parsed_data = []
    run_ids = []
    
    for idx, row in df_raw.iterrows():
        cell_value = row[first_col]
        parsed = parse_json_cell(cell_value)
        
        if parsed:
            run_id = idx + 2  # Row number (row 1 = header, row 2 = first run)
            for item in parsed:
                if isinstance(item, dict):
                    item['run_id'] = run_id
                    item['run_number'] = idx + 1
                    # Convert timestamp if exists
                    if 'timestamp' in item:
                        try:
                            item['timestamp'] = pd.to_datetime(item['timestamp'])
                        except:
                            pass
            all_parsed_data.extend(parsed)
            run_ids.append(run_id)
    
    return pd.DataFrame(all_parsed_data), run_ids

def load_observations():
    """Load observations from local CSV (JSON array format)"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Observations.csv')
    return load_csv_with_json_arrays(csv_path)

def load_summary():
    """Load summary from local CSV (JSON array format)"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Summary.csv')
    df, runs = load_csv_with_json_arrays(csv_path)
    return df, runs

def load_anomalies():
    """Load anomalies from local CSV (JSON array format)"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Anomalies.csv')
    df, runs = load_csv_with_json_arrays(csv_path)
    return df, runs

def load_insights():
    """Load insights from local CSV (JSON array format)"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Insights.csv')
    df, runs = load_csv_with_json_arrays(csv_path)
    return df, runs

def get_last_sync_time():
    """Get last sync time from file modification"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Observations.csv')
    if os.path.exists(csv_path):
        mod_time = os.path.getmtime(csv_path)
        return datetime.fromtimestamp(mod_time)
    return None

def get_run_summary(observations_df):
    """Get summary of available runs"""
    if observations_df.empty or 'run_number' not in observations_df.columns:
        return []
    
    runs = observations_df.groupby('run_number').agg({
        'timestamp': ['min', 'max', 'count'],
        'consumption_kW': ['mean', 'max']
    }).reset_index()
    
    runs.columns = ['run_number', 'start_time', 'end_time', 'num_obs', 'avg_kW', 'peak_kW']
    
    # Format time columns
    if 'start_time' in runs.columns:
        runs['start_time'] = pd.to_datetime(runs['start_time']).dt.strftime('%H:%M')
        runs['end_time'] = pd.to_datetime(runs['end_time']).dt.strftime('%H:%M')
    
    return runs.to_dict('records')

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Energy Dashboard (Local)",
    page_icon="⚡",
    layout="wide"
)

# ============================================
# MAIN DASHBOARD
# ============================================
def main():
    st.title("⚡ Energy Optimization Dashboard")
    st.markdown("**Local Mode** - Reading from CSV files with JSON arrays in Column A")
    
    # Show last sync time
    last_sync = get_last_sync_time()
    if last_sync:
        st.caption(f"Data synced: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Sidebar
    with st.sidebar:
        st.image("https://img.icons8.com/fluency/96/energy.png", width=80)
        st.markdown("## ⚡ Energy Dashboard")
        st.markdown("---")
        
        auto_refresh = st.checkbox("Auto-refresh (30 sec)", value=False)
        
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### Data Source")
        st.info(f"📁 Local CSV files\n`{LOCAL_DATA_DIR}/`")
        
        # Show file status
        files = ['Observations.csv', 'Summary.csv', 'Anomalies.csv', 'Insights.csv']
        for f in files:
            path = os.path.join(LOCAL_DATA_DIR, f)
            if os.path.exists(path):
                size = os.path.getsize(path)
                st.markdown(f"✅ {f} ({size:,} bytes)")
            else:
                st.markdown(f"❌ {f} - Not found")
        
        st.markdown("---")
        st.markdown(f"**Last Updated:** {datetime.now().strftime('%H:%M:%S')}")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Load data
    with st.spinner("Loading local data..."):
        observations_df, obs_runs = load_observations()
        summary_df, sum_runs = load_summary()
        anomalies_df, anom_runs = load_anomalies()
        insights_df, ins_runs = load_insights()
    
    # Check if we have data
    if observations_df.empty:
        st.warning("⚠️ No local data found. Run sync script first:")
        st.code("python sync_google_sheets_local.py", language="bash")
        st.info("""
        **Expected CSV Format:**
        - Each CSV has one column with JSON arrays
        - Row 1: Header
        - Row 2, 3, 4...: Each cell contains a JSON array of observations
        """)
        return
    
    # Get available runs
    available_runs = sorted(observations_df['run_number'].unique()) if 'run_number' in observations_df else []
    
    # Run selector in sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown("### Select Run")
        
        if available_runs:
            selected_run = st.selectbox(
                "Analysis Run",
                options=available_runs,
                index=len(available_runs) - 1,
                format_func=lambda x: f"Run {x}"
            )
        else:
            selected_run = None
    
    # Filter by selected run
    if selected_run and 'run_number' in observations_df.columns:
        current_observations = observations_df[observations_df['run_number'] == selected_run]
        current_anomalies = anomalies_df[anomalies_df['run_number'] == selected_run] if 'run_number' in anomalies_df else pd.DataFrame()
        current_insights = insights_df[insights_df['run_number'] == selected_run] if 'run_number' in insights_df else pd.DataFrame()
        current_summary = summary_df[summary_df['run_number'] == selected_run] if 'run_number' in summary_df else pd.DataFrame()
    else:
        # Use latest run
        if 'run_number' in observations_df.columns:
            latest_run = observations_df['run_number'].max()
            current_observations = observations_df[observations_df['run_number'] == latest_run]
            current_anomalies = anomalies_df[anomalies_df['run_number'] == latest_run] if 'run_number' in anomalies_df else pd.DataFrame()
            current_insights = insights_df[insights_df['run_number'] == latest_run] if 'run_number' in insights_df else pd.DataFrame()
            current_summary = summary_df[summary_df['run_number'] == latest_run] if 'run_number' in summary_df else pd.DataFrame()
        else:
            current_observations = observations_df
            current_anomalies = anomalies_df
            current_insights = insights_df
            current_summary = summary_df
    
    # Display run info
    if available_runs:
        st.info(f"📊 Showing **Run {selected_run if selected_run else latest_run}** | Total runs available: {len(available_runs)}")
    
    # Display metrics
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        peak = current_observations['consumption_kW'].max() if not current_observations.empty else 0
        st.metric("Peak Demand", f"{peak:.1f} kW")
    
    with col2:
        avg = current_observations['consumption_kW'].mean() if not current_observations.empty else 0
        st.metric("Average Demand", f"{avg:.1f} kW")
    
    with col3:
        if not current_summary.empty and 'total_cost' in current_summary.columns:
            cost = current_summary['total_cost'].iloc[-1]
        elif not current_observations.empty and 'tariff' in current_observations.columns:
            cost = (current_observations['consumption_kW'] * current_observations['tariff']).sum()
        else:
            cost = 0
        st.metric("Total Cost", f"${cost:.2f}")
    
    with col4:
        critical = len(current_observations[current_observations['status'] == 'CRITICAL']) if 'status' in current_observations.columns else 0
        st.metric("Critical Alerts", critical)
    
    st.markdown("---")
    
    # Consumption Chart
    st.subheader("📈 Consumption Pattern")
    
    if 'timestamp' in current_observations.columns and 'consumption_kW' in current_observations.columns:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=current_observations['timestamp'],
            y=current_observations['consumption_kW'],
            mode='lines+markers',
            name='Consumption',
            line=dict(color='#667eea', width=2),
            marker=dict(size=6)
        ))
        
        # Highlight critical points
        if 'status' in current_observations.columns:
            critical_points = current_observations[current_observations['status'] == 'CRITICAL']
            if not critical_points.empty:
                fig.add_trace(go.Scatter(
                    x=critical_points['timestamp'],
                    y=critical_points['consumption_kW'],
                    mode='markers',
                    name='Critical Alerts',
                    marker=dict(color='red', size=12, symbol='circle')
                ))
        
        fig.update_layout(
            title="Electricity Consumption Over Time",
            xaxis_title="Time",
            yaxis_title="Consumption (kW)",
            height=500,
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Timestamp or consumption data not available")
    
    st.markdown("---")
    
    # Anomalies and Insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚨 Anomalies")
        if not current_anomalies.empty:
            for _, row in current_anomalies.iterrows():
                st.warning(f"**{row.get('timestamp', 'Unknown')}**: {row.get('reason', 'No reason')}")
        else:
            st.success("✅ No anomalies detected")
    
    with col2:
        st.subheader("💡 Insights")
        if not current_insights.empty and 'insights' in current_insights.columns:
            insights_text = current_insights['insights'].iloc[-1]
            if insights_text:
                for insight in str(insights_text).split(' | ')[:3]:
                    if insight.strip():
                        st.info(insight.strip())
        else:
            st.info("Run analysis to see insights")
    
    st.markdown("---")
    
    # Recommendations
    st.subheader("📋 Recommendations")
    if not current_insights.empty and 'recommendations' in current_insights.columns:
        recs = current_insights['recommendations'].iloc[-1]
        if recs:
            for i, rec in enumerate(str(recs).split(' | '), 1):
                if rec.strip():
                    st.write(f"{i}. {rec.strip()}")
    else:
        st.info("Run analysis to see recommendations")
    
    st.markdown("---")
    
    # Selected Strategy
    if not current_insights.empty:
        if 'selected_strategy' in current_insights.columns:
            strategy = current_insights['selected_strategy'].iloc[-1]
            savings = current_insights['expected_savings'].iloc[-1] if 'expected_savings' in current_insights.columns else 0
            if strategy and strategy != 'None':
                st.subheader("🎯 Selected Optimization Strategy")
                st.success(f"**{strategy}** - Expected Savings: ${savings}")
    
    # Historical Runs Summary (if multiple runs)
    if len(available_runs) > 1 and 'run_number' in observations_df.columns:
        st.markdown("---")
        st.subheader("📊 Historical Performance Across Runs")
        
        # Aggregate by run
        historical = observations_df.groupby('run_number').agg({
            'consumption_kW': ['mean', 'max']
        }).reset_index()
        historical.columns = ['run_number', 'avg_consumption', 'peak_consumption']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=historical['run_number'],
            y=historical['peak_consumption'],
            mode='lines+markers',
            name='Peak Consumption',
            line=dict(color='#ff6b6b', width=2),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=historical['run_number'],
            y=historical['avg_consumption'],
            mode='lines+markers',
            name='Average Consumption',
            line=dict(color='#667eea', width=2),
            marker=dict(size=8)
        ))
        
        fig.update_layout(
            title="Peak vs Average Consumption Across Analysis Runs",
            xaxis_title="Run Number",
            yaxis_title="Consumption (kW)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.caption("⚡ Energy Optimization Agent | Local Mode | JSON arrays in Column A | Each row = One workflow run")

if __name__ == "__main__":
    main()