import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from src.utils import load_master_data

st.set_page_config(page_title="Correlation Lab", page_icon="🔗", layout="wide")

# Analyzes correlation strength and flags high-residual outliers.
def generate_insights(dataframe, x_col, y_col):
    insights = []
    
    correlation = dataframe[x_col].corr(dataframe[y_col])
    corr_strength = "weak"
    if abs(correlation) > 0.7: corr_strength = "very strong"
    elif abs(correlation) > 0.4: corr_strength = "strong"
    elif abs(correlation) > 0.2: corr_strength = "moderate"
    corr_direction = "positive" if correlation > 0 else "negative"

    if corr_strength != "weak":
        insights.append(f"🔎 **Strong Correlation Found:** There is a **{corr_strength} {corr_direction} correlation** ({correlation:.2f}) between {x_col} and {y_col}.")
    else:
        insights.append(f"🔎 **Weak Correlation Found:** There appears to be no significant correlation ({correlation:.2f}) between {x_col} and {y_col}.")

    model = np.polyfit(dataframe[x_col], dataframe[y_col], 1)
    predict = np.poly1d(model)
    dataframe['residuals'] = dataframe[y_col] - predict(dataframe[x_col])
    
    outliers_high = dataframe.nlargest(2, 'residuals')
    for _, row in outliers_high.iterrows():
        insights.append(f"❗ **Key Outlier (High):** **{row['Suburb']}** shows a much higher rate of **{y_col}** than its level of **{x_col}** would predict.")

    return insights

st.title("🔗 Correlation Lab")
st.write("Investigate relationships between crime and socio-economic factors. Each point on the chart is a suburb.")

master_df = load_master_data()

if master_df.empty:
    st.error("Master data file is empty or not found.")
else:
    st.sidebar.header("🔬 Lab Controls")
    all_cols = master_df.columns.tolist()
    socio_metrics = [col for col in ['Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount'] if col in all_cols]
    crime_metrics = [col for col in all_cols if col not in socio_metrics and col not in ['Suburb', 'Year']]
    available_years = sorted(master_df['Year'].unique(), reverse=True)

    if available_years:
        selected_year = st.sidebar.slider("Select Year to Analyze:", min_value=min(available_years), max_value=max(available_years), value=max(available_years))
        x_axis = st.sidebar.selectbox("Select X-Axis (Socio-Economic Factor):", options=socio_metrics)
        y_axis = st.sidebar.selectbox("Select Y-Axis (Crime Factor):", options=crime_metrics)
        
        year_df = master_df[master_df['Year'] == selected_year].copy()

        st.header(f"Analysis for {selected_year}")

        if year_df.empty or y_axis not in year_df.columns:
            st.warning(f"No data for '{y_axis}' in {selected_year}.")
        else:
            st.subheader("Automated Insights")
            with st.container(border=True):
                insights = generate_insights(year_df, x_axis, y_axis)
                for insight in insights:
                    st.markdown(f"- {insight}")
            
            st.subheader(f"Interactive Plot: {y_axis} vs. {x_axis}")
            correlation_fig = px.scatter(
                year_df, x=x_axis, y=y_axis,
                hover_name='Suburb',
                trendline="ols",
                title=f"{y_axis} vs. {x_axis} ({selected_year})",
                template='plotly_white'
            )
            st.plotly_chart(correlation_fig, use_container_width=True)
