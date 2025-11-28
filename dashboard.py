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

def style_grades(value):
    """Style function for grade columns - gradient green for positive, gradient red for negative"""
    if pd.isna(value):
        return ''
    
    try:
        grade = float(value)
        if grade > 0:
            # Positive: green gradient from light to dark green
            # Scale from 0 to 100, creating a smooth gradient
            intensity = min(grade / 100.0, 1.0)
            # Green gradient: 180 (light green) to 50 (dark green)
            # Higher values = darker green
            green_value = int(180 - (130 * intensity))
            # Ensure minimum visibility
            green_value = max(50, green_value)
            return f'background-color: rgb(0, {green_value}, 0); color: white; font-weight: 600;'
        elif grade < 0:
            # Negative: red gradient from light to dark red
            # Scale from -30 to 0, creating a smooth gradient
            intensity = min(abs(grade) / 30.0, 1.0)
            # Red gradient: 180 (light red) to 100 (dark red)
            # More negative = darker red
            red_value = int(180 - (80 * intensity))
            red_value = max(100, red_value)
            return f'background-color: rgb({red_value}, 0, 0); color: white; font-weight: 600;'
        else:
            # Zero: light gray/neutral
            return 'background-color: rgb(240, 240, 240); color: black; font-weight: 600;'
    except:
        return ''

st.set_page_config(page_title="Bet Analysis Dashboard", layout="wide")

st.title("Bet Correlation Analysis Dashboard")
st.markdown("Analyzing relationship between Risk, Grades, and Results")

# Load data
def load_data_dataframe(file_source):
    """Load and clean data from file source (path or file-like object)"""
    df = pd.read_csv(file_source)
    
    # Convert date to datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    
    # Remove rows where risk or grade is null
    if 'risk' in df.columns and 'grade' in df.columns:
        df = df.dropna(subset=['risk', 'grade'])
        
        # Filter grades to [-30, 100]
        df = df[(df['grade'] >= -30) & (df['grade'] <= 100)]
    
    return df

# Try to load data from file first, with file uploader as fallback
df = None

# Check if file exists locally
import os
if os.path.exists('combined.csv'):
    try:
        df = load_data_dataframe('combined.csv')
    except Exception as e:
        st.error(f"Error loading combined.csv: {e}")
        df = None

# If no data loaded, show file uploader
if df is None:
    st.error("### ⚠️ Data file not found")
    st.markdown("""
    The `combined.csv` file was not found. Please upload the file using the file uploader below.
    """)
    
    uploaded_file = st.file_uploader(
        "Upload combined.csv",
        type=['csv'],
        help="Upload your combined.csv file to analyze"
    )
    
    if uploaded_file is not None:
        try:
            df = load_data_dataframe(uploaded_file)
            st.success("✅ File loaded successfully!")
        except Exception as e:
            st.error(f"Error loading uploaded file: {e}")
            st.stop()
    else:
        st.info("Please upload a CSV file to continue.")
        st.stop()

# Ensure df is not None for rest of app
if df is None or len(df) == 0:
    st.warning("No data available. Please upload combined.csv file.")
    st.stop()

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
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("R²", f"{r_squared:.4f}")
        col2.metric("Slope", f"{slope:.6f}")
        col3.metric("P-value", f"{p_value:.4f}" if p_value < 0.0001 else f"{p_value:.6f}")
        
        # Risk of Adverse Selection: Strong if p-value is significant, Low if not
        is_significant = p_value < 0.05
        adverse_risk = "Strong" if is_significant else "Low"
        
        # Display with colored text only (matching other metrics style)
        with col4:
            risk_color = "#ff4444" if is_significant else "#44ff44"  # Red for Strong, Green for Low
            st.markdown(
                f'<div style="font-size: 0.8rem; color: #888; margin-bottom: 0.25rem;">Risk of Adverse Selection</div>'
                f'<div style="font-size: 1.75rem; font-weight: 600; color: {risk_color};">{adverse_risk}</div>',
                unsafe_allow_html=True
            )
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
    bucket_size = st.sidebar.slider("Risk Bucket Size ($)", min_value=50, max_value=500, value=500, step=50)
    
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
    })
    
    # Reset index and rename
    bucket_stats = bucket_stats.reset_index()
    bucket_stats = bucket_stats.rename(columns={'risk_bucket_label': 'Bucket', 'grade': 'Avg Grade', 'risk': 'Total Risk', 'result': 'Total Result'})
    
    # Round columns: avg grade to 1 decimal, risk and result to 0 decimals
    bucket_stats['Avg Grade'] = bucket_stats['Avg Grade'].round(1)
    bucket_stats['Total Risk'] = bucket_stats['Total Risk'].round(0).astype(int)
    bucket_stats['Total Result'] = bucket_stats['Total Result'].round(0).astype(int)
    
    # Calculate ROI (result/risk) as percentage, rounded to 1 decimal
    bucket_stats['ROI'] = (bucket_stats['Total Result'] / bucket_stats['Total Risk'] * 100).round(1)
    
    # Format ROI as percentage with % sign
    bucket_stats['ROI'] = bucket_stats['ROI'].apply(lambda x: f"{x:.1f}%")
    
    # Reorder columns: bucket, avg grade, total risk, total result, roi (Count removed)
    bucket_stats = bucket_stats[['Bucket', 'Avg Grade', 'Total Risk', 'Total Result', 'ROI']]
    
    # Sort by numeric bucket value (extract the first number from bucket label like "$0 - $499")
    bucket_stats = bucket_stats.copy()
    bucket_stats['_sort_key'] = bucket_stats['Bucket'].str.extract(r'\$(\d+)').astype(int)
    bucket_stats = bucket_stats.sort_values('_sort_key').drop('_sort_key', axis=1).reset_index(drop=True)
    
    # Display table with color shading for Avg Grade
    styled_bucket_stats = bucket_stats.style.applymap(
        style_grades,
        subset=['Avg Grade']
    )
    st.dataframe(
        styled_bucket_stats,
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
    
    # Bar chart of average grade by bucket
    st.markdown("### Average Grade by Risk Bucket")
    
    # Create bar chart with average grades
    fig_bar = px.bar(
        bucket_stats,
        x='Bucket',
        y='Avg Grade',
        title='Average Grade by Risk Bucket',
        labels={'Bucket': 'Risk Bucket', 'Avg Grade': 'Average Grade'},
        height=500,
        color='Avg Grade',
        color_continuous_scale=['red', 'yellow', 'green']  # Red to green scale
    )
    
    fig_bar.update_layout(
        xaxis_title='Risk Bucket',
        yaxis_title='Average Grade',
        showlegend=False,
        coloraxis_colorbar=dict(title="Avg Grade")
    )
    
    # Update bar colors based on positive/negative
    colors = ['red' if x < 0 else 'green' for x in bucket_stats['Avg Grade']]
    fig_bar.update_traces(marker_color=colors)
    
    st.plotly_chart(fig_bar, use_container_width=True)
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
    })
    
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
    
    # Round columns: avg grade to 1 decimal, risk and result to 0 decimals
    dynamic_stats['Avg Grade'] = dynamic_stats['Avg Grade'].round(1)
    dynamic_stats['Total Risk'] = dynamic_stats['Total Risk'].round(0).astype(int)
    dynamic_stats['Total Result'] = dynamic_stats['Total Result'].round(0).astype(int)
    
    # Calculate ROI (result/risk) as percentage, rounded to 1 decimal
    dynamic_stats['ROI'] = (dynamic_stats['Total Result'] / dynamic_stats['Total Risk'] * 100).round(1)
    
    # Format ROI as percentage with % sign
    dynamic_stats['ROI'] = dynamic_stats['ROI'].apply(lambda x: f"{x:.1f}%")
    
    # Reorder columns: dynamic, count, avg grade, total risk, total result, roi
    dynamic_stats = dynamic_stats[['Dynamic', 'Count', 'Avg Grade', 'Total Risk', 'Total Result', 'ROI']]
    
    # Sort by total risk
    dynamic_stats = dynamic_stats.sort_values('Total Risk', ascending=False)
    
    # Display table with color shading for Avg Grade
    styled_dynamic_stats = dynamic_stats.style.applymap(
        style_grades,
        subset=['Avg Grade']
    )
    st.dataframe(
        styled_dynamic_stats,
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
    # Apply color shading to grade column if it exists
    if 'grade' in df.columns:
        styled_df = df.style.applymap(
            style_grades,
            subset=['grade']
        )
        st.dataframe(styled_df, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)
    
    # Download filtered data
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Filtered Data as CSV",
        data=csv,
        file_name="filtered_combined_data.csv",
        mime="text/csv"
    )

