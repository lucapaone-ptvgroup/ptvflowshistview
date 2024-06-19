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
    st.title("API Data Table")

    # Text input for API key
    api_key = st.text_input("Enter your API key:")

    # Button to fetch data
    if st.button("Fetch Data"):
        if api_key:
            # Fetch data from the API
            API_KEY = api_key
            kpi_ids_df = fetch_all_kpis(api_key)

            if kpi_ids_df is not None:

                                #st.write(data.dtypes)
                # Display the data in a table
                st.dataframe(kpi_ids_df)
                more_data_btn = st.button("Load last 24 hours")
                if more_data_btn:
                    #print (kpi_ids_df)
                    kpi_ids =     kpi_ids_df['kpiId']

                    last_24_hours_data = pd.DataFrame()
                    loading = st.write("...")
                    '''
                    for kpi_id in kpi_ids:
                        loading.write(f"kpi_id {kpi_id}")
                        data = fetch_last_24_hours_data(kpi_id)
                        last_24_hours_data = pd.concat([last_24_hours_data, data], ignore_index=True)

                    if 'results' in last_24_hours_data.columns:
                        #print("Dropping 'results' column from last 24 hours data.")
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
                        lambda row: row['RoundedTimeStamp'] + timedelta(seconds=row['timetostart']) , axis=1
                    )

                    last_24_hours_data = merged_data
                    print("Last 24 hours data head:")
                    print(last_24_hours_data.head())      
      

                    # Display additional data tables
                    st.write("Last 24 Hours Data:")
                    st.dataframe(last_24_hours_data)

                    historical_stats_data = fetch_historical_stats(kpi_id)
                    st.write("Historical Stats Data:")
                    st.dataframe(historical_stats_data)
                    '''
                else:
                    st.warning("Nodata?")
        else:
            st.warning("Please enter an API key.")
if __name__ == "__main__":
    main()

