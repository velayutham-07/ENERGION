import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import os
import json
import time
import threading
from datetime import datetime
import subprocess

# ============================================
# CONFIGURATION
# ============================================
WEBHOOK_URL = "https://api.agents.snsihub.ai/webhook/3849c989-1879-4f71-a86e-f1baedc2f6b4"
LOCAL_DATA_DIR = 'local_data'

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="ENERGION",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    }
    
    .main-header {
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        text-align: center;
        color: #a0aec0;
        margin-bottom: 2rem;
    }
    
    .trigger-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        font-size: 1.2rem;
        font-weight: 600;
        border-radius: 50px;
        cursor: pointer;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .trigger-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.15) 100%);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1.2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: white;
    }
    
    .alert-critical {
        background: linear-gradient(135deg, rgba(255, 71, 71, 0.15) 0%, rgba(255, 107, 107, 0.1) 100%);
        border-left: 4px solid #ff4747;
        border-radius: 12px;
        padding: 0.8rem;
        margin: 0.5rem 0;
    }
    
    .insight-card {
        background: linear-gradient(135deg, rgba(72, 187, 120, 0.1) 0%, rgba(56, 161, 105, 0.05) 100%);
        border-left: 4px solid #48bb78;
        border-radius: 12px;
        padding: 0.8rem;
        margin: 0.5rem 0;
    }
    
    .status-box {
        background: rgba(0,0,0,0.5);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        margin: 1rem 0;
    }
    
    .custom-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #667eea, #764ba2, transparent);
        margin: 1.5rem 0;
    }
    
    .badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 20px;
        padding: 0.25rem 0.75rem;
        font-size: 0.7rem;
        font-weight: 600;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# HELPER FUNCTIONS
# ============================================
def parse_json_cell(cell_value):
    """Parse JSON from a single cell value"""
    if not cell_value or pd.isna(cell_value):
        return []
    
    if isinstance(cell_value, (list, dict)):
        return cell_value if isinstance(cell_value, list) else [cell_value]
    
    if isinstance(cell_value, str):
        try:
            parsed = json.loads(cell_value)
            return parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            return []
    
    return []

def load_csv_with_json_arrays(csv_path):
    """Load CSV where each row's first column contains a JSON array"""
    if not os.path.exists(csv_path):
        return pd.DataFrame(), []
    
    df_raw = pd.read_csv(csv_path)
    
    if df_raw.empty:
        return pd.DataFrame(), []
    
    first_col = df_raw.columns[0]
    all_parsed_data = []
    run_ids = []
    
    for idx, row in df_raw.iterrows():
        cell_value = row[first_col]
        parsed = parse_json_cell(cell_value)
        
        if parsed:
            run_id = idx + 2
            for item in parsed:
                if isinstance(item, dict):
                    item['run_id'] = run_id
                    item['run_number'] = idx + 1
                    if 'timestamp' in item:
                        try:
                            item['timestamp'] = pd.to_datetime(item['timestamp'])
                        except:
                            pass
            all_parsed_data.extend(parsed)
            run_ids.append(run_id)
    
    return pd.DataFrame(all_parsed_data), run_ids

def load_observations():
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Observations.csv')
    return load_csv_with_json_arrays(csv_path)

def load_summary():
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Summary.csv')
    df, runs = load_csv_with_json_arrays(csv_path)
    return df, runs

def load_anomalies():
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Anomalies.csv')
    df, runs = load_csv_with_json_arrays(csv_path)
    return df, runs

def load_insights():
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Insights.csv')
    df, runs = load_csv_with_json_arrays(csv_path)
    return df, runs

def trigger_workflow():
    """Trigger the n8n workflow via webhook"""
    try:
        response = requests.post(
            WEBHOOK_URL,
            json={
                "trigger": "manual",
                "timestamp": datetime.now().isoformat(),
                "source": "streamlit_dashboard"
            },
            timeout=30
        )
        return response.status_code == 200, response.status_code
    except Exception as e:
        return False, str(e)

def get_last_sync_time():
    csv_path = os.path.join(LOCAL_DATA_DIR, 'Observations.csv')
    if os.path.exists(csv_path):
        mod_time = os.path.getmtime(csv_path)
        return datetime.fromtimestamp(mod_time)
    return None

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'analysis_running' not in st.session_state:
    st.session_state.analysis_running = False
if 'analysis_complete' not in st.session_state:
    st.session_state.analysis_complete = False
if 'last_trigger_time' not in st.session_state:
    st.session_state.last_trigger_time = None
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = False

# ============================================
# MAIN DASHBOARD
# ============================================
def main():
    # Header
    st.markdown('<div class="main-header">⚡ ENERGION</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Intelligent energy management with real-time AI analysis</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎛️ CONTROL PANEL")
        st.markdown("---")
        
        # Big Trigger Button
        st.markdown("#### 🚀 START ANALYSIS")
        
        # Disable button while analysis is running
        trigger_disabled = st.session_state.analysis_running
        
        if st.button("⚡ RUN ENERGY ANALYSIS", use_container_width=True, disabled=trigger_disabled):
            with st.spinner("🔄 Triggering workflow..."):
                success, result = trigger_workflow()
                
                if success:
                    st.session_state.analysis_running = True
                    st.session_state.analysis_complete = False
                    st.session_state.last_trigger_time = datetime.now()
                    st.success("✅ Analysis started! Waiting for results...")
                    st.rerun()
                else:
                    st.error(f"❌ Failed: {result}")
        
        # Show status if analysis is running
        if st.session_state.analysis_running:
            st.markdown("""
            <div class="status-box">
                ⏳ <strong>Analysis in progress...</strong><br>
                This takes about 30-45 seconds.<br>
                Results will appear automatically.
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Auto-refresh toggle
        st.session_state.auto_refresh = st.toggle("🔄 Auto-refresh", value=st.session_state.auto_refresh)
        
        if st.button("⟳ Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📁 DATA SOURCE")
        st.info(f"📂 `{LOCAL_DATA_DIR}/`")
        
        # Show last trigger time
        if st.session_state.last_trigger_time:
            st.markdown(f"🕐 Last trigger: {st.session_state.last_trigger_time.strftime('%H:%M:%S')}")
        
        st.markdown("---")
        st.markdown("### ℹ️ SYSTEM STATUS")
        st.markdown("🟢 **Workflow:** Online")
        st.markdown("🟢 **LLM Model:** Gemini 2.5 Flash-Lite")
        st.markdown("🟢 **Dashboard:** Active")
    
    # Auto-refresh logic
    if st.session_state.auto_refresh:
        time.sleep(30)
        st.rerun()
    
    # Load and display data
    with st.spinner("📊 Loading energy intelligence data..."):
        observations_df, obs_runs = load_observations()
        summary_df, sum_runs = load_summary()
        anomalies_df, anom_runs = load_anomalies()
        insights_df, ins_runs = load_insights()
    
    # Check if new data arrived (if analysis was running)
    if st.session_state.analysis_running and not observations_df.empty:
        # Check if there's a new run
        if 'run_number' in observations_df.columns:
            latest_run = observations_df['run_number'].max()
            if st.session_state.get('last_run', 0) != latest_run:
                st.session_state.analysis_running = False
                st.session_state.analysis_complete = True
                st.session_state.last_run = latest_run
                st.success("✅ Analysis complete! New results available.")
                st.balloons()
                st.rerun()
    
    if observations_df.empty:
        st.info("📭 No data available. Click 'RUN ENERGY ANALYSIS' to start your first analysis.")
        
        # Show instructions
        with st.expander("📖 How it works"):
            st.markdown("""
            1. Click the **RUN ENERGY ANALYSIS** button
            2. Workflow fetches data from Google Sheets
            3. AI analyzes consumption patterns
            4. Results appear here automatically
            """)
        return
    
    # Get available runs
    available_runs = sorted(observations_df['run_number'].unique()) if 'run_number' in observations_df else []
    
    # Run selector
    if available_runs:
        selected_run = st.selectbox(
            "📊 Select Analysis Run",
            options=available_runs,
            index=len(available_runs) - 1,
            format_func=lambda x: f"🏃 Run {x} ({len(observations_df[observations_df['run_number'] == x])} observations)"
        )
    else:
        selected_run = None
    
    # Filter data by selected run
    if selected_run and 'run_number' in observations_df.columns:
        current_observations = observations_df[observations_df['run_number'] == selected_run]
        current_anomalies = anomalies_df[anomalies_df['run_number'] == selected_run] if 'run_number' in anomalies_df else pd.DataFrame()
        current_insights = insights_df[insights_df['run_number'] == selected_run] if 'run_number' in insights_df else pd.DataFrame()
        current_summary = summary_df[summary_df['run_number'] == selected_run] if 'run_number' in summary_df else pd.DataFrame()
    else:
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
    
    # Show run badge
    if available_runs:
        st.markdown(f"<span class='badge'>📊 RUN {selected_run if selected_run else latest_run}</span>", unsafe_allow_html=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Key Metrics
    st.markdown("### 📈 KEY PERFORMANCE INDICATORS")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        peak = current_observations['consumption_kW'].max() if not current_observations.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">⚡ PEAK DEMAND</div>
            <div class="metric-value">{peak:.1f}<span style="font-size:1rem;"> kW</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        avg = current_observations['consumption_kW'].mean() if not current_observations.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📊 AVERAGE DEMAND</div>
            <div class="metric-value">{avg:.1f}<span style="font-size:1rem;"> kW</span></div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if not current_summary.empty and 'total_cost' in current_summary.columns:
            cost = current_summary['total_cost'].iloc[-1]
        else:
            cost = (current_observations['consumption_kW'] * current_observations['tariff']).sum() if not current_observations.empty else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">💰 TOTAL COST</div>
            <div class="metric-value">${cost:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        critical = len(current_observations[current_observations['status'] == 'CRITICAL']) if 'status' in current_observations.columns else 0
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">⚠️ CRITICAL ALERTS</div>
            <div class="metric-value">{critical}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Consumption Chart
    st.markdown("### 📉 CONSUMPTION PATTERN")
    
    if 'timestamp' in current_observations.columns and 'consumption_kW' in current_observations.columns:
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=current_observations['timestamp'],
            y=current_observations['consumption_kW'],
            mode='lines+markers',
            name='Consumption',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8, color='#764ba2')
        ))
        
        if 'status' in current_observations.columns:
            critical_points = current_observations[current_observations['status'] == 'CRITICAL']
            if not critical_points.empty:
                fig.add_trace(go.Scatter(
                    x=critical_points['timestamp'],
                    y=critical_points['consumption_kW'],
                    mode='markers',
                    name='⚠️ Critical Alerts',
                    marker=dict(color='#ff4747', size=14, symbol='x')
                ))
        
        fig.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            height=450,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Anomalies and Insights
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚨 ANOMALY DETECTION")
        if not current_anomalies.empty:
            for _, row in current_anomalies.iterrows():
                st.markdown(f"""
                <div class="alert-critical">
                    <strong>⚠️ {row.get('type', 'Anomaly').upper()}</strong><br>
                    📍 {row.get('timestamp', 'Unknown')}<br>
                    💡 {row.get('reason', 'No reason')}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="insight-card">✅ No anomalies detected</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 💡 KEY INSIGHTS")
        if not current_insights.empty and 'insights' in current_insights.columns:
            insights_text = current_insights['insights'].iloc[-1]
            if insights_text:
                for insight in str(insights_text).split(' | ')[:3]:
                    if insight.strip():
                        st.markdown(f'<div class="insight-card">💡 {insight.strip()}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="insight-card">🔮 Run analysis to see AI insights</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Recommendations
    st.markdown("### 📋 AI-GENERATED RECOMMENDATIONS")
    
    if not current_insights.empty and 'recommendations' in current_insights.columns:
        recs = current_insights['recommendations'].iloc[-1]
        if recs:
            for i, rec in enumerate(str(recs).split(' | '), 1):
                if rec.strip():
                    st.markdown(f'<div class="insight-card">{i}. {rec.strip()}</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
    
    # Selected Strategy
    if not current_insights.empty and 'selected_strategy' in current_insights.columns:
        strategy = current_insights['selected_strategy'].iloc[-1]
        savings = current_insights['expected_savings'].iloc[-1] if 'expected_savings' in current_insights.columns else 0
        if strategy and strategy != 'None' and savings > 0:
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <div class="metric-label">🎯 RECOMMENDED STRATEGY</div>
                <div class="metric-value">{strategy}</div>
                <div class="metric-label">Expected Savings: ${savings}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1rem 0;">
        <p style="color: #a0aec0; font-size: 0.8rem;">
            ⚡ ENERGION | Powered by Gemini 2.5 Flash-Lite
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()