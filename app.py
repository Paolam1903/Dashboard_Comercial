
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import sqlite3
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np
import math

# =============================
# CONFIG
# =============================
st.set_page_config("Dashboard Comercial - Julio CVS 2026", layout="wide")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "comisiones.db"
LOGO_PATH = BASE_DIR / "logo.png"

RUTA_LIQ = DATA_DIR / "liquidacion_final.xlsx"
RUTA_METAS = DATA_DIR / "metas.xlsx"
RUTA_GENERAL = DATA_DIR / "general.xlsx"
RUTA_ADICIONALES = DATA_DIR / "adicionales.xlsx"

# =============================
# VALIDACIÓN
# =============================
if not RUTA_LIQ.exists() or not RUTA_METAS.exists():
    st.error("❌ Faltan archivos en /data")
    st.stop()

# =============================
# HEADER
# =============================
st.markdown("""
<div style="background-color:#E30613;padding:15px;border-radius:10px">
<h1 style="color:white;text-align:center">📊 Dashboard Cierre Comercial – CVS Julio 2026</h1>
</div>
""", unsafe_allow_html=True)

# =============================
# LOGO
# =============================
if LOGO_PATH.exists():
    st.sidebar.image(str(LOGO_PATH), use_container_width=True)

# =============================
# CARGA DATOS
# =============================
df = pd.read_excel(RUTA_LIQ)
df_meta = pd.read_excel(RUTA_METAS)

df["Fecha"] = pd.to_datetime(df["Fecha"])
df["Mes"] = df["Fecha"].dt.strftime("%Y-%m")

for c in ["Sucursal", "Producto", "Rol"]:
    if c in df.columns:
        df[c] = df[c].astype(str).str.upper().str.strip()
    if c in df_meta.columns:
        df_meta[c] = df_meta[c].astype(str).str.upper().str.strip()

columnas_meta = [col for col in df_meta.columns if col not in ["Mes", "Sucursal", "Producto"]]
df = df.merge(df_meta[["Sucursal", "Producto"] + columnas_meta], 
              on=["Sucursal", "Producto"], how="left")

# =============================
# FILTROS
# =============================
st.sidebar.subheader("📅 Filtros")

meses = ["Todos"] + sorted(df["Mes"].dropna().unique())
mes_sel = st.sidebar.selectbox("Mes", meses)

st.sidebar.subheader("🏪 CVS")
cvs_sel = st.sidebar.selectbox(
    "Selecciona CVS",
    ["Todos"] + sorted(df["Sucursal"].dropna().unique())
)

# Permitir edición
es_director = True
es_admin = True

# =============================
# APLICAR FILTROS
# =============================
df_f = df.copy()

if mes_sel != "Todos":
    df_f = df_f[df_f["Mes"] == mes_sel]

if cvs_sel != "Todos":
    df_f = df_f[df_f["Sucursal"] == cvs_sel]

# =============================
# KPI CVS PLUS (ANTES DE LOS TABS)
# =============================

if cvs_sel and cvs_sel != "Todos":

    df_cvs_plus = df_f[
        (df_f["Sucursal"] == cvs_sel) &
        (df_f["Producto"].str.upper() == "CVS PLUS")
    ]



# =============================
# KPI CVS PLUS
# =============================

if cvs_sel and cvs_sel != "Todos":

    df_cvs_plus = df_f[
        (df_f["Sucursal"] == cvs_sel) &
        (df_f["Producto"] == "CVS PLUS")
    ]

    # Meta CVS PLUS
    meta_plus = df_cvs_plus["Meta_Producto"].max()

    # Ejecutado CVS PLUS
    ejec_plus = df_cvs_plus["Cantidad"].sum()

    # % cumplimiento cantidad
    if meta_plus > 0:
        pct_plus = round((ejec_plus / meta_plus) * 100, 1)
    else:
        pct_plus = 0

    # % Encuestas
    df_turno = df_f[
        (df_f["Sucursal"] == cvs_sel) &
        (df_f["Producto"] == "TURNO")
    ]

    if not df_turno.empty:
        pct_encuestas = round(
            float(df_turno["Cantidad"].iloc[0]),
            1
        )
    else:
        pct_encuestas = 0

    # Semáforo
    if pct_plus >= 100 and pct_encuestas >= 5:
        color = "#2ecc71"
        estado = "Cumple cantidad y encuestas"

    elif pct_plus >= 100 and pct_encuestas < 5:
        color = "#f39c12"
        estado = "Cumple cantidad, no cumple encuestas"

    else:
        color = "#e74c3c"
        estado = "No cumple condiciones"

    st.markdown(
        f"""
        <div style="
            background-color:{color};
            padding:20px;
            border-radius:12px;
            text-align:center;
            color:white;
            font-size:22px;
            font-weight:bold;
            margin-bottom:15px;
        ">
        📦 CVS PLUS — {cvs_sel}<br><br>

        Meta: {int(meta_plus):,} |
        Ejecutado: {int(ejec_plus):,}<br>

        Cumplimiento: {pct_plus}%<br>
        Encuestas: {pct_encuestas}%<br><br>

        {estado}
        </div>
        """,
        unsafe_allow_html=True
    )



# =============================
# TABS
# =============================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "💰 Presupuesto / Comisión", "📊 Reporte General CVS", "⚖️Cumplimiento General", "📌 Adicionales"])

# =============================
# TAB 1 – DASHBOARD
# =============================
# =============================
# TAB 1 – DASHBOARD
# =============================
with tab1:

    # EVITA TICK / RERUN
    if not cvs_sel or cvs_sel == "Todos":
        st.info("Selecciona una sucursal para visualizar el dashboard")
        st.stop()

    st.subheader("📦 Cumplimiento por Producto")

    # =============================
    # COLORES CORPORATIVOS
    # =============================
    COLOR_META = "#1F3C88"        # Azul corporativo
    COLOR_EJEC = "#00A99D"        # Verde/teal moderno
    COLOR_TENDENCIA = "#E53935"   # Rojo elegante

    # =============================
    # DOS COLUMNAS
    # =============================
    col1, col2 = st.columns([2, 1])

    # =============================
    # GRÁFICO PRODUCTOS
    # =============================
    with col1:

        productos_base = ["HOGAR", "POSTPAGO", "TERMINALES", "CVS PLUS", "OTROS"]

        prod = df_f.groupby("Producto").agg(
            Meta=("Meta_Producto", "max"),
            Ejecutado=("Cantidad", "sum")
        ).reset_index()

        # Asegurar productos base
        prod = pd.DataFrame(productos_base, columns=["Producto"]).merge(
            prod,
            on="Producto",
            how="left"
        ).fillna(0)

        # % cumplimiento
        prod["% Cumplimiento"] = (
            prod["Ejecutado"] / prod["Meta"]
        ).replace([np.inf, -np.inf], 0).fillna(0) * 100

        prod["Meta"] = prod["Meta"].astype(int)
        prod["Ejecutado"] = prod["Ejecutado"].astype(int)
        prod["% Cumplimiento"] = prod["% Cumplimiento"].round(1)

        # Orden
        prod = prod.sort_values("Ejecutado", ascending=False).reset_index(drop=True)

        x = np.arange(len(prod["Producto"]))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 5))

        # 🔵 BARRAS
        bars_meta = ax.bar(
            x - width/2,
            prod["Meta"],
            width,
            label="Meta",
            color=COLOR_META
        )

        bars_ejec = ax.bar(
            x + width/2,
            prod["Ejecutado"],
            width,
            label="Ejecutado",
            color=COLOR_EJEC
        )

        # Etiquetas META
        for bar in bars_meta:
            height = bar.get_height()

            ax.text(
                bar.get_x() + bar.get_width()/2,
                height,
                f"{int(height):,}".replace(",", "."),
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold"
            )

        # Etiquetas EJECUTADO
        for i, bar in enumerate(bars_ejec):

            height = bar.get_height()
            pct = prod["% Cumplimiento"].iloc[i]

            ax.text(
                bar.get_x() + bar.get_width()/2,
                height,
                f"{int(height):,}\n{pct:.1f}%",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold"
            )

        # 🔴 LÍNEA TENDENCIA
        z = np.polyfit(x, prod["Ejecutado"], 1)
        p = np.poly1d(z)

        ax.plot(
            x,
            p(x),
            linestyle="--",
            linewidth=2,
            color=COLOR_TENDENCIA,
            label="Tendencia"
        )

        ax.set_xticks(x)
        ax.set_xticklabels(prod["Producto"], rotation=20)

        ax.set_ylabel("Cantidad")
        ax.set_title("Meta vs Ejecutado por Producto")

        ax.grid(axis="y", linestyle="--", alpha=0.3)

        ax.legend(frameon=False)

        st.pyplot(fig, clear_figure=True)
        plt.close(fig)

    # =============================
    # META GENERAL
    # =============================
# =============================
# META GENERAL VS EJECUTADO
# =============================

with col2:

    st.markdown("## 🎯 Meta General")

    # Meta general sin duplicar CVS
    meta_general = (
        df_f[["Sucursal", "Meta_General"]]
        .drop_duplicates()
        ["Meta_General"]
        .sum()
    )

    # Ejecutado general
    ejecutado_general = df_f["Puntos"].sum()

    # % cumplimiento general
    pct_general = (
        (ejecutado_general / meta_general) * 100
        if meta_general > 0 else 0
    )

    # =============================
    # DATAFRAME
    # =============================
    df_general = pd.DataFrame({
        "Concepto": ["Meta", "Ejecutado"],
        "Valor": [meta_general, ejecutado_general]
    })

    # =============================
    # GRÁFICO ESTABLE
    # =============================
    fig2, ax2 = plt.subplots(figsize=(5, 5))

    colores = ["#1E3A8A", "#0F766E"]

    bars = ax2.bar(
        df_general["Concepto"],
        df_general["Valor"],
        color=colores,
        width=0.75
    )

    # Etiquetas
    for bar in bars:

        height = bar.get_height()

        ax2.text(
            bar.get_x() + bar.get_width()/2,
            height * 1.01,
            f"{height:,.0f}".replace(",", "."),
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold"
        )

    # Título fijo
    ax2.set_title(
        f"Cumplimiento: {pct_general:.1f}%",
        fontsize=18,
        fontweight="bold",
        pad=15
    )

    # Formato eje Y
    ax2.yaxis.set_major_formatter(
        plt.FuncFormatter(
            lambda x, _: f"{int(x):,}".replace(",", ".")
        )
    )

    # Grid
    ax2.grid(axis="y", linestyle="--", alpha=0.3)

    # Eliminar bordes superiores
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    # 🔴 IMPORTANTE
    fig2.tight_layout(pad=2)

    st.pyplot(fig2, clear_figure=True)
    plt.close(fig)


# =====================
# SUPERNUMERARIOS
# =====================
# =====================
# SUPERNUMERARIOS
# =====================
SUPERNUMERARIOS = [
    "Johan Daniel Herrera Mazo",
    "Kelly Yuliana Ospina Saldarriaga",
    "Sara Julieth Acevedo Gutierrez"
]

# =====================
# REGLA DE DISTRIBUCIÓN
# =====================
def calcular_distribucion(n_asesores, cvs, nombre=None, rol=None):

    cvs = str(cvs).upper()
    nombre = str(nombre).upper() if nombre else ""


    # ==================================================
    # ==================================================
    # 🔴 REGLA ESPECIAL FRONTINO
    # ==================================================
    if cvs == "FRONTINO":
        if rol == "LIDER":
            return 0.50
        else:
            return 0.50

    if cvs == "EL BAGRE":
        return 1 / 3
    
    # ==================================================
    # ITAGUI
    # ==================================================

    if cvs == "ITAGUI":

        # Líder Marcela
        if rol == "LIDER":
            return 910 / 2500

        # Asesora Diana
        elif "DIANA" in nombre:
            return 1005 / 2500

        # Asesora Dailyn Del Valle
        elif "DAILYN" in nombre:
            return 585 / 2500
        
    # ==================================================
    # ZARAGOZA
    # ==================================================

    if cvs == "ZARAGOZA":

        # Líder Carol
        if rol == "LIDER":
            return 387 / 2200

        # Asesora Paola
        elif "PAOLA" in nombre:
            return 1813 / 2200

    # ==================================================
    # YARUMAL
    # ==================================================

    if cvs == "YARUMAL":

        # Líder Geraldin Angulo
        if rol == "LIDER":
            return 1152 / 1800

        # Asesora Laura Carolina
        elif "LAURA" in nombre:
            return 648 / 1800
        
    # ==================================================
    # DON MATIAS
    # ==================================================

    if cvs == "DON MATIAS":

        # Líder Diana Ruiz
        if rol == "LIDER":
            return 1140 / 1500

        # Asesora Evelyn
        elif "EVELYN" in nombre:
            return 360 / 1500
        

    # ==================================================
    # BARBOSA
    # ==================================================

    if cvs == "BARBOSA":

        # Líder Sandra Milena
        if rol == "LIDER":
            return 816 / 2400

        # Asesora Evelis
        elif "EVELIS" in nombre:
            return 1224 / 2400

        # Asesora Sene
        elif "SENE" in nombre:
            return 360 / 2400
        
    # ==================================================
    # COPACABANA
    # ==================================================

    if cvs == "COPACABANA":

        # Líder Vanessa
        if rol == "LIDER":
            return 1020 / 3000

        # Asesora Bibiana
        elif "BIBIANA" in nombre:
            return 1530 / 3000

        # Asesora Alexandra
        elif "ALEXANDRA" in nombre:
            return 450 / 3000
        

    # ==================================================
    # CALDAS
    # ==================================================

    if cvs == "CALDAS":

        # Líder Yolima
        if rol == "LIDER":
            return 1036 / 3700

        # Asesora Darinela
        elif "DARINELA" in nombre:
            return 1554 / 3700

        # Asesora Johnson
        elif "JOHNSON" in nombre:
            return 1110 / 3700

    # ==================================================
    # SABANETA
    # ==================================================

    if cvs == "SABANETA":

        # LÃ­der Sandra
        if rol == "LIDER":
            return 806 / 2600

        # Andrea
        elif "ANDREA" in nombre:
            return 1209 / 2600

        # María
        elif "MARIA" in nombre:
            return 585 / 2600

    # ==================================================
    # ENVIGADO
    # ==================================================

    if cvs == "ENVIGADO":

        # Líder
        if rol == "LIDER":
            return 938 / 3500

        # Paola
        elif "YESSICA" in nombre:
            return 1155 / 3500

        # Luz
        elif "LUZ" in nombre:
            return 1407 / 3500


    # ==================================================
    # 🔴 REGLAS NORMALES
    # ==================================================

    # Si no hay asesores
    if n_asesores == 0:
        return 1.0

    if rol == "LIDER":

        if n_asesores == 1:
            return 0.40
        elif n_asesores == 2:
            return 0.25
        elif n_asesores >= 3:
            return 0.20

    else:

        if n_asesores == 1:
            return 0.60
        elif n_asesores == 2:
            return 0.375
        elif n_asesores >= 3:
            return 0.266

    return 1.0



# =====================
# MAESTRO DE PRODUCTOS
# =====================
def maestro_productos_por_cvs(df, cvs_sel):

    # Filtrar solo el CVS seleccionado
    df_cvs = df[df["Sucursal"] == cvs_sel].copy()

    # Tomar metas únicas por producto
    maestro = (
        df_cvs[["Producto", "Meta_Producto"]]
        .drop_duplicates()
        .set_index("Producto")["Meta_Producto"]
        .to_dict()
    )

    # Productos que deben aparecer siempre
    productos_base = [
        "POSTPAGO",
        "HOGAR",
        "TERMINALES",
        "OTROS",
        "CVS PLUS"
    ]

    # Crear un maestro solo con esos productos
    maestro = {
        p: maestro.get(p, 0)
        for p in productos_base
    }

    # Reemplazar NaN por 0
    for p in productos_base:
        if pd.isna(maestro[p]):
            maestro[p] = 0

    return maestro

# =====================
# TABLA PRODUCTOS
# =====================
def construir_tabla_productos(df_vendedor, maestro, df_cvs, rol):

    # 🔴 EXCLUIR SUPERNUMERARIOS
    df_cvs_kpi = df_cvs[
        ~df_cvs["Nombre_Vendedor"].isin(SUPERNUMERARIOS)
    ]

    n_asesores = df_cvs_kpi[
        df_cvs_kpi["Rol"] == "ASESOR"
    ]["Nombre_Vendedor"].nunique()

    cvs = df_cvs["Sucursal"].iloc[0]

    nombre = df_vendedor["Nombre_Vendedor"].iloc[0]

    # =========================
    # PORCENTAJE PERSONALIZADO
    # =========================
    porcentaje = calcular_distribucion(
        n_asesores,
        cvs,
        nombre,
        rol
    )

    # =========================
    # EJECUTADO PRODUCTOS
    # =========================
    # =====================================
    # PRODUCTOS QUE SÍ CUENTAN PARA EL KPI
    # =====================================
    productos_kpi = [
        "POSTPAGO",
        "HOGAR",
        "TERMINALES",
        "OTROS",
        "CVS PLUS"
    ]

    # Excluir TURNO y cualquier otro producto
    df_vendedor_kpi = df_vendedor[
        df_vendedor["Producto"].isin(productos_kpi)
    ]

    # Ejecutado únicamente de los productos KPI
    ejec = (
        df_vendedor_kpi
        .groupby("Producto")["Cantidad"]
        .sum()
        .to_dict()
    )

    filas = []

    for producto, meta in maestro.items():

        # Si la meta viene vacía la convierte en 0
        if pd.isna(meta):
            meta = 0

        meta = float(meta)

        meta_ajustada = math.floor((meta * porcentaje) + 0.5)

        # Redondeo comercial
        meta_ajustada = int(meta_ajustada + 0.5)

        ejecutado = ejec.get(producto, 0)

        if meta_ajustada > 0:
            pct = int(round((ejecutado / meta_ajustada) * 100))
        else:
            pct = 0

        filas.append({
            "Producto": producto,
            "Meta_Producto": meta_ajustada,
            "Ejecutado": int(ejecutado),
            "% Cumplimiento": f"{pct}%"
        })

    tabla = pd.DataFrame(filas)
    # =========================
    # ORDEN FIJO PRODUCTOS
    # =========================
    orden_productos = [
        "POSTPAGO",
        "HOGAR",
        "TERMINALES",
        "OTROS",
        "CVS PLUS"
    ]

    tabla["Producto"] = pd.Categorical(
        tabla["Producto"],
        categories=orden_productos,
        ordered=True
    )

    tabla = tabla.sort_values("Producto")

    return tabla


# =====================
# KPI DE PUNTOS
# =====================
def calcular_kpi_puntos(df_cvs, df_persona, rol):

    # 🔴 EXCLUIR SUPERNUMERARIOS
    df_cvs_kpi = df_cvs[
        ~df_cvs["Nombre_Vendedor"].isin(SUPERNUMERARIOS)
    ]

    meta_general = df_cvs_kpi["Meta_General"].iloc[0]

    n_asesores = df_cvs_kpi[
        df_cvs_kpi["Rol"] == "ASESOR"
    ]["Cedula_Vendedor"].nunique()

    cvs = df_cvs_kpi["Sucursal"].iloc[0]

    nombre = df_persona["Nombre_Vendedor"].iloc[0]

    # =========================
    # PORCENTAJE PERSONALIZADO
    # =========================
    porcentaje = calcular_distribucion(
        n_asesores,
        cvs,
        nombre,
        rol
    )

    # 🔴 META PERSONALIZADA
    meta = math.floor((meta_general * porcentaje) + 0.5)

    # 🔴 EJECUTADO
    ejecutado = df_persona["Puntos"].sum()

    # 🔴 % CUMPLIMIENTO
    cumplimiento = (
        round((ejecutado / meta) * 100, 1)
        if meta > 0 else 0
    )

    return meta, ejecutado, cumplimiento


# =======================
# Archivo histórico central
# =======================
RUTA_HISTORICO = DATA_DIR / "historico_comisiones.xlsx"

# Cargar histórico existente (si existe)
if RUTA_HISTORICO.exists():
    df_historico = pd.read_excel(RUTA_HISTORICO)
else:
    df_historico = pd.DataFrame(
        columns=[
            "Mes", "CVS", "Nombre", "Rol", "Producto",
            "Meta_Producto", "Ejecutado", "% Cumplimiento",
            "Tipo Pago Comisión", "Observación",
            "ACC"
        ]
    )

# Guardar en session_state
if "historico_decisiones" not in st.session_state:
    st.session_state["historico_decisiones"] = df_historico.to_dict("records")

with st.sidebar:
    st.subheader("Filtros")
    meses = sorted(df["Mes"].dropna().unique())
    mes_sel = st.selectbox("Selecciona el mes historico", meses)



# =======================
# TAB 2 – PRESUPUESTO / COMISIÓN (LIMPIO)
# =======================
with tab2:
    st.subheader("📍 Detalle por CVS")

    if cvs_sel == "Todos" or not cvs_sel:
        st.info("Selecciona un CVS en el panel lateral")
        st.stop()

    # =========================
    # DATA COMPLETA
    # =========================
    df_cvs = df_f[df_f["Sucursal"] == cvs_sel].copy()

    # limpiar nombres (evita errores)
    df_cvs["Nombre_Vendedor"] = df_cvs["Nombre_Vendedor"].astype(str).str.strip()

    # =========================
    # DATA SOLO PARA META (SIN SUPERNUMERARIOS)
    # =========================
    df_cvs_meta = df_cvs[
        ~df_cvs["Nombre_Vendedor"].isin(SUPERNUMERARIOS)
    ]

    # =========================
    # SUPERNUMERARIOS
    # =========================
    df_super = df_cvs[
        df_cvs["Nombre_Vendedor"].isin(SUPERNUMERARIOS)
    ]

    maestro = maestro_productos_por_cvs(df_f, cvs_sel)

    # =====================
    # LÍDER
    # =====================
    df_lider = df_cvs[df_cvs["Rol"] == "LIDER"].copy()

    if not df_lider.empty:
        nombre_lider = df_lider["Nombre_Vendedor"].iloc[0]
        st.markdown(f"## 👔 Líder: **{nombre_lider}**")

        # 🔥 USAR df_cvs_meta (CLAVE)
        meta_p, ejec_p, pct_p = calcular_kpi_puntos(df_cvs_meta, df_lider, "LIDER")

        if pct_p >= 100:
            color = "#2ecc71"
        elif pct_p >= 80:
            color = "#f39c12"
        else:
            color = "#e74c3c"

        st.markdown(f"""
        <div style="
            background-color:{color};
            padding:10px;
            border-radius:10px;
            text-align:center;
            color:white;
            font-weight:bold;
            margin-bottom:10px;">
            {int(ejec_p)} / {int(meta_p)}<br>
            {pct_p}%
        </div>
        """, unsafe_allow_html=True)

        st.metric("🎯 KPI Puntos", f"{int(ejec_p)} / {int(meta_p)}", f"{pct_p}%")

        tabla_lider = construir_tabla_productos(df_lider, maestro, df_cvs, "LIDER")

        st.data_editor(
            tabla_lider,
            disabled=not es_director,
            use_container_width=True,
            key="editor_lider"
        )

    # =====================
    # ASESORES
    # =====================
    st.markdown("## 👥 Asesoras")

    df_asesoras = df_cvs[
        (df_cvs["Rol"] == "ASESOR") &
        (~df_cvs["Nombre_Vendedor"].isin(SUPERNUMERARIOS))
    ]

    asesoras = list(df_asesoras.groupby("Nombre_Vendedor"))

    cols = st.columns(3)

    for i, (nombre, g) in enumerate(asesoras):

        col = cols[i % 3]

        with col:
            st.markdown(f"### 👤 {nombre}")

            # 🔥 USAR df_cvs_meta (CLAVE)
            meta_p, ejec_p, pct_p = calcular_kpi_puntos(df_cvs_meta, g, "ASESOR")

            if pct_p >= 100:
                color = "#2ecc71"
            elif pct_p >= 80:
                color = "#f39c12"
            else:
                color = "#e74c3c"

            st.markdown(f"""
            <div style="
                background-color:{color};
                padding:10px;
                border-radius:10px;
                text-align:center;
                color:white;
                font-weight:bold;
                margin-bottom:10px;">
                {int(ejec_p)} / {int(meta_p)}<br>
                {pct_p}%
            </div>
            """, unsafe_allow_html=True)

            tabla = construir_tabla_productos(g, maestro, df_cvs, "ASESOR")
            st.dataframe(tabla, use_container_width=True)

    # =====================
    # SUPERNUMERARIOS (SOLO VISUAL)
    # =====================
    st.markdown("## 🧩 Supernumerarios (Sin Meta)")

    if df_super.empty:
        st.info("No hay supernumerarios en este CVS")
    else:

        cols = st.columns(3)

        for i, (nombre, g) in enumerate(df_super.groupby("Nombre_Vendedor")):

            col = cols[i % 3]

            with col:
                st.markdown(f"### 👤 {nombre}")

                ejecutado = g["Puntos"].sum()

                st.markdown(f"""
                <div style="
                    background-color:#7f8c8d;
                    padding:10px;
                    border-radius:10px;
                    text-align:center;
                    color:white;
                    font-weight:bold;
                    margin-bottom:10px;">
                    {int(ejecutado)} puntos<br>
                    Sin meta
                </div>
                """, unsafe_allow_html=True)

                tabla = construir_tabla_productos(g, maestro, df_cvs, "ASESOR")
                st.dataframe(tabla, use_container_width=True)


# =======================
# TAB 3 – REPORTE GENERAL LIMPIO
# =======================
with tab3:
    st.subheader("📊 Reporte General CVS")

    if not RUTA_GENERAL.exists():
        st.error("❌ No se encontró el archivo general.xlsx en /data")
        st.stop()

    df_general = pd.read_excel(RUTA_GENERAL)

    # =========================
    # LIMPIAR NOMBRES DE COLUMNAS
    # =========================
    df_general.columns = df_general.columns.str.strip()

    # =========================
    # FORMATEAR COLUMNAS %
    # =========================
    cols_pct = [c for c in df_general.columns if "%" in c.upper()]

    for col in cols_pct:
        df_general[col] = df_general[col].apply(
            lambda x: f"{round(x*100,1)}%" if pd.notnull(x) and isinstance(x, (int, float)) else x
        )

    # =========================
    # SEMÁFORO
    # =========================
    def color_cumplimiento(val):
        try:
            if isinstance(val, str) and "%" in val:
                num = float(val.replace("%", ""))
            else:
                num = float(val)

            if num >= 100:
                return "background-color: #2ecc71; color: white"
            elif num >= 80:
                return "background-color: #f39c12; color: white"
            else:
                return "background-color: #e74c3c; color: white"
        except:
            return ""

    # =========================
    # FORMATO MONEDA
    # =========================
    cols_money = [
        "Accesorios",
        "Ejecutado.6"
    ]

    for col in cols_money:
        if col in df_general.columns:
            df_general[col] = pd.to_numeric(df_general[col], errors="coerce")
            df_general[col] = df_general[col].apply(
                lambda x: f"$ {int(x):,}".replace(",", ".") if pd.notnull(x) else ""
            )

    # =========================
    # LIMPIAR DECIMALES (ENTEROS)
    # =========================
    cols_enteros = [
        "Meta en puntos",
        "Ejecutado",
        "CVS PLUS",
        "Otros",
        "Postpago",
        "Terminales",
        "Hogar"
    ]

    for col in cols_enteros:
        if col in df_general.columns:
            df_general[col] = pd.to_numeric(df_general[col], errors="coerce")
            df_general[col] = df_general[col].fillna(0).astype(int)
            df_general[col] = df_general[col].apply(
                lambda x: f"{x:,}".replace(",", ".")
            )

    # =========================
    # APLICAR ESTILO
    # =========================
    styled_df = df_general.style

    for col in cols_pct:
        if col in df_general.columns:
            styled_df = styled_df.map(color_cumplimiento, subset=[col])

    # =========================
    # MOSTRAR
    # =========================
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=600
    )



# =======================
# =========================
# TAB 4 – PANEL COORDINADOR
# =========================
with tab4:
    st.subheader("⚖️Cumplimiento General")

    # =========================
    # TOTALES GENERALES
    # =========================

    # Meta total (sin duplicar sucursal)
    meta_total = (
        df_f[["Sucursal", "Meta_General"]]
        .drop_duplicates()
        ["Meta_General"]
        .sum()
    )

    # Puntos totales
    puntos_total = df_f["Puntos"].sum()

    # Cantidad total
    cantidad_total = df_f["Cantidad"].sum()

    # % cumplimiento
    if meta_total > 0:
        pct_total = (puntos_total / meta_total) * 100
    else:
        pct_total = 0

    pct_total = round(pct_total, 1)

    # =========================
    # KPI SEMÁFORO
    # =========================
    if pct_total >= 100:
        color = "green"
        estado = "Excelente"
    elif pct_total >= 90:
        color = "orange"
        estado = "Aceptable"
    else:
        color = "red"
        estado = "Crítico"

    # =========================
    # PANEL SUPERIOR
    # =========================
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🎯 Meta total", f"{meta_total:,.0f}".replace(",", "."))
    col2.metric("⭐ Puntos totales", f"{puntos_total:,.0f}".replace(",", "."))
    col3.metric("📦 Cantidad total", f"{cantidad_total:,.0f}".replace(",", "."))
    col4.metric("📈 Cumplimiento", f"{pct_total} %")

    # Semáforo visual
    st.markdown(
        f"""
        <div style="background-color:{color};
                    padding:15px;
                    border-radius:10px;
                    text-align:center;
                    color:white;
                    font-size:20px;
                    font-weight:bold;">
            KPI General: {estado} ({pct_total}%)
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # =========================
    # RESUMEN POR PRODUCTO
    # =========================
    st.subheader("📦 Resumen por producto")

    resumen_prod = df_f.groupby("Producto").agg(
        Cantidad=("Cantidad", "sum"),
        Puntos=("Puntos", "sum")
    ).reset_index()

    st.dataframe(resumen_prod, use_container_width=True)



# =======================
# TAB 5 – ADICIONALES
# =======================
with tab5:
    st.subheader("📌 Reporte Adicionales")

    if not RUTA_ADICIONALES.exists():
        st.error("❌ No se encontró el archivo adicionales.xlsx en /data")
        st.stop()

    df_add = pd.read_excel(RUTA_ADICIONALES)

    # =========================
    # DIVIDIR SECCIONES
    # =========================

    # Resumen Prepago
    resumen_prepago = df_add.iloc[2:23, 0:2]

    # Portabilidad
    portabilidad = df_add.iloc[2:20, 5:7]

    # Top equipos
    top_equipos = df_add.iloc[2:12, 9:11]

    # Top planes
    top_planes = df_add.iloc[2:12, 13:16]

    # Informe cajeras
    fila_inicio = df_add[
        df_add.apply(lambda row: row.astype(str).str.contains("Informe Cajeras", case=False).any(), axis=1)
    ].index

    if len(fila_inicio) > 0:
        cajeras = df_add.iloc[fila_inicio[0]+1:, :]
    else:
        cajeras = df_add.copy()

    # =========================
    # MOSTRAR EN COLUMNAS
    # =========================

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 📱 Prepago vs Postpago")
        st.dataframe(resumen_prepago, use_container_width=True)

    with col2:
        st.markdown("### 🔄 Portabilidad")
        st.dataframe(portabilidad, use_container_width=True)

    with col3:
        st.markdown("### 📦 Top Equipos")
        st.dataframe(top_equipos, use_container_width=True)

    with col4:
        st.markdown("### 📊 Top Planes")
        st.dataframe(top_planes, use_container_width=True)

    st.divider()

    st.markdown("### 🧾 Informe Cajeras")
    st.dataframe(cajeras, use_container_width=True)
