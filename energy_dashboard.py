import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os
from datetime import datetime
import time

# ============================================
# CONFIGURATION
# ============================================
LOCAL_DATA_DIR = 'local_data'

# ============================================
# LOAD LOCAL DATA FUNCTIONS
# ============================================
@st.cache_data(ttl=60)
def load_local_observations():
    """Load observations from local CSV"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Observations.csv')
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        # Parse timestamp if needed
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    return pd.DataFrame()

@st.cache_data(ttl=60)
def load_local_summary():
    """Load summary from local CSV"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Summary.csv')
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()

@st.cache_data(ttl=60)
def load_local_anomalies():
    """Load anomalies from local CSV"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Anomalies.csv')
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()

@st.cache_data(ttl=60)
def load_local_insights():
    """Load insights from local CSV"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Insights.csv')
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()

def get_last_sync_time():
    """Get last sync time from file modification"""
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Observations.csv')
    if os.path.exists(csv_path):
        mod_time = os.path.getmtime(csv_path)
        return datetime.fromtimestamp(mod_time)
    return None

# Page config
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
    st.markdown("**Local Mode** - Reading from cached CSV files")
    
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
        observations_df = load_local_observations()
        summary_df = load_local_summary()
        anomalies_df = load_local_anomalies()
        insights_df = load_local_insights()
    
    # Check if we have data
    if observations_df.empty:
        st.warning("⚠️ No local data found. Run sync script first:")
        st.code("python sync_google_sheets_local.py", language="bash")
        st.info("""
        **Setup Instructions:**
        1. Make sure your service account JSON file is in the same folder
        2. Run `python sync_google_sheets_local.py` to download data
        3. Run `python auto_sync.py` for automatic updates
        4. Refresh this dashboard
        """)
        return
    
    # Display metrics
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        peak = observations_df['consumption_kW'].max() if 'consumption_kW' in observations_df else 0
        st.metric("Peak Demand", f"{peak:.1f} kW")
    
    with col2:
        avg = observations_df['consumption_kW'].mean() if 'consumption_kW' in observations_df else 0
        st.metric("Average Demand", f"{avg:.1f} kW")
    
    with col3:
        if not summary_df.empty and 'total_cost' in summary_df.columns:
            cost = summary_df['total_cost'].iloc[-1]
        elif 'consumption_kW' in observations_df and 'tariff' in observations_df:
            cost = (observations_df['consumption_kW'] * observations_df['tariff']).sum()
        else:
            cost = 0
        st.metric("Total Cost", f"${cost:.2f}")
    
    with col4:
        critical = len(observations_df[observations_df['status'] == 'CRITICAL']) if 'status' in observations_df else 0
        st.metric("Critical Alerts", critical)
    
    st.markdown("---")
    
    # Consumption Chart
    st.subheader("📈 Consumption Pattern")
    
    if 'timestamp' in observations_df and 'consumption_kW' in observations_df:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=observations_df['timestamp'],
            y=observations_df['consumption_kW'],
            mode='lines+markers',
            name='Consumption',
            line=dict(color='#667eea', width=2),
            marker=dict(size=6)
        ))
        
        # Highlight critical points
        if 'status' in observations_df:
            critical_points = observations_df[observations_df['status'] == 'CRITICAL']
            if not critical_points.empty:
                fig.add_trace(go.Scatter(
                    x=critical_points['timestamp'],
                    y=critical_points['consumption_kW'],
                    mode='markers',
                    name='Critical Alerts',
                    marker=dict(color='red', size=12, symbol='circle')
                ))
        
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Timestamp or consumption data not available")
    
    st.markdown("---")
    
    # Anomalies and Insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🚨 Anomalies")
        if not anomalies_df.empty:
            for _, row in anomalies_df.iterrows():
                st.warning(f"**{row.get('timestamp', 'Unknown')}**: {row.get('reason', 'No reason')}")
        else:
            st.success("✅ No anomalies detected")
    
    with col2:
        st.subheader("💡 Insights")
        if not insights_df.empty and 'insights' in insights_df.columns:
            insights_text = insights_df['insights'].iloc[-1]
            if insights_text:
                for insight in str(insights_text).split(' | ')[:3]:
                    if insight.strip():
                        st.info(insight.strip())
        else:
            st.info("Run analysis to see insights")
    
    st.markdown("---")
    
    # Recommendations
    st.subheader("📋 Recommendations")
    if not insights_df.empty and 'recommendations' in insights_df.columns:
        recs = insights_df['recommendations'].iloc[-1]
        if recs:
            for i, rec in enumerate(str(recs).split(' | '), 1):
                if rec.strip():
                    st.write(f"{i}. {rec.strip()}")
    else:
        st.info("Run analysis to see recommendations")
    
    st.markdown("---")
    st.caption("⚡ Energy Optimization Agent | Local Mode | Data from CSV files")

if __name__ == "__main__":
    main()