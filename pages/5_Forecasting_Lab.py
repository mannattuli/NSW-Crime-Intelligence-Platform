import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from src.utils import load_master_data

st.set_page_config(page_title="Forecasting Lab", page_icon="🔮", layout="wide")
st.title("🔮 Trend Forecasting Lab")
st.write("This tool uses a simple linear regression model to forecast potential future trends based on historical data. This is for analytical purposes and is not a guarantee of future outcomes.")

master_df = load_master_data()

if master_df.empty:
    st.error("Master data file is empty or not found.")
else:
    st.sidebar.header("🔬 Forecasting Parameters")
    suburbs = sorted(master_df['Suburb'].unique())
    crime_metrics = [col for col in master_df.columns if col not in ['Suburb', 'Year', 'Suburb_Clean', 'Suburb_For_Join', 'geometry', 'Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount']]

    selected_suburb = st.sidebar.selectbox("Select a Suburb to Forecast:", options=suburbs)
    selected_offence = st.sidebar.selectbox("Select an Offence Category to Forecast:", options=crime_metrics)

    st.header(f"Forecast for '{selected_offence}' in {selected_suburb}")

    time_series_df = master_df[['Year', 'Suburb', selected_offence]].copy()
    time_series_df = time_series_df[time_series_df['Suburb'] == selected_suburb]
    time_series_df['Date'] = pd.to_datetime(time_series_df['Year'].astype(str) + '-12-31')

    if len(time_series_df) < 3:
        st.warning("Not enough historical data points (<3 years) to create a reliable forecast.")
    else:
        time_series_df['TimeIndex'] = (time_series_df['Date'] - time_series_df['Date'].min()).dt.days
        
        X_train = time_series_df[['TimeIndex']]
        y_train = time_series_df[selected_offence]

        model = LinearRegression()
        model.fit(X_train, y_train)

        last_date = time_series_df['Date'].max()
        future_dates = pd.date_range(start=last_date + pd.DateOffset(years=1), periods=3, freq='A-DEC')
        future_time_index = (future_dates - time_series_df['Date'].min()).days.values.reshape(-1, 1)
        future_predictions = model.predict(future_time_index)
        future_predictions[future_predictions < 0] = 0

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time_series_df['Date'], y=y_train, mode='lines+markers', name='Historical Incidents'))
        fig.add_trace(go.Scatter(x=time_series_df['Date'], y=model.predict(X_train), mode='lines', name='Learned Trend', line={'dash': 'dot'}))
        fig.add_trace(go.Scatter(x=future_dates, y=future_predictions, mode='lines+markers', name='Forecast (3 Years)', line={'color': 'red'}))
        
        st.plotly_chart(fig, use_container_width=True)