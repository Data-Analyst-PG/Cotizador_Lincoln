import streamlit as st
from supabase import create_client, Client
import pandas as pd

# --- CONFIGURACIÓN SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- CARGAR DATOS GENERALES ---
datos_generales = pd.read_csv("datos_generales.csv").iloc[0]

# --- GENERADOR ID_RUTA ---
def generar_nuevo_id():
    data = supabase.table("Rutas_Lincoln").select("ID_Ruta").order("ID_Ruta", desc=True).limit(1).execute()
    if data.data:
        last_id = data.data[0]["ID_Ruta"]
        num = int(last_id.replace("LIN", ""))
        return f"LIN{num+1:06d}"
    return "LIN000001"

# --- FORMULARIO ---
st.title("🚛 Captura de Rutas - Lincoln")

with st.form("form_ruta"):
    fecha = st.date_input("Fecha")
    tipo_viaje = st.selectbox("Tipo de viaje", ["NB", "PPNB", "SB", "PPSB", "DOMUSA", "DOMMEX"])
    cliente = st.text_input("Cliente")
    modo_viaje = st.selectbox("Modo de viaje", ["Operator", "Team"])

    st.subheader("Segmento USA")
    origen_usa = st.text_input("Origen USA")
    destino_usa = st.text_input("Destino USA")
    millas_usa = st.number_input("Millas USA", min_value=0.0)
    millas_vacias = st.number_input("Millas Vacías", min_value=0.0)
    ingreso_milla = st.number_input("Ingreso por milla", min_value=0.0)
    moneda_usa = st.selectbox("Moneda USA", ["USD", "MXP"])

    st.subheader("Segmento MEX")
    mexican_line = st.selectbox("Mexican Line", ["Propia", "Filial/Externa"])
    origen_mex = st.text_input("Origen MEX")
    destino_mex = st.text_input("Destino MEX")
    millas_mex = st.number_input("Millas MEX", min_value=0.0)
    ingreso_mex = st.number_input("Ingreso MEX", min_value=0.0)
    cargo_mex = st.number_input("Cargo MEX", min_value=0.0)
    moneda_mex = st.selectbox("Moneda MEX", ["USD", "MXP"])

    st.subheader("Cruce")
    tipo_cruce = st.selectbox("Tipo de Cruce", ["Propio", "Filial/Externo"])
    tipo_carga_cruce = st.selectbox("Tipo de carga cruce", ["Loaded", "Empty"])
    ingreso_cruce = st.number_input("Ingreso cruce", min_value=0.0)
    moneda_ingreso_cruce = st.selectbox("Moneda ingreso cruce", ["USD", "MXP"])
    cargo_cruce = st.number_input("Cargo cruce", min_value=0.0)
    moneda_cargo_cruce = st.selectbox("Moneda cargo cruce", ["USD", "MXP"])

    st.subheader("Cargos Extras USA")
    extras = {}
    for campo in ["Fianzas", "Aditional Insurance", "Demoras/Detention", "Movimiento extraordinario",
                  "Lumper fees", "Maniobras", "Loadlocks", "Lay over", "Gatas", "Accessories", "Guias"]:
        extras[campo] = st.number_input(campo, min_value=0.0)

    submitted = st.form_submit_button("Guardar Ruta")

    if submitted:
        # --- CONVERSIÓN MONEDA ---
        tc = datos_generales["Dollar exchange rate"]
        ingreso_fuel_usa = datos_generales["Fuel"] * millas_usa
        ingreso_usa = (ingreso_milla * millas_usa)
        ingreso_usa = ingreso_usa * tc if moneda_usa == "MXP" else ingreso_usa
        ingreso_usa += ingreso_fuel_usa
        ingreso_mex_total = ingreso_mex if moneda_mex == "USD" else ingreso_mex / tc
        ingreso_cruce_total = ingreso_cruce if moneda_ingreso_cruce == "USD" else ingreso_cruce / tc

        # --- SUELDO ---
        if modo_viaje == "Operator":
            sueldo_usa = millas_usa * datos_generales["Operator pay per mile"] + \
                         millas_vacias * datos_generales["Operator pay per empty mile"] + \
                         datos_generales["Operator bonus"]
            sueldo_mex = datos_generales["Operator pay mex"] + datos_generales["Operator bonus mex"]
            pago_km = datos_generales["Operator pay per mile"]
            pago_km_empty = datos_generales["Operator pay per empty mile"]
            pago_mex = datos_generales["Operator pay mex"]
        else:
            sueldo_usa = (millas_usa * datos_generales["Team pay per mile"] + \
                         millas_vacias * datos_generales["Team pay per empty mile"]) * 2 + \
                         datos_generales["Team bonus"] * 2
            sueldo_mex = datos_generales["Team pay mex"] * 2 + datos_generales["Operator bonus mex"] * 2
            pago_km = datos_generales["Team pay per mile"]
            pago_km_empty = datos_generales["Team pay per empty mile"]
            pago_mex = datos_generales["Team pay mex"]

        if mexican_line != "Propia":
            sueldo_mex = 0

        sueldo_cruce = 0
        if tipo_cruce == "Propio":
            sueldo_cruce = datos_generales["Loaded crossborder payment"] if tipo_carga_cruce == "Loaded" \
                else datos_generales["Empty crossborder payment"]

        sueldo_total = sueldo_usa + sueldo_mex + sueldo_cruce

        diesel_usa = (millas_usa / datos_generales["Truck performance"]) * datos_generales["Diesel"]
        diesel_mex = (millas_mex / datos_generales["Truck performance"]) * datos_generales["Diesel"] if mexican_line == "Propia" else 0
        charge_fuel_usa = datos_generales["Fuel"] * millas_usa

        extras_total = sum(extras.values())
        cargos_usa = sueldo_usa + diesel_usa + charge_fuel_usa
        cargos_mex = sueldo_mex + diesel_mex if mexican_line == "Propia" else cargo_mex
        cargo_cruce_final = cargo_cruce if moneda_cargo_cruce == "USD" else cargo_cruce / tc

        total_cargos = cargos_usa + cargos_mex + extras_total + cargo_cruce_final
        total_ingresos = ingreso_usa + ingreso_mex_total + ingreso_cruce_total
        utilidad_bruta = total_ingresos - total_cargos
        porcentaje_bruta = utilidad_bruta / total_ingresos if total_ingresos > 0 else 0
        costos_indirectos = total_ingresos * 0.35
        utilidad_neta = utilidad_bruta - costos_indirectos
        porcentaje_neta = utilidad_neta / total_ingresos if total_ingresos > 0 else 0

        nuevo_id = generar_nuevo_id()

        # --- GUARDAR EN SUPABASE ---
        ruta = {
            "ID_Ruta": nuevo_id,
            "Fecha": str(fecha),
            "Tipo_Viaje": tipo_viaje,
            "Cliente": cliente,
            "Modo_Viaje": modo_viaje,
            "Origen_USA": origen_usa,
            "Destino_USA": destino_usa,
            "Millas_USA": millas_usa,
            "Millas_Vacias_USA": millas_vacias,
            "Ingreso_por_Milla": ingreso_milla,
            "Moneda_USA": moneda_usa,
            "Mexican_Line": mexican_line,
            "Origen_MEX": origen_mex,
            "Destino_MEX": destino_mex,
            "Millas_MEX": millas_mex,
            "Ingreso_MEX": ingreso_mex,
            "Cargo_MEX": cargo_mex,
            "Moneda_MEX": moneda_mex,
            "Tipo_Cruce": tipo_cruce,
            "Tipo_Carga_Cruce": tipo_carga_cruce,
            "Ingreso_Cruce": ingreso_cruce,
            "Moneda_Ingreso_Cruce": moneda_ingreso_cruce,
            "Cargo_Cruce": cargo_cruce,
            "Moneda_Cargo_Cruce": moneda_cargo_cruce,
            "Sueldo_USA": sueldo_usa,
            "Sueldo_MEX": sueldo_mex,
            "Sueldo_Cruce": sueldo_cruce,
            "Diesel_USA": diesel_usa,
            "Diesel_MEX": diesel_mex,
            "Ingreso_USA_Total": ingreso_usa,
            "Ingreso_MEX_Total": ingreso_mex_total,
            "Ingreso_Cruce_Total": ingreso_cruce_total,
            "Ingreso_Total": total_ingresos,
            "Cargos_USA": cargos_usa,
            "Cargos_MEX": cargos_mex,
            "Cargos_Cruce": cargo_cruce_final,
            "Total_Costos": total_cargos,
            "Utilidad_Bruta": utilidad_bruta,
            "Porcentaje_Utilidad_Bruta": porcentaje_bruta,
            "Costos_Indirectos": costos_indirectos,
            "Utilidad_Neta": utilidad_neta,
            "Porcentaje_Utilidad_Neta": porcentaje_neta,
            "Pago_KM_USA": pago_km,
            "Pago_KM_empty_USA": pago_km_empty,
            "Pago_MEX": pago_mex,
            "Diesel": datos_generales["Diesel"],
            "Truck_performance": datos_generales["Truck performance"],
            "Dollar_exchange_rate": datos_generales["Dollar exchange rate"],
            **extras
        }

        supabase.table("Rutas_Lincoln").insert(ruta).execute()
        st.success(f"✅ Ruta guardada con ID: {nuevo_id}")

