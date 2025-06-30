import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard PLAN 986 (Sitios Complementarios)", layout="wide")
st.image("10 Años.jpg", width=None)
st.markdown("""
    <div style='text-align: center;'>
        <h1 style='margin-top: 0;'>📍 Dashboard PLAN 986 (Sitios Complementarios)</h1>
        <div style='font-size: 14px; color: gray; margin-top: 5px;'>
            <em>By MLOPEZQ</em>
        </div>
    </div>
""", unsafe_allow_html=True)

@st.cache_data
def load_data(uploaded_file):
    df = pd.read_excel(uploaded_file, engine='openpyxl', dtype={'Estatus': str})
    df.columns = df.columns.str.strip()
    df.dropna(subset=['Estatus'], inplace=True)
    df['Complementario'] = df['Complementario'].astype(str).str.strip().str.lower()
    df['Proyecto'] = df['Proyecto'].astype(str).str.strip().str.lower()
    if 'Fecha Entrega a Construcción' in df.columns:
        df['Fecha Entrega a Construcción'] = pd.to_datetime(df['Fecha Entrega a Construcción'], errors='coerce')
    df = df[df['Estatus'].str.match(r'^\d+\.')].copy()
    df['Estatus Limpio'] = df['Estatus'].str.replace(r'^\d+\.\-\s*', '', regex=True)
    return df

uploaded_file = st.file_uploader("Carga tu archivo Excel PLAN986.xlsx", type=["xlsx"])
if uploaded_file is not None:
    df_original = load_data(uploaded_file)
else:
    st.warning("Por favor, sube el archivo Excel para continuar.")
    st.stop()

df = df_original[(df_original['Proyecto'] == 'plan 986') & (df_original['Complementario'] == 'si')]
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

if 'selected_status' not in st.session_state:
    st.session_state.selected_status = None

def set_selected_status(status):
    st.session_state.selected_status = status

# SECCIÓN DE MÉTRICAS
st.subheader("📊 SEGUIMIENTO")

total_sitios_filtrados = len(df_filtrado)
cantidad_eliminado = df_filtrado[df_filtrado['Estatus Limpio'] == 'Eliminado'].shape[0]
cantidad_standby = df_filtrado[df_filtrado['Estatus Limpio'] == 'Standby'].shape[0]
total_gestion_activa = total_sitios_filtrados - (cantidad_eliminado + cantidad_standby)

l_spacer, col_total, col_activa, r_spacer = st.columns([1, 2, 2, 1])

with col_total:
    st.metric("Total de Sitios", total_sitios_filtrados)

with col_activa:
    st.metric(
        label="Sitios en Gestión Activa", 
        value=total_gestion_activa,
        help=f"Total Sitios ({total_sitios_filtrados}) - Eliminados ({cantidad_eliminado}) - Standby ({cantidad_standby})"
    )

# TARJETAS
st.divider()
st.subheader("📈 Resumen ESTATUS")

if 'Estatus' in df_filtrado.columns:
    status_counts = df_filtrado.groupby(['Estatus', 'Estatus Limpio']).agg(Cantidad=("Sitio", "count")).reset_index()
    status_counts['Orden'] = status_counts['Estatus'].str.extract(r'(\d+)').astype(int)
    status_counts = status_counts.sort_values('Orden', ascending=True).reset_index(drop=True)

    status_icons = {
        "Eliminado": "🗑️", "Procuración": "🔍", "Carpeta Completa - Pend ING": "📁",
        "En borrador": "📝", "En búsqueda": "🕵️‍♂️", "Firmado": "✍️",
        "Standby": "⏸️", "En programación TSS": "📅", "Pendiente TSS": "⏳",
        "TSS Realizada": "✅", "Carpeta Ingresada": "🗂️"
    }

    num_cols = 5
    cols = st.columns(num_cols)
    for i, row in status_counts.iterrows():
        with cols[i % num_cols]:
            with st.container(border=True):
                icon = status_icons.get(row['Estatus Limpio'], '📊')
                st.metric(label=f"{icon} {row['Estatus Limpio']}", value=row['Cantidad'])
                st.button("Ver Detalle", key=f"btn_{row['Estatus Limpio']}", on_click=set_selected_status, args=(row['Estatus Limpio'],), use_container_width=True)

    if st.session_state.selected_status:
        st.divider()
        col_header, col_button = st.columns([4, 1])
        with col_header:
            st.subheader(f"🔎 INFO SITIOS: {st.session_state.selected_status}")
        with col_button:
            st.button("Ocultar Detalle", on_click=set_selected_status, args=(None,), use_container_width=True)

        detalle_df = df_filtrado[df_filtrado['Estatus Limpio'] == st.session_state.selected_status]
        columnas_info = ['AB+ALt', 'Nombre Sitio', 'Comuna', 'Región', 'Proyecto', 'Complementario', 'Lat', 'Long', 'Stopper']
        columnas_existentes = [col for col in columnas_info if col in detalle_df.columns]
        st.dataframe(detalle_df[columnas_existentes], use_container_width=True)

    # --- INICIO DE LA SECCIÓN DE GRÁFICO MODIFICADA ---
    st.divider()
    st.subheader("📊 Detalle por Stopper (Sitios en Gestión Activa)")

    if 'Stopper' in df_filtrado.columns:
        # 1. Filtrar el DataFrame para incluir solo sitios en gestión activa
        estatus_excluir = ['Eliminado', 'Standby']
        df_gestion_activa = df_filtrado[~df_filtrado['Estatus Limpio'].isin(estatus_excluir)]
        
        # Continuar solo si hay sitios en gestión activa
        if not df_gestion_activa.empty:
            stopper_df = df_gestion_activa.copy()
            stopper_df['Stopper'] = stopper_df['Stopper'].fillna("Sin Stopper")
            
            stopper_counts = stopper_df.groupby('Stopper').agg(
                Cantidad=('Sitio', 'count'),
                Sitios=('Sitio', lambda x: '<br>'.join(x))
            ).reset_index()

            # Crear el gráfico de barras con la nueva gama de colores
            fig_stopper_bar = px.bar(
                stopper_counts, 
                x='Cantidad', 
                y='Stopper', 
                orientation='h', 
                text='Cantidad',
                custom_data=['Sitios'], 
                color='Cantidad', 
                color_continuous_scale=px.colors.sequential.Purples_r # 2. Cambiado a gama de morados
            )
            fig_stopper_bar.update_layout(
                yaxis={'categoryorder':'total ascending'},
                yaxis_title=None, 
                xaxis_title="Cantidad de Sitios", 
                showlegend=False,
                coloraxis_showscale=False, 
                height=300 + len(stopper_counts) * 30
            )
            fig_stopper_bar.update_traces(
                textposition='inside', 
                hovertemplate='<b>%{y}</b><br>Cantidad de Sitios: %{x}<br><br><b>Sitios Afectados:</b><br>%{customdata[0]}<extra></extra>'
            )
            st.plotly_chart(fig_stopper_bar, use_container_width=True)
        else:
            st.info("No hay sitios en gestión activa para analizar stoppers.")
    else:
        st.info("La columna 'Stopper' no se encontró en los datos.")
    # --- FIN DE LA SECCIÓN DE GRÁFICO MODIFICADA ---

else:
    st.info("No hay datos de estatus para mostrar.")

#INFO
st.divider()
st.subheader("🗂️ Información de Todos los Sitios (Filtro Actual)")

columnas_info_general = ['AB+ALt', 'Nombre Sitio', 'Comuna', 'Región', 'Proyecto', 'Complementario', 'Lat', 'Long', 'Stopper']
columnas_existentes_general = [col for col in columnas_info_general if col in df_filtrado.columns]
st.dataframe(df_filtrado[columnas_existentes_general], use_container_width=True)

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
    fig_mapa = px.scatter_mapbox(mapa_df, lat="Lat", lon="Long", zoom=4, hover_name="Nombre Sitio",
                                 hover_data={"Comuna": True, "Gestor": True}, color_discrete_sequence=["mediumpurple"])
    fig_mapa.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_mapa, use_container_width=True, config={"scrollZoom": True})
else:
    st.info("No hay coordenadas disponibles para mostrar en el mapa.")
