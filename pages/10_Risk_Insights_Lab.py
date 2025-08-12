import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from pathlib import Path
from datetime import datetime
import pytz

# --- Page Config ---
st.set_page_config(page_title="Risk Engine", page_icon="🛡️", layout="wide")

# --- Data Loading ---
@st.cache_data
def load_risk_grid():
    """Loads the pre-computed risk grid data."""
    project_root = Path(__file__).parent.parent
    data_file_path = project_root / "risk_grid.parquet"
    try:
        return pd.read_parquet(data_file_path)
    except FileNotFoundError:
        return None

# --- Main App ---
st.title("🛡️ Live Address-Specific Risk Engine")
st.write("A decision-support tool to analyze location-based risk, combining historical data with live temporal factors.")

risk_grid = load_risk_grid()

if risk_grid is None:
    st.error("Risk grid data not found. Please run `precompute_risk.py` locally first.")
else:
    address_input = st.text_input("Enter a specific address in NSW (e.g., 44 Bridge St, Sydney):", "44 Bridge St, Sydney NSW 2000")

    if st.button("Assess Live Risk"):
        geolocator = Nominatim(user_agent="nsw_crime_risk_app", timeout=10)
        try:
            location = geolocator.geocode(address_input)
            if location:
                lat, lon = location.latitude, location.longitude
                
                cell = risk_grid[
                    (lon >= risk_grid['min_lon']) & (lon < risk_grid['max_lon']) &
                    (lat >= risk_grid['min_lat']) & (lat < risk_grid['max_lat'])
                ]

                if not cell.empty:
                    # --- Risk Calculation (Final, More Nuanced Model) ---
                    historical_crime_risk = cell['CrimeRisk'].iloc[0]
                    venue_proximity_risk = cell['VenueRisk'].iloc[0]
                    
                    sydney_tz = pytz.timezone('Australia/Sydney')
                    now = datetime.now(sydney_tz)
                    st.info(f"Analysis based on current time: **{now.strftime('%A, %I:%M %p')}**")
                    
                    # --- UPGRADED LOGIC: More Granular Temporal Factors ---
                    temporal_risk_bonus = 0.0
                    temporal_reasons = []
                    
                    # Define risk periods
                    is_peak_weekend_night = (now.weekday() in [4, 5]) and (22 <= now.hour or now.hour <= 3) # Fri/Sat 10pm-3am
                    is_standard_night = (20 <= now.hour or now.hour <= 4) and not is_peak_weekend_night
                    is_evening_rush = 16 <= now.hour < 19

                    if is_peak_weekend_night:
                        temporal_risk_bonus += 2.5
                        temporal_reasons.append("It is a **peak weekend night**, a period with the highest historical risk.")
                    elif is_standard_night:
                        temporal_risk_bonus += 1.0
                        temporal_reasons.append("It is currently **late night**, a period with an elevated baseline risk.")
                    
                    if is_evening_rush:
                        temporal_risk_bonus += 0.5
                        temporal_reasons.append("It is the **evening rush hour**, which can see a slight increase in opportunistic crime.")

                    base_risk = (historical_crime_risk * 0.7) + (venue_proximity_risk * 0.3)
                    final_risk_score = min(base_risk + temporal_risk_bonus, 10.0)
                    # --- END OF UPGRADED LOGIC ---

                    # --- Display Results ---
                    st.subheader(f"Live Risk Assessment for: {location.address}")
                    
                    color = "green"
                    if final_risk_score > 6.5: color = "red"
                    elif final_risk_score > 4: color = "orange"
                    
                    st.metric(
                        label="Live Risk Score", 
                        value=f"{final_risk_score:.1f} / 10",
                        delta=f"{'High' if color=='red' else 'Moderate' if color=='orange' else 'Low'} Risk",
                        delta_color="inverse"
                    )

                    with st.container(border=True):
                        st.markdown("##### Contributing Factors:")
                        st.markdown(f"- **Historical Crime Density:** `{historical_crime_risk:.1f}/10` (The baseline risk for this specific location based on past incidents)")
                        st.markdown(f"- **Venue Proximity Density:** `{venue_proximity_risk:.1f}/10` (The influence of nearby licensed venues)")
                        st.markdown("##### Live Temporal Factors:")
                        if temporal_reasons:
                            for reason in temporal_reasons:
                                st.markdown(f"- {reason}")
                        else:
                            st.markdown("- No significant temporal risk factors at this time (e.g., standard business hours).")
                    
                    # --- NEW: Explanation Section ---
                    with st.expander("How is this score calculated?"):
                        st.markdown("""
                        The Live Risk Score is a composite index designed for decision support. It's calculated by:
                        1.  **Establishing a Base Risk:** We create a weighted average of the historical crime density and the density of nearby licensed venues for the selected location.
                        2.  **Applying a Temporal Bonus:** We then add a risk bonus based on the current time and day. A late night on a Saturday carries a much higher bonus than a Tuesday afternoon.
                        3.  **Final Score:** The final score is the sum of the base risk and the temporal bonus, capped at 10. This provides a snapshot of the location's risk profile right now, relative to other areas and times.
                        """)

                else:
                    st.warning("Location is outside the primary analysis grid (Greater Sydney).")
            else:
                st.error("Could not find the address.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
