import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard PLAN 986", layout="wide")
st.image("9 años.jpg", width=None)
st.markdown("""
    <div style='text-align: center;'>
        <h1 style='margin-top: 0;'>📍 Dashboard PLAN 986</h1>
        <div style='font-size: 14px; color: gray; margin-top: 5px;'>
            <em>By MLOPEZQ</em>
        </div>
    </div>
""", unsafe_allow_html=True)

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

df = df[(df['Proyecto'] == 'plan 986') & (df['Complementario'] == 'si')]
df['Sitio'] = df['AB+ALt'].astype(str) + " - " + df['Nombre Sitio'].astype(str)

st.sidebar.header("Filtros")

gestores = df['Gestor'].dropna().unique().tolist()
gestor_sel = st.sidebar.selectbox("Seleccionar Gestor", ["Todos"] + sorted(gestores))
df_filtrado = df.copy()
if gestor_sel != "Todos":
    df_filtrado = df[df['Gestor'] == gestor_sel]

sitios_filtrados = df_filtrado['Sitio'].dropna().unique().tolist()
sitio_sel = st.sidebar.selectbox("Seleccionar Sitio", ["Todos"] + sorted(sitios_filtrados))

if sitio_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Sitio'] == sitio_sel]

#MÉTRICAS
st.subheader("📊 IMPORTANTE")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total de Sitios", len(df) if gestor_sel == "Todos" else df[df['Gestor'] == gestor_sel].shape[0])

def mostrar_valor(col):
    if sitio_sel != "Todos":
        valor = df_filtrado[col].iloc[0] if not df_filtrado[col].empty else "-"
    else:
        valor = df_filtrado[col].notna().sum()
    return valor

col3.metric("Forecast", mostrar_valor('Forecast Firma'))
col5.metric("Stopper", mostrar_valor('Stopper'))

# --- MODIFICACIÓN DE LA VISUALIZACIÓN DE GRÁFICA ---
st.divider()
st.subheader("📈 Resumen Ejecutivo por Status")

if 'Estatus' in df_filtrado.columns and not df_filtrado.empty:
    # Preparar datos
    status_counts = df_filtrado.groupby('Estatus').agg({"Sitio": lambda x: list(x), "Estatus": "count"}).rename(columns={"Estatus": "Cantidad"}).reset_index()
    status_counts['Estatus Limpio'] = status_counts['Estatus'].str.replace(r'^\d+\.\-\s*', '', regex=True)
    status_counts['Sitios'] = status_counts['Sitio'].apply(lambda x: '<br>'.join(x))
    status_counts = status_counts.sort_values('Cantidad', ascending=False)

    # Tarjetas
    num_cols = 4 # Puedes ajustar el número de columnas
    cols = st.columns(num_cols)
    for index, row in status_counts.iterrows():
        with cols[index % num_cols]:
            st.metric(label=row['Estatus Limpio'], value=row['Cantidad'])

    st.divider()
    st.subheader("📊 Detalle Gráfico por Status")

    #Visualización horizontal
    status_counts_sorted_for_chart = status_counts.sort_values('Cantidad', ascending=True)

    fig_bar = px.bar(
        status_counts_sorted_for_chart,
        x='Cantidad',
        y='Estatus Limpio',
        orientation='h',
        text='Cantidad',
        custom_data=['Sitios'],
        title='Distribución de Sitios por Status'
    )
    fig_bar.update_traces(
        textposition='inside',
        marker_color='#6A0DAD', # Un color púrpura profesional
        hovertemplate='<b>%{y}</b><br>Cantidad: %{x}<br><br><b>Sitios:</b><br>%{customdata[0]}<extra></extra>'
    )
    fig_bar.update_layout(
        yaxis_title=None,
        xaxis_title="Cantidad de Sitios",
        showlegend=False,
        height=400 + len(status_counts) * 20 # Altura dinámica según la cantidad de status
    )
    st.plotly_chart(fig_bar, use_container_width=True)

else:
    st.info("No hay datos de estatus para mostrar.")

#INFO
st.subheader("🗂️ Información del Sitio")
columnas_info = ['AB+ALt', 'Nombre Sitio', 'Comuna', 'Región', 'Proyecto', 'Complementario', 'Lat', 'Long', 'Tipo de Sitio', 'Renta']
columnas_existentes = [col for col in columnas_info if col in df_filtrado.columns]
st.dataframe(df_filtrado[columnas_existentes], use_container_width=True)

#OBS
st.subheader("📝 Comentarios")
with st.expander("Ver comentarios por sitio"):
    if not df_filtrado[['Nombre Sitio', 'Observaciones']].dropna().empty:
        for _, row in df_filtrado[['Nombre Sitio', 'Observaciones']].dropna().iterrows():
            st.markdown(f"**{row['Nombre Sitio']}**: {row['Observaciones']}")
    else:
        st.info("No hay comentarios para los filtros seleccionados.")

#MAPS
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
```
