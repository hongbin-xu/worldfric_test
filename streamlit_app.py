
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
st.set_page_config(layout="wide")
from urllib.request import urlopen
import json
from htbuilder import HtmlElement, div, ul, li, br, hr, a, p, img, styles, classes, fonts
from htbuilder.units import percent, px
from htbuilder.funcs import rgba, rgb

def image(src_as_string, **style):
    return img(src=src_as_string, style=styles(**style))

def link(link, text, **style):
    return a(_href=link, _target="_blank", style=styles(**style))(text)

def layout(*args):
    style = """
    <style>
      # MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
     .stApp { bottom: 105px; }
    </style>
    """
    style_div = styles(
        position="fixed",
        left=0,
        bottom=0,
        margin=px(0, 0, 0, 0),
        width=percent(100),
        color="black",
        text_align="center",
        height="auto",
        opacity=1
    )

    style_hr = styles(
        display="block",
        margin=px(8, 8, "auto", "auto"),
        border_style="inset",
        border_width=px(2)
    )

    body = p()
    foot = div(
        style=style_div
    )(
        hr(
            style=style_hr
        ),
        body
    )

    st.markdown(style, unsafe_allow_html=True)

    for arg in args:
        if isinstance(arg, str):
            body(arg)

        elif isinstance(arg, HtmlElement):
            body(arg)

    st.markdown(str(foot), unsafe_allow_html=True)


def footer():
    myargs = [
        "Made by Hongbin Xu",
        #image('https://avatars3.githubusercontent.com/u/45109972?s=400&v=4',
        #      width=px(25), height=px(25)),

        #link("https://twitter.com/ChristianKlose3", "@ChristianKlose3"),
        br(),
        "The University of Texas at Austin",
        #link("https://buymeacoffee.com/chrischross", image('https://i.imgur.com/thJhzOO.png')),
    ]
    layout(*myargs)



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

# MySQL connection and load data
conn = st.experimental_connection("mysql", type="sql")
data, txCounty = dataLoad(_conn=conn)

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

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
        varthreshold = st.slider("threshold:",  min_value=data_temp[paraOpt+"_"+modelOpt].min(), max_value=data_temp[paraOpt+"_"+modelOpt].max(), value=data_temp[paraOpt+"_"+modelOpt].min())

        # pivot information based on the threshold       
        pivot_info = dataPivot(data = data_temp, threshold = varthreshold, para = paraOpt, model = modelOpt)
        datAbove = txCounty.merge(pivot_info.loc[pivot_info["compare"], ["County_FIPS_Code", "compare", "count"]], how = "left", on = "County_FIPS_Code").replace(np.nan,0)
        dataBelow = txCounty.merge(pivot_info.loc[~pivot_info["compare"], ["County_FIPS_Code", "compare", "count"]], how = "left", on = "County_FIPS_Code").replace(np.nan,0)

        st.write("Number of project with "+ paraOpt + " above threshold")
        fig = px.choropleth(datAbove, geojson=counties, locations='County_FIPS_Code', color='count',
                           color_continuous_scale="Viridis",
                           scope="usa",
                           hover_data = ["District_Name", "County_Name", "count"])
        fig.update_geos(fitbounds="locations")
        st.plotly_chart(fig,use_container_width=True)

        st.write("Number of project with "+ paraOpt + " below threshold")
        fig = px.choropleth(dataBelow, geojson=counties, locations='County_FIPS_Code', color='count',
                           color_continuous_scale="Viridis",
                           scope="usa",
                           hover_data = ["District_Name", "County_Name", "count"])
        fig.update_geos(fitbounds="locations")
        st.plotly_chart(fig,use_container_width=True)

    
    
if __name__ == "__main__":
    footer()