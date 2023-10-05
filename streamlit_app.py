
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.figure_factory as ff
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
    txCounty = conn.query('SELECT * from tx_county_district;') 
    return data, txCounty


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
    """
        histogram
        DISTRICT
        HIGHWAY FUN
        PAVMENT TYPE
        AADT
        TRUCK PCT
        tavg
        prcp
    """
    fig1 = px.histogram(data, x=para+"_"+model, log_y = True).update_layout(xaxis_title = para)
    fig1.update_traces(marker_line_width=1,marker_line_color="black", xbins=dict(start=0.0))
    fig2 = px.box(data, x = "District_Name", y=para+"_"+model).update_layout(yaxis_title = para)
    fig3 = px.box(data, x = "HIGHWAY_FUN", y=para+"_"+model).update_layout(yaxis_title = para)
    fig4 = px.box(data, x = "PAV_TYPE", y=para+"_"+model).update_layout(yaxis_title = para)

    fig5 = px.scatter(data, x="AADT", y=para+"_"+model).update_layout(yaxis_title = para)
    fig6 = px.scatter(data, x="TRUCK_PCT", y=para+"_"+model).update_layout(yaxis_title = para)
    fig7 = px.scatter(data, x="tavg", y=para+"_"+model).update_layout(yaxis_title = para)
    fig8 = px.scatter(data, x="prcp",y=para+"_"+model).update_layout(yaxis_title = para)
 
    col1, col2 = st.columns(2)
    with col1:
        with st.container():
            st.plotly_chart(fig1,use_container_width=True)
            st.plotly_chart(fig2,use_container_width=True)
            st.plotly_chart(fig3,use_container_width=True)
            st.plotly_chart(fig4,use_container_width=True)
    with col2:
        with st.container():
            st.plotly_chart(fig5,use_container_width=True)
            st.plotly_chart(fig6,use_container_width=True)
            st.plotly_chart(fig7,use_container_width=True)
            st.plotly_chart(fig8,use_container_width=True)

# MySQL connection and load data
conn = st.experimental_connection("mysql", type="sql")
data, txCounty = dataLoad(_conn=conn)


col1, col2 = st.columns([3,2], gap = "medium")
with col1:
    with st.container():
        st.subheader("Effect of variables")

        col11, col12 = st.columns(2)
        with col11:
            modelOpt = st.selectbox("select model:",('m1', 'm2'))
        with col12:
            paraOpt = st.selectbox("select parameter:", ("a", "b", "c", "t0"))

        data_temp = dataFilter(data, model = modelOpt) # Select data for selected model
        distPlot(data= data_temp, para = paraOpt, model = modelOpt) # plot distribution and effect of variables

with col2:
    with st.container():
        st.subheader("Geo Distribution")
        varthreshold = st.slider("threshold:",  min_value=None, max_value=None, value=0)

        # pivot information based on the threshold       
        pivot_info = dataPivot(data = data_temp, threshold = varthreshold, para = paraOpt, model = modelOpt)
        dataMap = txCounty.merge(pivot_info[["County_FIPS_Code", "compare", "count"]], how = "left", on = "County_FIPS_Code")
        st.write(dataMap)
        
        fig = ff.create_choropleth(
            fips=dataMap["County_FIPS_Code"].astype("int").tolist(), values=dataMap["count"].tolist(),
            scope=["Texas"], county_outline={'color': 'rgb(255,255,255)', 'width': 0.5},
            legend_title='Population per county')
        fig.update_layout(
            legend_x = 0,
            annotations = {'x': -0.12, 'xanchor': 'left'}
        )

        fig.layout.template = None
        
        st.plotly_chart(fig)

    
    
    
