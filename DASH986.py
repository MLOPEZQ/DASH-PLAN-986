import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard PLAN 986 (Sitios Complementarios)", layout="wide")
st.image("9 años.jpg", width=None)
st.markdown("""
    <div style='text-align: center;'>
        <h1 style='margin-top: 0;'>📍 Dashboard PLAN 986 (Sitios Complementarios)</h1>
        <div style='font-size: 14px; color: gray; margin-top: 5px;'>
            <em>By MLOPEZQ</em>
        </div>
    </div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Carga tu archivo Excel PLAN986.xlsx", type=["xlsx"])
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file, engine='openpyxl', dtype={'Estatus': str})
    df.columns = df.columns.str.strip()
    df.dropna(subset=['Estatus'], inplace=True)
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

if df_filtrado.empty:
    st.warning("⚠️ No se encontraron datos para los filtros seleccionados. Por favor, ajuste su selección.")
    st.stop()

#MÉTRICAS
st.subheader("📊 SEGUIMIENTO")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total de Sitios", len(df_filtrado))

def mostrar_valor(col):
    if sitio_sel != "Todos":
        valor = df_filtrado[col].iloc[0] if not df_filtrado[col].empty else "-"
    else:
        valor = df_filtrado[col].notna().sum()
    return valor

col3.metric("Forecast", mostrar_valor('Forecast Firma'))
col5.metric("Stopper", mostrar_valor('Stopper'))


# TARJETAS
st.divider()
st.subheader("📈 Resumen ESTATUS")

if 'Estatus' in df_filtrado.columns:
    status_counts = df_filtrado.groupby('Estatus').agg({"Sitio": "count"}).rename(columns={"Sitio": "Cantidad"}).reset_index()
    
    status_counts = status_counts[status_counts['Estatus'].str.match(r'^\d+\.')].copy()
    
    status_counts['Orden'] = status_counts['Estatus'].str.extract(r'(\d+)').astype(int)
    status_counts = status_counts.sort_values('Orden', ascending=True).reset_index(drop=True)
    status_counts['Estatus Limpio'] = status_counts['Estatus'].str.replace(r'^\d+\.\-\s*', '', regex=True)

    status_icons = {
        "Eliminado": "🗑️", "Procuración": "🔍", "Carpeta Completa - Pend ING": "📁",
        "En borrador": "📝", "En búsqueda": "🕵️‍♂️", "Firmado": "✍️",
        "Standby": "⏸️", "En programación TSS": "📅", "Pendiente TSS": "⏳",
        "TSS Realizada": "✅"
    }

    num_cols = 5
    cols = st.columns(num_cols)
    for i, row in status_counts.iterrows():
        with cols[i % num_cols]:
            with st.container(border=True):
                icon = status_icons.get(row['Estatus Limpio'], '📊')
                st.metric(label=f"{icon} {row['Estatus Limpio']}", value=row['Cantidad'])
    
    # --- INICIO DE LA NUEVA VISUALIZACIÓN ---
    st.divider()

    # Calcular la métrica
    cantidad_eliminado = 0
    if 'Eliminado' in status_counts['Estatus Limpio'].values:
        cantidad_eliminado = status_counts.loc[status_counts['Estatus Limpio'] == 'Eliminado', 'Cantidad'].iloc[0]
        
    cantidad_standby = 0
    if 'Standby' in status_counts['Estatus Limpio'].values:
        cantidad_standby = status_counts.loc[status_counts['Estatus Limpio'] == 'Standby', 'Cantidad'].iloc[0]

    total_gestion_activa = len(df_filtrado) - (cantidad_eliminado + cantidad_standby)

    # Mostrar la métrica centrada y en grande
    col_izq, col_centro, col_der = st.columns([1, 2, 1])
    with col_centro:
        with st.container(border=True):
            st.metric(
                label="⚙️ Sitios en Gestión Activa", 
                value=total_gestion_activa,
                help=f"Total Sitios ({len(df_filtrado)}) - Eliminados ({cantidad_eliminado}) - Standby ({cantidad_standby})"
            )
    # --- FIN DE LA NUEVA VISUALIZACIÓN ---

    st.divider()
    st.subheader("📊 Detalle Gráfico")
    
    sitios_por_status = df_filtrado.groupby('Estatus')['Sitio'].apply(lambda x: '<br>'.join(x)).reset_index(name='Sitios')
    status_counts = pd.merge(status_counts, sitios_por_status, on='Estatus')

    fig_bar = px.bar(
        status_counts,
        x='Cantidad',
        y='Estatus Limpio',
        orientation='h',
        text='Cantidad',
        custom_data=['Sitios'],
        color='Cantidad',
        color_continuous_scale=px.colors.sequential.Purples_r
    )
    
    fig_bar.update_layout(
        yaxis={'categoryorder':'array', 'categoryarray': status_counts['Estatus Limpio'].tolist()[::-1]},
        yaxis_title=None,
        xaxis_title="Cantidad de Sitios",
        showlegend=False,
        coloraxis_showscale=False,
        height=400 + len(status_counts) * 20
    )
    
    fig_bar.update_traces(
        textposition='inside',
        hovertemplate='<b>%{y}</b><br>Cantidad: %{x}<br><br><b>Sitios:</b><br>%{customdata[0]}<extra></extra>'
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
