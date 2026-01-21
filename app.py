# app.py
import streamlit as st
from gpr_agent import GPRDefectAgent
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sqlite3
import re


import os
from pathlib import Path

# Auto-create database if it doesn't exist (for deployment)
if not Path('gpr_defects.db').exists():
    import database_setup
    conn = database_setup.create_database()
    database_setup.populate_sample_data(conn)
    conn.close()
# Page config
st.set_page_config(
    page_title="GPR Defect Analysis Agent",
    page_icon="🔍",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .sql-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = GPRDefectAgent()
if 'query_history' not in st.session_state:
    st.session_state.query_history = []
if 'show_sql' not in st.session_state:
    st.session_state.show_sql = False
if 'last_sql' not in st.session_state:
    st.session_state.last_sql = None

# Helper functions
def extract_sql_from_output(output_text):
    """Extract SQL queries from agent output"""
    sql_queries = []
    
    # Pattern to match SQL queries in the verbose output
    patterns = [
        r'Action Input:\s*(SELECT.*?)(?:\n|$)',
        r'sql_db_query.*?(SELECT.*?)(?:\n|$)',
        r'(SELECT\s+.*?FROM.*?)(?:\n|$)',
        r'(INSERT\s+.*?INTO.*?)(?:\n|$)',
        r'(UPDATE\s+.*?SET.*?)(?:\n|$)',
        r'(DELETE\s+.*?FROM.*?)(?:\n|$)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, output_text, re.IGNORECASE | re.DOTALL)
        sql_queries.extend(matches)
    
    return sql_queries if sql_queries else None

@st.cache_data
def get_db_stats():
    """Get database statistics"""
    conn = sqlite3.connect('gpr_defects.db')
    stats = {}
    stats['total_scans'] = pd.read_sql("SELECT COUNT(*) as count FROM scans", conn).iloc[0]['count']
    stats['total_defects'] = pd.read_sql("SELECT COUNT(*) as count FROM defects", conn).iloc[0]['count']
    stats['critical_defects'] = pd.read_sql(
        "SELECT COUNT(*) as count FROM defects WHERE severity='critical'", conn
    ).iloc[0]['count']
    stats['pending_repairs'] = pd.read_sql(
        "SELECT COUNT(*) as count FROM repair_history WHERE status IN ('planned', 'in_progress')", conn
    ).iloc[0]['count']
    conn.close()
    return stats

@st.cache_data
def get_defect_distribution():
    """Get defect type distribution"""
    conn = sqlite3.connect('gpr_defects.db')
    df = pd.read_sql("""
        SELECT defect_type, severity, COUNT(*) as count
        FROM defects
        GROUP BY defect_type, severity
    """, conn)
    conn.close()
    return df

@st.cache_data
def get_location_stats():
    """Get defect stats by location"""
    conn = sqlite3.connect('gpr_defects.db')
    df = pd.read_sql("""
        SELECT 
            s.location,
            COUNT(*) as defect_count,
            AVG(d.depth_cm) as avg_depth,
            SUM(CASE WHEN d.severity='critical' THEN 1 ELSE 0 END) as critical_count
        FROM defects d
        JOIN scans s ON d.scan_id = s.scan_id
        GROUP BY s.location
        ORDER BY defect_count DESC
    """, conn)
    conn.close()
    return df

# Sidebar
with st.sidebar:
    st.markdown("### 🔍 GPR Defect Analysis")
    st.markdown("---")
    
    # Database stats
    stats = get_db_stats()
    st.metric("Total Scans", stats['total_scans'])
    st.metric("Total Defects", stats['total_defects'])
    st.metric("Critical Defects", stats['critical_defects'])
    st.metric("Pending Repairs", stats['pending_repairs'])
    
    st.markdown("---")
    
    # Settings
    st.session_state.show_sql = st.checkbox("Show Generated SQL", value=st.session_state.show_sql)
    
    st.markdown("---")
    
    # Example queries
    st.markdown("### 💡 Example Queries")
    examples = [
        "How many defects total?",
        "Show all critical cavities",
        "Average repair cost by type",
        "Which roads need urgent repairs?",
        "Count defects by severity",
        "Show defects in Gangnam-daero"
    ]
    
    for i, ex in enumerate(examples):
        if st.button(ex, key=f"ex_{i}", width='stretch'):
            st.session_state.current_query = ex

# Main header
st.markdown('<p class="main-header">🛣️ GPR Defect Analysis Agent</p>', unsafe_allow_html=True)
st.markdown("AI-powered natural language interface for road infrastructure analysis")

# Tabs
tab1, tab2, tab3 = st.tabs(["💬 Chat Agent", "📊 Dashboard", "📚 History"])

# Tab 1: Chat Agent
with tab1:
    st.markdown("### Ask questions about your GPR data in natural language")
    
    # Query input
    col1, col2 = st.columns([5, 1])
    with col1:
        query = st.text_input(
            "Your question:",
            value=st.session_state.get('current_query', ''),
            placeholder="e.g., Show me all critical defects detected last month",
            key="query_input",
            label_visibility="collapsed"
        )
    with col2:
        execute_btn = st.button("🚀 Ask", type="primary", width='stretch')
    
    if execute_btn and query:
        with st.spinner("🤔 Thinking..."):
            try:
                # Capture the agent's verbose output
                import sys
                from io import StringIO
                
                # Redirect stdout to capture verbose output
                old_stdout = sys.stdout
                sys.stdout = captured_output = StringIO()
                
                # Execute query
                result = st.session_state.agent.query(query)
                
                # Get the captured output
                verbose_output = captured_output.getvalue()
                sys.stdout = old_stdout
                
                # Extract SQL from verbose output
                sql_queries = extract_sql_from_output(verbose_output)
                st.session_state.last_sql = sql_queries
                
                # Store in history
                st.session_state.query_history.append({
                    'timestamp': datetime.now(),
                    'query': query,
                    'result': result,
                    'sql': sql_queries
                })
                
                # Display result
                st.markdown("---")
                st.markdown(f"**Question:** {query}")
                
                # Show SQL if enabled
                if st.session_state.show_sql and sql_queries:
                    st.markdown("**Generated SQL:**")
                    for i, sql in enumerate(sql_queries):
                        st.code(sql.strip(), language="sql")
                
                st.markdown(f"**Answer:**")
                st.info(result)
                
                # Clear current query
                if 'current_query' in st.session_state:
                    del st.session_state.current_query
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Show last SQL if available
    if st.session_state.show_sql and st.session_state.last_sql and not execute_btn:
        with st.expander("🔍 Last Generated SQL"):
            for i, sql in enumerate(st.session_state.last_sql):
                st.code(sql.strip(), language="sql")
    
    # Schema info
    with st.expander("📋 View Database Schema"):
        st.code(st.session_state.agent.get_schema_info(), language="sql")

# Tab 2: Dashboard
with tab2:
    st.markdown("### 📊 Database Analytics")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Defects", stats['total_defects'])
    with col2:
        st.metric("Critical", stats['critical_defects'])
    with col3:
        detection_rate = round(stats['total_defects'] / stats['total_scans'], 1)
        st.metric("Defects/Scan", detection_rate)
    with col4:
        st.metric("Pending Repairs", stats['pending_repairs'])
    
    st.markdown("---")
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Defect Distribution")
        df_dist = get_defect_distribution()
        fig = px.sunburst(
            df_dist, 
            path=['defect_type', 'severity'], 
            values='count',
            color='severity',
            color_discrete_map={
                'low': '#90EE90', 
                'medium': '#FFD700', 
                'high': '#FFA500', 
                'critical': '#FF4500'
            }
        )
        st.plotly_chart(fig, width='stretch')
    
    with col2:
        st.markdown("#### Defects by Location")
        df_loc = get_location_stats()
        fig = px.bar(
            df_loc, 
            x='location', 
            y='defect_count',
            color='critical_count',
            title="Total Defects per Location"
        )
        st.plotly_chart(fig, width='stretch')
    
    # Data table
    st.markdown("#### Location Statistics")
    st.dataframe(
        df_loc.style.background_gradient(subset=['defect_count'], cmap='YlOrRd'),
        width='stretch'
    )

# Tab 3: History
with tab3:
    st.markdown("### 📚 Query History")
    
    if st.session_state.query_history:
        for i, item in enumerate(reversed(st.session_state.query_history)):
            with st.expander(
                f"🕒 {item['timestamp'].strftime('%H:%M:%S')} - {item['query'][:60]}...",
                expanded=(i == 0)
            ):
                st.markdown(f"**Query:** {item['query']}")
                
                # Show SQL if available
                if item.get('sql'):
                    st.markdown("**Generated SQL:**")
                    for sql in item['sql']:
                        st.code(sql.strip(), language="sql")
                
                st.markdown(f"**Answer:**")
                st.info(item['result'])
                
                if st.button("Rerun", key=f"rerun_{i}"):
                    st.session_state.current_query = item['query']
                    st.rerun()
    else:
        st.info("No queries yet. Start asking questions in the Chat Agent tab!")
    
    if st.button("Clear History"):
        st.session_state.query_history = []
        st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        GPR Defect Analysis Agent | Powered by Claude Sonnet & LangChain
    </div>
    """,
    unsafe_allow_html=True
)
