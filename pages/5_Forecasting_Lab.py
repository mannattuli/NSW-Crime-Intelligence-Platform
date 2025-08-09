# pages/4_Forecasting_Lab.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression

# --- Page Config ---
st.set_page_config(page_title="Forecasting Lab", page_icon="🔮", layout="wide")

# --- Data Loading ---
@st.cache_data
# Loads the processed crime data used for forecasting tasks.
def load_forecasting_dataset(file_path='crime_data_processed.parquet'):
    forecasting_source_dataframe = pd.read_parquet(file_path)
    return forecasting_source_dataframe

# --- Main App ---
st.title("🔮 Crime Forecasting Lab")
st.write("Use historical data to train a simple model and forecast future crime trends.")

forecasting_source_dataframe = load_forecasting_dataset()

# --- Sidebar Filters ---
st.sidebar.header("🔬 Forecasting Parameters")
suburbs = sorted(forecasting_source_dataframe['Suburb'].unique())
offence_categories = sorted(forecasting_source_dataframe['OffenceCategory'].unique())

selected_suburb = st.sidebar.selectbox("Select a Suburb to Forecast:", options=suburbs, index=suburbs.index('Sydney'))
selected_offence = st.sidebar.selectbox("Select an Offence Category to Forecast:", options=offence_categories, index=offence_categories.index('Theft'))

# --- Model Training and Forecasting ---
st.header(f"Forecast for '{selected_offence}' in {selected_suburb}")

# Isolate the specific time series for the user's selection
suburb_offence_timeseries_dataframe = forecasting_source_dataframe[
    (forecasting_source_dataframe['Suburb'] == selected_suburb) &
    (forecasting_source_dataframe['OffenceCategory'] == selected_offence)
].copy()

# Ensure we have enough data to model
if len(suburb_offence_timeseries_dataframe) < 12:
    st.warning("Not enough historical data points (<12 months) to create a reliable forecast.")
else:
    # --- Feature Engineering ---
    # The model needs a numerical representation of time
    suburb_offence_timeseries_dataframe['TimeIndex'] = (suburb_offence_timeseries_dataframe['Date'] - suburb_offence_timeseries_dataframe['Date'].min()).dt.days
    
    # --- Model Training ---
    # X is our feature (time), y is our target (incidents)
    time_index_feature_dataframe = suburb_offence_timeseries_dataframe[['TimeIndex']]
    incidents_target_series = suburb_offence_timeseries_dataframe['Incidents']

    # We use a simple Linear Regression model to find the trend
    trend_regression_model = LinearRegression()
    trend_regression_model.fit(time_index_feature_dataframe, incidents_target_series)

    # --- Forecasting ---
    # Create future dates for the next 12 months
    last_observed_date = suburb_offence_timeseries_dataframe['Date'].max()
    forecast_horizon_dates = pd.date_range(start=last_observed_date + pd.DateOffset(months=1), periods=12, freq='M')
    
    # Create future time index for prediction
    forecast_horizon_time_index = (forecast_horizon_dates - suburb_offence_timeseries_dataframe['Date'].min()).days.values.reshape(-1, 1)

    # Make predictions for the future
    forecast_incident_predictions_array = trend_regression_model.predict(forecast_horizon_time_index)
    forecast_incident_predictions_array[forecast_incident_predictions_array < 0] = 0 

    # --- Visualization ---
    forecasting_chart = go.Figure()

    # 1. Add historical data
    forecasting_chart.add_trace(go.Scatter(x=suburb_offence_timeseries_dataframe['Date'], y=suburb_offence_timeseries_dataframe['Incidents'], mode='lines', name='Historical Incidents'))
    
    # 2. Add the model's trend line over the historical data
    forecasting_chart.add_trace(go.Scatter(x=suburb_offence_timeseries_dataframe['Date'], y=trend_regression_model.predict(time_index_feature_dataframe), mode='lines', name='Learned Trend', line={'dash': 'dot'}))

    # 3. Add the forecasted data
    forecasting_chart.add_trace(go.Scatter(x=forecast_horizon_dates, y=forecast_incident_predictions_array, mode='lines', name='Forecasted Trend', line={'color': 'red'}))
    
    st.plotly_chart(forecasting_chart, use_container_width=True)