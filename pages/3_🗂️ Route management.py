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
data = supabase.table("Routes_Lincoln").select("*").execute()
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
id_eliminar = st.multiselect("Select the route ID to delete", df["ID_Route"].tolist())
if st.button("Eliminar rutas seleccionadas") and id_eliminar:
    for idr in id_eliminar:
        supabase.table("Routes_Lincoln").delete().eq("ID_Route", idr).execute()
    st.success("✅ Routes successfully deleted.")
    st.experimental_rerun()

# --- EDITAR RUTA ---
st.markdown("---")
st.subheader("✏️ Edit Existing Route")
id_editar = st.selectbox("Select the route ID to edit", df["ID_Route"].tolist())

if id_editar:
    ruta = df[df["ID_Route"] == id_editar].iloc[0].to_dict()
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
        # --- SETTINGS / DATOS GENERALES ---
        tc = float(datos_generales["Dollar exchange rate"])
        fuel_rate = float(datos_generales["Fuel"])
        diesel_rate = float(datos_generales["Diesel"])
        rendimiento = float(datos_generales["Truck performance"])

        # --- ENTRADAS BASE ---
        miles_usa = float(ruta["Miles_USA"])
        miles_empty = float(ruta["Miles_Empty"])
        miles_mex = float(ruta["Miles_MEX"])

        # --- SALARIOS (USA / MEX / CRUCE) ---
        if ruta["Trip_mode"] == "Operator":
            salary_usa = (
                miles_usa * float(datos_generales["Operator pay per mile"])
                + miles_empty * float(datos_generales["Operator pay per empty mile"])
                + float(datos_generales["Operator bonus"])
            )
            salary_mex = (
                float(datos_generales["Operator pay mex"])
                + float(datos_generales["Operator bonus mex"])
            )
        else:  # Team
            salary_usa = (
                miles_usa * float(datos_generales["Team pay per mile"])
                + miles_empty * float(datos_generales["Team pay per empty mile"])
            ) * 2 + float(datos_generales["Team bonus"]) * 2
            salary_mex = float(datos_generales["Team pay mex"]) * 2 + float(datos_generales["Operator bonus mex"]) * 2

        # Si la línea MEX no es propia, el salario MEX no aplica
        if ruta["Mexican_Line"] != "Propia":
        salary_mex = 0.0

        # Pago de cruce (solo si cruce propio)
        salary_cruce = float(datos_generales["Loaded crossborder payment"]) if ruta["Load_type_crossborder"] == "Loaded" else float(datos_generales["Empty crossborder payment"])
        if ruta["Type_of_crossborder"] != "Propio":
            salary_cruce = 0.0

        # --- INGRESOS ---
        # Ingreso x milla USA en USD (si viene en MXP, dividir por tc)
        income_base_usa = float(ruta["Income_per_mile"]) * miles_usa
        if ruta["Currency_USA"] == "MXP":
            income_base_usa = income_base_usa / tc

        # Fuel surcharge (ingreso). Normalmente en USD por settings.
        income_fuel_usa = fuel_rate * miles_usa

        income_usa = income_base_usa + income_fuel_usa

        # Income MEX (a USD)
        income_mex = float(ruta["Income_MEX"])
        if ruta["Currency_MEX"] == "MXP":
            income_mex = income_mex / tc

        # Income cruce (a USD)
        income_cruce = float(ruta["Crossborder_income"])
        if ruta["Currency_Crossborder"] == "MXP":
            income_cruce = income_cruce / tc

        # --- CARGOS / COSTOS ---
        # Diesel (gasto real) en USD
        diesel_usa = (miles_usa / rendimiento) * diesel_rate
        diesel_mex = (miles_mex / rendimiento) * diesel_rate if ruta["Mexican_Line"] == "Propia" else 0.0

        # Fuel como cargo (solo si en tu Captura también existe como gasto espejo).
        # Si NO lo usas como gasto en Captura, pon 0.0 aquí para evitar desalinear.
        charge_fuel_usa = 0.0  # <- AJUSTA A 0.0 o = fuel_rate * miles_usa, según tu Captura

        # Cargo MEX (cuando línea no es propia), convertir a USD si viene en MXP.
        cargo_mex = float(ruta["Charge_MEX"])
        # Si de momento no tienes selector específico de moneda para cargo MEX,
        # puedes reutilizar temporalmente Currency_MEX (mejor: agrega Currency_MEX_charge).
        if ruta["Mexican_Line"] != "Propia":
            if ruta["Currency_MEX"] == "MXP":
                cargo_mex = cargo_mex / tc
            charges_mex = cargo_mex
        else:
            charges_mex = salary_mex + diesel_mex

        # Cargo de cruce (a USD)
        charge_cruce = float(ruta["Crossborder_charge"])
        if ruta["Currency_Crossborder_charge"] == "MXP":
            charge_cruce = charge_cruce / tc

        # Extras
        extras_total = float(sum(extras.values()))

        # Charges USA
        charges_usa = salary_usa + diesel_usa + charge_fuel_usa + salary_cruce

        # Totales
        total_charges = charges_usa + charges_mex + extras_total + charge_cruce
        total_income = income_usa + income_mex + income_cruce
        utilidad_bruta = total_income - total_charges
        margen_bruto = (utilidad_bruta / total_income) if total_income > 0 else 0.0
        costos_indirectos = total_income * 0.35
        utilidad_neta = utilidad_bruta - costos_indirectos
        margen_neto = (utilidad_neta / total_income) if total_income > 0 else 0.0

        # --- PREPARAR PAYLOAD PARA DB ---
        # Serializa la fecha a ISO (YYYY-MM-DD) para evitar problemas de tipos
        fecha_iso = None
        try:
            fecha_iso = pd.to_datetime(ruta["Date"]).date().isoformat()
        except Exception:
            fecha_iso = str(ruta["Date"])

        ruta.update(extras)
        ruta.update({
            "Date": fecha_iso,

            # Totales (usa exactamente los mismos nombres/case que tu tabla)
            "Income_Total": total_income,
            "Charges_Total": total_charges,
            "Gross_profit": utilidad_bruta,
            "Net_profit": utilidad_neta,
            "Gross_margin": margen_bruto,
            "Net_margin": margen_neto,

            # (Opcional) Desgloses útiles para auditoría/coherencia con Captura:
            "Income_USA": income_usa,
            "Income_MEX_Total": income_mex,
            "Income_Cruce_Total": income_cruce,
            "Income_Fuel_USA": income_fuel_usa,

            "Charges_USA": charges_usa,
            "Diesel_USA": diesel_usa,
            "Diesel_MEX": diesel_mex,
            "Charge_Fuel_USA": charge_fuel_usa,
            "Salary_USA": salary_usa,
            "Salary_MEX": salary_mex,
            "Salary_Cruce": salary_cruce,

            "Charge_MEX_Total": charges_mex if ruta["Mexican_Line"] == "Propia" else cargo_mex,
            "Crossborder_Charge_Total": charge_cruce,
            "Extras_Total": extras_total,
            "Indirect_Costs": costos_indirectos,
        })

        # --- UPDATE DB ---
        supabase.table("Routes_Lincoln").update(ruta).eq("ID_Route", id_editar).execute()
        st.success("✅ Route updated successfully.")
        st.experimental_rerun()

