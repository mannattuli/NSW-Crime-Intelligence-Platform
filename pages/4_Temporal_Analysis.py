import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils import load_processed_crime_data

st.set_page_config(page_title="Trend Analysis", page_icon="📈", layout="wide")
st.title("📈 Trend Analysis Dashboard")
st.write("Analyze historical crime trends over time to identify weekly, seasonal, and long-term patterns.")

crime_df = load_processed_crime_data()

if crime_df.empty:
    st.error("Could not load temporal crime data.")
else:
    crime_df['Year'] = crime_df['Date'].dt.year
    crime_df['Month'] = crime_df['Date'].dt.month_name()
    crime_df['DayOfWeek'] = crime_df['Date'].dt.day_name()

    st.sidebar.header("🗓️ Temporal Filters")
    suburbs = sorted(crime_df['Suburb'].unique())
    offence_categories = sorted(crime_df['OffenceCategory'].unique())

    selected_suburb = st.sidebar.selectbox("Select a Suburb", options=suburbs)
    selected_offence = st.sidebar.selectbox("Select an Offence Category", options=offence_categories)

    filtered_df = crime_df[
        (crime_df['Suburb'] == selected_suburb) &
        (crime_df['OffenceCategory'] == selected_offence)
    ]

    if filtered_df.empty:
        st.warning(f"No '{selected_offence}' data found for {selected_suburb}.")
    else:
        st.success(f"Displaying analysis for **{selected_offence}** in **{selected_suburb}**.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Incidents by Day of the Week")
            day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_df = filtered_df.groupby('DayOfWeek')['Incidents'].sum().reindex(day_order).reset_index()
            fig_day = px.bar(day_df, x='DayOfWeek', y='Incidents', title="Weekly Crime Rhythm")
            st.plotly_chart(fig_day, use_container_width=True)

        with col2:
            st.subheader("Incidents by Month")
            month_order = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            month_df = filtered_df.groupby('Month')['Incidents'].sum().reindex(month_order).reset_index()
            fig_month = px.bar(month_df, x='Month', y='Incidents', title="Seasonal Crime Variation")
            st.plotly_chart(fig_month, use_container_width=True)

        st.subheader("Long-Term Trend by Year")
        year_df = filtered_df.groupby('Year')['Incidents'].sum().reset_index()
        fig_year = px.line(year_df, x='Year', y='Incidents', title="Annual Trend", markers=True)
        st.plotly_chart(fig_year, use_container_width=True)
