import streamlit as st
import pandas as pd
import altair as alt
import boto3
import time
import os
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Set page configuration
st.set_page_config(
    page_title="TelcoPulse: Real-Time Network Metrics",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        color: #424242;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f7f7f7;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .stPlotlyChart {
        background-color: white;
        border-radius: 5px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
</style>
""", unsafe_allow_html=True)

# ------------------ AWS Athena Connection Functions ------------------
def initialize_athena_client():
    """Initialize AWS Athena client."""
    client = boto3.client('athena')
    return client

def run_athena_query(query, database, output_location):
    """Execute an Athena query and return the results."""
    client = initialize_athena_client()
    
    # Start the query execution
    response = client.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': database},
        ResultConfiguration={'OutputLocation': output_location}
    )
    query_execution_id = response['QueryExecutionId']
    
    # Wait for query to complete
    query_status = 'RUNNING'
    while query_status in ('RUNNING', 'QUEUED'):
        time.sleep(1)
        response = client.get_query_execution(QueryExecutionId=query_execution_id)
        query_status = response['QueryExecution']['Status']['State']
        
    if query_status == 'SUCCEEDED':
        # Get the results
        results = client.get_query_results(QueryExecutionId=query_execution_id)
        
        # Process the results into a DataFrame
        columns = [col['Label'] for col in results['ResultSet']['ResultSetMetadata']['ColumnInfo']]
        data = []
        for row in results['ResultSet']['Rows'][1:]:  # Skip the header row
            data.append([value.get('VarCharValue', '') for value in row['Data']])
            
        df = pd.DataFrame(data, columns=columns)
        return df
    else:
        st.error(f"Query execution failed: {query_status}")
        return None

# ------------------ Data Fetching Functions ------------------
@st.cache_data(ttl=300)  # Cache data for 5 minutes
def get_operator_metrics(athena_database, athena_output_location, time_filter="1 hour"):
    """Fetch the average signal strength and precision by operator."""
    query = f"""
    SELECT operator, 
           AVG("avg_signal_#0") as avg_signal_strength, 
           AVG("avg_precission_#1") as avg_precision
    FROM average_by_operator
    WHERE CONCAT(ingest_year, '-', ingest_month, '-', ingest_day, ' ', ingest_hour, ':00:00') >= 
          DATE_FORMAT(DATE_ADD('hour', -{time_filter.split()[0]}, CURRENT_TIMESTAMP), '%Y-%m-%d %H:%i:%s')
    GROUP BY operator
    ORDER BY avg_signal_strength DESC
    """
    
    df = run_athena_query(query, athena_database, athena_output_location)
    if df is not None:
        df['avg_signal_strength'] = pd.to_numeric(df['avg_signal_strength'])
        df['avg_precision'] = pd.to_numeric(df['avg_precision'])
    return df

@st.cache_data(ttl=300)  # Cache data for 5 minutes
def get_postal_code_status(athena_database, athena_output_location, time_filter="1 hour"):
    """Fetch the count of network statuses by postal code."""
    query = f"""
    SELECT postal_code, 
           description as status_description, 
           SUM("count_status_#0") as status_count
    FROM status_by_postal_code
    WHERE CONCAT(ingest_year, '-', ingest_month, '-', ingest_day, ' ', ingest_hour, ':00:00') >= 
          DATE_FORMAT(DATE_ADD('hour', -{time_filter.split()[0]}, CURRENT_TIMESTAMP), '%Y-%m-%d %H:%i:%s')
    GROUP BY postal_code, description
    ORDER BY postal_code, status_count DESC
    """
    
    df = run_athena_query(query, athena_database, athena_output_location)
    if df is not None:
        df['status_count'] = pd.to_numeric(df['status_count'])
    return df

@st.cache_data(ttl=300)  # Cache data for 5 minutes
def get_hourly_metrics(athena_database, athena_output_location, time_filter="24 hours"):
    """Fetch the hourly evolution of metrics."""
    query = f"""
    SELECT operator,
           CONCAT(ingest_year, '-', ingest_month, '-', ingest_day, ' ', ingest_hour, ':00:00') as hour,
           AVG("avg_signal_#0") as avg_signal_strength,
           AVG("avg_precission_#1") as avg_precision
    FROM average_by_operator
    WHERE CONCAT(ingest_year, '-', ingest_month, '-', ingest_day, ' ', ingest_hour, ':00:00') >= 
          DATE_FORMAT(DATE_ADD('hour', -{time_filter.split()[0]}, CURRENT_TIMESTAMP), '%Y-%m-%d %H:%i:%s')
    GROUP BY operator, CONCAT(ingest_year, '-', ingest_month, '-', ingest_day, ' ', ingest_hour, ':00:00')
    ORDER BY hour, operator
    """
    
    df = run_athena_query(query, athena_database, athena_output_location)
    if df is not None:
        df['hour'] = pd.to_datetime(df['hour'])
        df['avg_signal_strength'] = pd.to_numeric(df['avg_signal_strength'])
        df['avg_precision'] = pd.to_numeric(df['avg_precision'])
    return df

# ------------------ Main App ------------------
def main():
    # Sidebar configuration
    st.sidebar.image("https://via.placeholder.com/150x80?text=TelcoPulse", width=150)
    st.sidebar.title("Dashboard Settings")
    
    # AWS Configuration
    with st.sidebar.expander("AWS Configuration", expanded=False):
        athena_database = st.text_input("Athena Database", value="project-9")
        athena_output_location = st.text_input("Athena Output Location", value="s3://athena-zuki/queries/")
    
    # Time Filter
    time_filter = st.sidebar.selectbox(
        "Time Window",
        ["1 hour", "3 hours", "6 hours", "12 hours", "24 hours", "7 days"],
        index=2
    )
    
    # Refresh Rate
    refresh_rate = st.sidebar.slider(
        "Auto-refresh Interval (minutes)",
        min_value=1,
        max_value=30,
        value=5
    )
    
    # Auto-refresh placeholder
    refresh_placeholder = st.sidebar.empty()
    
    # Current time display
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.sidebar.markdown(f"**Last Updated:** {current_time}")
    
    # Main Area
    st.markdown("<h1 class='main-header'>TelcoPulse: Real-Time Network Metrics Dashboard</h1>", unsafe_allow_html=True)
    
    # Load data
    with st.spinner("Loading data from AWS Athena..."):
        operator_metrics = get_operator_metrics(athena_database, athena_output_location, time_filter)
        postal_code_status = get_postal_code_status(athena_database, athena_output_location, time_filter)
        hourly_metrics = get_hourly_metrics(athena_database, athena_output_location, time_filter)
    
    if operator_metrics is None or postal_code_status is None:
        st.error("Failed to load data from Athena. Please check your AWS credentials and settings.")
        return
    
    # KPI Summary Cards
    st.markdown("<h2 class='sub-header'>Network Performance Overview</h2>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Operators",
            value=len(operator_metrics) if operator_metrics is not None else "N/A"
        )
    
    with col2:
        st.metric(
            label="Average Signal Strength",
            value=f"{operator_metrics['avg_signal_strength'].mean():.2f}" if operator_metrics is not None else "N/A"
        )
    
    with col3:
        st.metric(
            label="Average GPS Precision",
            value=f"{operator_metrics['avg_precision'].mean():.2f}" if operator_metrics is not None else "N/A"
        )
    
    with col4:
        st.metric(
            label="Total Postal Codes",
            value=len(postal_code_status['postal_code'].unique()) if postal_code_status is not None else "N/A"
        )
    
    # Operator Metrics Section
    st.markdown("<h2 class='sub-header'>Operator Performance Metrics</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if operator_metrics is not None:
            fig = px.bar(
                operator_metrics,
                x='operator',
                y='avg_signal_strength',
                title='Average Signal Strength by Operator',
                color='avg_signal_strength',
                color_continuous_scale=px.colors.sequential.Blues,
                height=400
            )
            fig.update_layout(
                xaxis_title="Operator",
                yaxis_title="Average Signal Strength",
                coloraxis_showscale=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        if operator_metrics is not None:
            fig = px.bar(
                operator_metrics,
                x='operator',
                y='avg_precision',
                title='Average GPS Precision by Operator',
                color='avg_precision',
                color_continuous_scale=px.colors.sequential.Greens,
                height=400
            )
            fig.update_layout(
                xaxis_title="Operator",
                yaxis_title="Average GPS Precision",
                coloraxis_showscale=False
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Time Series Data
    st.markdown("<h2 class='sub-header'>Hourly Metrics Evolution</h2>", unsafe_allow_html=True)
    
    if hourly_metrics is not None:
        tab1, tab2 = st.tabs(["Signal Strength Over Time", "GPS Precision Over Time"])
        
        with tab1:
            fig = px.line(
                hourly_metrics,
                x='hour',
                y='avg_signal_strength',
                color='operator',
                title='Signal Strength Evolution Over Time',
                height=500
            )
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Average Signal Strength",
                legend_title="Operator"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with tab2:
            fig = px.line(
                hourly_metrics,
                x='hour',
                y='avg_precision',
                color='operator',
                title='GPS Precision Evolution Over Time',
                height=500
            )
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="Average GPS Precision",
                legend_title="Operator"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # Network Status by Postal Code
    st.markdown("<h2 class='sub-header'>Network Status by Postal Code</h2>", unsafe_allow_html=True)
    
    if postal_code_status is not None:
        # Create a pivot table to show status counts by postal code
        pivot_df = postal_code_status.pivot_table(
            index='postal_code',
            columns='status_description',
            values='status_count',
            aggfunc='sum',
            fill_value=0
        ).reset_index()
        
        # Create a stacked bar chart
        fig = go.Figure()
        
        status_descriptions = postal_code_status['status_description'].unique()
        for status in status_descriptions:
            if status in pivot_df.columns:
                fig.add_trace(go.Bar(
                    x=pivot_df['postal_code'],
                    y=pivot_df[status],
                    name=status
                ))
        
        fig.update_layout(
            title='Network Status Distribution by Postal Code',
            xaxis_title='Postal Code',
            yaxis_title='Count',
            barmode='stack',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Table view
        st.markdown("<h3>Detailed Network Status Data</h3>", unsafe_allow_html=True)
        st.dataframe(postal_code_status, use_container_width=True)
    
    # Schedule the next refresh
    if st.sidebar.button("Refresh Data Now"):
        st.rerun()
    
    # Auto-refresh logic
    if refresh_rate > 0:
        refresh_placeholder.info(f"Dashboard will auto-refresh every {refresh_rate} minutes.")
        time_to_refresh = refresh_rate * 60
        
        # Add a countdown timer
        countdown_placeholder = st.sidebar.empty()
        for remaining in range(time_to_refresh, 0, -1):
            minutes, seconds = divmod(remaining, 60)
            countdown_placeholder.text(f"Next refresh in: {minutes:02d}:{seconds:02d}")
            time.sleep(1)
            
        # Trigger a rerun after the countdown
        countdown_placeholder.empty()
        st.rerun()

if __name__ == "__main__":
    main()