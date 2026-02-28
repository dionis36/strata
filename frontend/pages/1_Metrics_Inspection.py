import streamlit as st
import requests
import pandas as pd
import json
import os

st.set_page_config(page_title="Strata - Metrics Inspection", layout="wide")
st.title("Structural Database Inspection")
st.markdown("Query the raw structural matrix generated per analysis run for specific bottlenecks.")

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://api:8000")
METRICS_URL = FASTAPI_URL.replace("/health", "") + "/metrics"

run_id = st.number_input("Enter Run ID to Inspect:", min_value=1, step=1)

if st.button("Query Structural Matrix"):
    with st.spinner(f"Querying Run {run_id} from SQLite..."):
        try:
            response = requests.get(f"{METRICS_URL}/{run_id}", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                components = data.get("components", [])
                
                if not components:
                    st.warning("No components found for this Run ID.")
                else:
                    # Convert raw JSON to Pandas DataFrame for native sorting
                    df = pd.DataFrame(components)
                    
                    # Ensure specific column order for readability
                    cols = ["name", "in_degree", "out_degree", "betweenness", "scc_size", "blast_radius"]
                    df = df[cols]
                    
                    st.subheader(f"Run {run_id} Results Matrix")
                    st.dataframe(
                        df, 
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "name": "Component Name",
                            "in_degree": "In-Degree",
                            "out_degree": "Out-Degree",
                            "betweenness": st.column_config.NumberColumn("Betweenness (Hub Rank)", format="%.4f"),
                            "scc_size": "SCC Size (Cycle Check)",
                            "blast_radius": "Blast Radius"
                        }
                    )
                    
                    st.markdown("### Export")
                    # Create JSON download button
                    json_str = json.dumps(data, indent=2)
                    st.download_button(
                        label="Download Raw JSON",
                        data=json_str,
                        file_name=f"run_{run_id}_metrics.json",
                        mime="application/json"
                    )
            elif response.status_code == 404:
                 st.error("Run ID not found in database.")
            else:
                st.error(f"Failed to fetch: {response.status_code}")
                
        except Exception as e:
            st.error(f"Connection Error: {e}")
