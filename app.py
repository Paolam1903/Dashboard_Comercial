
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import sqlite3
from PIL import Image
import matplotlib.pyplot as plt
import numpy as np

# =============================
# CONFIG
# =============================
st.set_page_config("Dashboard Comercial - Abril CVS 2026", layout="wide")

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
<h1 style="color:white;text-align:center">📊 Dashboard Cierre Comercial – CVS Abril 2026</h1>
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
# KPI CVS PLUS
# =============================
if cvs_sel != "Todos":

    df_cvs_plus = df_f[
        (df_f["Sucursal"] == cvs_sel) &
        (df_f["Producto"] == "CVS PLUS")
    ]

    meta_plus = df_cvs_plus["Meta_Producto"].max()
    ejec_plus = df_cvs_plus["Cantidad"].iloc[0] if not df_cvs_plus.empty else 0

    pct_plus = (ejec_plus / meta_plus * 100) if meta_plus > 0 else 0
    pct_plus = round(pct_plus, 1)

    if pct_plus >= 100:
        color = "#2ecc71"
        estado = "Cumplido"
    elif pct_plus >= 80:
        color = "#f39c12"
        estado = "En riesgo"
    else:
        color = "#e74c3c"
        estado = "Bajo cumplimiento"

    st.markdown(f"""
    <div style="background-color:{color};padding:20px;border-radius:12px;text-align:center;color:white;font-size:22px;font-weight:bold;">
    📦 CVS PLUS — {cvs_sel}<br><br>
    Meta: {int(meta_plus):,} | Ejecutado: {int(ejec_plus):,}<br>
    Cumplimiento: {pct_plus}% ({estado})
    </div>
    """, unsafe_allow_html=True)






# =============================
# TABS
# =============================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Dashboard", "💰 Presupuesto / Comisión", "📊 Reporte General CVS", "⚖️Cumplimiento General", "📌 Adicionales"])

# =============================
# TAB 1 – DASHBOARD
# =============================
with tab1:
    st.subheader("📦 Cumplimiento por Producto")
    
    # Lista fija de productos
    productos_base = ["HOGAR", "POSTPAGO", "TERMINALES", "CVS PLUS", "OTROS"]
    
    
    # Agrupar meta y ejecutado por producto
    prod = df_f.groupby("Producto").agg(
        Meta=("Meta_Producto", "max"),   # meta única
        Ejecutado=("Cantidad", "sum")    # cantidad vendida
    ).reset_index()


    # Asegurar productos base
    prod = pd.DataFrame(productos_base, columns=["Producto"]).merge(
        prod, on="Producto", how="left"
    ).fillna(0)


    # Calcular % cumplimiento
    prod["% Cumplimiento"] = (
        prod["Ejecutado"] / prod["Meta"]
    ).replace([np.inf, -np.inf], 0).fillna(0) * 100

    # Convertir a enteros
    prod["Meta"] = prod["Meta"].astype(int)
    prod["Ejecutado"] = prod["Ejecutado"].astype(int)
    prod["% Cumplimiento"] = prod["% Cumplimiento"].round(1)

    # Ordenar por ejecutado
    prod = prod.sort_values("Ejecutado", ascending=False).reset_index(drop=True)

    # Posiciones
    x = np.arange(len(prod["Producto"]))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))

    bars_meta = ax.bar(x - width/2, prod["Meta"], width, label="Meta")
    bars_ejec = ax.bar(x + width/2, prod["Ejecutado"], width, label="Ejecutado")

    # Etiquetas para META
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

    # Etiquetas para EJECUTADO + %
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

    # Línea de tendencia
    z = np.polyfit(x, prod["Ejecutado"], 1)
    p = np.poly1d(z)
    ax.plot(x, p(x), linestyle="--", linewidth=2, label="Tendencia Ejecutado")

    ax.set_xticks(x)
    ax.set_xticklabels(prod["Producto"], rotation=45, ha="right")
    ax.set_ylabel("Puntos")
    ax.set_title("Meta vs Ejecutado por Producto")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    st.pyplot(fig)





    # =============================
    # META GENERAL VS EJECUTADO
    # =============================

    st.subheader("🎯 Meta General vs Ejecutado")

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
    pct_general = (ejecutado_general / meta_general * 100) if meta_general > 0 else 0

    # DataFrame gráfico
    df_general = pd.DataFrame({
        "Concepto": ["Meta General", "Ejecutado"],
        "Valor": [meta_general, ejecutado_general]
    })

    # Gráfico
    fig, ax = plt.subplots(figsize=(5, 3))
    bars = ax.bar(df_general["Concepto"], df_general["Valor"])

    for bar in bars:
        height = bar.get_height()
        valor = f"{height:,.0f}".replace(",", ".")
        ax.text(
            bar.get_x() + bar.get_width()/2,
            height * 1.01,
            valor,
            ha="center",
            va="bottom",
            fontsize=8,
            fontweight="bold"
        )

    # Título con % cumplimiento
    ax.set_title(f"Cumplimiento general: {pct_general:.1f}%", fontsize=8)


    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{int(x):,}".replace(",", "."))
    )

    # Reducir tamaño de números del eje Y
    ax.tick_params(axis='y', labelsize=6)

    ax.grid(axis="y", linestyle="--", alpha=0.5)

    st.pyplot(fig)

# =====================
# SUPERNUMERARIOS
# =====================
SUPERNUMERARIOS = [
    "Johan Daniel Herrera Mazo",
    "Kelly Yuliana Ospina Saldarriaga",
    "Lider Zargoza Kelly Celsa",
    "Sara Julieth Acevedo Gutierrez"
]

# =====================
# REGLA DE DISTRIBUCIÓN
# =====================
def calcular_distribucion(n_asesores, cvs):
    # Regla especial para Frontino
    if str(cvs).upper() == "FRONTINO":
        return 0.50, 0.50
    
    # Si no hay asesores, el líder cumple al 100%
    if n_asesores == 0:
        return 1.0, 1.0  # 100% meta productos, 100% meta general

    # Reglas normales
    if n_asesores == 1:
        return 0.40, 0.60
    elif n_asesores == 2:
        return 0.25, 0.375
    elif n_asesores >= 3:
        return 0.20, 0.266
    else:
        return 1.0, 0.0


# =====================
# MAESTRO DE PRODUCTOS
# =====================
def maestro_productos_por_cvs(df, cvs_sel):
    df_cvs = df[df["Sucursal"] == cvs_sel]

    # Tomar metas únicas por producto
    maestro = (
        df_cvs[["Producto", "Meta_Producto"]]
        .drop_duplicates()
        .set_index("Producto")["Meta_Producto"]
        .to_dict()
    )

    # Asegurar que siempre existan estos productos
    productos_base = ["HOGAR", "POSTPAGO", "TERMINALES", "CVS PLUS", "OTROS"]

    for p in productos_base:
        if p not in maestro:
            maestro[p] = 0

    return maestro



def construir_tabla_productos(df_vendedor, maestro, df_cvs, rol):
    """
    Construye tabla de productos mostrando meta, ejecución y cumplimiento
    aplicando la distribución por rol.
    """

    # =====================
    # CALCULAR Nº ASESORES
    # =====================
    n_asesores = df_cvs[df_cvs["Rol"] == "ASESOR"]["Nombre_Vendedor"].nunique()

    # Obtener porcentajes
    porc_asesor, porc_lider = calcular_distribucion(n_asesores, df_cvs["Sucursal"].iloc[0])


    if rol == "ASESOR":
        porcentaje = porc_lider
    else:
        porcentaje = porc_asesor

    # =====================
    # VENTAS POR PRODUCTO
    # =====================
    ejec = (
        df_vendedor.groupby("Producto")["Cantidad"]
        .sum()
        .to_dict()
    )

    filas = []

    for producto, meta in maestro.items():

        # aplicar distribución
        meta_ajustada = meta * porcentaje

        ejecutado = ejec.get(producto, 0)

        if meta_ajustada > 0:
            pct = int(round((ejecutado / meta_ajustada) * 100))
        else:
            pct = 0

        filas.append({
            "Producto": producto,
            "Meta_Producto": int(round(meta_ajustada)),
            "Ejecutado": int(ejecutado),
            "% Cumplimiento": f"{pct}%"
        })

    tabla = pd.DataFrame(filas)


    # Orden fijo de productos
    orden_productos = [ "POSTPAGO", "HOGAR", "TERMINALES", "OTROS", "CVS PLUS" ]

    tabla["Producto"] = pd.Categorical(tabla["Producto"], categories=orden_productos, ordered=True)
    tabla = tabla.sort_values("Producto")

    return tabla




# =====================
# KPI DE PUNTOS
# =====================
def calcular_kpi_puntos(df_cvs, df_persona, rol):
    meta_general = df_cvs["Meta_General"].iloc[0]

    n_asesores = df_cvs[df_cvs["Rol"] == "ASESOR"]["Cedula_Vendedor"].nunique()
    cvs = df_cvs["Sucursal"].iloc[0]
    pct_lider, pct_asesor_individual = calcular_distribucion(n_asesores, cvs)


    if rol == "LIDER":
        meta = meta_general * pct_lider
    else:
        meta = meta_general * pct_asesor_individual

    ejecutado = df_persona["Puntos"].sum()
    cumplimiento = round((ejecutado / meta) * 100, 1) if meta > 0 else 0

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
