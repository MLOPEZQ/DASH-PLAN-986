import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Dashboard PLAN 986 (Sitios Complementarios)", layout="wide")

# --- INICIO: CSS PERSONALIZADO PARA LAS TARJETAS DE MÉTRICA ---
st.markdown("""
<style>
.metric-card {
    background: linear-gradient(to right, #4a00e0, #8e2de2);
    border-radius: 10px;
    color: white;
    padding: 20px;
    text-align: center;
    box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
    transition: 0.3s;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 150px;
}
.metric-value {font-size: 3em; font-weight: bold; color: white;}
.metric-label {font-size: 1.1em; color: #f0f2f6;}
.metric-spacer {min-height: 20px;}
.stButton>button {
    width: 100%; border: 1px solid white; color: white; background-color: rgba(255, 255, 255, 0.2);
}
.stButton>button:hover {
    border: 1px solid #c9c9c9; color: #c9c9c9; background-color: rgba(255, 255, 255, 0.3);
}
</style>
""", unsafe_allow_html=True)
# --- FIN: CSS PERSONALIZADO ---

st.image("10 Años.jpg", width=None)
st.markdown("""<div style='text-align: center;'><h1 style='margin-top: 0;'>📍 Dashboard PLAN 986 (Sitios Complementarios)</h1><div style='font-size: 14px; color: gray; margin-top: 5px;'><em>By MLOPEZQ</em></div></div>""", unsafe_allow_html=True)

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

def set_selected_status(status):
    st.session_state.selected_status = status

def display_detail_view(title, dataframe):
    st.divider()
    col_header, col_button = st.columns([4, 1])
    with col_header:
        st.subheader(title)
    with col_button:
        st.button("Ocultar Detalle", on_click=set_selected_status, args=(None,), use_container_width=True, key=f"hide_detail_btn_{title}")
    columnas_info = ['AB+ALt', 'Nombre Sitio', 'Comuna', 'Región', 'Proyecto', 'Complementario', 'Lat', 'Long', 'Stopper']
    columnas_existentes = [col for col in columnas_info if col in dataframe.columns]
    st.dataframe(dataframe[columnas_existentes], use_container_width=True)
    st.subheader("📝 Comentarios Asociados")
    with st.expander("Ver/Ocultar comentarios para esta selección"):
        comments_df = dataframe[['Nombre Sitio', 'Observaciones']].dropna()
        if not comments_df.empty:
            for _, row in comments_df.iterrows():
                st.markdown(f"**{row['Nombre Sitio']}**: {row['Observaciones']}")
        else:
            st.info("No hay comentarios para los sitios en esta selección.")

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

st.subheader("📊 SEGUIMIENTO")
total_sitios_filtrados = len(df_filtrado)
estatus_excluir = ['Eliminado', 'Standby']
df_gestion_activa = df_filtrado[~df_filtrado['Estatus Limpio'].isin(estatus_excluir)]
total_gestion_activa = len(df_gestion_activa)

l_spacer, col_total, col_activa, r_spacer = st.columns([1, 2, 2, 1])

with col_total:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Total de Sitios</div><div class="metric-value">{total_sitios_filtrados}</div><div class="metric-spacer"> </div></div>""", unsafe_allow_html=True)
    st.button("Ver Detalle de Todos", on_click=set_selected_status, args=('ALL',), use_container_width=True, key="btn_all_sites")
with col_activa:
    st.markdown(f"""<div class="metric-card"><div class="metric-label">Sitios en Gestión Activa</div><div class="metric-value">{total_gestion_activa}</div><div class="metric-spacer"> </div></div>""", unsafe_allow_html=True)
    st.button("Ver Detalle Activos", on_click=set_selected_status, args=('ACTIVE',), use_container_width=True, key="btn_active_sites")

if st.session_state.selected_status in ['ALL', 'ACTIVE']:
    if st.session_state.selected_status == 'ALL':
        display_detail_view(title="🗂️ Detalle: Total de Sitios", dataframe=df_filtrado)
    elif st.session_state.selected_status == 'ACTIVE':
        display_detail_view(title="⚙️ Detalle: Sitios en Gestión Activa", dataframe=df_gestion_activa)

st.subheader("📈 Resumen ESTATUS")
if 'Estatus' in df_filtrado.columns:
    status_counts = df_filtrado.groupby(['Estatus', 'Estatus Limpio']).agg(Cantidad=("Sitio", "count")).reset_index()
    status_counts['Orden'] = status_counts['Estatus'].str.extract(r'(\d+)').astype(int)
    status_counts = status_counts.sort_values('Orden', ascending=True).reset_index(drop=True)
    status_icons = {"Eliminado": "🗑️", "Procuración": "🔍", "Carpeta Completa - Pend ING": "📁", "En borrador": "📝", "En búsqueda": "🕵️‍♂️", "Firmado": "✍️", "Standby": "⏸️", "En programación TSS": "📅", "Pendiente TSS": "⏳", "TSS Realizada": "✅", "Carpeta Ingresada": "🗂️"}
    
    num_cols = 5
    cols = st.columns(num_cols)
    for i, row in status_counts.iterrows():
        with cols[i % num_cols]:
            with st.container(border=True):
                icon = status_icons.get(row['Estatus Limpio'], '📊')
                st.metric(label=f"{icon} {row['Estatus Limpio']}", value=row['Cantidad'])
                st.button("Ver Detalle", key=f"btn_{row['Estatus Limpio']}", on_click=set_selected_status, args=(row['Estatus Limpio'],), use_container_width=True)

    if st.session_state.selected_status and st.session_state.selected_status not in ['ALL', 'ACTIVE']:
        detalle_df = df_filtrado[df_filtrado['Estatus Limpio'] == st.session_state.selected_status]
        display_detail_view(title=f"🔎 Detalle: Estatus {st.session_state.selected_status}", dataframe=detalle_df)

st.divider()
st.subheader("📊 Detalle por Stopper (Sitios en Gestión Activa)")
if 'Stopper' in df_filtrado.columns:
    if not df_gestion_activa.empty:
        stopper_df = df_gestion_activa.copy()
        stopper_df['Stopper'] = stopper_df['Stopper'].fillna("Sin Stopper")
        stopper_counts = stopper_df.groupby('Stopper').agg(Cantidad=('Sitio', 'count'), Sitios=('Sitio', lambda x: '<br>'.join(x))).reset_index()
        fig_stopper_bar = px.bar(stopper_counts, x='Cantidad', y='Stopper', orientation='h', text='Cantidad', custom_data=['Sitios'], color='Cantidad', color_continuous_scale=px.colors.sequential.Purples_r)
        fig_stopper_bar.update_layout(yaxis={'categoryorder':'total ascending'}, yaxis_title=None, xaxis_title="Cantidad de Sitios", showlegend=False, coloraxis_showscale=False, height=300 + len(stopper_counts) * 30)
        fig_stopper_bar.update_traces(textposition='inside', hovertemplate='<b>%{y}</b><br>Cantidad de Sitios: %{x}<br><br><b>Sitios Afectados:</b><br>%{customdata[0]}<extra></extra>')
        st.plotly_chart(fig_stopper_bar, use_container_width=True)
    else:
        st.info("No hay sitios en gestión activa para analizar stoppers.")
else:
    st.info("La columna 'Stopper' no se encontró en los datos.")

# --- INICIO DE LA NUEVA SECCIÓN DE FORECAST ---
st.divider()
st.subheader("🗓️ Forecast de Firma (Semanas)")

if 'Forecast Firma' in df_gestion_activa.columns:
    # 1. Preparar los datos del forecast
    forecast_df = df_gestion_activa.dropna(subset=['Forecast Firma']).copy()
    # Extraer el número de la semana y convertir a entero, manejando errores
    forecast_df['WeekNum'] = pd.to_numeric(forecast_df['Forecast Firma'].str.extract(r'(\d+)')[0], errors='coerce')
    forecast_df = forecast_df.dropna(subset=['WeekNum'])
    forecast_df['WeekNum'] = forecast_df['WeekNum'].astype(int)

    if not forecast_df.empty:
        # 2. Obtener la semana actual
        current_week = datetime.now().isocalendar().week
        st.info(f"Semana Actual: W{current_week}")

        # 3. Agrupar sitios por semana de forecast
        forecast_groups = forecast_df.sort_values('WeekNum').groupby('WeekNum')['Sitio'].apply(list).reset_index()

        # 4. Mostrar los forecasts en tarjetas
        num_cols = 4  # Tarjetas por fila
        cols = st.columns(num_cols)
        col_index = 0
        for _, row in forecast_groups.iterrows():
            week = row['WeekNum']
            sites = row['Sitio']
            with cols[col_index % num_cols]:
                with st.container(border=True):
                    # Asignar color y título según si está atrasado, actual o futuro
                    if week < current_week:
                        st.error(f"🔴 W{week} (Atrasado)")
                    elif week == current_week:
                        st.warning(f"🎯 W{week} (Semana Actual)")
                    else:
                        st.success(f"🗓️ W{week}")
                    
                    # Listar los sitios
                    for site in sites:
                        st.markdown(f"- {site}")
                col_index += 1
    else:
        st.info("No hay sitios con forecast definido en la selección activa.")
else:
    st.info("La columna 'Forecast Firma' no se encontró en los datos.")
# --- FIN DE LA NUEVA SECCIÓN DE FORECAST ---


# MAPS
st.divider()
st.subheader("🌐 Georeferencia")
mapa_df = df_filtrado.dropna(subset=['Lat', 'Long'])
if not mapa_df.empty:
    fig_mapa = px.scatter_mapbox(mapa_df, lat="Lat", lon="Long", zoom=4, hover_name="Nombre Sitio", hover_data={"Comuna": True, "Gestor": True}, color_discrete_sequence=["mediumpurple"])
    fig_mapa.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_mapa, use_container_width=True, config={"scrollZoom": True})
else:
    st.info("No hay coordenadas disponibles para mostrar en el mapa.")
