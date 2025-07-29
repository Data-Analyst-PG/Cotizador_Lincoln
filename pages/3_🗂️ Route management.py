import streamlit as st
import pandas as pd
from supabase import create_client

# --- CONEXIÓN SUPABASE ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("🗂️ Route management - Lincoln")

# --- CARGAR DATOS GENERALES ---
@st.cache_data
def cargar_datos_generales():
    try:
        return pd.read_csv("datos_generales.csv").iloc[0].to_dict()
    except:
        return {}

datos_generales = cargar_datos_generales()

# --- CARGAR RUTAS ---
data = supabase.table("Rutas_Lincoln").select("*").execute()
df = pd.DataFrame(data.data)

if df.empty:
    st.warning("⚠️ There are no registered routes yet.")
    st.stop()

# --- VISUALIZAR TABLA ---
st.subheader("📋 Registered Routes")
st.dataframe(df, use_container_width=True)
st.markdown(f"**Total registered routes:** {len(df)}")

# --- ELIMINAR RUTAS ---
st.markdown("---")
st.subheader("🗑️ Delete routes")
id_eliminar = st.multiselect("Select the route ID to delete", df["ID_Ruta"].tolist())
if st.button("Eliminar rutas seleccionadas") and id_eliminar:
    for idr in id_eliminar:
        supabase.table("Rutas_Lincoln").delete().eq("ID_Ruta", idr).execute()
    st.success("✅ Routes successfully deleted.")
    st.experimental_rerun()

# --- EDITAR RUTA ---
st.markdown("---")
st.subheader("✏️ Edit Existing Route")
id_editar = st.selectbox("Select the route ID to edit", df["ID_Ruta"].tolist())

if id_editar:
    ruta = df[df["ID_Ruta"] == id_editar].iloc[0].to_dict()
    with st.form("form_editar"):
        col1, col2 = st.columns(2)
        with col1:
            ruta["Date"] = st.date_input("Date", pd.to_datetime(ruta["Date"], errors='coerce'))
            ruta["Type_of_trip"] = st.selectbox("Type of trip", ["NB", "PPNB", "SB", "PPSB", "DOMUSA", "DOMMEX"], index=0 if ruta["Type_of_trip"] not in ["NB", "PPNB", "SB", "PPSB", "DOMUSA", "DOMMEX"] else ["NB", "PPNB", "SB", "PPSB", "DOMUSA", "DOMMEX"].index(ruta["Type_of_trip"]))
            ruta["Customer"] = st.text_input("Customer", value=ruta["Customer"])
            ruta["Trip_mode"] = st.selectbox("Trip mode", ["Operator", "Team"], index=0 if ruta["Trip_mode"] == "Operator" else 1)
            ruta["Origin_USA"] = st.text_input("Origin USA", value=ruta["Origin_USA"])
            ruta["Destination_USA"] = st.text_input("Destination USA", value=ruta["Destination_USA"])
            ruta["Miles_USA"] = st.number_input("Miles USA", min_value=0.0, value=float(ruta["Miles_USA"]))
            ruta["Miles_Empty"] = st.number_input("Miles Empty", min_value=0.0, value=float(ruta["Miles_Empty"]))
            ruta["Income_per_mile"] = st.number_input("Income per mile", min_value=0.0, value=float(ruta["Income_per_mile"]))
            ruta["Currency_USA"] = st.selectbox("Currency USA", ["USD", "MXP"], index=0 if ruta["Currency_USA"] == "USD" else 1)
            ruta["Mexican_Line"] = st.selectbox("Mexican Line", ["Propia", "Filial/Externa"], index=0 if ruta["Mexican_Line"] == "Propia" else 1)

        with col2:
            ruta["Origin_MEX"] = st.text_input("Origin MEX", value=ruta["Origin_MEX"])
            ruta["Destination_MEX"] = st.text_input("Destination MEX", value=ruta["Destination_MEX"])
            ruta["Miles_MEX"] = st.number_input("Miles MEX", min_value=0.0, value=float(ruta["Miles_MEX"]))
            ruta["Income_MEX"] = st.number_input("Income MEX", min_value=0.0, value=float(ruta["Income_MEX"]))
            ruta["Charge_MEX"] = st.number_input("Charge MEX", min_value=0.0, value=float(ruta["Charge_MEX"]))
            ruta["Currency_MEX"] = st.selectbox("Currency MEX", ["USD", "MXP"], index=0 if ruta["Currency_MEX"] == "USD" else 1)
            ruta["Type_of_crossborder"] = st.selectbox("Type of crossborder", ["Propio", "Filial/Externo"], index=0 if ruta["Type_of_crossborder"] == "Propio" else 1)
            ruta["Load_type_crossborder"] = st.selectbox("Load type crossborder", ["Loaded", "Empty"], index=0 if ruta["Load_type_crossborder"] == "Loaded" else 1)
            ruta["Crossborder_income"] = st.number_input("Crossborder income", min_value=0.0, value=float(ruta["Crossborder_income"]))
            ruta["Currency_Crossborder"] = st.selectbox("Currency Crossborder", ["USD", "MXP"], index=0 if ruta["Currency_Crossborder"] == "USD" else 1)
            ruta["Crossborder_charge"] = st.number_input("Crossborder charge", min_value=0.0, value=float(ruta["Crossborder_charge"]))
            ruta["Currency_Crossborder_charge"] = st.selectbox("Currency Crossborder charge", ["USD", "MXP"], index=0 if ruta["Currency_Crossborder_charge"] == "USD" else 1)

        # Extras
        st.subheader("💵 Chargue Extras (USA)")
        extras = {}
        campos_extras = [
            "Fianzas", "Aditional Insurance", "Demoras/Detention", "Movimiento extraordinario",
            "Lumper fees", "Maniobras", "Loadlocks", "Lay over", "Gatas", "Accessories", "Guias"
        ]
        cols_extras = st.columns(3)
        for idx, campo in enumerate(campos_extras):
            with cols_extras[idx % 3]:
                extras[campo] = st.number_input(campo, min_value=0.0, value=float(ruta.get(campo, 0.0)), key=f"{campo}_edit")

        # --- GUARDAR ---
        submit = st.form_submit_button("💾 Save changes")
        if submit:
            tc = datos_generales["Dollar exchange rate"]
            fuel_rate = datos_generales["Fuel"]
            diesel_rate = datos_generales["Diesel"]
            rendimiento = datos_generales["Truck performance"]

            miles_usa = ruta["Miles_USA"]
            miles_empty = ruta["Miles_Empty"]
            if ruta["Trip_mode"] == "Operator":
                salary_usa = miles_usa * datos_generales["Operator pay per mile"] + \
                             miles_empty * datos_generales["Operator pay per empty mile"] + \
                             datos_generales["Operator bonus"]
                salary_mex = datos_generales["Operator pay mex"] + datos_generales["Operator bonus mex"]
            else:
                salary_usa = (miles_usa * datos_generales["Team pay per mile"] + \
                             miles_empty * datos_generales["Team pay per empty mile"]) * 2 + \
                             datos_generales["Team bonus"] * 2
                salary_mex = datos_generales["Team pay mex"] * 2 + datos_generales["Operator bonus mex"] * 2
            if ruta["Mexican_Line"] != "Propia":
                salary_mex = 0
            salary_cruce = datos_generales["Loaded crossborder payment"] if ruta["Load_type_crossborder"] == "Loaded" else datos_generales["Empty crossborder payment"]
            if ruta["Type_of_crossborder"] != "Propio":
                salary_cruce = 0

            income_fuel_usa = fuel_rate * miles_usa
            income_usa = ruta["Income_per_mile"] * miles_usa
            if ruta["Currency_USA"] == "MXP":
                income_usa *= tc
            income_usa += income_fuel_usa

            income_mex = ruta["Income_MEX"] if ruta["Currency_MEX"] == "USD" else ruta["Income_MEX"] / tc
            income_cruce = ruta["Crossborder_income"] if ruta["Currency_Crossborder"] == "USD" else ruta["Crossborder_income"] / tc
            diesel_usa = (miles_usa / rendimiento) * diesel_rate
            diesel_mex = (ruta["Miles_MEX"] / rendimiento) * diesel_rate if ruta["Mexican_Line"] == "Propia" else 0
            charge_fuel_usa = fuel_rate * miles_usa
            extras_total = sum(extras.values())
            charges_usa = salary_usa + diesel_usa + charge_fuel_usa
            charges_mex = salary_mex + diesel_mex if ruta["Mexican_Line"] == "Propia" else ruta["Charge_MEX"]
            charge_cruce = ruta["Crossborder_charge"] if ruta["Currency_Crossborder_charge"] == "USD" else ruta["Crossborder_charge"] / tc

            total_charges = charges_usa + charges_mex + extras_total + charge_cruce
            total_income = income_usa + income_mex + income_cruce
            utilidad_bruta = total_income - total_charges
            margen_bruto = utilidad_bruta / total_income if total_income > 0 else 0
            costos_indirectos = total_income * 0.35
            utilidad_neta = utilidad_bruta - costos_indirectos
            margen_neto = utilidad_neta / total_income if total_income > 0 else 0

            # Actualizar en Supabase
            ruta.update(extras)
            ruta.update({
                "Income_total": total_income,
                "Charges_total": total_charges,
                "Gross_profit": utilidad_bruta,
                "Net_profit": utilidad_neta,
                "Gross_margin": margen_bruto,
                "Net_margin": margen_neto
            })
            supabase.table("Rutas_Lincoln").update(ruta).eq("ID_Ruta", id_editar).execute()
            st.success("✅ Route updated successfully.")
            st.experimental_rerun()
