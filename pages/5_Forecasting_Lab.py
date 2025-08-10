import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from src.utils import load_master_data

# --- Page Config ---
st.set_page_config(page_title="Forecasting Lab", page_icon="🔮", layout="wide")

# --- Main App ---
st.title("🔮 Crime Forecasting Lab")
st.write("Use historical data to train a simple model and forecast future crime trends.")

# Use the central function to load the master dataset
master_df = load_master_data()

if master_df.empty:
    st.error("Master data file is empty or not found.")
else:
    # --- Sidebar Filters ---
    st.sidebar.header("🔬 Forecasting Parameters")
    suburbs = sorted(master_df['Suburb'].unique())
    # Dynamically find the crime columns for the dropdown
    crime_metrics = [col for col in master_df.columns if col not in ['Suburb', 'Year', 'Suburb_Clean', 'Suburb_For_Join', 'geometry', 'Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount']]

    selected_suburb = st.sidebar.selectbox("Select a Suburb to Forecast:", options=suburbs)
    selected_offence = st.sidebar.selectbox("Select an Offence Category to Forecast:", options=crime_metrics)

    # --- Model Training and Forecasting ---
    st.header(f"Forecast for '{selected_offence}' in {selected_suburb}")

    # Isolate the specific time series for the user's selection
    time_series_df = master_df[['Year', 'Suburb', selected_offence]].copy()
    time_series_df = time_series_df[time_series_df['Suburb'] == selected_suburb]
    # Create a proper date for plotting
    time_series_df['Date'] = pd.to_datetime(time_series_df['Year'].astype(str) + '-12-31') 

    if len(time_series_df) < 3: # Need at least 3 data points for a trend
        st.warning("Not enough historical data points (<3 years) to create a reliable forecast.")
    else:
        # --- Feature Engineering ---
        time_series_df['TimeIndex'] = (time_series_df['Date'] - time_series_df['Date'].min()).dt.days
        
        # --- Model Training ---
        X_train = time_series_df[['TimeIndex']]
        y_train = time_series_df[selected_offence]

        model = LinearRegression()
        model.fit(X_train, y_train)

        # --- Forecasting ---
        last_date = time_series_df['Date'].max()
        # Forecast for the next 3 years
        future_dates = pd.date_range(start=last_date + pd.DateOffset(years=1), periods=3, freq='A-DEC')
        future_time_index = (future_dates - time_series_df['Date'].min()).days.values.reshape(-1, 1)
        future_predictions = model.predict(future_time_index)
        future_predictions[future_predictions < 0] = 0 

        # --- Visualization ---
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=time_series_df['Date'], y=y_train, mode='lines+markers', name='Historical Incidents'))
        fig.add_trace(go.Scatter(x=time_series_df['Date'], y=model.predict(X_train), mode='lines', name='Learned Trend', line={'dash': 'dot'}))
        fig.add_trace(go.Scatter(x=future_dates, y=future_predictions, mode='lines+markers', name='Forecast (3 Years)', line={'color': 'red'}))
        
        st.plotly_chart(fig, use_container_width=True)