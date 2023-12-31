
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from urllib.request import urlopen
import json

st.set_page_config(layout="wide", 
                   page_title='Variabele effect', 
                   menu_items={
                       'Get help': "mailto:hongbinxu@utexas.edu",
                       'About': "Developed and maintained by Hongbin Xu",
                   })


# Authentication function
def check_password():
    """Returns `True` if the user had a correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if (
            st.session_state["username"] in st.secrets["passwords"]
            and st.session_state["password"]
            == st.secrets["passwords"][st.session_state["username"]]
        ):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store username + password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show inputs for username + password.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.text_input("Username", on_change=password_entered, key="username")
        st.text_input(
            "Password", type="password", on_change=password_entered, key="password"
        )
        st.error("😕 User not known or password incorrect")
        return False
    else:
        # Password correct.
        return True

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
    model_data = data.loc[(data["a_"+model].notna())&(data["a_"+model].notna())&(data["PAV_TYPE"]!="other")].reset_index(drop = True)
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

try:
    if st.session_state["allow"]:
        # MySQL connection and load data
        conn = st.connection("mysql", type="sql")
        data, txCounty = dataLoad(_conn=conn)

        with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
            counties = json.load(response)

        with st.sidebar:
            modelOpt = st.selectbox("select model:",('m1', 'm2'))
            paraOpt = st.selectbox("select parameter:", ("a", "b", "c", "t0"))
            data_temp = dataFilter(data, model = modelOpt) # Select data for selected model
            varthreshold = st.slider("threshold:",  min_value=data_temp[paraOpt+"_"+modelOpt].min(), max_value=data_temp[paraOpt+"_"+modelOpt].max(), value=data_temp[paraOpt+"_"+modelOpt].min())


        col1, col2 = st.columns([3,2], gap = "medium")
        with col1:
            with st.container():
                st.subheader("Effect of variables")

                col11, col12 = st.columns(2)
                distPlot(data= data_temp, para = paraOpt, model = modelOpt) # plot distribution and effect of variables

        with col2:
            with st.container():
                st.subheader("Geo Distribution")

                # pivot information based on the threshold       
                pivot_info = dataPivot(data = data_temp, threshold = varthreshold, para = paraOpt, model = modelOpt)
                datAbove = txCounty.merge(pivot_info.loc[pivot_info["compare"], ["County_FIPS_Code", "compare", "count"]], how = "left", on = "County_FIPS_Code").replace(np.nan,0)
                dataBelow = txCounty.merge(pivot_info.loc[~pivot_info["compare"], ["County_FIPS_Code", "compare", "count"]], how = "left", on = "County_FIPS_Code").replace(np.nan,0)

                st.write("Number of project with "+ paraOpt + " above threshold")
                fig = px.choropleth(datAbove, geojson=counties, locations='County_FIPS_Code', color='count',
                                color_continuous_scale="Viridis",
                                scope="usa",
                                range_color=(0, datAbove["count"].max()),
                                hover_data = ["District_Name", "County_Name", "count"])
                fig.update_geos(fitbounds="locations")
                st.plotly_chart(fig,use_container_width=True)

                st.write("Number of project with "+ paraOpt + " below threshold")
                fig = px.choropleth(dataBelow, geojson=counties, locations='County_FIPS_Code', color='count',
                                color_continuous_scale="Viridis",
                                scope="usa",
                                range_color=(0, dataBelow["count"].max()),
                                hover_data = ["District_Name", "County_Name", "count"])
                fig.update_geos(fitbounds="locations")
                st.plotly_chart(fig,use_container_width=True)
    else:
        st.write("Login to view the app")
        st.session_state["allow"] = check_password()
except:
    st.write("Login to view the app")
    st.session_state["allow"] = check_password()

        
