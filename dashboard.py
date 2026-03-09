import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from reglas_meta import calcular_distribucion



st.set_page_config(layout="wide")

st.title("📊 Dashboard Comercial CVS")

# ================================
# CARGAR ARCHIVOS
# ================================

ventas = pd.read_excel("ventas_ejecutadas.xlsx")
meta_lider = pd.read_excel("meta_lider.xlsx")
meta_asesor = pd.read_excel("meta_asesor.xlsx")
cajeras = pd.read_excel("cajeras.xlsx")

# ================================
# LIMPIAR COLUMNAS
# ================================

ventas.columns = ventas.columns.str.strip()
meta_lider.columns = meta_lider.columns.str.strip()
meta_asesor.columns = meta_asesor.columns.str.strip()
cajeras.columns = cajeras.columns.str.strip()

ventas["Sucursal"] = ventas["Sucursal"].str.upper()
ventas["Mes"] = ventas["Mes"].str.capitalize()

meta_lider["Sucursal"] = meta_lider["Sucursal"].str.upper()
meta_lider["Mes"] = meta_lider["Mes"].str.capitalize()

meta_asesor["Sucursal"] = meta_asesor["Sucursal"].str.upper()
meta_asesor["Mes"] = meta_asesor["Mes"].str.capitalize()

cajeras["Sucursal"] = cajeras["Sucursal"].str.upper()
cajeras["Mes"] = cajeras["Mes"].str.capitalize()

# ================================
# VALIDAR COLUMNAS
# ================================

if "producto" not in ventas.columns:
    ventas["producto"] = ventas["ProductoDeVenta"]

ventas["producto"] = ventas["producto"].str.upper()

ventas["PUNTOS"] = pd.to_numeric(ventas["PUNTOS"], errors="coerce")

# ================================
# QUITAR SUPERNUMERARIOS PARA META
# ================================

ventas_meta = ventas[ventas["RolVendedor"] != "SUPERNUMERARIO"]

# ================================
# EJECUTADO POR SUCURSAL
# ================================

ejecutado_sucursal = (
    ventas_meta
    .groupby(["Sucursal","Mes"])["PUNTOS"]
    .sum()
    .reset_index()
)

# ================================
# META LIDER PUNTOS
# ================================

meta_puntos = meta_lider[["Sucursal","Mes","PUNTOS"]]

# ================================
# UNION META VS EJECUTADO
# ================================

resumen = meta_puntos.merge(
    ejecutado_sucursal,
    on=["Sucursal","Mes"],
    how="left"
)

resumen = resumen.rename(columns={
    "PUNTOS_x":"META_PUNTOS",
    "PUNTOS_y":"EJECUTADO_PUNTOS"
})

resumen["EJECUTADO_PUNTOS"] = resumen["EJECUTADO_PUNTOS"].fillna(0)

# ================================
# % CUMPLIMIENTO
# ================================

resumen["CUMPLIMIENTO"] = (
    resumen["EJECUTADO_PUNTOS"] /
    resumen["META_PUNTOS"]
)

resumen["% CUMPLIMIENTO"] = (
    resumen["CUMPLIMIENTO"]
    .fillna(0)
    .apply(lambda x: f"{round(x*100)}%")
)

# ================================
# PRODUCTOS
# ================================

productos = (
    ventas
    .groupby(["Sucursal","Mes","producto"])["PUNTOS"]
    .sum()
    .reset_index()
)

# ================================
# TABS
# ================================

tab1, tab2, tab3 = st.tabs(["Resultado Sucursal","Detalle CVS", "📊 Cierre Trimestral Recaudos Cajeras"])

# ====================================================
# TAB 1 RESULTADO POR SUCURSAL
# ====================================================

with tab1:
    orden_meses = ["Diciembre", "Enero", "Febrero"]
    st.subheader("Cumplimiento por Sucursal")
    orden_meses = ["Diciembre", "Enero", "Febrero"]
    # ============================================
    # TABLA META VS EJECUTADO
    # ============================================

    tabla = resumen.pivot_table(
        index="Sucursal",
        columns="Mes",
        values=["META_PUNTOS","EJECUTADO_PUNTOS","% CUMPLIMIENTO"],
        aggfunc="first"
    )

    st.dataframe(tabla, use_container_width=True)

    # ============================================
    # PREPARAR DATA GRAFICO
    # ============================================

    grafico = resumen.copy()

    grafico["CUMPLIMIENTO_NUM"] = (
        grafico["EJECUTADO_PUNTOS"] /
        grafico["META_PUNTOS"]
    )

    grafico["CUMPLIMIENTO_NUM"] = grafico["CUMPLIMIENTO_NUM"].replace([float("inf")],0)
    grafico["CUMPLIMIENTO_NUM"] = grafico["CUMPLIMIENTO_NUM"].fillna(0)

    grafico["PORCENTAJE"] = (
        grafico["CUMPLIMIENTO_NUM"] * 100
    ).round(0)

    # Ordenar de mayor a menor
    grafico = grafico.sort_values(
        "EJECUTADO_PUNTOS",
        ascending=False
    )
    
    # ============================================
    # GRAFICO META VS EJECUTADO (SOLO %)
    # ============================================
    
    st.subheader("Cumplimiento de Meta por Sucursal (%)")

    grafico = resumen.copy()

    # calcular porcentaje
    grafico["PORCENTAJE"] = (
        grafico["EJECUTADO_PUNTOS"] /
        grafico["META_PUNTOS"]
    ) * 100

    grafico["PORCENTAJE"] = grafico["PORCENTAJE"].fillna(0).round(0)

    # ordenar de mayor a menor
    grafico = grafico.sort_values(
        "PORCENTAJE",
        ascending=False
    )

    fig = px.bar(
        grafico,
        x="Sucursal",
        y="PORCENTAJE",
        facet_col="Mes",
        text="PORCENTAJE",
        title="Cumplimiento de Meta por Sucursal (%)",
        color="PORCENTAJE",
        color_continuous_scale="RdYlGn"
    )

    fig.update_traces(
        texttemplate="%{text}%",
        textposition="outside"
    )

    fig.update_layout(
        height=450,
        yaxis_title="% Cumplimiento",
        xaxis_title="Sucursal"
    )

    st.plotly_chart(fig, use_container_width=True)





    # ============================================
    # GRAFICO PRODUCTOS CON FILTRO
    # ============================================

    st.subheader("Resultados por Producto")

    # lista de productos
    lista_productos = ["TODOS"] + sorted(ventas["producto"].dropna().unique())

    producto_sel = st.selectbox(
        "Filtrar por producto",
        lista_productos
    )

    data = ventas.copy()

    # aplicar filtro
    if producto_sel != "TODOS":
        data = data[data["producto"] == producto_sel]

    # ============================================
    # CREAR RESULTADO SEGUN PRODUCTO
    # ============================================

    def obtener_resultado(row):

        if row["producto"] == "CVS PLUS":
            return row.get("Cantidad",0)

        elif row["producto"] in ["ACCESORIOS","TECNOLOGIA"]:
            return row.get("ValorNeto",0)

        else:
            return row.get("PUNTOS",0)

    data["RESULTADO"] = data.apply(obtener_resultado, axis=1)

    # ============================================
    # AGRUPAR PARA GRAFICO
    # ============================================

    graf_prod = data.groupby(
        ["Sucursal","Mes","producto"],
        as_index=False
    )["RESULTADO"].sum()

    # total por sucursal
    graf_prod["TOTAL_CVS"] = graf_prod.groupby(
        ["Sucursal","Mes"]
    )["RESULTADO"].transform("sum")

    # porcentaje
    graf_prod["PORCENTAJE"] = (
        graf_prod["RESULTADO"] /
        graf_prod["TOTAL_CVS"]
    ).fillna(0)

    # etiqueta
    graf_prod["LABEL"] = graf_prod.apply(
        lambda x: f'{round(x["RESULTADO"])} ({round(x["PORCENTAJE"]*100)}%)',
        axis=1
    )

    # ============================================
    # GRAFICO
    # ============================================

    fig2 = px.bar(
        graf_prod,
        x="Sucursal",
        y="RESULTADO",
        color="producto",
        facet_col="Mes",
        text="LABEL",
        title="Resultados por Producto",
        color_continuous_scale="RdYlGn"
    )

    fig2.update_traces(
        textposition="outside"
    )

    fig2.update_layout(
        height=650
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )
    


    # ============================================
    # VENTAS TECNOLOGIA POR MES Y CVS - CORREGIDO
    # ============================================

    import plotly.express as px
    import calendar

    st.subheader("📊 Ventas de Tecnología por CVS y Mes")

    # ==============================
    # NORMALIZAR COLUMNA MES
    # ==============================

    # Primero revisa la columna Mes
    st.write("Valores originales de Mes:", ventas["Mes"].unique())

    # Convertir a string y eliminar espacios
    ventas["Mes_str"] = ventas["Mes"].astype(str).str.strip()

    # Crear columna numérica de Mes
    mes_map = {
        "1":"1","Enero":"1","enero":"1",
        "2":"2","Febrero":"2","febrero":"2",
        "3":"3","Marzo":"3","marzo":"3",
        "4":"4","Abril":"4","abril":"4",
        "5":"5","Mayo":"5","mayo":"5",
        "6":"6","Junio":"6","junio":"6",
        "7":"7","Julio":"7","julio":"7",
        "8":"8","Agosto":"8","agosto":"8",
        "9":"9","Septiembre":"9","septiembre":"9",
        "10":"10","Octubre":"10","octubre":"10",
        "11":"11","Noviembre":"11","noviembre":"11",
        "12":"12","Diciembre":"12","diciembre":"12"
    }

    ventas["Mes_num"] = ventas["Mes_str"].map(mes_map)
    ventas["Mes_num"] = pd.to_numeric(ventas["Mes_num"], errors="coerce")

    # Crear columna con nombre del mes
    ventas["NombreMes"] = ventas["Mes_num"].apply(
        lambda x: calendar.month_name[int(x)] if pd.notnull(x) else ""
    )

    # ==============================
    # FILTRO GENERAL POR SUCURSAL
    # ==============================

    sucursal_sel = st.selectbox(
        "Filtrar por Sucursal",
        ["TODOS"] + sorted(ventas["Sucursal"].dropna().unique())
    )

    # ==============================
    # FILTRO POR MES
    # ==============================

    mes_sel = st.selectbox(
        "Filtrar por Mes",
        ["TODOS"] + sorted(ventas["NombreMes"].dropna().unique(), key=lambda x: list(calendar.month_name).index(x))
    )

    # ==============================
    # FILTRAR TECNOLOGIA
    # ==============================

    tec = ventas[ventas["producto"] == "TECNOLOGIA"].copy()

    if sucursal_sel != "TODOS":
        tec = tec[tec["Sucursal"] == sucursal_sel]

    if mes_sel != "TODOS":
        tec = tec[tec["NombreMes"] == mes_sel]

    # ==============================
    # VERIFICAR DATOS
    # ==============================

    if tec.empty:
        st.warning("No hay datos para mostrar con los filtros seleccionados")
        st.stop()

    # ==============================
    # AGRUPAR POR SUCURSAL Y MES
    # ==============================

    tec_graf = tec.groupby(
        ["Sucursal", "NombreMes"],
        as_index=False
    )["ValorNeto"].sum()

    tec_graf = tec_graf.sort_values(
        ["NombreMes", "ValorNeto"],
        ascending=[True, False]
    )

    # ==============================
    # GRAFICO MODERNO
    # ==============================

    fig_tec = px.bar(
        tec_graf,
        x="Sucursal",
        y="ValorNeto",
        color="Sucursal",
        facet_col="NombreMes" if mes_sel=="TODOS" else None,
        text_auto=".2s",
        title="Ventas Tecnología por Sucursal y Mes",
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig_tec.update_traces(
        textposition="outside",
        showlegend=False
    )

    fig_tec.update_layout(
        height=500,
        xaxis_title="Sucursal",
        yaxis_title="Ventas ($)",
        title_font_size=20,
        plot_bgcolor="white",
        bargap=0.2
    )

    st.plotly_chart(
        fig_tec,
        use_container_width=True
    )





# =========================================
# TAB 2: Detalle por Líder y Asesores
# =========================================
with tab2:

    st.subheader("Detalle por Líder y Asesores")

    # Normalizar columnas
    ventas.columns = ventas.columns.str.strip().str.upper()
    meta_lider.columns = meta_lider.columns.str.strip().str.upper()

    cvs = st.selectbox(
        "Seleccionar CVS",
        sorted(ventas["SUCURSAL"].unique())
    )

    ventas_cvs = ventas[ventas["SUCURSAL"] == cvs]

    meses_trimestre = ["Diciembre","Enero","Febrero"]

    # =====================================
    # CREAR DOS COLUMNAS VISUALES
    # =====================================

    col_puntos, col_productos = st.columns(2)

    # =====================================================
    # COLUMNA 1
    # KPI POR PUNTOS
    # =====================================================

    with col_puntos:

        st.markdown("### 🎯 KPI por Puntos")

        cumplimiento_list = []

        for mes in meses_trimestre:

            ventas_mes = ventas_cvs[ventas_cvs["MES"] == mes]

            if ventas_mes.empty:
                continue

            asesores_mes = ventas_mes[
                (ventas_mes["ROLVENDEDOR"].str.upper() == "ASESOR")
            ].groupby("NOMBREVENDEDOR")["PUNTOS"].sum()

            n_asesores = len(asesores_mes)

            meta_mes = meta_lider[
                (meta_lider["SUCURSAL"] == cvs) &
                (meta_lider["MES"] == mes)
            ]

            if meta_mes.empty:
                continue

            meta_total = meta_mes["PUNTOS"].sum()

            pct_lider, pct_asesor = calcular_distribucion(n_asesores, cvs)

            meta_lider_val = meta_total * pct_lider
            meta_asesores_val = meta_total * pct_asesor

            # ======================
            # LIDER
            # ======================

            lideres_mes = ventas_mes[
                ventas_mes["ROLVENDEDOR"].str.upper() == "LIDER"
            ].groupby("NOMBREVENDEDOR")["PUNTOS"].sum()

            for nombre, ejecutado in lideres_mes.items():

                porc = round((ejecutado / meta_lider_val) * 100, 1) if meta_lider_val > 0 else 0

                cumplimiento_list.append({
                    "MES": mes,
                    "ROL": "LIDER",
                    "VENDEDOR": nombre,
                    "META": int(meta_lider_val),
                    "EJECUTADO": int(ejecutado),
                    "% CUMPLIMIENTO": f"{porc}%"
                })

            # ======================
            # ASESORES
            # ======================

            for nombre, ejecutado in asesores_mes.items():

                porc = round((ejecutado / meta_asesores_val) * 100, 1) if meta_asesores_val > 0 else 0

                cumplimiento_list.append({
                    "MES": mes,
                    "ROL": "ASESOR",
                    "VENDEDOR": nombre,
                    "META": int(meta_asesores_val),
                    "EJECUTADO": int(ejecutado),
                    "% CUMPLIMIENTO": f"{porc}%"
                })

        df_cumplimiento = pd.DataFrame(cumplimiento_list)

        if not df_cumplimiento.empty:

            # convertir % a número para gráfico
            df_cumplimiento["CUMPLIMIENTO_NUM"] = (
                df_cumplimiento["% CUMPLIMIENTO"]
                .str.rstrip("%")
                .astype(float)
            )

            # ======================
            # GRAFICO
            # ======================

            fig_puntos = px.bar(
                df_cumplimiento,
                x="VENDEDOR",
                y="CUMPLIMIENTO_NUM",
                color="ROL",
                facet_col="MES",
                text="% CUMPLIMIENTO",
                color_discrete_map={
                    "LIDER": "#00CC96",
                    "ASESOR": "#636EFA"
                }
            )

            fig_puntos.update_traces(textposition="outside")

            fig_puntos.update_layout(
                yaxis_title="% Cumplimiento",
                xaxis_title="Vendedor"
            )

            st.plotly_chart(fig_puntos, use_container_width=True)

            # =====================================================
            # RESUMEN GENERAL POR ROL
            # =====================================================

            st.markdown("### 📊 Resumen KPI por Puntos")

            resumen_puntos = (
                df_cumplimiento
                .groupby("ROL")[["META", "EJECUTADO"]]
                .sum()
                .reset_index()
            )

            resumen_puntos["% CUMPLIMIENTO"] = (
                resumen_puntos["EJECUTADO"] /
                resumen_puntos["META"] * 100
            ).round(1)

            resumen_puntos["% CUMPLIMIENTO"] = resumen_puntos["% CUMPLIMIENTO"].astype(str) + "%"

            st.dataframe(
                resumen_puntos,
                use_container_width=True
            )

            # =====================================================
            # DETALLE POR VENDEDOR
            # =====================================================

            st.markdown("### 📋 Detalle por Vendedor")

            st.dataframe(
                df_cumplimiento[
                    ["MES", "ROL", "VENDEDOR", "META", "EJECUTADO", "% CUMPLIMIENTO"]
                ],
                use_container_width=True
            )





        # =====================================================
        # ACCESORIOS - META VS EJECUTADO EN PESOS
        # =====================================================

        st.markdown("## 💰 Cumplimiento Accesorios (COP)")

        meses_trimestre = ["Diciembre","Enero","Febrero"]

        accesorios_resumen = []

        for mes in meses_trimestre:

            # ==============================
            # FILTRO DE VENTAS (APLICA CVS)
            # ==============================

            ventas_mes = ventas[
                (ventas["MES"] == mes) &
                (ventas["PRODUCTODEVENTA"].str.upper() == "ACCESORIOS") &
                (ventas["SUCURSAL"] == cvs)
            ]

            if ventas_mes.empty:
                ejecutado = 0
            else:
                ejecutado = pd.to_numeric(
                    ventas_mes["VALORNETO"], errors="coerce"
                ).sum()

            # ==============================
            # META DEL MES (APLICA CVS)
            # ==============================

            meta_mes = meta_lider[
                (meta_lider["MES"] == mes) &
                (meta_lider["SUCURSAL"] == cvs)
            ]

            if meta_mes.empty:
                meta = 0
            else:
                meta = pd.to_numeric(
                    meta_mes["ACCESORIOS"], errors="coerce"
                ).sum()

            # ==============================
            # CALCULO CUMPLIMIENTO
            # ==============================

            if meta > 0:
                cumplimiento = (ejecutado / meta) * 100
            else:
                cumplimiento = 0

            accesorios_resumen.append({
                "MES": mes,
                "META_COP": meta,
                "EJECUTADO_COP": ejecutado,
                "CUMPLIMIENTO": round(cumplimiento,1)
            })

        df_accesorios = pd.DataFrame(accesorios_resumen)

        # ==============================
        # FORMATO
        # ==============================

        df_accesorios["META_COP"] = df_accesorios["META_COP"].round(0)
        df_accesorios["EJECUTADO_COP"] = df_accesorios["EJECUTADO_COP"].round(0)

        df_accesorios["% CUMPLIMIENTO"] = (
            df_accesorios["CUMPLIMIENTO"].astype(str) + "%"
        )

        # ==============================
        # GRAFICO
        # ==============================

        fig_acc = px.bar(
            df_accesorios,
            x="MES",
            y="CUMPLIMIENTO",
            text="% CUMPLIMIENTO",
            color="CUMPLIMIENTO",
            color_continuous_scale="Tealgrn"
        )

        fig_acc.update_traces(textposition="outside")

        fig_acc.update_layout(
            title="Cumplimiento de Accesorios (%)",
            yaxis_title="% Cumplimiento",
            xaxis_title="Mes",
            height=450
        )

        st.plotly_chart(fig_acc, use_container_width=True)

        # ==============================
        # TABLA
        # ==============================
        
        st.markdown("### 📊 Resumen Accesorios")


        # =====================================
        # FORMATEAR VALORES EN PESOS COLOMBIANOS
        # =====================================

        df_accesorios["META_COP"] = df_accesorios["META_COP"].apply(lambda x: f"$ {x:,.0f}")
        df_accesorios["EJECUTADO_COP"] = df_accesorios["EJECUTADO_COP"].apply(lambda x: f"$ {x:,.0f}")
        st.dataframe(
            df_accesorios[
                ["MES","META_COP","EJECUTADO_COP","% CUMPLIMIENTO"]
            ],
            use_container_width=True
        )




        # =====================================================
        # 📦 ACCESORIOS - RESUMEN POR REFERENCIA
        # =====================================================

        st.markdown("## 📦 Cantidades Vendidas de Accesorios por Referencia")

        # Filtrar accesorios
        ventas_accesorios = ventas[
            ventas["PRODUCTODEVENTA"].astype(str).str.upper() == "ACCESORIOS"
        ]

        # Quitar referencias vacías
        ventas_accesorios = ventas_accesorios[
            ventas_accesorios["REFERENCIA"].notna()
        ]

        # =====================================
        # RESUMEN POR MES Y REFERENCIA
        # =====================================

        resumen_ref = (
            ventas_accesorios
            .groupby(["MES","REFERENCIA"])
            .size()                # contar ventas
            .reset_index(name="CANTIDAD")
        )

        # Ordenar
        resumen_ref = resumen_ref.sort_values(
            ["MES","CANTIDAD"],
            ascending=[True,False]
        )

        # =====================================
        # TABLA
        # =====================================

        st.markdown("### 📊 Resumen Cantidades por Referencia")

        st.dataframe(
            resumen_ref,
            use_container_width=True
        )

        # =====================================
        # TOP 10 REFERENCIAS POR MES
        # =====================================

        top_ref = (
            resumen_ref
            .groupby("MES")
            .head(10)
        )

        # =====================================
        # GRAFICO
        # =====================================

        fig_ref = px.bar(
            top_ref,
            x="REFERENCIA",
            y="CANTIDAD",
            color="MES",
            facet_col="MES",
            text="CANTIDAD"
        )

        fig_ref.update_traces(textposition="outside")

        fig_ref.update_layout(
            title="Top 10 Referencias de Accesorios por Mes",
            xaxis_title="Referencia",
            yaxis_title="Cantidad Vendida",
            height=500
        )

        st.plotly_chart(fig_ref, use_container_width=True)













        # =====================================================
        # TOP 10 CUMPLIMIENTO GENERAL POR PUNTOS
        # =====================================================

        st.markdown("## 🏆 Ranking de Cumplimiento por Puntos (Top 10)")

        top_resultados = []

        for mes in meses_trimestre:

            ventas_mes = ventas[ventas["MES"] == mes].copy()

            if ventas_mes.empty:
                continue

            # -------------------------------------------------
            # LIMPIAR NOMBRES (evita errores de pandas)
            # -------------------------------------------------

            ventas_mes = ventas_mes[
                (ventas_mes["NOMBREVENDEDOR"].notna()) &
                (ventas_mes["NOMBREVENDEDOR"].astype(str).str.strip() != "") &
                (~ventas_mes["NOMBREVENDEDOR"].astype(str).str.upper().str.contains("SUPERNUMERARIO", na=False))
            ]

            if ventas_mes.empty:
                continue

            # -------------------------------------------------
            # AGRUPAR PUNTOS EJECUTADOS
            # -------------------------------------------------

            ejec = (
                ventas_mes
                .groupby(["SUCURSAL","ROLVENDEDOR","NOMBREVENDEDOR"])["PUNTOS"]
                .sum()
                .reset_index()
            )

            # -------------------------------------------------
            # CALCULAR META POR PERSONA
            # -------------------------------------------------

            for i, row in ejec.iterrows():

                sucursal = row["SUCURSAL"]
                rol = row["ROLVENDEDOR"]
                nombre = row["NOMBREVENDEDOR"]
                ejecutado = row["PUNTOS"]

                meta_mes = meta_lider[
                    (meta_lider["SUCURSAL"] == sucursal) &
                    (meta_lider["MES"] == mes)
                ]

                if meta_mes.empty:
                    continue

                meta_total = meta_mes["PUNTOS"].sum()

                asesores = ventas_mes[
                    (ventas_mes["SUCURSAL"] == sucursal) &
                    (ventas_mes["ROLVENDEDOR"].str.upper() == "ASESOR")
                ]["NOMBREVENDEDOR"].nunique()

                pct_lider, pct_asesor = calcular_distribucion(asesores, sucursal)

                if rol.upper() == "LIDER":
                    meta = meta_total * pct_lider
                else:
                    meta = meta_total * pct_asesor

                if meta == 0:
                    continue

                cumplimiento = (ejecutado / meta) * 100

                top_resultados.append({
                    "MES": mes,
                    "SUCURSAL": sucursal,
                    "ROL": rol,
                    "VENDEDOR": nombre,
                    "META": round(meta,0),
                    "EJECUTADO": ejecutado,
                    "CUMPLIMIENTO": cumplimiento
                })


        df_top = pd.DataFrame(top_resultados)

        if not df_top.empty:

            # -----------------------------
            # LIMPIAR DATOS PROBLEMÁTICOS
            # -----------------------------

            df_top["META"] = pd.to_numeric(df_top["META"], errors="coerce")
            df_top["EJECUTADO"] = pd.to_numeric(df_top["EJECUTADO"], errors="coerce")

            df_top = df_top.replace([np.inf, -np.inf], np.nan)

            df_top["META"] = df_top["META"].fillna(0)
            df_top["EJECUTADO"] = df_top["EJECUTADO"].fillna(0)

            # recalcular cumplimiento seguro
            df_top["CUMPLIMIENTO"] = np.where(
                df_top["META"] > 0,
                (df_top["EJECUTADO"] / df_top["META"]) * 100,
                0
            )

            df_top["CUMPLIMIENTO"] = df_top["CUMPLIMIENTO"].round(1)

            # eliminar nombres vacíos
            df_top = df_top[
                (df_top["VENDEDOR"].notna()) &
                (df_top["VENDEDOR"].astype(str).str.strip() != "")
            ]

            # -----------------------------
            # TOP 10 MAYOR CUMPLIMIENTO
            # -----------------------------

            st.markdown("### 🚀 Top 10 Mayor Cumplimiento de Líderes y Asesores")

            for mes in meses_trimestre:

                df_mes = df_top[df_top["MES"] == mes]

                if df_mes.empty:
                    continue

                top10 = (
                    df_mes
                    .sort_values("CUMPLIMIENTO", ascending=False)
                    .head(10)
                )

                st.markdown(f"#### 📅 {mes}")

                fig_top = px.bar(
                    top10,
                    x="VENDEDOR",
                    y="CUMPLIMIENTO",
                    color="ROL",
                    text="CUMPLIMIENTO",
                    hover_data=["SUCURSAL","META","EJECUTADO"]
                )

                fig_top.update_traces(
                    texttemplate='%{text:.0f}%',
                    textposition="outside"
                )

                st.plotly_chart(fig_top,use_container_width=True)










    # =====================================================
    # COLUMNA 2
    # CUMPLIMIENTO POR PRODUCTO (NUEVAS REGLAS FEBRERO)
    # =====================================================

    with col_productos:

        st.markdown("### 📦 Cumplimiento por Producto")

        productos = ["POSTPAGO","FOCO","TERMINALES","HOGAR","CVS PLUS","OTROS"]

        cumplimiento_producto = []

        for producto in productos:

            for mes in meses_trimestre:

                ventas_mes = ventas_cvs[
                    (ventas_cvs["MES"]==mes) &
                    (ventas_cvs["PRODUCTO"].str.upper()==producto)
                ]

                if ventas_mes.empty:
                    continue

                asesores_mes = ventas_mes[
                    ventas_mes["ROLVENDEDOR"].str.upper()=="ASESOR"
                ].groupby("NOMBREVENDEDOR")["CANTIDAD"].sum()

                n_asesores = len(asesores_mes)

                meta_mes = meta_lider[
                    (meta_lider["SUCURSAL"]==cvs) &
                    (meta_lider["MES"]==mes)
                ]

                if meta_mes.empty:
                    continue

                if producto in meta_mes.columns:
                    meta_total = meta_mes.iloc[0][producto]
                else:
                    meta_total = 0

                pct_lider, pct_asesor = calcular_distribucion(n_asesores, cvs)

                meta_lider_val = meta_total * pct_lider
                meta_asesores_val = meta_total * pct_asesor

                # =====================
                # LIDER
                # =====================
                lideres_mes = ventas_mes[
                    ventas_mes["ROLVENDEDOR"].str.upper()=="LIDER"
                ].groupby("NOMBREVENDEDOR")["CANTIDAD"].sum()

                for nombre, ejecutado in lideres_mes.items():

                    cumplimiento_producto.append({
                        "MES":mes,
                        "PRODUCTO":producto,
                        "ROL":"LIDER",
                        "VENDEDOR":nombre,
                        "META":int(meta_lider_val),
                        "EJECUTADO":int(ejecutado)
                    })

                # =====================
                # ASESORES
                # =====================
                for nombre, ejecutado in asesores_mes.items():

                    cumplimiento_producto.append({
                        "MES":mes,
                        "PRODUCTO":producto,
                        "ROL":"ASESOR",
                        "VENDEDOR":nombre,
                        "META":int(meta_asesores_val),
                        "EJECUTADO":int(ejecutado)
                    })

        df_cumplimiento_producto = pd.DataFrame(cumplimiento_producto)

        if not df_cumplimiento_producto.empty:

            producto_select = st.selectbox(
                "Producto",
                df_cumplimiento_producto["PRODUCTO"].unique()
            )

            df_producto = df_cumplimiento_producto[
                df_cumplimiento_producto["PRODUCTO"]==producto_select
            ]

            # =====================================================
            # RESUMEN META VS EJECUTADO POR VENDEDOR
            # =====================================================

            resumen = (
                df_producto
                .groupby(["MES","ROL","VENDEDOR"], as_index=False)
                .agg({
                    "META":"sum",
                    "EJECUTADO":"sum"
                })
            )

            # Calcular % correcto
            # Calcular % cumplimiento evitando división por 0
            resumen["CUMPLIMIENTO_NUM"] = np.where(
                resumen["META"] > 0,
                (resumen["EJECUTADO"] / resumen["META"]) * 100,
                0
            )

            resumen["CUMPLIMIENTO_NUM"] = resumen["CUMPLIMIENTO_NUM"].replace([np.inf, -np.inf], 0)
            resumen["CUMPLIMIENTO_NUM"] = resumen["CUMPLIMIENTO_NUM"].fillna(0).round(0)

            resumen["% CUMPLIMIENTO"] = resumen["CUMPLIMIENTO_NUM"].astype(int).astype(str) + "%"

            # =====================================================
            # GRAFICO
            # =====================================================

            fig_producto = px.bar(
                resumen,
                x="VENDEDOR",
                y="CUMPLIMIENTO_NUM",
                color="ROL",
                facet_col="MES",
                text="% CUMPLIMIENTO",
                color_discrete_map={
                    "LIDER":"#00CC96",
                    "ASESOR":"#636EFA"
                }
            )

            fig_producto.update_traces(textposition="outside")

            fig_producto.update_layout(
                yaxis_title="% Cumplimiento",
                xaxis_title="Vendedor",
                height=500
            )

            st.plotly_chart(fig_producto,use_container_width=True)

            # =====================================================
            # TABLA RESUMEN
            # =====================================================

            st.markdown("### 📋 Resumen de Cumplimiento")

            resumen = resumen.sort_values(["MES","ROL","VENDEDOR"])

            st.dataframe(
                resumen[["MES","ROL","VENDEDOR","META","EJECUTADO","% CUMPLIMIENTO"]],
                use_container_width=True
            )




    

        # =====================================================
        # TOP REFERENCIAS MÁS VENDIDAS POR MARCA
        # =====================================================

        st.markdown("## 📱 Top Referencias más Vendidas")

        marcas_interes = [
            "APPLE",
            "HONOR",
            "MOTOROLA",
            "OPPO",
            "SAMSUNG",
            "SIM CARD",
            "VIVO",
            "XIAOMI",
            "ZTE"
        ]

        # Normalizar columnas
        ventas["MARCA"] = ventas["MARCA"].astype(str).str.upper().str.strip()
        ventas["REFERENCIA"] = ventas["REFERENCIA"].astype(str).str.strip()

        # Filtrar marcas
        ventas_marcas = ventas[
            ventas["MARCA"].isin(marcas_interes)
        ]

        # Agrupar ventas
        ventas_ref = (
            ventas_marcas
            .groupby(["MES","MARCA","REFERENCIA"])["CANTIDAD"]
            .sum()
            .reset_index()
        )

        # Selector de marca
        marca_select = st.selectbox(
            "Seleccionar Marca",
            sorted(ventas_ref["MARCA"].unique())
        )

        df_marca = ventas_ref[
            ventas_ref["MARCA"] == marca_select
        ]

        # =====================================================
        # TOP 10 POR MES
        # =====================================================

        st.markdown("### 📊 Top 10 Referencias por Mes")

        for mes in sorted(df_marca["MES"].unique()):

            df_mes = df_marca[df_marca["MES"] == mes]

            if df_mes.empty:
                continue

            top10_mes = (
                df_mes
                .sort_values("CANTIDAD", ascending=False)
                .head(10)
            )

            fig_mes = px.bar(
                top10_mes,
                x="CANTIDAD",
                y="REFERENCIA",
                orientation="h",
                text="CANTIDAD",
                color="CANTIDAD",
                color_continuous_scale="Tealgrn",
                title=f"Top 10 Referencias - {mes}"
            )

            fig_mes.update_layout(
                yaxis=dict(autorange="reversed"),
                xaxis_title="Cantidad Vendida",
                yaxis_title="Referencia",
                height=450
            )

            fig_mes.update_traces(textposition="outside")

            st.plotly_chart(fig_mes, use_container_width=True)

        # =====================================================
        # TOP 10 REFERENCIAS MÁS VENDIDAS POR MES
        # (EXCLUYENDO ACCESORIOS Y TECNOLOGIA)
        # =====================================================

        st.markdown("## 🏆 Top 10 Referencias Más Vendidas por Mes")

        # Normalizar columnas
        ventas["REFERENCIA"] = ventas["REFERENCIA"].astype(str).str.strip()
        ventas["MES"] = ventas["MES"].astype(str).str.strip()
        ventas["PRODUCTODEVENTA"] = ventas["PRODUCTODEVENTA"].astype(str).str.upper().str.strip()

        for mes in meses_trimestre:

            df_mes = ventas[
                (ventas["MES"] == mes) &
                (~ventas["PRODUCTODEVENTA"].isin(["ACCESORIOS","TECNOLOGIA", "CVS PLUS"]))
            ]

            if df_mes.empty:
                continue

            # Agrupar por referencia
            top_ref = (
                df_mes
                .groupby("REFERENCIA")["CANTIDAD"]
                .sum()
                .reset_index()
                .sort_values("CANTIDAD", ascending=False)
                .head(10)
            )

            # ==========================
            # GRAFICO
            # ==========================

            fig_top_ref = px.bar(
                top_ref,
                x="CANTIDAD",
                y="REFERENCIA",
                orientation="h",
                text="CANTIDAD",
                color="CANTIDAD",
                color_continuous_scale="Tealgrn",
                title=f"Top 10 Referencias Más Vendidas - {mes}"
            )

            fig_top_ref.update_layout(
                yaxis=dict(autorange="reversed"),
                xaxis_title="Cantidad Vendida",
                yaxis_title="Referencia",
                height=450
            )

            fig_top_ref.update_traces(textposition="outside")

            st.plotly_chart(fig_top_ref, use_container_width=True)


# ====================================================
# TAB 3 Resultado de recaudos
# ====================================================

with tab3:

    st.subheader("📊 Resultado de Recaudos Cajeras")

    cajeras.columns = cajeras.columns.str.strip()

    # -----------------------------------
    # FILTRO POR MES
    # -----------------------------------

    meses = cajeras["Mes"].unique()

    mes_select = st.selectbox(
        "Seleccionar Mes",
        ["Trimestre Completo"] + list(meses)
    )

    if mes_select == "Trimestre Completo":
        df_trim = cajeras[
            cajeras["Mes"].isin(["Diciembre","Enero","Febrero"])
        ]
    else:
        df_trim = cajeras[
            cajeras["Mes"] == mes_select
        ]

    # -----------------------------------
    # AGRUPAR POR SUCURSAL
    # -----------------------------------

    resumen_trim = (
        df_trim
        .groupby("Sucursal")
        .agg({
            "SADMIN":"sum",
            "SICACOM":"sum",
            "PAGOS CLARO":"sum",
            "OTROS CONVENIOS":"sum",
            "TOTAL CORRESPONSAL":"sum",
            "TOTAL RECAUDOS":"sum",
            "SERCOM ACTIVOS":"sum"
        })
        .reset_index()
    )

    # -----------------------------------
    # CALCULO PORCENTAJES
    # -----------------------------------

    resumen_trim["SADMIN %"] = (
        resumen_trim["SADMIN"] /
        resumen_trim["TOTAL RECAUDOS"] * 100
    )

    resumen_trim["SICACOM %"] = (
        resumen_trim["SICACOM"] /
        resumen_trim["TOTAL RECAUDOS"] * 100
    )

    resumen_trim["TOTAL CORRESPONSAL %"] = (
        resumen_trim["TOTAL CORRESPONSAL"] /
        resumen_trim["TOTAL RECAUDOS"] * 100
    )

    # Formato %
    resumen_trim["SADMIN %"] = resumen_trim["SADMIN %"].map("{:.2f}%".format)
    resumen_trim["SICACOM %"] = resumen_trim["SICACOM %"].map("{:.2f}%".format)
    resumen_trim["TOTAL CORRESPONSAL %"] = resumen_trim["TOTAL CORRESPONSAL %"].map("{:.2f}%".format)

    # -----------------------------------
    # ORDENAR POR RECAUDO
    # -----------------------------------

    resumen_trim = resumen_trim.sort_values(
        by="TOTAL RECAUDOS",
        ascending=False
    )

    # -----------------------------------
    # KPIs
    # -----------------------------------

    total_recaudo = resumen_trim["TOTAL RECAUDOS"].sum()
    total_corresp = resumen_trim["TOTAL CORRESPONSAL"].sum()
    total_creditos = resumen_trim["SERCOM ACTIVOS"].sum()

    col1, col2, col3 = st.columns(3)

    col1.metric("💰 Total Recaudo", f"${total_recaudo:,.0f}")
    col2.metric("📑 Total Correspondencias", f"{total_corresp:,.0f}")
    col3.metric("💳 Sercom Activos", f"{total_creditos:,.0f}")

    # -----------------------------------
    # GRAFICO RECAUDO POR SUCURSAL
    # -----------------------------------

    st.subheader("Recaudo por Sucursal")

    fig1 = px.bar(
        resumen_trim,
        x="Sucursal",
        y="TOTAL RECAUDOS",
        text="TOTAL RECAUDOS"
    )

    fig1.update_traces(
        texttemplate='$%{text:,.0f}',
        textposition="outside"
    )

    fig1.update_layout(
        xaxis_title="Sucursal",
        yaxis_title="Recaudo"
    )

    st.plotly_chart(fig1, use_container_width=True)

    # -----------------------------------
    # DISTRIBUCION DE RECAUDO
    # -----------------------------------

    st.subheader("Distribución por Tipo de Recaudo")

    tipos = df_trim[
        ["SADMIN","SICACOM","PAGOS CLARO","OTROS CONVENIOS"]
    ].sum().reset_index()

    tipos.columns = ["Tipo","Valor"]

    tipos = tipos.sort_values(
        by="Valor",
        ascending=False
    )

    fig2 = px.bar(
        tipos,
        x="Tipo",
        y="Valor",
        text="Valor"
    )

    fig2.update_traces(
        texttemplate='$%{text:,.0f}',
        textposition="outside"
    )

    st.plotly_chart(fig2, use_container_width=True)

    # -----------------------------------
    # GRAFICO SERCOM ACTIVOS
    # -----------------------------------

    st.subheader("Sercom Activos por Sucursal")

    fig3 = px.bar(
        resumen_trim.sort_values("SERCOM ACTIVOS", ascending=False),
        x="Sucursal",
        y="SERCOM ACTIVOS",
        text="SERCOM ACTIVOS"
    )

    fig3.update_traces(
        texttemplate='%{text}',
        textposition="outside"
    )

    st.plotly_chart(fig3, use_container_width=True)

    # -----------------------------------
    # TABLA RESUMEN
    # -----------------------------------

    st.subheader("Resumen por Sucursal")

    st.dataframe(
        resumen_trim,
        use_container_width=True,
        hide_index=True
    )