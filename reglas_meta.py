import streamlit as st
import pandas as pd
import plotly.express as px

# ======================
# FUNCION DISTRIBUCION
# ======================

def calcular_distribucion(n_asesores, cvs):

    if str(cvs).upper() == "FRONTINO":
        return 0.50, 0.50

    if n_asesores == 0:
        return 1.0, 1.0

    if n_asesores == 1:
        return 0.40, 0.60

    elif n_asesores == 2:
        return 0.25, 0.375

    elif n_asesores >= 3:
        return 0.20, 0.266

    else:
        return 1.0, 0.0


# ======================
# DASHBOARD STREAMLIT
# ======================

st.title("Dashboard Comercial")