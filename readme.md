# ⚡ Energy Optimization AI System

Agentic AI system for large electricity consumers to optimize power consumption, forecast demand, and reduce energy costs.

## 🚀 Features

- **Real-time Monitoring** - Track consumption patterns instantly
- **Demand Forecasting** - Predict future energy needs with 85%+ accuracy
- **Anomaly Detection** - Identify unusual consumption patterns
- **AI Recommendations** - Get actionable optimization strategies
- **Google Sheets Integration** - Simple, no-code setup
- **Streamlit Dashboard** - Beautiful, interactive visualization

## 📋 Prerequisites

- Python 3.9+
- Google Cloud Account
- Gemini API Access
- Google Sheets with 4 tabs: Observations, Summary, Anomalies, Insights

## 🛠️ Installation

```bash
# Clone repository
git clone https://github.com/yourusername/energy-optimization.git
cd energy-optimization

# Install dependencies
pip install -r requirements.txt

# Set up credentials
# Add your service account JSON file
# Configure .env file with your sheet IDs

# Run sync script
python sync_google_sheets_local.py

# Launch dashboard
streamlit run dashboard.py