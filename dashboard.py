"""
Streamlit dashboard to analyze combined.csv
- Remove rows where risk or grade is null
- Filter grades to [-30, 100]
- Scatter plot: risk vs grade with line of best fit and R²
- Table: avg grade by risk bucket
- Filters: dynamic, risk amount, date
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Bet Analysis Dashboard", layout="wide")

st.title("Bet Correlation Analysis Dashboard")
st.markdown("Analyzing relationship between Risk, Grades, and Results")

# Load data
@st.cache_data
def load_data():
    """Load and clean combined.csv"""
    df = pd.read_csv('combined.csv')
    
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Remove rows where risk or grade is null
    df = df.dropna(subset=['risk', 'grade'])
    
    # Filter grades to [-30, 100]
    df = df[(df['grade'] >= -30) & (df['grade'] <= 100)]
    
    return df

df = load_data()

st.sidebar.header("Filters")

# Filter: Dynamic (multiple selection with checkboxes)
if 'dynamic' in df.columns:
    dynamic_options = sorted(df['dynamic'].dropna().unique().tolist())
    selected_dynamics = st.sidebar.multiselect(
        "Select Dynamics",
        options=dynamic_options,
        default=dynamic_options,  # Select all by default
        key="dynamic_filter"
    )
    
    # Filter by selected dynamics
    if selected_dynamics:
        df = df[df['dynamic'].isin(selected_dynamics)]

# Filter: Date Range
if 'date' in df.columns:
    min_date = df['date'].min().date()
    max_date = df['date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        df = df[(df['date'].dt.date >= date_range[0]) & (df['date'].dt.date <= date_range[1])]

# Filter: Risk Amount Range
if 'risk' in df.columns:
    min_risk = float(df['risk'].min())
    max_risk = float(df['risk'].max())
    
    risk_range = st.sidebar.slider(
        "Risk Amount Range",
        min_value=min_risk,
        max_value=max_risk,
        value=(min_risk, max_risk),
        step=10.0
    )
    
    df = df[(df['risk'] >= risk_range[0]) & (df['risk'] <= risk_range[1])]

# Display data info
st.markdown("### Data Overview")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Records", len(df))
col2.metric("Unique Dates", df['date'].nunique() if 'date' in df.columns else 0)
col3.metric("Avg Risk", f"${df['risk'].mean():.2f}" if 'risk' in df.columns else "N/A")
col4.metric("Avg Grade", f"{df['grade'].mean():.2f}" if 'grade' in df.columns else "N/A")

st.markdown("---")

# Scatter plot: Risk vs Grade
st.markdown("### Risk vs Grade Analysis")

if len(df) > 0 and 'risk' in df.columns and 'grade' in df.columns:
    # Calculate line of best fit
    x = df['risk'].values
    y = df['grade'].values
    
    # Remove any remaining NaN values
    mask = ~(np.isnan(x) | np.isnan(y))
    x_clean = x[mask]
    y_clean = y[mask]
    
    if len(x_clean) > 1:
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x_clean, y_clean)
        r_squared = r_value ** 2
        
        # Create line of best fit
        x_line = np.linspace(x_clean.min(), x_clean.max(), 100)
        y_line = slope * x_line + intercept
        
        # Create scatter plot with Plotly
        fig = go.Figure()
        
        # Add scatter points
        fig.add_trace(go.Scatter(
            x=x_clean,
            y=y_clean,
            mode='markers',
            marker=dict(
                size=8,
                opacity=0.6,
                color=y_clean,
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Grade")
            ),
            name='Data Points',
            hovertemplate='Risk: $%{x:.2f}<br>Grade: %{y:.2f}<extra></extra>'
        ))
        
        # Add line of best fit
        fig.add_trace(go.Scatter(
            x=x_line,
            y=y_line,
            mode='lines',
            name=f'Line of Best Fit<br>R² = {r_squared:.4f}',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title=f'Risk vs Grade (R² = {r_squared:.4f})',
            xaxis_title='Risk Amount ($)',
            yaxis_title='Grade',
            hovermode='closest',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Display statistics
        col1, col2, col3 = st.columns(3)
        col1.metric("R²", f"{r_squared:.4f}")
        col2.metric("Slope", f"{slope:.6f}")
        col3.metric("P-value", f"{p_value:.4f}" if p_value < 0.0001 else f"{p_value:.6f}")
    else:
        st.warning("Not enough data points for regression analysis.")
else:
    st.warning("Missing required columns for scatter plot.")

st.markdown("---")

# Table: Avg Grade by Risk Bucket
st.markdown("### Average Grade by Risk Amount Bucket")

if len(df) > 0 and 'risk' in df.columns and 'grade' in df.columns:
    # Create risk buckets
    df_buckets = df.copy()
    
    # Define buckets (you can customize these)
    bucket_size = st.sidebar.slider("Risk Bucket Size ($)", min_value=50, max_value=500, value=100, step=50)
    
    # Create buckets
    df_buckets['risk_bucket'] = (df_buckets['risk'] // bucket_size) * bucket_size
    df_buckets['risk_bucket'] = df_buckets['risk_bucket'].astype(int)
    df_buckets['risk_bucket_label'] = df_buckets['risk_bucket'].apply(
        lambda x: f"${x} - ${x + bucket_size - 1}"
    )
    
    # Calculate statistics by bucket
    bucket_stats = df_buckets.groupby('risk_bucket_label').agg({
        'grade': 'mean',
        'risk': 'sum',
        'result': 'sum' if 'result' in df.columns else 'sum'
    }).round(2)
    
    # Add count
    bucket_stats['Count'] = df_buckets.groupby('risk_bucket_label').size()
    
    # Reset index and rename
    bucket_stats = bucket_stats.reset_index()
    bucket_stats = bucket_stats.rename(columns={'risk_bucket_label': 'Bucket', 'grade': 'Avg Grade', 'risk': 'Total Risk', 'result': 'Total Result'})
    
    # Calculate ROI (result/risk) as percentage
    bucket_stats['ROI'] = (bucket_stats['Total Result'] / bucket_stats['Total Risk'] * 100).round(2)
    
    # Reorder columns: bucket, count, avg grade, total risk, total result, roi
    bucket_stats = bucket_stats[['Bucket', 'Count', 'Avg Grade', 'Total Risk', 'Total Result', 'ROI']]
    
    # Sort by bucket (risk amount)
    bucket_stats = bucket_stats.sort_values('Bucket')
    
    # Display table
    st.dataframe(
        bucket_stats,
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = bucket_stats.to_csv(index=False)
    st.download_button(
        label="Download Bucket Statistics as CSV",
        data=csv,
        file_name="risk_bucket_stats.csv",
        mime="text/csv"
    )
else:
    st.warning("Missing required columns for bucket analysis.")

st.markdown("---")

# Table: Statistics by Dynamic
st.markdown("### Statistics by Dynamic")

if len(df) > 0 and 'dynamic' in df.columns:
    # Calculate statistics by dynamic
    dynamic_stats = df.groupby('dynamic').agg({
        'grade': 'mean',
        'risk': 'sum',
        'result': 'sum' if 'result' in df.columns else 'sum'
    }).round(2)
    
    # Add count
    dynamic_stats['Count'] = df.groupby('dynamic').size()
    
    # Reset index
    dynamic_stats = dynamic_stats.reset_index()
    dynamic_stats = dynamic_stats.rename(columns={
        'dynamic': 'Dynamic',
        'grade': 'Avg Grade',
        'risk': 'Total Risk',
        'result': 'Total Result'
    })
    
    # Calculate ROI (result/risk) as percentage
    dynamic_stats['ROI'] = (dynamic_stats['Total Result'] / dynamic_stats['Total Risk'] * 100).round(2)
    
    # Reorder columns: dynamic, count, avg grade, total risk, total result, roi
    dynamic_stats = dynamic_stats[['Dynamic', 'Count', 'Avg Grade', 'Total Risk', 'Total Result', 'ROI']]
    
    # Sort by total risk
    dynamic_stats = dynamic_stats.sort_values('Total Risk', ascending=False)
    
    # Display table
    st.dataframe(
        dynamic_stats,
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = dynamic_stats.to_csv(index=False)
    st.download_button(
        label="Download Dynamic Statistics as CSV",
        data=csv,
        file_name="dynamic_stats.csv",
        mime="text/csv"
    )
else:
    st.warning("Missing required columns for dynamic analysis.")

# Show raw data option
st.markdown("---")
with st.expander("View Filtered Raw Data"):
    st.dataframe(df, use_container_width=True)
    
    # Download filtered data
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv,
        file_name="filtered_combined_data.csv",
        mime="text/csv"
    )

