import pandas as pd
import streamlit as st
import plotly.express as px
from data_processing import finalize_data
from datetime import datetime
import os
from oauth2client.service_account import ServiceAccountCredentials
import gspread

#PAGE 
st.set_page_config(layout="wide")
st.title("Kognisi x BPJS")
st.markdown("""
Welcome!
""")

with st.spinner("Loading data..."):
    df_combined = finalize_data()

st.sidebar.write(" Use the filters below to explore the data.")

email_filter = st.sidebar.text_input("Search by Email")

date_range = st.sidebar.date_input(
    "Filter by Date Range",
    value=(datetime(2024, 1, 1), datetime.now()),  # Default range
    key="date_range"
)

wilayah_filter = st.sidebar.multiselect(
    "Filter by Wilayah",
    options=sorted(df_combined['wilayah'].dropna().unique()) if 'wilayah' in df_combined.columns else [],
    default=None,
    key="wilayah_filter"
)

category_filter = st.sidebar.multiselect(
    "Filter by Category Name",
    options=sorted(df_combined['category_name'].dropna().unique()) if 'category_name' in df_combined.columns else [],
    default=None,
    key="category_filter"
)

# Apply Filters
filtered_df = df_combined.copy()

if email_filter:
    filtered_df = filtered_df[filtered_df['email'].str.contains(email_filter, case=False, na=False)]

if date_range and isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
    if 'enroll_date' in df_combined.columns:
        filtered_df = filtered_df[
            (filtered_df['enroll_date'].isnull()) |  # Include rows where 'enroll_date' is null
            (
                (pd.to_datetime(filtered_df['enroll_date'], errors='coerce') >= pd.to_datetime(start_date)) &
                (pd.to_datetime(filtered_df['enroll_date'], errors='coerce') <= pd.to_datetime(end_date))
            )
        ]

if wilayah_filter:
    filtered_df = filtered_df[filtered_df['wilayah'].isin(wilayah_filter)]

if category_filter:
    filtered_df = filtered_df[filtered_df['category_name'].isin(category_filter)]

# Display Filtered Data
st.write("#### **Filtered Data**:")
with st.expander("View Filtered Data"):
    st.write(filtered_df)

#VISUAL

col3, col4, col5, col8, col9 = st.columns(5)
col6, col7 = st.columns(2)

# Column 3: Count distinct emails as 'Jumlah User'
with col3:
    jumlah_user = filtered_df['email'].nunique()  # Count distinct emails
    st.metric("Jumlah Karyawan", jumlah_user)

# Column 4: Count distinct emails where 'no_transaksi' is not null as 'Enroll User'
with col4:
    enroll_user = filtered_df[filtered_df['no_transaksi'].notnull()]['email'].nunique()
    st.metric("Enroll User", enroll_user)

# Column 5: Percentage of enrollment
with col5:
    enrollment_percentage = (enroll_user / jumlah_user * 100) if jumlah_user > 0 else 0
    st.metric("Enrollment (%)", f"{enrollment_percentage:.2f}%")

# Column 6: Sum of 'price' as 'Jumlah Penggunaan'
with col6:
    jumlah_penggunaan = filtered_df['price'].sum() if 'price' in filtered_df.columns else 0
    st.metric("Jumlah Penggunaan", f"Rp {jumlah_penggunaan:,.0f}")

# Column 7: Remaining balance as 'Sisa Saldo'
with col7:
    initial_balance = 94575000
    sisa_saldo = initial_balance - jumlah_penggunaan
    st.metric("Sisa Saldo", f"Rp {sisa_saldo:,.0f}")

# Column 8: Average of 'progress' as 'Avg Progress'
with col8:
    avg_progress = filtered_df['progress'].mean() if 'progress' in filtered_df.columns else 0
    st.metric("Avg Progress", f"{avg_progress:.2f}%")

# Column 9: Sum of 'duration' converted from seconds to hours as 'Total Duration'
with col9:
    total_duration_sec = filtered_df['duration'].sum() if 'duration' in filtered_df.columns else 0
    total_duration_hours = total_duration_sec / 3600  # Convert seconds to hours
    st.metric("Total Duration (hours)", f"{total_duration_hours:,.2f}")



st.divider()


col1, col2 = st.columns(2)

with col1:
    # Top 10 'title' by count of unique emails (horizontal bars)
    if 'title' in filtered_df.columns and 'email' in filtered_df.columns:
        top_titles = (
            filtered_df.groupby('title')['email']
            .nunique()
            .reset_index()
            .rename(columns={'email': 'email_count'})
            .sort_values(by='email_count', ascending=True)
            .head(10)
        )
        
        # Manually wrap text in y-axis labels by inserting line breaks after every 4 spaces
        def wrap_text(text, max_words=6):
            words = text.split()  # Split text into words
            wrapped_text = [' '.join(words[i:i+max_words]) for i in range(0, len(words), max_words)]  # Wrap every 4 words
            return '<br>'.join(wrapped_text)  # Join with line breaks
        
        top_titles['title_wrapped'] = top_titles['title'].apply(wrap_text)
        
        # Create a horizontal bar chart with data labels
        fig_titles = px.bar(
            top_titles,
            y='title_wrapped',  # Use wrapped 'title' for y-axis
            x='email_count',
            text='email_count',  # Add data labels
            labels={'email_count': 'Email Count', 'title_wrapped': 'Title'},
            title="Top 10 Titles by Email Count"
        )
        
        # Update layout to show the data labels and adjust axis labels
        fig_titles.update_traces(texttemplate='%{text}', textposition='outside')
        
        # Adjust the y-axis to fit the labels better
        fig_titles.update_layout(
            yaxis=dict(
                tickangle=0,  # Ensure labels stay horizontal
            ),
            margin=dict(l=80),
            height=700  # Increase left margin to avoid clipping
        )
        st.plotly_chart(fig_titles)

with col2:
    # Top 10 'category_name' by count of unique emails (vertical bars)
    if 'category_name' in filtered_df.columns and 'email' in filtered_df.columns:
        top_categories = (
            filtered_df.groupby('category_name')['email']
            .nunique()
            .reset_index()
            .rename(columns={'email': 'email_count'})
            .sort_values(by='email_count', ascending=False)
            .head(10)
        )
        
        # Create a vertical bar chart with data labels
        fig_categories = px.bar(
            top_categories,
            x='category_name',
            y='email_count',
            text='email_count',  # Add data labels
            labels={'email_count': 'Email Count', 'category_name': 'Category'},
            title="Top 10 Categories by Email Count"
        )
        # Update layout to show the data labels
        fig_categories.update_traces(texttemplate='%{text}', textposition='outside')
        fig_titles.update_layout(
            height=700  # Increase left margin to avoid clipping
        )
        st.plotly_chart(fig_categories)

# Top 10 'wilayah' by count of unique emails
if 'wilayah' in filtered_df.columns and 'email' in filtered_df.columns:
    # Calculate email_count (Jumlah Karyawan)
    email_count = (
        filtered_df.groupby('wilayah')['email']
        .nunique()
        .reset_index()
        .rename(columns={'email': 'email_count'})
    )
    
    # Calculate enrollment (email_count with non-null no_transaksi)
    if 'no_transaksi' in filtered_df.columns:
        enrollment = (
            filtered_df[filtered_df['no_transaksi'].notnull()]
            .groupby('wilayah')['email']
            .nunique()
            .reset_index()
            .rename(columns={'email': 'enrollment'})
        )
    else:
        enrollment = pd.DataFrame(columns=['wilayah', 'enrollment'])
    
    # Merge email_count and enrollment
    top_wilayah = pd.merge(email_count, enrollment, on='wilayah', how='left')
    
    # Fill missing values in enrollment with 0
    top_wilayah['enrollment'] = top_wilayah['enrollment'].fillna(0).astype(int)
    
    # Calculate learning_adoption
    top_wilayah['learning_adoption'] = (
        top_wilayah['enrollment'] / top_wilayah['email_count']
    ).round(2)
    
    # Sort by email_count and show top 10
    top_wilayah = top_wilayah.sort_values(by='email_count', ascending=False).head(20)
    
    st.write("Top Wilayah")
    st.dataframe(top_wilayah)


# Top 10 users by count of titles
if 'title' in filtered_df.columns and 'nama' in filtered_df.columns:
    # Count title enrollment (count of titles grouped by nama)
    title_count = (
        filtered_df.groupby('nama')['title']
        .count()
        .reset_index()
        .rename(columns={'title': 'title_count'})
    )
    
    # Count progress when they already 100 (count rows where progress == 100 grouped by nama)
    if 'progress' in filtered_df.columns:
        progress_100_count = (
            filtered_df[filtered_df['progress'] == 100]
            .groupby('nama')
            .size()
            .reset_index(name='progress_100_count')
        )
    else:
        progress_100_count = pd.DataFrame(columns=['nama', 'progress_100_count'])
    
    # Merge the title_count and progress_100_count DataFrames
    top_users = pd.merge(title_count, progress_100_count, on='nama', how='left')
    
    # Fill missing values in progress_100_count with 0
    top_users['progress_100_count'] = top_users['progress_100_count'].fillna(0).astype(int)
    
    # Sort by progress_100_count and show top 20 users
    top_users = top_users.sort_values(by='progress_100_count', ascending=False).head(20)
    
    st.write("Top 20 Users by Progress 100 Count")
    st.dataframe(top_users)




















# Footer
st.markdown("---")
st.caption("Developed by Kognisi. © 2025.")
