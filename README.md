# NSW-Crime Intelligence Platform

An interactive platform for analyzing and forecasting crime patterns in NSW by fusing crime, geospatial, and socio-economic data.

---

## Features

- **Mission Control:** An executive dashboard with automated alerts and key insights.
- **Crime Hotspot Map:** An interactive geospatial map for visualizing crime hotspots.
- **Temporal Analysis:** Tools to find weekly, seasonal, and yearly crime trends.
- **Forecasting Lab:** A machine learning model to predict future crime incidents.
- **Correlation Lab:** An investigative tool to find relationships between crime and socio-economic factors.

## How to Run

1.  **Clone the repo.**
2.  **Create a virtual environment and install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Acquire Data:** Download the required raw data files from the official sources listed below.
4.  **Run the data pipeline:**
    ```bash
    python process_data.py
    python fuse_data.py
    ```
5.  **Launch the app:**
    ```bash
    streamlit run Mission_Control.py
    ```

---

## Data Sources

This platform utilizes publicly available data from the following official sources:

- **Crime Data:** [NSW Bureau of Crime Statistics and Research (BOCSAR)](https://www.bocsar.nsw.gov.au/Pages/bocsar_crime_stats/bocsar_crime_stats.aspx)
- **Geospatial & Socio-Economic Data:** [Australian Bureau of Statistics (ABS)](https://www.abs.gov.au/)
- **Licensed Venues Data:** [Data.NSW](https://data.nsw.gov.au/data/dataset/)
