import streamlit as st
import pandas as pd
import plotly.express as px

# === CONFIGURACIÓN GENERAL ===
st.set_page_config(page_title="Dashboard PLAN 986", layout="wide")

st.image("9 años.jpg", width=None)

# === LOGO Y TÍTULO ===
st.markdown("""
    <div style='text-align: center;'>
        <h1 style='margin-top: 0;'>📍 Dashboard PLAN 986</h1>
        <p><strong>By: MLOPEZQ</strong></p>
    </div>
""", unsafe_allow_html=True)

# === CARGA DE DATOS ===
uploaded_file = st.file_uploader("Carga tu archivo Excel PLAN986.xlsx", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, engine='openpyxl')
    df.columns = df.columns.str.strip()
    df['Complementario'] = df['Complementario'].astype(str).str.strip().str.lower()
    df['Proyecto'] = df['Proyecto'].astype(str).str.strip().str.lower()
    if 'Fecha Entrega a Construcción' in df.columns:
        df['Fecha Entrega a Construcción'] = pd.to_datetime(df['Fecha Entrega a Construcción'], errors='coerce')
else:
    st.warning("Por favor, sube el archivo Excel para continuar.")
    st.stop()

# === FILTRAR SOLO PROYECTO 986 Y COMPLEMENTARIO SI ===
df = df[(df['Proyecto'] == 'plan 986') & (df['Complementario'] == 'si')]

# === CREAR COLUMNA IDENTIFICADORA DE SITIOS ===
df['Sitio'] = df['AB+ALt'].astype(str) + " - " + df['Nombre Sitio'].astype(str)

# === FILTROS INTERACTIVOS ===
st.sidebar.header("Filtros")

# FILTRO PRINCIPAL: GESTOR
gestores = df['Gestor'].dropna().unique().tolist()
gestor_sel = st.sidebar.selectbox("Seleccionar Gestor", ["Todos"] + sorted(gestores))

# Aplicar filtro por Gestor antes de obtener sitios
df_filtrado = df.copy()
if gestor_sel != "Todos":
    df_filtrado = df[df['Gestor'] == gestor_sel]

# FILTRO SECUNDARIO: SITIO
sitios_filtrados = df_filtrado['Sitio'].dropna().unique().tolist()
sitio_sel = st.sidebar.selectbox("Seleccionar Sitio", ["Todos"] + sorted(sitios_filtrados))

if sitio_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Sitio'] == sitio_sel]

# === MÉTRICAS CLAVE ===
st.subheader("📊 IMPORTANTE")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total de Sitios", len(df) if gestor_sel == "Todos" else df[df['Gestor'] == gestor_sel].shape[0])

# Mostrar valor único si se filtra un sitio, si no mostrar cantidad con valor válido
def mostrar_valor(col):
    if sitio_sel != "Todos":
        valor = df_filtrado[col].iloc[0] if not df_filtrado[col].empty else "-"
    else:
        valor = df_filtrado[col].notna().sum()
    return valor

col3.metric("Forecast", mostrar_valor('Forecast Firma'))
col5.metric("Stopper", mostrar_valor('Stopper'))

# === GRÁFICO ESTATUS DONUT ===
st.subheader("📈 Distribución por Status")
if 'Estatus' in df_filtrado.columns:
    status_counts = df_filtrado.groupby('Estatus').agg({"Sitio": lambda x: list(x), "Estatus": "count"}).rename(columns={"Estatus": "Cantidad"}).reset_index()
    status_counts['Estatus Limpio'] = status_counts['Estatus'].str.replace(r'^\d+\.\-\s*', '', regex=True)
    status_counts['Sitios'] = status_counts['Sitio'].apply(lambda x: '<br>'.join(x))
    fig_donut = px.pie(
        status_counts,
        names='Estatus Limpio',
        values='Cantidad',
        hole=0.6,
        custom_data=['Sitios'],
        color_discrete_sequence=px.colors.sequential.Purples_r
    )
    fig_donut.update_traces(
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>%{customdata[0]}<extra></extra>',
        marker=dict(line=dict(color='#FFFFFF', width=2))
    )
    fig_donut.update_layout(showlegend=True, height=500)
    st.plotly_chart(fig_donut, use_container_width=True)
else:
    st.info("No hay datos de estatus para graficar.")

# === INFORMACIÓN BÁSICA Y OTROS DATOS UNIFICADOS ===
st.subheader("🗂️ Información del Sitio")
columnas_info = ['AB+ALt', 'Nombre Sitio', 'Comuna', 'Región', 'Proyecto', 'Complementario', 'Lat', 'Long', 'Tipo de Sitio', 'Renta']
columnas_existentes = [col for col in columnas_info if col in df_filtrado.columns]
st.dataframe(df_filtrado[columnas_existentes], use_container_width=True)

# === OBSERVACIONES ===
st.subheader("📝 Comentarios")
with st.expander("Ver comentarios por sitio"):
    for _, row in df_filtrado[['Nombre Sitio', 'Observaciones']].dropna().iterrows():
        st.markdown(f"**{row['Nombre Sitio']}**: {row['Observaciones']}")

# === MAPA INTERACTIVO ===
st.subheader("🌐 Georeferencia")
mapa_df = df_filtrado.dropna(subset=['Lat', 'Long'])

if not mapa_df.empty:
    fig_mapa = px.scatter_mapbox(
        mapa_df,
        lat="Lat",
        lon="Long",
        zoom=4,
        hover_name="Nombre Sitio",
        hover_data={"Comuna": True, "Gestor": True},
        color_discrete_sequence=["mediumpurple"]
    )
    fig_mapa.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_mapa, use_container_width=True, config={"scrollZoom": True})
else:
    st.info("No hay coordenadas disponibles para mostrar en el mapa.")
