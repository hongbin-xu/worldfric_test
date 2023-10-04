
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

@st.cache_data
def dataLoad(_conn):
    """
    mode1: select for each segment
    mode2: select for multiple segment
    creating 2d array of the height measurement
    """
    data = conn.query('SELECT * from est_per_proj;') 
    return data

# Pivot information based on the threshold
@st.cache_data
def dataPivot(data, threshold, para, model):
    model_data = data.loc[(data[para+"_"+model]!=np.inf)&(data[para+"_"+model]!=(-np.inf))]
    model_data["compare"] = model_data[para+"_"+model]>=threshold #compare with the threshold
    pivot_sum = model_data.groupby(by = ['District_Number', 'District_Name', 'District_Abbr', 'County_Number', 'County_FIPS_Code', 'County_Name', "compare"]).size().reset_index(name = "count") #pivot information based on the threshold    
    return pivot_sum

@st.cache_data
def distPlot(data, para, model):
    model_data = data.loc[(data[para+"_"+model]!=np.inf)&(data[para+"_"+model]!=(-np.inf))]

# MySQL connection
conn = st.experimental_connection("mysql", type="sql")
data = dataLoad(_conn=conn)

st.write(data)

col1, col2 = st.columns(2, gap = "medium")
with col1:
    with st.container():
        st.subheader("Effect of variables")
        modelOpt = st.selectbox("select model:",('m1', 'm2'))
        st.write(modelOpt)
        paraOpt = st.selectbox("select parameter:", ("a", "b", "c", "t0"))

        


with col2:
    with st.container():
        st.subheader("Geo Distribution")
        varthreshold = st.slider("threshold:",  min_value=None, max_value=None, value=0)
        pivot_info = dataPivot(data = data, threshold = varthreshold, para = paraOpt, model = modelOpt)
        # Extract transverse profile
                
        # Plot transverse profile
        fig = px.line(scanData_v1, x="DIST", y="Height", labels = {"DIST": "Transverse Distance (mm)", "Height": "Height (mm}"}, template = "plotly_dark")
        st.plotly_chart(fig)

        # View and download data
        st.download_button(label="Download profile", data=scanData_v1.to_csv().encode('utf-8'), file_name="transProfile_seg_" +str(segID)+"_scan_"+str(id_)+".csv", mime = "csv")
        if st.checkbox('Show raw transverse profile data'):
            st.write(scanData_v1)
    
    
    
    
