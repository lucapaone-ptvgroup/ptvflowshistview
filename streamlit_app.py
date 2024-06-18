# my_app.py
import streamlit as st
import pandas as pd
import requests
import logging

# Enable logging
logging.basicConfig(level=logging.DEBUG)

API_KEY = "put here your API key"
# Define the base URLs for the different API endpoints
KPI_ENG_URL = "https://api.myptv.com/kpieng/v1/instance/all"
KPI_HISTORICAL_URL = "https://api.myptv.com/kpistats/v1/historical/result/by-kpi-id"
KPI_24HOURS_URL = "https://api.myptv.com/kpieng/v1/result/by-kpi-id"


# Define headers for the API requests
HEADERS = {
    "apiKey": API_KEY,
    "Accept": "*/*",
    "Connection": "keep-alive"
}

def extract_timetostart(param_dict):
    try:
        return param_dict.get('parameters', {}).get('timetostart', None)
    except AttributeError:
        return None

# Fetch all KPI definitions
def fetch_all_kpis(api_key):
    try:
        print("Fetching all KPI definitions...")
        HEADERS["apiKey"]=api_key
        response = requests.get(KPI_ENG_URL, headers=HEADERS)
        response.raise_for_status()  # Raise an exception if the response status code is not 200
        kpi_data = response.json()
        kpi_df = pd.DataFrame(kpi_data)
        kpi_df['timetostart'] = kpi_df['kpiInstanceParameters'].apply(extract_timetostart)
        print(f"Fetched {len(kpi_df)} KPIs.")
        print(kpi_df.head())
        return kpi_df
    except requests.RequestException as e:
        st.error(f"Error fetching data: {e}")
        return None

def main():
    st.title("API Data Table")

    # Text input for API key
    api_key = st.text_input("Enter your API key:")

    # Button to fetch data
    if st.button("Fetch Data"):
        if api_key:
            # Fetch data from the API
            API_KEY = api_key
            data = fetch_all_kpis(api_key)

            if data is not None:

                                #st.write(data.dtypes)
                # Display the data in a table
                st.dataframe(data)
        else:
            st.warning("Please enter an API key.")

if __name__ == "__main__":
    main()

