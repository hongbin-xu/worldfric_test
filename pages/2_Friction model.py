
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
    data = conn.query('SELECT * from fric;') 
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

# with district effect
def mdistrict(x1, x2, data, model = "m1", group_method = "a"):
    if model == "m1":
        a = x1[0] 
        b = x1[1] + x1[2]*data["AC_Thick"]+x1[3]*data["COM"]+x1[4]*data["JCP"]+x1[5]*data["CRCP"]+ x1[6]*data["tavg"]+x1[7]*data["prcp"]+x1[8]*data["TRUCK_PCT"]
        c = x1[9]+x1[10]*data["AADT"]   
        dist = (x2[0]*data['DAL']+ x2[1]*data['AMA']+ x2[2]*data['HOU']+ 
                x2[3]*data['PAR']+x2[4]*data['WFS']+x2[5]*data['BRY']+x2[6]*data['CRP']+x2[7]*data['SAT']+ 
                x2[8]*data['YKM']+x2[9]*data['ODA']+x2[10]*data['BMT']+x2[11]*data['LFK'] +x2[12]*data['AUS'])
        if group_method == "a":
            a = a+dist
        if group_method == "b":
            b = b+dist
        return a + b*np.exp(-c*data["AGE"])

    if model == "m2":
        a = x1[0] +x1[1]*data["TRUCK_PCT"]
        b = x1[2] + x1[3]*data["AC_Thick"]+x1[4]*data["COM"]+x1[5]*data["JCP"]+x1[6]*data["CRCP"]+ x1[7]*data["tavg"]+x1[8]*data["prcp"]
        c = x1[9]+x1[10]*data["AADT"]
        t0 = x1[11]
        dist = (x2[0]*data['DAL']+ x2[1]*data['AMA']+ x2[2]*data['HOU']+ 
                x2[3]*data['PAR']+x2[4]*data['WFS']+x2[5]*data['BRY']+x2[6]*data['CRP']+x2[7]*data['SAT']+ 
                x2[8]*data['YKM']+x2[9]*data['ODA']+x2[10]*data['BMT']+x2[11]*data['LFK'] +x2[12]*data['AUS'])
        if group_method == "a":
            a = a+dist
        if group_method == "b":
            b = b+dist
        return a + b*np.exp(-c*(data["AGE"]-t0)) 
    
#const TRUCK_PCT
#const AC_Thick COM  JCP CRCP tavg prcp
#const AADT
#const
x1 = {"stepwise":{"m1":np.array([7.049209e+00, -2.600203e+00, -8.963720e+00, -1.236767e+01,
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

# Initial value
x = {"stepwise":{"m1":np.array([7.049209e+00, -2.600203e+00, -8.963720e+00, -1.236767e+01,
                                2.090193e+02, -5.817576e+00, -9.876824e+00, -1.143599e+01,
                                -8.430132e+00, -2.608191e+00,  1.906576e-01,  3.395223e-01,
                                1.083621e-01, -1.374227e-07]),
                 "m2":np.array([1.184951e+01, -2.705696e+00, -9.117392e+00, -1.275260e+01, 3.073346e-01,
                                2.116791e+02, -6.001680e+00, -1.025022e+01, -1.183063e+01, -8.687251e+00,-2.709774e+00,1.973484e-01,
                                1.345769e-01,-1.931186e-07,
                                5.967551e-01])},
     "step_iter":{"m1":np.array([7.049209e+00, -2.600203e+00, -8.963720e+00, -1.236767e+01,
                                2.090193e+02,-5.817576e+00, -9.876824e+00, -1.143599e+01, -8.430132e+00, -2.608191e+00, 1.906576e-01, 3.395223e-01,
                                1.083621e-01, -1.374227e-07]), #1
                  "m2":np.array([1.904065e+01, -2.780562e+00, -9.224207e+00, -1.299706e+01,
                                3.126058e-01,  1.975575e+02, -5.801182e+00, -9.939388e+00,
                                -1.147162e+01, -8.420724e+00, -2.633975e+00,  1.929804e-01,
                                1.491272e-01, -3.103310e-08,  3.117803e-01])},           #34
     "remove_facility":{"m1":np.array([2.74775611e+01,  1.87518114e+02, -5.99908654e+00, -1.24793455e+01,
                                        -1.98010817e+01, -1.06650145e+01, -2.58736894e+00,  2.66982783e-01,
                                        -8.24695544e-03, -3.02872924e-02,  9.07993449e-05]), #4
                        "m2":np.array([1.54551180e+01,  8.35200000e-03,  2.16724455e+02, -9.17442400e+00,
                                       -1.53231570e+01, -1.96587940e+01, -1.28957520e+01, -2.87093500e+00,
                                        2.43233000e-01,  1.24019000e-01,  2.00000000e-06,  2.76063000e-01])}, 
     'District-a': {'m1': np.array([-14.99377031,  -9.34209793,   0.38054699,   8.31692934,
                                    -3.05884358,  -1.91602142,  -3.72421799,  -2.42262516,
                                    -4.30360067,   0.98628697,   0.3731446 ,   2.0343066 ,
                                    -0.19648616]),
                    'm2': np.array([-15.17340897, -11.65252878,   3.51311267,   1.04489045,
                                    -9.58837323,  -6.1818586 ,   1.12447323,  -0.75967163,
                                    -1.2924821 ,  -1.65026649,   0.29063893,   3.45658544,
                                    1.89014777])},
    'District-b': {'m1': np.array([-1.55273302e+18,  8.55386115e+00, -1.64231067e+13,  8.18061439e+02,
                                    4.32513456e+01, -1.70839702e+00, -2.15732927e+05, -3.00884772e+10,
                                    -1.58046292e+04, -3.07578917e+03, -3.12837524e+08, -7.32758556e+00,
                                    -1.20692454e+16]),
                    'm2': np.array([-27.1920906 , -15.42510742,   6.90382704,   2.24347716,
                                    -11.40708527,  -7.58160632,   0.98342646,  -1.87753783,
                                    -1.71774125,  -2.43522073,   0.39888897,   4.19585498,
                                    2.54567803])}
     } #2


if st.session_state["allow"]:
    # MySQL connection and load data
    conn = st.connection("mysql", type="sql")
    data, distr_cont = dataLoad(_conn=conn)
    with st.sidebar:
        #modelOpt = st.selectbox("Select model:", ('m1', 'm2'))
        with st.expander("DISTR"):
            distOpt = st.multiselect("DISTR", distr_cont["DISTR"].unique(), 
                                    distr_cont["DISTR"].unique(), label_visibility="hidden")
        with st.expander("CONT"):
            contOpt = st.multiselect("CONT", distr_cont.loc[distr_cont["DISTR"].isin(distOpt)]["CONT"].values, 
                                    distr_cont.loc[distr_cont["DISTR"].isin(distOpt)]["CONT"].values,
                                    label_visibility="hidden")
        highOpt = st.multiselect("Facility", ("FM", "SH", "US", "IH"),("FM", "SH", "US", "IH"))
        pavOpt = st.multiselect("Pavement", ("AC_Thin", "AC_Thick", "AC_Com", "JCP", "CRCP"), ("AC_Thin", "AC_Thick", "AC_Com", "JCP", "CRCP"))
        data_v1 = data.loc[data["DISTR"].isin(distOpt)&data["CONT"].isin(contOpt)&data["HIGHWAY_FUN"].isin(highOpt)&data["PAV_TYPE"].isin(pavOpt)]

    # stepwise Model
    st.subheader("I: Stepwise")
    data_v1["pred1"] = m1(x["stepwise"]["m1"], data_v1)
    data_v1["pred2"] = m2(x["stepwise"]["m2"], data_v1)
    col1, col2 = st.columns(2)
    with col1:
        plotData = pd.melt(data_v1.rename(columns ={"SN_cummin": "observed", "SN": "original"}), id_vars="AGE", value_vars=["observed", "pred1"], value_name="SN", var_name = "pred vs. obs")
        fig= px.box(plotData, x = "AGE", y = "SN", color= "pred vs. obs") 
        st.plotly_chart(fig,use_container_width=True, theme= None)        
    
    with col2:
        plotData = pd.melt(data_v1.rename(columns ={"SN_cummin": "observed", "SN": "original"}), id_vars="AGE", value_vars=["observed", "pred2"], value_name="SN", var_name = "pred vs. obs")
        fig= px.box(plotData, x = "AGE", y = "SN", color= "pred vs. obs") 
        st.plotly_chart(fig,use_container_width=True, theme= None)
    
    # stepwise Model with iteration
    st.subheader("II: Stepwise with iteration")
    data_v1["pred1"] = m1(x["step_iter"]["m1"], data_v1)
    data_v1["pred2"] = m2(x["step_iter"]["m2"], data_v1)
    col1, col2 = st.columns(2)
    with col1:
        plotData = pd.melt(data_v1.rename(columns ={"SN_cummin": "observed", "SN": "original"}), id_vars="AGE", value_vars=["observed", "pred1"], value_name="SN", var_name = "pred vs. obs")
        fig= px.box(plotData, x = "AGE", y = "SN", color= "pred vs. obs") 
        st.plotly_chart(fig,use_container_width=True, theme= None)        
    
    with col2:
        plotData = pd.melt(data_v1.rename(columns ={"SN_cummin": "observed", "SN": "original"}), id_vars="AGE", value_vars=["observed", "pred2"], value_name="SN", var_name = "pred vs. obs")
        fig= px.box(plotData, x = "AGE", y = "SN", color= "pred vs. obs") 
        st.plotly_chart(fig,use_container_width=True, theme= None)

    # Model with no facility type
    st.subheader("III: Remove facility type")
    data_v1["pred1"] = m1_v1(x["remove_facility"]["m1"], data_v1)
    data_v1["pred2"] = m2_v1(x["remove_facility"]["m2"], data_v1)
    col1, col2 = st.columns(2)
    
    with col1:
        plotData = pd.melt(data_v1.rename(columns ={"SN_cummin": "observed", "SN": "original"}), id_vars="AGE", value_vars=["observed", "pred1"], value_name="SN", var_name = "pred vs. obs")
        fig= px.box(plotData, x = "AGE", y = "SN", color= "pred vs. obs") 
        st.plotly_chart(fig,use_container_width=True, theme= None)        
    
    with col2:
        plotData = pd.melt(data_v1.rename(columns ={"SN_cummin": "observed", "SN": "original"}), id_vars="AGE", value_vars=["observed", "pred2"], value_name="SN", var_name = "pred vs. obs")
        fig= px.box(plotData, x = "AGE", y = "SN", color= "pred vs. obs") 
        st.plotly_chart(fig,use_container_width=True, theme= None)

    # Model with no facility type with district effect
    st.subheader("III: Remove facility type, with district effect on a")
    data_v1["pred1"] = mdistrict(x["remove_facility"]["m1"], x["District-a"]["m1"], data_v1, model = "m1", group_method = "a")
    data_v1["pred2"] = mdistrict(x["remove_facility"]["m2"], x["District-a"]["m2"], data_v1, model = "m2", group_method = "a")
    col1, col2 = st.columns(2)
    
    with col1:
        plotData = pd.melt(data_v1.rename(columns ={"SN_cummin": "observed", "SN": "original"}), id_vars="AGE", value_vars=["observed", "pred1"], value_name="SN", var_name = "pred vs. obs")
        fig= px.box(plotData, x = "AGE", y = "SN", color= "pred vs. obs") 
        st.plotly_chart(fig,use_container_width=True, theme= None)        
    
    with col2:
        plotData = pd.melt(data_v1.rename(columns ={"SN_cummin": "observed", "SN": "original"}), id_vars="AGE", value_vars=["observed", "pred2"], value_name="SN", var_name = "pred vs. obs")
        fig= px.box(plotData, x = "AGE", y = "SN", color= "pred vs. obs") 
        st.plotly_chart(fig,use_container_width=True, theme= None)
    
    # Model with no facility type with district effect
    st.subheader("III: Remove facility type, with district effect on b")
    data_v1["pred1"] = mdistrict(x["remove_facility"]["m1"], x["District-b"]["m1"], data_v1, model = "m1", group_method = "b")
    data_v1["pred2"] = mdistrict(x["remove_facility"]["m2"], x["District-b"]["m2"], data_v1, model = "m2", group_method = "b")
    col1, col2 = st.columns(2)
    
    with col1:
        plotData = pd.melt(data_v1.rename(columns ={"SN_cummin": "observed", "SN": "original"}), id_vars="AGE", value_vars=["observed", "pred1"], value_name="SN", var_name = "pred vs. obs")
        fig= px.box(plotData, x = "AGE", y = "SN", color= "pred vs. obs") 
        st.plotly_chart(fig,use_container_width=True, theme= None)        
    
    with col2:
        plotData = pd.melt(data_v1.rename(columns ={"SN_cummin": "observed", "SN": "original"}), id_vars="AGE", value_vars=["observed", "pred2"], value_name="SN", var_name = "pred vs. obs")
        fig= px.box(plotData, x = "AGE", y = "SN", color= "pred vs. obs") 
        st.plotly_chart(fig,use_container_width=True, theme= None)
    
else:
    st.write("Login to view the app")
    st.session_state["allow"] = check_password()

