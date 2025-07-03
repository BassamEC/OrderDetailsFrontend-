import requests
import io
from config import BASE_URL  # Updated import - use BASE_URL instead
import pandas as pd
import streamlit as st

function_url = st.secrets["azure"]["function_url"]  # Update with your actual URL
function_key = st.secrets["azure"]["function_key"]

url_with_key = f"{function_url}/cluster?code={function_key}"
def call_backend(file_content: bytes, filename: str) -> dict:
    """
    Send file content to the backend for clustering
    
    Args:
        file_content: bytes content of the file
        filename: name of the file
    
    Returns:
        dict: Response from the backend
    """
    try:
        # Create a file-like object from the bytes content
        files = {'file': (filename, io.BytesIO(file_content), 'text/csv')}
        
        # Send POST request to backend - using BASE_URL from config
        response = requests.post(url_with_key,
            # json=payload,
            files=files,
            
            timeout=30)
        
        if response.status_code != 200:
            return {"error": f"HTTP {response.status_code}: {response.text}"}
        
        try:
            return response.json()
        except ValueError:
            return {"error": f"Invalid JSON response:\n{response.text}"}
            
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)}"}
    
continent_to_countries = {
    'All': [],
    'Europe': [
        'France', 'Spain', 'Italy', 'Germany', 'Sweden', 'Belgium',
        'UK', 'Norway', 'Finland', 'Switzerland', 'Austria',
        'Denmark', 'Ireland', 'Portugal', 'Netherlands', 'Poland'
    ],
    'Asia': ['Singapore', 'Japan'],
    'Oceania': ['Australia'],
    'South America': ['Brazil', 'Venezuela', 'Argentina'],
    'North America': ['USA', 'Canada', 'Mexico']
}

country_to_continent = {
    country: continent
    for continent, countries in continent_to_countries.items()
    for country in countries
}

def customer_continent_graph(df: pd.DataFrame) -> pd.DataFrame:
    """Generate chart data by continent."""
    # Count occurrences of each country
    country_counts = df.drop_duplicates(subset='CustomerID')['Country'].value_counts()

    continent_count= {
    'Europe':0,
    'Asia':0,
    'Oceania': 0,
    'South America': 0,
    'North America': 0}
    
    for country, count in country_counts.items():
        continent = country_to_continent.get(country, 'Other')
        if continent in continent_count:
            continent_count[continent] += count
    df=pd.DataFrame.from_dict(continent_count, orient='index', columns=['Continent'])
    df.reset_index(inplace=True)
    df.columns = ['Continent','Customer_Count']
    return df

def call_continent_analysis_backend(file_content, filename):
    """
    Call the backend API for continent analysis.
    
    Args:
        file_content: The CSV file content as bytes
        filename: The name of the uploaded file
    
    Returns:
        dict: Response from backend containing continent analysis data
              Expected format: {
                  "Europe": {"customer_count": 150, "total_revenue": 25000.50},
                  "Asia": {"customer_count": 80, "total_revenue": 15000.25},
                  ...
              }
              Or {"error": "error message"} if failed
    """
    try:
        # Prepare the file for upload
        files = {
            'file': (filename, file_content, 'text/csv')
        }
        
        # Make the POST request to backend - using BASE_URL from config
        response = requests.post(f"{BASE_URL}/continent-analysis", files=files, timeout=60)
        
        # Check if request was successful
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"Backend request failed with status {response.status_code}: {response.text}"
            }
            
    except requests.exceptions.Timeout:
        return {"error": "Backend request timed out. Please try again."}
    except requests.exceptions.ConnectionError:
        return {"error": "Could not connect to backend server. Please check if the server is running."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}