import streamlit as st
import pandas as pd
import datetime
import numpy as np
import plotly.express as plt

st.set_page_config(layout="wide")

@st.cache_data()
def load_data():
    data = pd.read_csv(r'./ContractOpportunitiesFullCSV_VOSB.csv', encoding='ISO-8859-1', dtype={
        'NaicsCode':'str',
        'AwardDate':'str',
        # 'Award$':'float'
        }
        )
    data.columns = data.columns.str.replace(' ', '')
    # data.columns = data.columns.str.replace('$', '_Dollars')
    # data[data['Award$']] = data[data['Award$']].apply(lambda x: x.str.replace('$','')).apply(lambda x: x.str.replace(',','')).astype(np.float64)
    data['PostedDate_corrected'] = data['PostedDate'].str[:10]
    data['PostedDate_corrected'] = pd.to_datetime(data['PostedDate_corrected']).dt.strftime('%Y-%m-%d')
    # data['AwardDate'] = pd.to_datetime(data['AwardDate']).dt.strftime('%Y-%m-%d')
    data['AwardDate'] = data['AwardDate'].str[:10]
    data = data[pd.notnull(data['NaicsCode'])]
    data = data[data['SetASide'].isin(['Service-Disabled Veteran-Owned Small Business (SDVOSB) Set-Aside (FAR 19.14)', 'Service-Disabled Veteran-Owned Small Business (SDVOSB) Sole Source (FAR 19.14)', 'Veteran-Owned Small Business Set-Aside (specific to Department of Veterans Affairs)'])].reset_index()
    return data

data = load_data()

st.title('SAM Contracts Dashboard')

st.sidebar.markdown('## Select Filters')
st.sidebar.markdown('### Filters only affect the first table.')

select_type = st.sidebar.multiselect('Select Contract Type', data['Type'].unique().tolist())

naics_code_values = data['NaicsCode'].unique().tolist()

select_naics = st.sidebar.multiselect('Select Naics Codes (Leaving empty will retain all codes)', naics_code_values)


filtered_data=data
if select_type!=[]:
    filtered_data = filtered_data[filtered_data['Type'].isin(select_type)].reset_index()
if select_naics!=[]:
    filtered_data = filtered_data[filtered_data['NaicsCode'].isin(select_type)].reset_index()
# else:
#     filtered_data=data

st.subheader('Posted Date Range: {} - {}'.format(filtered_data['PostedDate_corrected'].min(), filtered_data['PostedDate_corrected'].max()))
if 'Award Notice' in select_type:
    st.subheader('Award Date Range: {} - {}'.format(filtered_data['AwardDate'].min(), filtered_data['AwardDate'].max()))
st.dataframe(filtered_data, use_container_width=True)

st.subheader('Award Notice Pivot')
st.markdown('#### Only contains data for Award Type = Award Notice')
award_data = data[data['Type']=='Award Notice']
award_data['Award$'] = award_data['Award$'].astype(float)
award_data['NaicsCode'] = award_data['NaicsCode'].astype(str)
# award_data[award_data['Award$']] = award_data[award_data['Award$']].apply(lambda x: x.str.replace('$','')).apply(lambda x: x.str.replace(',','')).astype(np.float64)
# award_data[award_data['Award$']] = award_data[award_data['Award$']].replace('[^.0-9]', '', regex=True).astype(float)
award_data = award_data[['NaicsCode', 'Award$']]
# award_notice_pivot = pd.pivot_table(data=award_data, values=['Award$'], index=['NaicsCode'])
# award_notice_count = award_data.groupby(['NaicsCode']).count()
# award_notice_sum = award_data.groupby(['NaicsCode']).cumsum()
# award_notice_pivot = pd.merge(award_notice_count, award_notice_sum, on=['NaicsCode'])

award_notice_pivot = award_data.groupby('NaicsCode').agg(
    Count=('Award$', np.count_nonzero),
    Sum=('Award$', np.sum),
    Mean=('Award$', np.mean),
    StdDev=('Award$', np.std),
    Min=('Award$', np.min),
    Max=('Award$', np.max)
).reset_index()
st.dataframe(award_notice_pivot, use_container_width=True)

award_notice_plot_sum = plt.bar(award_notice_pivot, x='NaicsCode', y='Sum', title='Average Award Amount by Naics Code')
award_notice_plot_sum.update_xaxes(type='category')

st.plotly_chart(award_notice_plot_sum, use_container_width=True)

award_notice_plot_mean = plt.bar(award_notice_pivot, x='NaicsCode', y='Mean', title='Average Award Amount by Naics Code', error_y='StdDev')
award_notice_plot_mean.update_xaxes(type='category')

st.plotly_chart(award_notice_plot_mean, use_container_width=True)