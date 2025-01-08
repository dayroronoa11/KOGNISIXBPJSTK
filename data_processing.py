import streamlit as st
import pandas as pd
import numpy as np
from fetch_data import fetch_data_id, fetch_bpjs
from datetime import datetime

@st.cache_data(ttl=86400)
def fetch_combined():
    # Fetch data from both sources
    df_id = fetch_data_id()
    df_bpjs = fetch_bpjs() 

    # Check for the presence of 'email' column
    if 'email' not in df_id.columns or 'email' not in df_bpjs.columns:
        st.error("One or both dataframes are missing the 'email' column.")
        return None

    # Preprocess emails
    df_id['email'] = df_id['email'].str.strip().str.lower()
    df_bpjs['email'] = df_bpjs['email'].str.strip().str.lower()

    # Remove duplicate emails in each dataset
    df_id = df_id.drop_duplicates(subset='email')
    df_bpjs = df_bpjs.drop_duplicates(subset='email')

    # Merge the datasets on email
    df_combined = pd.merge(df_id, df_bpjs, on='email', how='outer', suffixes=('_id', '_bpjs'))

    return df_combined


def finalize_data():
    df_combined = fetch_combined()
    if df_combined is not None:
        return df_combined
    else:
        st.error("Failed to fetch combined data due to missing columns.")
        return pd.DataFrame()  

