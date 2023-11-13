
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from urllib.request import urlopen
import json
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(layout="wide", 
                   page_title='Sensitivity', 
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
    data = conn.query('SELECT * from fricPAwh;') 
    distr_cont = conn.query('SELECT * from distr_cont_onlineApp;') 
    return data, distr_cont


# Performance model I
def m1(x,data):
    a = x[0] + x[1]*data["SH"] + x[2]*data["US"]+x[3]*data["IH"]
    b = x[4] + x[5]*data["AC_Thick"]+x[6]*data["COM"]+x[7]*data["JCP"]+x[8]*data["CRCP"]+ x[9]*data["tavg"]+x[10]*data["prcp"]+x[11]*data["TRUCK_PCT"]
    c = x[12]+x[13]*data["AADT"]
    return a+b*np.exp(-c*data["AGE"])

x1 = np.array([7.049209e+00, -2.600203e+00, -8.963720e+00, -1.236767e+01,
               2.090193e+02,-5.817576e+00, -9.876824e+00, -1.143599e+01, -8.430132e+00, -2.608191e+00, 1.906576e-01, 3.395223e-01,
               1.083621e-01, -1.374227e-07])
# a: const  SH US IH 
# b: const AC_Thick COM JCP CRCP tavg prcp TRUCK_PCT    
# c: const AADT

# Performance model II    
def m2(x,data):
    a = x[0] + x[1]*data["SH"] + x[2]*data["US"]+x[3]*data["IH"]+x[4]*data["TRUCK_PCT"]
    b = x[5] + x[6]*data["AC_Thick"]+x[7]*data["COM"]+x[8]*data["JCP"]+x[9]*data["CRCP"]+ x[10]*data["tavg"]+x[11]*data["prcp"]
    c = x[12]+x[13]*data["AADT"]
    t0 = x[14]
    return a+b*np.exp(-c*(data["AGE"]-t0))   

x2 = np.array([1.184951e+01, -2.705696e+00, -9.117392e+00, -1.275260e+01, 3.073346e-01,
               2.116791e+02, -6.001680e+00, -1.025022e+01, -1.183063e+01, -8.687251e+00,-2.709774e+00,1.973484e-01,
               1.345769e-01,-1.931186e-07,
               5.967551e-01])

#const SH US IH TRUCK_PCT
#const AC_Thick COM  JCP CRCP tavg prcp
#const AADT
#const

try:
    if st.session_state["allow"]:

        st.write("success")
    else:
        st.write("Login to view the app")
        st.session_state["allow"] = check_password()
except:
    st.write("Login to view the app")
    st.session_state["allow"] = check_password()

plotData = pd.DataFrame({"AGE": np.repeat(range(11),21), 
                            "PAV_TYPE": (["AC_Thin", "AC_Thick", "COM", "JCP", "CRCP"]+["AC_Thick"]*16)*11, 
                            "HIGHWAY_FUN": (["FM"]*5+ ["FM", "SH", "US", "IH"]+ ["FM"]*12)*11, 
                            "AADT": ([5000]*9+[2000, 5000, 15000]+[5000]*9)*11, 
                            "TRUCK_PCT": ([15]*12+ [10, 15, 25]+[15]*6)*11, 
                            "tavg": ([67]*15+ [56, 67, 72]+[67]*3)*11, 
                            "prcp":([35]*18+[33,35,45])*11, 
                            "tag": (["PAV_TYPE"]*5 + ["HIGHWAY_FUN"]*4+["AADT"]*3+["TRUCK_PCT"]*3+["tavg"]*3+["prcp"]*3)*11}).sort_values(by = ["tag", "AGE"])

plotData_v1 = pd.get_dummies(plotData[["PAV_TYPE", "HIGHWAY_FUN"]]).rename({'PAV_TYPE_AC_Thick': "AC_Thick", 
                                                                            'PAV_TYPE_AC_Thin':"AC_Thin",
                                                                            'PAV_TYPE_COM': "COM",
                                                                            'PAV_TYPE_CRCP':"CRCP",
                                                                            'PAV_TYPE_JCP':"JCP", 
                                                                            'HIGHWAY_FUN_FM':"FM", 
                                                                            'HIGHWAY_FUN_IH':"IH",
                                                                            'HIGHWAY_FUN_SH':"SH", 
                                                                            'HIGHWAY_FUN_US':"US"})
plotData = pd.concat([plotData, plotData_v1], axis= 1)

with st.sidebar:
    modelOpt = st.selectbox("Select model:", ('m1', 'm2'))
    # plot
    if modelOpt == "m1":
        plotData["SN"] = m1(x1, plotData)
    if modelOpt == "m2":       
        plotData["SN"] = m2(x2, plotData)

col1, col2, col3 = st.columns(3)
with col1:
    with st.container():
        st.write("Pavement Type")
        fig = px.line(plotData.loc[plotData["tag"] == "PAV_TYPE"], 
                        x = "AGE", 
                        y = "SN", 
                        color= "PAV_TYPE")
        st.plotly_chart(fig,use_container_width=True)

    with st.container():
        st.write("Facility Type")
        fig = px.line(plotData.loc[plotData["tag"] == "HIGHWAY_FUN"], 
                        x = "AGE", 
                        y = "SN", 
                        color= "HIGHWAY_FUN")
        st.plotly_chart(fig,use_container_width=True)

with col2:
    with st.container():
        st.write("AADT")
        fig = px.line(plotData.loc[plotData["tag"] == "AADT"], 
                        x = "AGE", 
                        y = "SN", 
                        color= "AADT")
        st.plotly_chart(fig,use_container_width=True)


    with st.container():
        st.write("Truck Percentage")
        fig = px.line(plotData.loc[plotData["tag"] == "TRUCK_PCT"], 
                        x = "AGE", 
                        y = "SN", 
                        color= "TRUCK_PCT")
        st.plotly_chart(fig,use_container_width=True)

with col3:
    with st.container():
        st.write("tavg")
        fig = px.line(plotData.loc[plotData["tag"] == "tavg"], 
                        x = "AGE", 
                        y = "SN", 
                        color= "tavg")
        st.plotly_chart(fig,use_container_width=True)

    with st.container():
        st.write("Precipitation")
        fig = px.line(plotData.loc[plotData["tag"] == "prcp"], 
                        x = "AGE", 
                        y = "SN", 
                        color= "prcp")
        st.plotly_chart(fig,use_container_width=True)