import streamlit as st
import pandas as pd
from utilsfe import call_backend, call_continent_analysis_backend 
from ui_components import (
    display_clustered_data, # Re-including in case you want to show it in results tab
    create_and_display_heatmap,
    display_summary_statistics,
    display_top_countries_by_cluster,
    render_user_chart,render_backend_continent_analysis # Add the new function import
)
import matplotlib.pyplot as plt # Import plt to ensure we can close figures properly

# Optional: Set page config to wide mode for better display
st.set_page_config(layout="wide")

st.title("Customer Clustering Frontend")

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

# Initialize session state for results if not already present
# This is crucial to retain results when the app reruns (e.g., tab switch)
if 'clustering_result' not in st.session_state:
    st.session_state.clustering_result = None
if 'clustered_df_display' not in st.session_state:
    st.session_state.clustered_df_display = None
if 'heatmap_data_display' not in st.session_state:
    st.session_state.heatmap_data_display = None

if uploaded_file:
    df = None
    try:
        # Try utf-8 encoding first
        df = pd.read_csv(uploaded_file, encoding='utf-8')
    except Exception as e1:
        uploaded_file.seek(0)  # rewind file before second try
        try:
            # Try latin1 encoding as fallback
            df = pd.read_csv(uploaded_file, encoding='latin1')
        except Exception as e2:
            st.error(f"Failed to read CSV file.\nutf-8 error: {e1}\nlatin1 error: {e2}")
            df = None # Ensure df is None if both fail

    if df is not None:
        # Create tabs - Added new "Continent Analysis" tab
        tab_data_preview, tab_clustering_results, tab_continent_analysis = st.tabs([
            "Data Preview", 
            "Clustering Results", 
            "Continent Analysis"
        ])

        with tab_data_preview:
            st.write("### Uploaded Data")
            st.dataframe(df) # Display the full DataFrame here

        with tab_clustering_results:
            # Check if clustering results are already available in session state
            if st.session_state.clustered_df_display is not None and st.session_state.heatmap_data_display is not None:
                st.success("Clustering complete! Results are displayed below.")
                st.write("### Clustering Results")

                # Optional: display the clustered data table
                # display_clustered_data(st.session_state.clustered_df_display)

                create_and_display_heatmap(st.session_state.clustered_df_display) # This function expects clustered_df
                display_summary_statistics(st.session_state.heatmap_data_display)
                display_top_countries_by_cluster(st.session_state.heatmap_data_display)

                # Add a button to re-run clustering if needed, after results are shown
                if st.button("Re-run Clustering"):
                    # Clear results to show the "Run Clustering" button again
                    st.session_state.clustering_result = None
                    st.session_state.clustered_df_display = None
                    st.session_state.heatmap_data_display = None
                    st.rerun() # Rerun the app to show the initial button state
            elif st.session_state.clustering_result and "error" in st.session_state.clustering_result:
                # If there was an error in clustering
                st.error("Clustering failed. Please check the 'Raw Results' below for details.")
                st.write("### Raw Results")
                st.json(st.session_state.clustering_result)
                # Allow re-run after an error
                if st.button("Try Clustering Again"):
                    st.session_state.clustering_result = None
                    st.rerun()
            else:
                # Initial state: no results yet, show the "Run Clustering" button
                st.write("### Initiate Customer Clustering")
                st.info("Click the button below to start the clustering process.")
                if st.button("Run Clustering"):
                    # Clear any stale results before running
                    st.session_state.clustering_result = None
                    st.session_state.clustered_df_display = None
                    st.session_state.heatmap_data_display = None

                    with st.spinner("Clustering in progress... This may take a moment."):
                        uploaded_file.seek(0)
                        file_content = uploaded_file.read()
                        result = call_backend(file_content, uploaded_file.name)

                        st.session_state.clustering_result = result # Store raw result

                        if "error" in result:
                            st.error(f"Error: {result['error']}")
                            # Keep error in session state so it's displayed on rerun
                        else:
                            st.success("Clustering complete!")
                            try:
                                clustered_df = pd.DataFrame.from_dict(result, orient='index')
                                clustered_df.reset_index(inplace=True)
                                clustered_df.rename(columns={'index': 'Country'}, inplace=True)
                                cluster_names = {'0': 'Premium', '1': 'Frequent', '2': 'Budget'}
                                clustered_df.rename(columns=cluster_names, inplace=True)

                                st.session_state.clustered_df_display = clustered_df

                                heatmap_data = clustered_df.set_index('Country')[['Premium', 'Frequent', 'Budget']]
                                heatmap_data['Total'] = heatmap_data.sum(axis=1)
                                heatmap_data = heatmap_data.sort_values('Total', ascending=False).drop('Total', axis=1)
                                st.session_state.heatmap_data_display = heatmap_data
                                # Important: Rerun to update the display based on new session state
                                st.rerun()

                            except Exception as e:
                                st.error(f"Error processing clustering results: {str(e)}")
                                st.write("### Raw Results (Failed Processing)")
                                st.json(result)
                                # Store the error in session state to persist
                                st.session_state.clustering_result = {"error": f"Client-side processing error: {str(e)}"}
                                st.session_state.clustered_df_display = None
                                st.session_state.heatmap_data_display = None
                                st.rerun() # Rerun to display the error state

        with tab_continent_analysis:            
            if st.button("Analyze Continents"):
                with st.spinner("Analyzing continent data... This may take a moment."):
                    uploaded_file.seek(0)  # Reset pointer
                    file_content = uploaded_file.read()

                    # ✅ Send file to backend for analysis
                    result = call_continent_analysis_backend(file_content, uploaded_file.name)

                    # ✅ Check for error
                    if "error" in result:
                        st.error(f"Error: {result['error']}")
                    else:
                        st.success("Analysis complete!")
                        
                        # DEBUG: Show what backend returned
                        # st.write("Backend Response:")
                        # st.json(result)
                        
                        # ✅ Render continent analysis output
                        render_backend_continent_analysis(result)
                        # Optionally, you can store the result in session state if needed