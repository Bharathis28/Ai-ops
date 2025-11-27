"""AI Ops Sentry - Streamlit Dashboard Application.

This is the main entry point for the AIOps observability dashboard.
It provides a multi-page interface for monitoring services, anomalies, and actions.
"""

import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Ops Sentry",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern, clean design
st.markdown("""
<style>
    /* Main container */
    .main {
        padding: 0rem 1rem;
    }
    
    /* KPI cards */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 8px;
    }
    
    /* Severity badges */
    .badge {
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        display: inline-block;
    }
    
    .badge-critical {
        background-color: #dc3545;
        color: white;
    }
    
    .badge-high {
        background-color: #fd7e14;
        color: white;
    }
    
    .badge-medium {
        background-color: #ffc107;
        color: #000;
    }
    
    .badge-low {
        background-color: #28a745;
        color: white;
    }
    
    .badge-healthy {
        background-color: #20c997;
        color: white;
    }
    
    .badge-degraded {
        background-color: #ffc107;
        color: #000;
    }
    
    .badge-down {
        background-color: #dc3545;
        color: white;
    }
    
    /* Header styling */
    h1 {
        color: #667eea;
        font-weight: 700;
    }
    
    h2, h3 {
        color: #495057;
    }
</style>
""", unsafe_allow_html=True)

# Import page modules
import importlib.util

pages_dir = Path(__file__).parent / "pages"

# Helper to load page modules
def load_page_module(page_name: str):
    """Dynamically load a page module."""
    page_path = pages_dir / f"{page_name}.py"
    if not page_path.exists():
        return None
    spec = importlib.util.spec_from_file_location(page_name, page_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

# Main app
def main():
    """Main dashboard application."""
    
    # Top navbar
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.title("🛡️ AI Ops Sentry")
    
    with col2:
        environment = st.selectbox(
            "Environment",
            ["production", "staging", "development"],
            index=0,
            key="environment",
        )
    
    with col3:
        st.write("")
        st.write(f"**Active:** {datetime.now().strftime('%H:%M:%S')}")
    
    st.markdown("---")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["📊 Overview", "🔍 Anomalies", "⚙️ Services", "🔧 Actions", "⚙️ Settings"],
        index=0,
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Quick Stats")
    st.sidebar.metric("Uptime", "99.95%", "0.02%")
    st.sidebar.metric("Active Alerts", "3", "-2")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**Version:** 1.0.0  \n"
        "**Last Updated:** Nov 27, 2025"
    )
    
    # Store environment in session state
    st.session_state["environment"] = environment
    
    # Route to appropriate page
    if page == "📊 Overview":
        overview_page = load_page_module("overview")
        if overview_page:
            overview_page.show()
    elif page == "🔍 Anomalies":
        anomalies_page = load_page_module("anomalies")
        if anomalies_page:
            anomalies_page.show()
    elif page == "⚙️ Services":
        services_page = load_page_module("services")
        if services_page:
            services_page.show()
    elif page == "🔧 Actions":
        actions_page = load_page_module("actions")
        if actions_page:
            actions_page.show()
    elif page == "⚙️ Settings":
        settings_page = load_page_module("settings")
        if settings_page:
            settings_page.show()


if __name__ == "__main__":
    main()
