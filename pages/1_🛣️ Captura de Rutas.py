import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURACIÓN SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# --- CARGAR DATOS GENERALES DESDE CSV ---
@st.cache_data
def cargar_datos_generales():
    try:
        return pd.read_csv("datos_generales.csv").iloc[0].to_dict()
    except:
        return {
            "Operator pay per mile": 0.0,
            "Operator pay per empty mile": 0.0,
            "Team pay per mile": 0.0,
            "Team pay per empty mile": 0.0,
            "Operator bonus": 0.0,
            "Team bonus": 0.0,
            "Truck performance": 2.5,
            "Diesel": 24.0,
            "Fuel": 1.0,
            "Dollar exchange rate": 18.0,
            "Loaded crossborder payment": 300.0,
            "Empty crossborder payment": 200.0,
            "Operator pay mex": 1000.0,
            "Team pay mex": 900.0,
            "Operator bonus mex": 400.0
        }

def guardar_datos_generales(data_dict):
    df = pd.DataFrame([data_dict])
    df.to_csv("datos_generales.csv", index=False)

datos_generales = cargar_datos_generales()

st.title("🛣️ Captura de Rutas - Lincoln")

st.header("⚙️ General data")
col1, col2 = st.columns(2)

with col1:
    datos_generales["Operator pay per mile"] = st.number_input("Operator pay per mile", value=datos_generales["Operator pay per mile"])
    datos_generales["Operator pay per empty mile"] = st.number_input("Operator pay per empty mile", value=datos_generales["Operator pay per empty mile"])
    datos_generales["Team pay per mile"] = st.number_input("Team pay per mile", value=datos_generales["Team pay per mile"])
    datos_generales["Team pay per empty mile"] = st.number_input("Team pay per empty mile", value=datos_generales["Team pay per empty mile"])
    datos_generales["Operator bonus"] = st.number_input("Operator bonus", value=datos_generales["Operator bonus"])
    datos_generales["Team bonus"] = st.number_input("Team bonus", value=datos_generales["Team bonus"])
    datos_generales["Truck performance"] = st.number_input("Truck performance", value=datos_generales["Truck performance"])

with col2:
    datos_generales["Diesel"] = st.number_input("Diesel", value=datos_generales["Diesel"])
    datos_generales["Fuel"] = st.number_input("Fuel", value=datos_generales["Fuel"])
    datos_generales["Dollar exchange rate"] = st.number_input("Dollar exchange rate", value=datos_generales["Dollar exchange rate"])
    datos_generales["Loaded crossborder payment"] = st.number_input("Loaded crossborder payment", value=datos_generales["Loaded crossborder payment"])
    datos_generales["Empty crossborder payment"] = st.number_input("Empty crossborder payment", value=datos_generales["Empty crossborder payment"])
    datos_generales["Operator pay mex"] = st.number_input("Operator pay mex", value=datos_generales["Operator pay mex"])
    datos_generales["Team pay mex"] = st.number_input("Team pay mex", value=datos_generales["Team pay mex"])
    datos_generales["Operator bonus mex"] = st.number_input("Operator bonus mex",

st.header("📝 Route Capture Form")

with st.form("formulario_ruta"):
    col1, col2 = st.columns(2)

    with col1:
        fecha = st.date_input("Date")
        tipo_viaje = st.selectbox("Type of trip", ["NB", "PPNB", "SB", "PPSB", "DOMUSA", "DOMMEX"])
        cliente = st.text_input("Customer")
        modo_viaje = st.selectbox("Trip mode", ["Operator", "Team"])
        origen_usa = st.text_input("Origin USA")
        destino_usa = st.text_input("Destination USA")
        millas_usa = st.number_input("Miles USA", min_value=0.0)
        millas_vacias = st.number_input("Miles Empty", min_value=0.0)
        ingreso_milla = st.number_input("Income per mile", min_value=0.0)
        moneda_usa = st.selectbox("Currency USA", ["USD", "MXP"])
        ingreso_fuel_usa = datos_generales["Fuel"] * millas_usa

    with col2:
        mexican_line = st.selectbox("Mexican Line", ["Propia", "Filial/Externa"])
        origen_mex = st.text_input("Origin MEX")
        destino_mex = st.text_input("Destination MEX")
        millas_mex = st.number_input("Miles MEX", min_value=0.0)
        ingreso_mex = st.number_input("Income MEX", min_value=0.0)
        cargo_mex = st.number_input("Charge MEX", min_value=0.0)
        moneda_mex = st.selectbox("Currency MEX", ["USD", "MXP"])
        tipo_cruce = st.selectbox("Type of crossborder", ["Propio", "Filial/Externo"])
        tipo_carga_cruce = st.selectbox("Load type crossborder", ["Loaded", "Empty"])
        ingreso_cruce = st.number_input("Crossborder income", min_value=0.0)
        moneda_ingreso_cruce = st.selectbox("Currency Crossborder", ["USD", "MXP"])
        cargo_cruce = st.number_input("Crossborder charge", min_value=0.0)
        moneda_cargo_cruce = st.selectbox("Currency Crossborder charge", ["USD", "MXP"])

    st.subheader("💵 Chargue Extras (USA)")
    extras = {}
    cols_extras = st.columns(3)
    campos_extras = [
        "Fianzas", "Aditional Insurance", "Demoras/Detention", "Movimiento extraordinario",
        "Lumper fees", "Maniobras", "Loadlocks", "Lay over", "Gatas", "Accessories", "Guias"
    ]
    for idx, campo in enumerate(campos_extras):
        with cols_extras[idx % 3]:
            extras[campo] = st.number_input(campo, min_value=0.0, key=campo)

    boton_revisar = st.form_submit_button("🔎 Check route")
