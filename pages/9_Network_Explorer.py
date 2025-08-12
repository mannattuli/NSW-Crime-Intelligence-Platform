
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
from src.utils import load_master_data

st.set_page_config(page_title="Network Explorer", page_icon="🕸️", layout="wide")
st.title("🕸️ Crime Network Explorer")
st.write("Discover hidden relationships between different types of crime. This tool uses a force-directed layout to visualize which offences tend to occur together.")

master_df = load_master_data()

if master_df.empty:
    st.error("Master data file not found.")
else:
    st.sidebar.header("🕸️ Network Controls")
    
    crime_cols = [col for col in master_df.columns if col not in ['Suburb', 'Year', 'Suburb_Clean', 'Suburb_For_Join', 'geometry', 'Index of Relative Socio-economic Advantage and Disadvantage', 'Index of Economic Resources', 'Index of Education and Occupation', 'VenueCount']]
    
    selected_crime = st.sidebar.selectbox("Select a Central Crime to Analyze:", options=crime_cols, index=crime_cols.index('Theft') if 'Theft' in crime_cols else 0)
    correlation_threshold = st.sidebar.slider("Correlation Strength Threshold:", 0.1, 1.0, 0.3, 0.05, help="Only show connections stronger than this value.")

    st.header(f"Network of Crimes Related to '{selected_crime}'")

    correlation_matrix = master_df[crime_cols].corr()
    related_crimes = correlation_matrix[selected_crime]
    strong_correlations = related_crimes[abs(related_crimes) > correlation_threshold].drop(selected_crime, errors='ignore')

    if strong_correlations.empty:
        st.warning(f"No strong correlations found for '{selected_crime}' at the selected threshold.")
    else:
        G = nx.Graph()
        G.add_node(selected_crime)
        for crime, corr_value in strong_correlations.items():
            G.add_node(crime)
            G.add_edge(selected_crime, crime, weight=abs(corr_value))

        pos = nx.spring_layout(G, k=0.8, iterations=50)

        edge_x, edge_y = [], []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        node_x, node_y, node_text = [], [], []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=edge_x, y=edge_y, mode='lines', line=dict(width=0.7, color='#888'), hoverinfo='none'))
        fig.add_trace(go.Scatter(
            x=node_x, y=node_y, mode='markers+text', text=node_text,
            textposition="bottom center", hoverinfo='text',
            marker=dict(
                showscale=True, colorscale='YlGnBu', size=25,
                color=[1] + list(strong_correlations.values),
                colorbar=dict(thickness=15, title=dict(text='Correlation Strength', side='right')),
                line_width=2
            )
        ))
        fig.update_layout(
            title=f"Crimes strongly correlated with '{selected_crime}'",
            showlegend=False, hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("Show Correlation Data"):
            st.dataframe(strong_correlations.sort_values(ascending=False))
