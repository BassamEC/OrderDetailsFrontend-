# Switch between 'local' and 'azure'
ENVIRONMENT = 'local'  # or 'azure'

AZURE_URL = "https://<your-azure-function>.azurewebsites.net/api/<function-name>"
LOCAL_URL = "http://127.0.0.1:5000"
import streamlit as st
import os

# Try to get from Streamlit secrets first, fallback to hardcoded values
try:
    ENVIRONMENT = st.secrets["api"]["environment"]
    AZURE_URL = st.secrets["api"]["azure_url"]
    LOCAL_URL = st.secrets["api"]["local_url"]
except (KeyError, FileNotFoundError):
    # Fallback to environment variables or defaults
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'local')
    AZURE_URL = os.getenv('AZURE_URL', "https://your-flask-app-name.azurewebsites.net")
    LOCAL_URL = os.getenv('LOCAL_URL', "http://127.0.0.1:5000")

# Select URL based on environment
if ENVIRONMENT == 'azure':
    BASE_URL = AZURE_URL
else:
    BASE_URL = LOCAL_URL