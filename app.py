import streamlit as st
import pandas as pd
import requests
import json
import io
from utilsfe import call_backend, call_continent_analysis_backend 
from ui_components import (
    display_clustered_data, # Re-including in case you want to show it in results tab
    create_and_display_heatmap,
    display_summary_statistics,
    display_top_countries_by_cluster,
    render_backend_continent_analysis # Add the new function import
)
import matplotlib.pyplot as plt # Import plt to ensure we can close figures properly

# Optional: Set page config to wide mode for better display
st.set_page_config(layout="wide")

# Azure Function Configuration
function_url = st.secrets["azure"]["function_url"]  # Update with your actual URL
function_key = st.secrets["azure"]["function_key"]

url_with_key = f"{function_url}?code={function_key}"


def call_azure_function(company_identifier):
    """Call Azure Function to get company data"""
    try:
        payload = {
            "company_identifier": company_identifier,
            "password": st.secrets["azure"]["password"]  # Use the password from secrets
        }
        
        response = requests.post(
            url_with_key,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return {"error": "No data found for the specified company"}
        elif response.status_code == 401:
            return {"error": "Invalid credentials"}
        else:
            return {"error": f"Azure Function error: {response.status_code}"}
            
    except requests.exceptions.RequestException as e:
        return {"error": f"Azure Function not working: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

def convert_dataframe_to_file_content(df):
    """Convert DataFrame to file content that backend functions expect"""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    return csv_content.encode('utf-8')

def login_page():
    """Display login form"""
    st.title("Company Data Access")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Login")
        
        with st.form("login_form"):
            company_identifier = st.text_input(
                "Company ID or Company Name",
                placeholder="Enter company ID (e.g., '1') or company name (e.g., 'Alfreds Futterkiste')",
                help="You can login using either the company ID number or the full company name"
            )
            
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                if not company_identifier.strip():
                    st.error("Please enter a company identifier")
                else:
                    with st.spinner("Authenticating and loading data..."):
                        result = call_azure_function(company_identifier.strip())
                        
                        if "error" in result:
                            st.error(result["error"])
                        else:
                            # Login successful, store data in session state
                            st.session_state.logged_in = True
                            st.session_state.company_identifier = company_identifier.strip()
                            st.session_state.company_data = pd.DataFrame(result["data"])
                            st.session_state.total_records = result["total_records"]
                            
                            # Clear any existing clustering results
                            st.session_state.clustering_result = None
                            st.session_state.clustered_df_display = None
                            st.session_state.heatmap_data_display = None
                            
                            st.success(f"Login successful! Loaded {result['total_records']} records.")
                            st.rerun()

def main_app():
    """Display main application after login"""
    st.title("Customer Clustering Frontend")
    
    # Header with company info and logout
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.info(f"📊 **Company:** {st.session_state.company_identifier} | **Records:** {st.session_state.total_records}")
    
    with col3:
        if st.button("Logout", type="secondary"):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Get company data from session state
    df = st.session_state.company_data
    
    # Create tabs - Same as your original app
    tab_data_preview, tab_clustering_results, tab_continent_analysis = st.tabs([
        "Data Preview", 
        "Clustering Results", 
        "Continent Analysis"
    ])

    with tab_data_preview:
        st.write("### Company Data")
        st.dataframe(df) # Display the company's filtered data

    with tab_clustering_results:
        # Check if clustering results are already available in session state
        if st.session_state.get('clustered_df_display') is not None and st.session_state.get('heatmap_data_display') is not None:
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
        elif st.session_state.get('clustering_result') and "error" in st.session_state.clustering_result:
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
                    # Convert DataFrame to file content for backend
                    file_content = convert_dataframe_to_file_content(df)
                    file_name = f"company_{st.session_state.company_identifier}_data.csv"
                    
                    result = call_backend(file_content, file_name)

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
                # Convert DataFrame to file content for backend
                file_content = convert_dataframe_to_file_content(df)
                file_name = f"company_{st.session_state.company_identifier}_data.csv"

                # ✅ Send file to backend for analysis
                result = call_continent_analysis_backend(file_content, file_name)

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

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Initialize other session state variables for clustering results
if 'clustering_result' not in st.session_state:
    st.session_state.clustering_result = None
if 'clustered_df_display' not in st.session_state:
    st.session_state.clustered_df_display = None
if 'heatmap_data_display' not in st.session_state:
    st.session_state.heatmap_data_display = None

# Main app logic
if st.session_state.logged_in:
    main_app()
else:
    login_page()