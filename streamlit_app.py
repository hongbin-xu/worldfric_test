
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

st.set_page_config(layout="wide")

@st.cache_data
def dataLoad(_conn):
    """
    mode1: select for each segment
    mode2: select for multiple segment
    creating 2d array of the height measurement
    """
    data = conn.query('SELECT * from est_per_proj;') 
    data.replace("#NAME?", np.nan, inplace = True)
    return data


# Filter data for different model
@st.cache_data
def dataFilter(data, model):
    model_data = data.loc[(data["a_"+model].notna())&(data["a_"+model].notna())].reset_index(drop = True)
    return model_data


# Pivot information based on the threshold
@st.cache_data
def dataPivot(data, threshold, para, model):
    data = data.copy()
    data["compare"] = data[para+"_"+model]>=threshold #compare with the threshold
    pivot_sum = data.groupby(by = ['District_Number', 'District_Name', 'District_Abbr', 'County_Number', 'County_FIPS_Code', 'County_Name', "compare"]).size().reset_index(name = "count") #pivot information based on the threshold    
    return pivot_sum



@st.cache_data
def distPlot(data, para, model):
    fig = make_subplots(rows =4, cols=2)
    fig.add_trace(px.histogram(data, x = paraOpt+"_"+modelOpt))
    fig.show()

# MySQL connection and load data
conn = st.experimental_connection("mysql", type="sql")
data = dataLoad(_conn=conn)

col1, col2 = st.columns([3,2], gap = "medium")
with col1:
    with st.container():
        st.subheader("Effect of variables")

        col11, col12 = st.columns(2)
        with col11:
            modelOpt = st.selectbox("select model:",('m1', 'm2'))
        with col12:
            paraOpt = st.selectbox("select parameter:", ("a", "b", "c", "t0"))
        
        data_temp = dataFilter(data, model = modelOpt)
# Histogram, District, HIGHWAY_FUN, PAV_TYPE, AADT, TRUCK_PCT, tavg, prcp
        fig = px.histogram(data_temp, paraOpt +"_"+modelOpt)
        fig.show()
        distPlot(data= data_temp, para = paraOpt, model = modelOpt)


with col2:
    with st.container():
        st.subheader("Geo Distribution")
        varthreshold = st.slider("threshold:",  min_value=None, max_value=None, value=0)
        pivot_info = dataPivot(data = data_temp, threshold = varthreshold, para = paraOpt, model = modelOpt)
        st.write(pivot_info)
        # Extract transverse profile
                
        # Plot transverse profile
        fig = px.line(scanData_v1, x="DIST", y="Height", labels = {"DIST": "Transverse Distance (mm)", "Height": "Height (mm}"}, template = "plotly_dark")
        st.plotly_chart(fig)

        # View and download data
        st.download_button(label="Download profile", data=scanData_v1.to_csv().encode('utf-8'), file_name="transProfile_seg_" +str(segID)+"_scan_"+str(id_)+".csv", mime = "csv")
        if st.checkbox('Show raw transverse profile data'):
            st.write(scanData_v1)
    
    
    
    
