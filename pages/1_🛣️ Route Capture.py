import streamlit as st
import pandas as pd
from supabase import create_client
import traceback

if "mostrar_resumen" not in st.session_state:
    st.session_state["mostrar_resumen"] = False
if "resultados_calculo" not in st.session_state:
    st.session_state["resultados_calculo"] = {}

# --- CONFIGURACIÓN SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# --- CARGAR DATOS GENERALES DESDE CSV ---
@st.cache_data
def cargar_datos_generales():
    try:
        return pd.read_csv("datos_generales.csv").iloc[0].to_dict()
    except:
        return {
            "Operator pay per mile": 0.38,
            "Operator pay per empty mile": 0.30,
            "Team pay per mile": 0.30,
            "Team pay per empty mile": 0.25,
            "Operator bonus": 50.0,
            "Team bonus": 30.0,
            "Truck performance": 7.3,
            "Diesel": 3.0,
            "Fuel": 0.60,
            "Dollar exchange rate": 18.0,
            "Loaded crossborder payment": 50.0,
            "Empty crossborder payment": 5.0,
            "Operator pay mex": 200.0,
            "Team pay mex": 150.0,
            "Operator bonus mex": 50.0
        }

def guardar_datos_generales(data_dict):
    df = pd.DataFrame([data_dict])
    df.to_csv("datos_generales.csv", index=False)

datos_generales = cargar_datos_generales()

st.title("🛣️ Route Capture - Lincoln")

with st.expander("⚙️ General data", expanded=False):
    col1, col2, col3 = st.columns(3)

    with col1:
        datos_generales["Operator pay per mile"] = st.number_input("Operator pay per mile", value=datos_generales["Operator pay per mile"])
        datos_generales["Operator pay per empty mile"] = st.number_input("Operator pay per empty mile", value=datos_generales["Operator pay per empty mile"])
        datos_generales["Team pay per mile"] = st.number_input("Team pay per mile", value=datos_generales["Team pay per mile"])
        datos_generales["Team pay per empty mile"] = st.number_input("Team pay per empty mile", value=datos_generales["Team pay per empty mile"])
        datos_generales["Operator bonus"] = st.number_input("Operator bonus", value=datos_generales["Operator bonus"])
    with col2:
        datos_generales["Team bonus"] = st.number_input("Team bonus", value=datos_generales["Team bonus"])
        datos_generales["Truck performance"] = st.number_input("Truck performance", value=datos_generales["Truck performance"])
        datos_generales["Diesel"] = st.number_input("Diesel", value=datos_generales["Diesel"])
        datos_generales["Fuel"] = st.number_input("Fuel", value=datos_generales["Fuel"])
        datos_generales["Dollar exchange rate"] = st.number_input("Dollar exchange rate", value=datos_generales["Dollar exchange rate"])
    with col3:
        datos_generales["Loaded crossborder payment"] = st.number_input("Loaded crossborder payment", value=datos_generales["Loaded crossborder payment"])
        datos_generales["Empty crossborder payment"] = st.number_input("Empty crossborder payment", value=datos_generales["Empty crossborder payment"])
        datos_generales["Operator pay mex"] = st.number_input("Operator pay mex", value=datos_generales["Operator pay mex"])
        datos_generales["Team pay mex"] = st.number_input("Team pay mex", value=datos_generales["Team pay mex"])
        datos_generales["Operator bonus mex"] = st.number_input("Operator bonus mex", value=datos_generales["Operator bonus mex"])
     
    if st.button("💾 Save Settings"):
        guardar_datos_generales(datos_generales)
        st.success("✅ General settings saved successfully.")

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
        mexican_line = st.selectbox("Mexican Line", ["Propia", "Filial/Externa"])

    with col2:
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

    if boton_revisar:
        tc = datos_generales["Dollar exchange rate"]
        fuel_rate = datos_generales["Fuel"]
        diesel_rate = datos_generales["Diesel"]
        rendimiento = datos_generales["Truck performance"]
        
        #Extras
        fianzas = extras["Fianzas"]
        aditional_insurance = extras["Aditional Insurance"]
        demoras = extras["Demoras/Detention"]
        movimiento_extra = extras["Movimiento extraordinario"]
        lumper_fees = extras["Lumper fees"]
        maniobras = extras["Maniobras"]
        loadlocks = extras["Loadlocks"]
        layover = extras["Lay over"]
        gatas = extras["Gatas"]
        accessories = extras["Accessories"]
        guias = extras["Guias"]


        # Income
        income_fuel_usa = fuel_rate * millas_usa
        income_usa = (ingreso_milla * millas_usa)
        if moneda_usa == "MXP":
            income_usa *= tc
        income_usa += income_fuel_usa

        income_mex_total = ingreso_mex if moneda_mex == "USD" else ingreso_mex / tc
        income_cruce_total = ingreso_cruce if moneda_ingreso_cruce == "USD" else ingreso_cruce / tc

        # Salary
        if modo_viaje == "Operator":
            salary_usa = millas_usa * datos_generales["Operator pay per mile"] + \
                         millas_vacias * datos_generales["Operator pay per empty mile"] + \
                         datos_generales["Operator bonus"]
            salary_mex = datos_generales["Operator pay mex"] + datos_generales["Operator bonus mex"]
            pay_km = datos_generales["Operator pay per mile"]
            pay_km_empty = datos_generales["Operator pay per empty mile"]
            pay_mex = datos_generales["Operator pay mex"]
        else:
            salary_usa = (millas_usa * datos_generales["Team pay per mile"] + \
                         millas_vacias * datos_generales["Team pay per empty mile"]) * 2 + \
                         datos_generales["Team bonus"] * 2
            salary_mex = datos_generales["Team pay mex"] * 2 + datos_generales["Operator bonus mex"] * 2
            pay_km = datos_generales["Team pay per mile"]
            pay_km_empty = datos_generales["Team pay per empty mile"]
            pay_mex = datos_generales["Team pay mex"]

        if mexican_line != "Propia":
            salary_mex = 0

        salary_cruce = 0
        if tipo_cruce == "Propio":
            salary_cruce = datos_generales["Loaded crossborder payment"] if tipo_carga_cruce == "Loaded" else datos_generales["Empty crossborder payment"]

        total_salary = salary_usa + salary_mex + salary_cruce

        # Diesel
        diesel_usa = (millas_usa / rendimiento) * diesel_rate
        diesel_mex = (millas_mex / rendimiento) * diesel_rate if mexican_line == "Propia" else 0

        # Extras
        extras_total = sum(extras.values())

        # Charges
        charge_fuel_usa = fuel_rate * millas_usa
        charges_usa = salary_usa + diesel_usa + charge_fuel_usa
        charges_mex = salary_mex + diesel_mex if mexican_line == "Propia" else cargo_mex
        cargo_cruce_final = salary_cruce + cargo_cruce if moneda_cargo_cruce == "USD" else cargo_cruce / tc

        total_charges = charges_usa + charges_mex + extras_total + cargo_cruce_final
        total_income = income_usa + income_mex_total + income_cruce_total
        utilidad_bruta = total_income - total_charges
        porcentaje_bruta = utilidad_bruta / total_income if total_income > 0 else 0
        costos_indirectos = total_income * 0.35
        utilidad_neta = utilidad_bruta - costos_indirectos
        porcentaje_neta = utilidad_neta / total_income if total_income > 0 else 0

        # Al final guarda resultados
        st.session_state["mostrar_resumen"] = True
        st.session_state["resultados_calculo"] = {
            "income_usa": income_usa,
            "income_mex": income_mex_total,
            "income_cruce": income_cruce_total,
            "salary_usa": salary_usa,
            "salary_mex": salary_mex,
            "salary_cruce": salary_cruce,
            "diesel_usa": diesel_usa,
            "diesel_mex": diesel_mex,
            "charge_fuel_usa": charge_fuel_usa,
            "charges_usa": charges_usa,
            "charges_mex": charges_mex,
            "extras_total": extras_total,
            "cargo_cruce_final": cargo_cruce_final,
            "total_charges": total_charges,
            "total_income": total_income,
            "utilidad_bruta": utilidad_bruta,
            "porcentaje_bruta": porcentaje_bruta,
            "costos_indirectos": costos_indirectos,
            "utilidad_neta": utilidad_neta,
            "porcentaje_neta": porcentaje_neta,
            "pay_km": pay_km,
            "pay_km_empty": pay_km_empty,
            "pay_mex": pay_mex
        }
        
# --- Mostrar resumen si ya se revisó ---
if st.session_state["mostrar_resumen"]:
    r = st.session_state["resultados_calculo"]

    with st.expander("📍 Summary USA"):
        st.write(f"Operator salary USA: ${r['salary_usa']:,.2f}")
        st.write(f"Diesel USA: ${r['diesel_usa']:,.2f}")
        st.write(f"Fuel charge USA: ${r['charge_fuel_usa']:,.2f}")
        st.write(f"Total charges USA: ${r['charges_usa']:,.2f}")
        st.write(f"Total income USA: ${r['income_usa']:,.2f}")

    with st.expander("📍 Summary MEX"):
        st.write(f"Operator salary MEX: ${r['salary_mex']:,.2f}")
        st.write(f"Diesel MEX: ${r['diesel_mex']:,.2f}")
        st.write(f"Mexican charge (if Filial/Externa): ${cargo_mex:,.2f}")
        st.write(f"Total charges MEX: ${r['charges_mex']:,.2f}")
        st.write(f"Total income MEX: ${r['income_mex']:,.2f}")

    with st.expander("📍 General Summary"):
        st.write(f"Crossborder income: ${r['income_cruce']:,.2f}")
        st.write(f"Crossborder charge: ${r['cargo_cruce_final']:,.2f}")
        st.write(f"Crossborder salary: ${r['salary_cruce']:,.2f}")
        st.write(f"Extras total: ${r['extras_total']:,.2f}")
        st.write(f"Total income: ${r['total_income']:,.2f}")
        st.write(f"Total charges: ${r['total_charges']:,.2f}")
        st.write(f"Gross profit: ${r['utilidad_bruta']:,.2f} ({r['porcentaje_bruta']:.2%})")
        st.write(f"Indirect costs (35%): ${r['costos_indirectos']:,.2f}")
        st.write(f"Net profit: ${r['utilidad_neta']:,.2f} ({r['porcentaje_neta']:,.2%})")

    # Generador de ID
    def generar_nuevo_id():
        respuesta = supabase.table("Routes_Lincoln").select("ID_Route").order("ID_Route", desc=True).limit(1).execute()
        if respuesta.data:
            ultimo = respuesta.data[0]["ID_Route"]
            numero = int(ultimo[2:]) + 1
        else:
            numero = 1
        return f"LF{numero:06d}"

    if st.button("✅ Save route"):
        nuevo_id = generar_nuevo_id()
        data_row = {
            "ID_Route": nuevo_id,
            "Date": str(fecha),
            "Type_of_trip": tipo_viaje,
            "Customer": cliente,
            "Trip_mode": modo_viaje,
            "Origin_USA": origen_usa,
            "Destination_USA": destino_usa,
            "Miles_USA": millas_usa,
            "Miles_Empty": millas_vacias,
            "Income_per_mile": ingreso_milla,
            "Currency_USA": moneda_usa,
            "Mexican_Line": mexican_line,
            "Origin_MEX": origen_mex,
            "Destination_MEX": destino_mex,
            "Miles_MEX": millas_mex,
            "Income_MEX": ingreso_mex,
            "Charge_MEX": cargo_mex,
            "Currency_MEX": moneda_mex,
            "Type_of_crossborder": tipo_cruce,
            "Load_type_crossborder": tipo_carga_cruce,
            "Crossborder_income": ingreso_cruce,
            "Currency_Crossborder": moneda_ingreso_cruce,
            "Crossborder_charge": cargo_cruce,
            "Currency_Crossborder_charge": moneda_cargo_cruce,
            "Diesel": diesel_rate,
            "Truck_performance": rendimiento,
            "Dollar_exchange_rate": tc,
            "Pay_KM_USA": r["pay_km"],
            "Pay_KM_empty_USA": r["pay_km_empty"],
            "Pay_MEX": r["pay_mex"],
            "Income_Total": r["total_income"],
            "Charges_total": r["total_charges"],
            "Gross_profit": r["utilidad_bruta"],
            "Net_profit": r["utilidad_neta"],
            "Gross_margin": r["porcentaje_bruta"],
            "Net_margin": r["porcentaje_neta"],
            "Income_Fuel_USA": income_fuel_usa,
            "Charge_Fuel_USA": charge_fuel_usa,
            "Diesel_USA": diesel_usa,
            "Salary_USA": salary_usa,
            "Diesel_MEX": diesel_mex,
            "Salary_Cruce": salary_cruce,
            "Fianzas": fianzas,
            "Aditional_Insurance": aditional_insurance,
            "Demoras": demoras,
            "Movimiento_Extra": movimiento_extra,
            "Lumper_Fees": lumper_fees,
            "Maniobras": maniobras,
            "Loadlocks": loadlocks,
            "Layover": layover,
            "Gatas": gatas,
            "Accessories": accessories,
            "Guias": guias,
            "Extras_Total": extras_total,
            "Income_USA": income_usa,
            "Income_MEX_Total": income_mex_total,
            "Income_Cruce_Total": income_cruce_total,
            "Charges_USA": charges_usa,
            "Crossborder_Charge_Total": cargo_cruce_final,
            "Indirect_Costs": r['costos_indirectos'],
            "Charge_MEX_Total": charge_mex,
            "Salary_MEX": salary_mex,
            
        }
        try:
            # Validación de campos vacíos o no válidos
            for key, val in data_row.items():
                if val is None:
                    st.warning(f"⚠️ El campo '{key}' tiene valor None. Revisa este dato.")
                elif isinstance(val, float) and pd.isna(val):
                    st.warning(f"⚠️ El campo '{key}' tiene valor NaN. Revisa este dato.")
    
            # Intento de inserción
            respuesta = supabase.table("Rutas_Lincoln").insert(data_row).execute()
    
            # Validación del resultado
            if hasattr(respuesta, "status_code") and respuesta.status_code >= 400:
                st.error(f"❌ Error en la respuesta de Supabase: {respuesta.status_code} - {respuesta.data}")
            else:
                st.success(f"✅ Route saved with ID: {nuevo_id}")
                st.session_state["mostrar_resumen"] = False

        except Exception as e:
            st.error("❌ Ocurrió un error al intentar guardar la ruta.")
            st.exception(e)
            st.text(traceback.format_exc())  # Esto imprime la traza completa del error

