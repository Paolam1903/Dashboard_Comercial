import pandas as pd

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



# =================================================
# META GENERAL + EJECUCIÓN (RESUMEN POR CVS)
# =================================================
def resumen_meta_general_por_cvs(df):
    resultados = []

    for sucursal, grupo in df.groupby("Sucursal"):
        meta_total = grupo["Meta_General"].iloc[0]

        n_asesores = grupo[grupo["Rol"] == "ASESOR"]["Cedula_Vendedor"].nunique()
        pct_lider, pct_asesores = calcular_distribucion(n_asesores, sucursal)


        puntos_lider = grupo[grupo["Rol"] == "LIDER"]["Puntos"].sum()
        puntos_asesores = grupo[grupo["Rol"] == "ASESOR"]["Puntos"].sum()

        resultados.append({
            "Sucursal": sucursal,
            "Estructura": f"1 Líder + {n_asesores} Asesor(es)",

            "Meta CVS": meta_total,

            "Meta Líder": meta_total * pct_lider,
            "Ejecutado Líder": puntos_lider,
            "Cumplimiento Líder %": round(
                (puntos_lider / (meta_total * pct_lider)) * 100, 2
            ) if meta_total * pct_lider > 0 else 0,

            "Meta Asesores": meta_total * pct_asesores,
            "Ejecutado Asesores": puntos_asesores,
            "Cumplimiento Asesores %": round(
                (puntos_asesores / (meta_total * pct_asesores)) * 100, 2
            ) if meta_total * pct_asesores > 0 else 0,
        })

    return pd.DataFrame(resultados)


# =================================================
# KPI POR PRODUCTO + EJECUCIÓN (RESUMEN POR CVS)
# =================================================
def resumen_kpi_producto_por_cvs(df):
    resultados = []

    for (sucursal, producto), grupo in df.groupby(["Sucursal", "Producto"]):
        meta_producto = grupo["Meta_Producto"].iloc[0]

        n_asesores = grupo[grupo["Rol"] == "ASESOR"]["Cedula_Vendedor"].nunique()
        pct_lider, pct_asesores = calcular_distribucion(n_asesores, sucursal)


        puntos_lider = grupo[grupo["Rol"] == "LIDER"]["Puntos"].sum()
        puntos_asesores = grupo[grupo["Rol"] == "ASESOR"]["Puntos"].sum()

        resultados.append({
            "Sucursal": sucursal,
            "Producto": producto,

            "Meta Producto": meta_producto,

            "Meta Líder": meta_producto * pct_lider,
            "Ejecutado Líder": puntos_lider,
            "Cumplimiento Líder %": round(
                (puntos_lider / (meta_producto * pct_lider)) * 100, 2
            ) if meta_producto * pct_lider >= 0 else 0,

            "Meta Asesores": meta_producto * pct_asesores,
            "Ejecutado Asesores": puntos_asesores,
            "Cumplimiento Asesores %": round(
                (puntos_asesores / (meta_producto * pct_asesores)) * 100, 2
            ) if meta_producto * pct_asesores >= 0 else 0,
        })

    return pd.DataFrame(resultados)
