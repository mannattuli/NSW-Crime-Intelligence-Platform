import streamlit as st
import pandas as pd
import plotly.express as px
from src.utils import load_master_data

st.set_page_config(
    page_title="NSW Crime Insights Lab",
    page_icon="📡",
    layout="wide"
)

st.title("📡 NSW Crime Insights Lab")
st.caption("A decision-support tool for analyzing historical crime patterns.")

master_df = load_master_data()

if master_df is not None and not master_df.empty:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🚨 Key Anomaly Alerts")
        with st.container(border=True):
            latest_year = master_df['Year'].max()
            baseline_year_start = latest_year - 3
            
            historical_df = master_df[(master_df['Year'] >= baseline_year_start) & (master_df['Year'] < latest_year)]
            current_year_df = master_df[master_df['Year'] == latest_year]
            
            crime_cols = [col for col in master_df.columns if col not in ['Suburb', 'Year', 'Suburb_Clean', 'Suburb_For_Join', 'geometry', 'Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount']]
            
            stats = historical_df.groupby('Suburb')[crime_cols].agg(['mean', 'std']).reset_index()
            stats.columns = ['_'.join(col).strip() for col in stats.columns.values]
            
            merged_df = pd.merge(current_year_df, stats, left_on='Suburb', right_on='Suburb_', how='left')

            alerts = []
            for crime in crime_cols:
                mean_col, std_col = f'{crime}_mean', f'{crime}_std'
                merged_df['z_score'] = (merged_df[crime] - merged_df[mean_col]).divide(merged_df[std_col].replace(0, pd.NA)).fillna(0)
                anomalies = merged_df[(merged_df['z_score'] > 2.5) & (merged_df[crime] > 5)]
                for _, row in anomalies.iterrows():
                    alerts.append((row['z_score'], f"**{row['Suburb']}** is a hotspot for **{crime}** ({int(row[crime])} incidents vs. avg of {row[mean_col]:.1f})"))
            
            alerts.sort(key=lambda x: x[0], reverse=True)
            if alerts:
                for _, alert_text in alerts[:5]:
                    st.warning(alert_text)
            else:
                st.info("No significant anomalies found in the latest data.")
            st.caption(f"Showing top 5 of {len(alerts)} anomalies for {latest_year} vs. the {baseline_year_start}-{latest_year-1} average.")

    with col2:
        st.subheader("🔥 Top 5 Crime Hotspots")
        with st.container(border=True):
            latest_year_df = master_df[master_df['Year'] == master_df['Year'].max()]
            most_common_crime = latest_year_df[crime_cols].sum().idxmax()
            
            top_5_suburbs = latest_year_df.nlargest(5, most_common_crime)
            
            st.info(f"Displaying top 5 hotspots for **{most_common_crime}** in {latest_year}.")
            st.dataframe(top_5_suburbs[['Suburb', most_common_crime]].rename(columns={most_common_crime: 'Incidents'}), hide_index=True)
            st.caption("Go to the 'Geospatial Insights' page for a full interactive map.")

    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("📈 Major Crime Trends (NSW)")
        with st.container(border=True):
            top_3_crimes = master_df[crime_cols].sum().nlargest(3).index.tolist()
            trend_df = master_df.groupby('Year')[top_3_crimes].sum().reset_index()
            
            trend_chart = px.line(trend_df, x='Year', y=top_3_crimes, title="Annual Trend for Top 3 Crimes", markers=True)
            trend_chart.update_layout(margin={"r":10,"t":40,"l":10,"b":10}, height=350)
            st.plotly_chart(trend_chart, use_container_width=True)
            st.caption("Go to the 'Trend Analysis' page for more detail.")

    with col4:
        st.subheader("🔗 Strongest Insight")
        with st.container(border=True):
            latest_year_df = master_df[master_df['Year'] == master_df['Year'].max()]
            socio_metrics = [col for col in ['Index of Economic Resources', 'VenueCount'] if col in latest_year_df.columns]
            
            strongest_corr = 0
            best_pair = (None, None)
            
            for s_metric in socio_metrics:
                for c_metric in crime_cols:
                    corr = latest_year_df[s_metric].corr(latest_year_df[c_metric])
                    if abs(corr) > abs(strongest_corr):
                        strongest_corr = corr
                        best_pair = (s_metric, c_metric)

            if best_pair[0]:
                st.metric(label=f"Strongest Correlation in {latest_year}", value=f"{strongest_corr:.3f}")
                st.info(f"The strongest link found was between **{best_pair[0]}** and **{best_pair[1]}**.")
                st.caption("Go to the 'Correlation Lab' page to investigate further.")
            else:
                st.info("No strong correlations found in the latest data.")
else:
    st.error("Could not load master data. Please ensure you have run the data processing scripts (`process_data.py` and `fuse_data.py`) in your project folder.")

