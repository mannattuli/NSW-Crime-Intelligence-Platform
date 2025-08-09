import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# --- Page Config ---
st.set_page_config(page_title="Correlation Lab", page_icon="🔗", layout="wide")

# --- Data Loading ---
@st.cache_data
# Loads the fused master analytics dataset for correlation analysis.
def load_fused_data():
    try:
        master_analytics_dataframe = pd.read_parquet('master_analytics_data.parquet')
        return master_analytics_dataframe
    except FileNotFoundError:
        return pd.DataFrame()

# --- NEW: Automated Interpretation Function ---
def generate_insights(analysis_dataframe, x_axis_column_name, y_axis_column_name):
    # Analyzes correlation strength and flags high-residual outliers for the selected year.
    insights = []
    
    # 1. Analyze the correlation strength
    correlation = analysis_dataframe[x_axis_column_name].corr(analysis_dataframe[y_axis_column_name])
    corr_strength = "weak"
    if abs(correlation) > 0.7:
        corr_strength = "very strong"
    elif abs(correlation) > 0.4:
        corr_strength = "strong"
    elif abs(correlation) > 0.2:
        corr_strength = "moderate"

    corr_direction = "positive" if correlation > 0 else "negative"

    if corr_strength != "weak":
        insights.append(f"🔎 **Strong Correlation Found:** There is a **{corr_strength} {corr_direction} correlation** ({correlation:.2f}) between {x_axis_column_name} and {y_axis_column_name}. This suggests a significant link between the two.")
    else:
        insights.append(f"🔎 **Weak Correlation Found:** There appears to be no significant correlation ({correlation:.2f}) between {x_axis_column_name} and {y_axis_column_name}.")

    # 2. Find the biggest outliers from the trendline
    linear_fit_model = np.polyfit(analysis_dataframe[x_axis_column_name], analysis_dataframe[y_axis_column_name], 1)
    linear_predictor_function = np.poly1d(linear_fit_model)
    analysis_dataframe['residuals'] = analysis_dataframe[y_axis_column_name] - linear_predictor_function(analysis_dataframe[x_axis_column_name])
    
    # Find the top 2 positive outliers (much higher crime than predicted)
    high_residuals_suburbs_dataframe = analysis_dataframe.nlargest(2, 'residuals')
    for _, suburb_row in high_residuals_suburbs_dataframe.iterrows():
        insights.append(f"❗ **Key Outlier (High):** **{suburb_row['Suburb']}** shows a much higher rate of **{y_axis_column_name}** than its level of **{x_axis_column_name}** would predict.")

    return insights

# --- Main App ---
st.title("🔗 Correlation Lab")
st.write("Investigate relationships between crime and socio-economic factors. Each point on the chart is a suburb.")

master_analytics_dataframe = load_fused_data()

if master_analytics_dataframe.empty:
    st.error("Master data file is empty or not found. Please run `fuse_data.py` successfully first.")
else:
    # --- Sidebar Filters ---
    st.sidebar.header("🔬 Lab Controls")
    all_columns = master_analytics_dataframe.columns.tolist()
    socio_economic_metric_columns = [column_name for column_name in ['Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount'] if column_name in all_columns]
    crime_metric_columns = [column_name for column_name in all_columns if column_name not in socio_economic_metric_columns and column_name not in ['Suburb', 'Year']]
    available_years = sorted(master_analytics_dataframe['Year'].unique(), reverse=True)

    if available_years:
        selected_year = st.sidebar.slider("Select Year to Analyze:", min_value=min(available_years), max_value=max(available_years), value=max(available_years))
        x_axis = st.sidebar.selectbox("Select X-Axis (Socio-Economic Factor):", options=socio_economic_metric_columns)
        y_axis = st.sidebar.selectbox("Select Y-Axis (Crime Factor):", options=crime_metric_columns)
        
        selected_year_dataframe = master_analytics_dataframe[master_analytics_dataframe['Year'] == selected_year].copy()

        st.header(f"Analysis for {selected_year}")

        if selected_year_dataframe.empty or y_axis not in selected_year_dataframe.columns:
            st.warning(f"No data for '{y_axis}' in {selected_year}.")
        else:
            # --- NEW: Display Automated Insights ---
            st.subheader("Automated Insights")
            with st.container(border=True):
                insights = generate_insights(selected_year_dataframe, x_axis, y_axis)
                for insight in insights:
                    st.markdown(f"- {insight}")
            
            # --- The Chart ---
            st.subheader(f"Interactive Plot: {y_axis} vs. {x_axis}")
            correlation_scatter_chart = px.scatter(
                selected_year_dataframe, x=x_axis, y=y_axis,
                hover_name='Suburb',
                trendline="ols",
                title=f"{y_axis} vs. {x_axis} ({selected_year})",
                template='plotly_white'
            )
            st.plotly_chart(correlation_scatter_chart, use_container_width=True)