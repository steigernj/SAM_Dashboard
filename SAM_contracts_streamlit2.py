import streamlit as st
import pandas as pd
import datetime
import numpy as np
import plotly.express as plt

st.set_page_config(layout="wide")

@st.cache_data()
def load_data():
    data = pd.read_csv(r'./ContractOpportunitiesFullCSV.zip', encoding='ISO-8859-1', dtype={
        'NaicsCode':'str',
        'AwardDate':'str',
        'Award$':'str'
        }
        )
    data = data.drop_duplicates()

    data['Award$'] = data['Award$'].str.replace('$','')
    data['Award$'] = data['Award$'].str.replace(',','')
    data['Award$'] = data['Award$'].str.replace('12000000.00 Ceiling/1729413.52 First Delivery Order','12000000.00')
    data['Award$'] = data['Award$'].str.replace('35000000 Ceiling for all 5 basics First Orders: Richard FA8232-18-F-0124 132247.00 Borsight FA8232-18-F-0125 200 Cherokee FA8232-18-F-0126 200 Global FA8232-18-F-0127 200 and Interconnect FA8232-18-F-0128 200','35000000')
    data['Award$'] = data['Award$'].astype(float)
    
    data['SetASide'] = data['SetASide'].fillna('-')
    data['SetASide'] = data['SetASide'].astype('string')
    
    data['Type'] = data['Type'].astype(str)
    
    data.columns = data.columns.str.replace(' ', '')
    
    data['PostedDate_corrected'] = data['PostedDate'].str[:10]
    data['PostedDate_corrected'] = pd.to_datetime(data['PostedDate_corrected']).dt.strftime('%Y-%m-%d')
    data['PostedDate_year'] = pd.to_datetime(data['PostedDate_corrected']).dt.year
    
    data['AwardDate'] = data['AwardDate'].str[:10]
    data['AwardDate_corrected'] = pd.to_datetime(data['AwardDate'], errors='coerce').dt.strftime('%Y-%m-%d')
    data['AwardDate_year'] = pd.to_datetime(data['AwardDate_corrected']).dt.year
    data['AwardDate_year'][data['AwardDate_year']>2024] = None
    data['AwardDate_year'] = data['AwardDate_year'].round().astype(int, errors='ignore')

    data['NaicsCode'] = data['NaicsCode'].astype(str)
    data['NaicsCode'] = data['NaicsCode'].replace(' ', '-')
    # data['NaicsCode'] = data['NaicsCode'].str[:-2]
    # data = data[pd.notnull(data['NaicsCode'])]

    return data

data = load_data()

st.title('SAM Contracts Dashboard')

st.sidebar.markdown('## Select Filters')
st.sidebar.markdown('### Filters Affect All Tables and Calculations')

checkbox_veteran = st.sidebar.checkbox('Select Veteran Owned Company Set A Side Categories')

filtered_data=data

setaside_values = sorted(filtered_data['SetASide'].unique().tolist())
# select_setaside = st.sidebar.multiselect('Select Contract Set A Side', setaside_values)
if checkbox_veteran==True:
    select_setaside = st.sidebar.multiselect('Select Contract Set A Side', setaside_values, default=['Service-Disabled Veteran-Owned Small Business (SDVOSB) Set-Aside (FAR 19.14)', 'Service-Disabled Veteran-Owned Small Business (SDVOSB) Sole Source (FAR 19.14)', 'Veteran-Owned Small Business Set-Aside (specific to Department of Veterans Affairs)', 'Veteran-Owned Small Business Sole source (specific to Department of Veterans Affairs)'])
else:
    select_setaside = st.sidebar.multiselect('Select Contract Set A Side', setaside_values)
if select_setaside!=[]:
    filtered_data = filtered_data[filtered_data['SetASide'].isin(select_setaside)].reset_index(drop=True)

type_values = sorted(filtered_data['Type'].unique().tolist())
select_type = st.sidebar.multiselect('Select Contract Type', type_values)
if select_type!=[]:
    filtered_data = filtered_data[filtered_data['Type'].isin(select_type)].reset_index(drop=True)

naics_code_values = sorted(filtered_data['NaicsCode'].unique().tolist())
select_naics = st.sidebar.multiselect('Select Naics Codes', naics_code_values)
if select_naics!=[]:
    filtered_data = filtered_data[filtered_data['NaicsCode'].isin(select_naics)].reset_index(drop=True)

checkbox_naics_remove_nan = st.sidebar.checkbox('Select to remove Naics Code values listed as nan(missing)')
if checkbox_naics_remove_nan==True:
    filtered_data  = filtered_data[filtered_data['NaicsCode'].notnull()]
    filtered_data  = filtered_data[filtered_data['NaicsCode']!='nan']

filtered_posted_date_min = filtered_data['PostedDate_year'].min()
filtered_posted_date_max = filtered_data['PostedDate_year'].max()

# if select_posted_date_range != []:   
if filtered_posted_date_min==filtered_posted_date_max:
    st.sidebar.markdown('### PostedDate values are all: {}'.format(filtered_posted_date_min))
else:
    select_posted_date_range = st.sidebar.slider('Select Posted Date range', value=[filtered_posted_date_min, filtered_posted_date_max], min_value=filtered_posted_date_min,max_value=filtered_posted_date_max)
    filtered_data = filtered_data[filtered_data['PostedDate_year'].between(select_posted_date_range[0], select_posted_date_range[1])].reset_index(drop=True)

filtered_award_date_min = filtered_data['AwardDate_year'].min().astype(int)
filtered_award_date_max = filtered_data['AwardDate_year'].max().astype(int)
select_award_date_range = st.sidebar.slider('Select Award Date range', value=[filtered_award_date_min, filtered_award_date_max], min_value=filtered_award_date_min,max_value=filtered_award_date_max)
# if select_award_date_range != []:
#     filtered_data = filtered_data[filtered_data['AwardDate_year'].between(select_award_date_range[0], select_award_date_range[1])].reset_index(drop=True)

st.markdown('#### Raw Filtered Data')
st.metric('Number of Rows', value=f'{len(filtered_data):,}')
st.dataframe(filtered_data, use_container_width=True, column_config={"Link": st.column_config.LinkColumn()})


st.sidebar.markdown('## Pivot Table Options')
select_pivot_rows = st.sidebar.selectbox('Select Row Variable', options=filtered_data.columns.to_list(), index=17)

select_pivot_cols = st.sidebar.selectbox('Select Column Variable', options=filtered_data.columns.to_list(), index=27)

st.subheader('Filtered Data Pivot')
st.markdown('#### {} vs {}'.format(select_pivot_rows, select_pivot_cols))
# award_data = data[data['Type']=='Award Notice']

pivot_data = filtered_data[[select_pivot_rows, select_pivot_cols]]

pivot_from_pivot_data = pivot_data.groupby(select_pivot_rows).agg(
    Count=(select_pivot_cols, np.count_nonzero),
    Sum=(select_pivot_cols, np.sum),
    Mean=(select_pivot_cols, np.mean),
    StdDev=(select_pivot_cols, np.std),
    Min=(select_pivot_cols, np.min),
    Max=(select_pivot_cols, np.max)
).reset_index()
st.dataframe(pivot_from_pivot_data, use_container_width=True)

pivot_plot_sum = plt.bar(pivot_from_pivot_data, x=select_pivot_rows, y='Sum', title='Sum Total {} by {}'.format(select_pivot_cols, select_pivot_rows))
pivot_plot_sum.update_xaxes(type='category')
pivot_plot_sum.update_layout(
    yaxis=dict(
        tickfont=dict(size=15),
    ),
    xaxis=dict(
        tickfont=dict(size=15)
    ),
    yaxis_title=dict(
        font=dict(size=20)
    ),
    xaxis_title=dict(
        font=dict(size=20)
    ),
    title=dict(
        font=dict(size=20)
    )
)

st.plotly_chart(pivot_plot_sum, use_container_width=True)

pivot_plot_mean = plt.bar(pivot_from_pivot_data, x=select_pivot_rows, y='Mean', title='Average {} by {}'.format(select_pivot_cols, select_pivot_rows), error_y='StdDev')
pivot_plot_mean.update_xaxes(type='category')
pivot_plot_mean.update_layout(
    yaxis=dict(
        tickfont=dict(size=15),
    ),
    xaxis=dict(
        tickfont=dict(size=15)
    ),
    yaxis_title=dict(
        text='Mean +/- StdDev',
        font=dict(size=20)
    ),
    xaxis_title=dict(
        font=dict(size=20)
    ),
    title=dict(
        font=dict(size=20)
    )
)

st.plotly_chart(pivot_plot_mean, use_container_width=True)