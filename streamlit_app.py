import streamlit as st
import pandas as pd
import requests
import logging
from datetime import datetime, timedelta

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
        HEADERS["apiKey"] = api_key
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

# Fetch last 24 hours data for a specific KPI
def fetch_last_24_hours_data(kpi_id):
    print(f"Fetching last 24 hours data for KPI: {kpi_id}")
    url = f"{KPI_24HOURS_URL}?kpiId={kpi_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        df = pd.json_normalize(data)
        if 'timeStamp' in df.columns:
            df['RoundedTimeStamp'] = df['timeStamp'].apply(round_to_nearest_5min)
        df['kpiId'] = kpi_id  # Ensure 'kpiId' is in the DataFrame
        print(f"Fetched last 24 hours data for KPI: {kpi_id}")
        return df
    else:
        print(f"Failed to fetch data for KPI: {kpi_id}, Status Code: {response.status_code}, Response: {response.text}")
    return pd.DataFrame()

# Fetch historical stats for a specific KPI
def fetch_historical_stats(kpi_id):
    print(f"Fetching historical stats for KPI: {kpi_id}")
    url = f"{KPI_HISTORICAL_URL}?kpiId={kpi_id}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        data = response.json()
        historical_data = []
        for entry in data:
            if 'timeStamp' in entry and 'results' in entry:
                timestamp = entry['timeStamp']
                for result in entry['results']:
                    result['timeStamp'] = timestamp  # Ensure the 'timeStamp' is included in each result
                    result['RoundedTimeStamp'] = round_to_nearest_5min(timestamp)
                    result['kpiId'] = kpi_id
                    historical_data.append(result)
        df = pd.DataFrame(historical_data)
        print(f"Fetched historical stats for KPI: {kpi_id}")
        return df
    else:
        print(f"Failed to fetch historical stats for KPI: {kpi_id}, Status Code: {response.status_code}, Response: {response.text}")
    return pd.DataFrame()

# Round datetime to the nearest 5-minute bucket
def round_to_nearest_5min(timestamp):
    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    new_minute = (dt.minute // 5) * 5
    return dt.replace(minute=new_minute, second=0, microsecond=0)

def main():
    data = None
    st.title("PTV FLOWS data analysis")
    # Text input for API key
    api_key_input = st.text_input("Enter your API key:")
    fetch_KPIdef_button = st.button("Fetch KPI definitions and last data")
    loading_txt = st.empty()
    loading_txt.text("...")

    # Button to fetch data
    if fetch_KPIdef_button:
        if api_key_input:
            # Fetch data from the API
            API_KEY = api_key_input
            kpi_ids_df = fetch_all_kpis(api_key_input)

            if kpi_ids_df is not None:
                # Display the data in a table
                st.dataframe(kpi_ids_df)
                loading_txt.text("Loading last 24 hours data...")

                kpi_ids = kpi_ids_df['kpiId']
                last_24_hours_data = pd.DataFrame()

                for kpi_id in kpi_ids:
                    loading_txt.text(f"Fetching data for KPI ID: {kpi_id}")
                    data = fetch_last_24_hours_data(kpi_id)
                    last_24_hours_data = pd.concat([last_24_hours_data, data], ignore_index=True)

                if 'results' in last_24_hours_data.columns:
                    last_24_hours_data.drop(columns=['results'], inplace=True)

                print(f"Columns in last_24_hours_data: {last_24_hours_data.columns.tolist()}")

                # Merge to include 'timetostart' in last_24_hours_data
                merged_data = last_24_hours_data.merge(kpi_ids_df[['kpiId', 'timetostart']], on='kpiId', how='left')

                # Check the merged data
                print("Merged DataFrame with 'timetostart':")
                print(merged_data.head())

                # Now you can use the 'timetostart' in your calculations
                # For example, adding 'timetostart' to 'RoundedTimeStamp'
                merged_data['ForecastedTimestamp'] = merged_data.apply(
                    lambda row: row['RoundedTimeStamp'] + timedelta(seconds=row['timetostart']), axis=1
                )

                last_24_hours_data = merged_data
                print("Last 24 hours data head:")
                print(last_24_hours_data.head())      

                # Display additional data tables
                st.write("Last 24 Hours Data:")
                st.dataframe(last_24_hours_data)
                historical_stats_data = pd.DataFrame()
                for kpi_id in kpi_ids:
                    loading_txt.text(f"Fetching HIST data for KPI ID: {kpi_id}")
                    data = fetch_historical_stats(kpi_id)
                    if(data is not None):
                        historical_stats_data = pd.concat([historical_stats_data, data], ignore_index=True)
                
                st.write("Historical Stats Data:")
                st.dataframe(historical_stats_data)

                # Group historical data and create groupedHistoricalData
                groupedHistoricalData = historical_stats_data.groupby(
                    ['kpiId', 'RoundedTimeStamp']
                ).agg(
                    {
                        'defaultValue': 'sum',
                        'value': 'sum',
                        'averageValue': 'sum',
                        'unusualValue': 'sum',
                        'progressive': 'max'
                    }
                ).reset_index()

                st.write("Grouped Historical Stats Data:")
                st.dataframe(groupedHistoricalData)

                loading_txt.empty()  # Remove the loading text
                
                comparison = None
                # Compare quality of forecasted data with historical data
                if not last_24_hours_data.empty and not groupedHistoricalData.empty:
                    print("Comparing forecasted data with historical data...")
                    # Perform inner join on 'kpiId' and 'ForecastedTimestamp' from merged_data with 'kpiId' and 'RoundedTimeStamp' from groupedHistoricalData
                    comparison = pd.merge(
                        last_24_hours_data, 
                        groupedHistoricalData, 
                        left_on=['kpiId', 'ForecastedTimestamp', 'overallResult.progressive'], 
                        right_on=['kpiId', 'RoundedTimeStamp', 'progressive'], 
                        how='inner'
                    )
                    comparison['AbsDelta'] = (comparison['overallResult.value'] - comparison['value']).abs()
                    comparison['ErrorPerc'] = (comparison['AbsDelta'] / comparison['value']) * 100
                    # Merge to include 'name' from kpi_ids_df in comparison
                    comparison = pd.merge(comparison, kpi_ids_df[['kpiId', 'name']], on='kpiId', how='left')

                    print("Comparison Results:")
                    print(comparison.head())
                    st.write("Comparison Results:")
                    st.dataframe(comparison)
                else:
                    warning = "No data available for comparison" 
                    print(warning)
                    st.warning(warning)

        else:
            st.warning("Please enter an API key.")

if __name__ == "__main__":
    main()
