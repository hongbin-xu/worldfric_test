
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
                   page_title='Friction model', 
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


# Pivot information based on the thresho

# Performance model I
def m1(x,data):
    a = x[0] + x[1]*data["SH"] + x[2]*data["US"]+x[3]*data["IH"]
    b = x[4] + x[5]*data["AC_Thick"]+x[6]*data["COM"]+x[7]*data["JCP"]+x[8]*data["CRCP"]+ x[9]*data["tavg"]+x[10]*data["prcp"]+x[11]*data["TRUCK_PCT"]
    c = x[12]+x[13]*data["AADT"]
    return a+b*np.exp(-c*data["AGE"])


# Performance model II    
def m2(x,data):
    a = x[0] + x[1]*data["SH"] + x[2]*data["US"]+x[3]*data["IH"]+x[4]*data["TRUCK_PCT"]
    b = x[5] + x[6]*data["AC_Thick"]+x[7]*data["COM"]+x[8]*data["JCP"]+x[9]*data["CRCP"]+ x[10]*data["tavg"]+x[11]*data["prcp"]
    c = x[12]+x[13]*data["AADT"]
    t0 = x[14]
    return a+b*np.exp(-c*(data["AGE"]-t0))   

# a: const  SH US IH 
# b: const AC_Thick COM JCP CRCP tavg prcp TRUCK_PCT    
# c: const AADT

#const SH US IH TRUCK_PCT
#const AC_Thick COM  JCP CRCP tavg prcp
#const AADT
#const

def m1_v1(x,data):
    a = x[0] 
    b = x[1] + x[2]*data["AC_Thick"]+x[3]*data["COM"]+x[4]*data["JCP"]+x[5]*data["CRCP"]+ x[6]*data["tavg"]+x[7]*data["prcp"]+x[8]*data["TRUCK_PCT"]
    c = x[9]+x[10]*data["AADT"]
    return a+b*np.exp(-c*data["AGE"])
# a: const
# b: const AC_Thick COM JCP CRCP tavg prcp TRUCK_PCT    
# c: const AADT

def m2_v1(x,data):
    a = x[0] +x[1]*data["TRUCK_PCT"]
    b = x[2] + x[3]*data["AC_Thick"]+x[4]*data["COM"]+x[5]*data["JCP"]+x[6]*data["CRCP"]+ x[7]*data["tavg"]+x[8]*data["prcp"]
    c = x[9]+x[10]*data["AADT"]
    t0 = x[11]
    return a+b*np.exp(-c*(data["AGE"]-t0))   

#const TRUCK_PCT
#const AC_Thick COM  JCP CRCP tavg prcp
#const AADT
#const
x = {"stepwise":{"m1":np.array([7.049209e+00, -2.600203e+00, -8.963720e+00, -1.236767e+01,
                                2.090193e+02,-5.817576e+00, -9.876824e+00, -1.143599e+01, -8.430132e+00, -2.608191e+00, 1.906576e-01, 3.395223e-01,
                                1.083621e-01, -1.374227e-07]),
                 "m2":np.array([1.184951e+01, -2.705696e+00, -9.117392e+00, -1.275260e+01, 3.073346e-01,
                                2.116791e+02, -6.001680e+00, -1.025022e+01, -1.183063e+01, -8.687251e+00,-2.709774e+00,1.973484e-01,
                                1.345769e-01,-1.931186e-07,
                                5.967551e-01])},
     "step_iter":{"m1":np.array([7.049209e+00, -2.600203e+00, -8.963720e+00, -1.236767e+01,
                                2.090193e+02,-5.817576e+00, -9.876824e+00, -1.143599e+01, -8.430132e+00, -2.608191e+00, 1.906576e-01, 3.395223e-01,
                                1.083621e-01, -1.374227e-07]), #1
                  "m2":np.array([1.904065e+01, -2.780562e+00,-9.224207e+00,-1.299706e+01,3.126058e-01, 
                                 1.975575e+02,-5.801182e+00,-9.939388e+00,-1.147162e+01,-8.420724e+00,-2.633975e+00,1.929804e-01,
                                 1.491272e-01,-3.103310e-08,
                                 3.117803e-01])},           #34
     "remove_facility":{"m1":np.array([21.838598,244.464013,-10.340636,-17.486844,-22.654649,-14.556765,-3.339557,0.280081,-0.005669,0.179864,0.000003]), #4
                        "m2":np.array([15.455118,0.008352,216.724455,-9.174424,-15.323157,-19.658794,-12.895752,-2.870935,0.243233,0.124019,0.000002,0.276063])}} #2

try:
    if st.session_state["allow"]:
        # MySQL connection and load data
        conn = st.connection("mysql", type="sql")
        data, distr_cont = dataLoad(_conn=conn)

        with st.sidebar:
            modelOpt = st.selectbox("Select model:", ('m1', 'm2'))
            with st.expander("DISTR"):
                distOpt = st.multiselect("DISTR", distr_cont["DISTR"].unique(), 
                                        distr_cont["DISTR"].unique(), label_visibility="hidden")
            with st.expander("CONT"):
                contOpt = st.multiselect("CONT", distr_cont.loc[distr_cont["DISTR"].isin(distOpt)]["CONT"].values, 
                                        distr_cont.loc[distr_cont["DISTR"].isin(distOpt)]["CONT"].values,
                                        label_visibility="hidden")
            highOpt = st.multiselect("Facility", ("FM", "SH", "US", "IH"),("FM", "SH", "US", "IH"))
            pavOpt = st.multiselect("Pavement", ("AC_Thin", "AC_Thick", "COM", "JCP", "CRCP"), ("AC_Thin", "AC_Thick", "COM", "JCP", "CRCP"))
            data_v1 = data.loc[data["DISTR"].isin(distOpt)&data["CONT"].isin(contOpt)&data["HIGHWAY_FUN"].isin(highOpt)&data["PAV_TYPE"].isin(pavOpt)]

        col1, col2 = st.colummns()
        with col1:
            st.write("m1")
        if modelOpt == "m1":
            st.write("m2")
            #plotData = pd.melt(data_v1.rename(columns ={"SN_cummin": "observed", "SN": "original"}), id_vars="AGE", value_vars=["observed", "pred1"], value_name="SN", var_name = "pred vs. obs")
            #fig= px.box(plotData, x = "AGE", y = "SN", color= "pred vs. obs") 
            #st.plotly_chart(fig,use_container_width=True, theme= None)

        if modelOpt == "m2":       
            st.write("m2")

            #plotData = pd.melt(data_v1.rename(columns ={"SN_cummin": "observed", "SN": "original"}), id_vars="AGE", value_vars=["observed", "pred2"], value_name="SN", var_name = "pred vs. obs")
            #fig= px.box(plotData, x = "AGE", y = "SN", color= "pred vs. obs") 
            #st.plotly_chart(fig,use_container_width=True, theme= None)
        
        with col1:
            st.write("m1")
    else:
        st.write("Login to view the app")
        st.session_state["allow"] = check_password()
except:
    st.write("Login to view the app")
    st.session_state["allow"] = check_password()
        
