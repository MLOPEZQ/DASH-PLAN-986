import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    df = pd.read_excel(uploaded_file, engine='openpyxl', dtype={'Estatus': str, 'Forecast Firma': str, 'Forecast Móvil': str})
    df.columns = df.columns.str.strip()
    df.dropna(subset=['Estatus'], inplace=True)
    df['Complementario'] = df['Complementario'].astype(str).str.strip().str.lower()
    df['Proyecto'] = df['Proyecto'].astype(str).str.strip().str.lower()
    for col in ['Fecha Entrega a Construcción', 'Fecha TSS']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
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
    
    columnas_info = ['AB+ALt', 'Nombre Sitio', 'Comuna', 'Región', 'Proyecto', 'Complementario', 'Renta', 'Lat', 'Long', 'Stopper']
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
    uploaded_file.seek(0)
    df_tss_raw = pd.read_excel(uploaded_file, engine='openpyxl')
    df_tss_raw.columns = df_tss_raw.columns.str.strip()
else:
    st.warning("Por favor, sube el archivo Excel para continuar.")
    st.stop()

df = df_original[(df_original['Proyecto'] == 'plan 986') & (df_original['Complementario'] == 'si')]
df['Sitio'] = df['AB+ALt'].astype(str) + " - " + df['Nombre Sitio'].astype(str)
df = pd.merge(df, df_tss_raw[['AB+ALt', 'Fecha TSS']], on='AB+ALt', how='left', suffixes=('', '_raw'))
df['Fecha TSS'] = df['Fecha TSS_raw']
df.drop(columns=['Fecha TSS_raw'], inplace=True)

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
        fig_stopper_bar = px.bar(stopper_counts, x='Cantidad', y='Stopper', orientation='h', text='Cantidad', custom_data=['Sitios'], color='Cantidad', color_continuous_scale=px.colors.sequential.Purples)
        fig_stopper_bar.update_layout(yaxis={'categoryorder':'total ascending'}, yaxis_title=None, xaxis_title="Cantidad de Sitios", showlegend=False, coloraxis_showscale=False, height=300 + len(stopper_counts) * 30)
        fig_stopper_bar.update_traces(textposition='inside', hovertemplate='<b>%{y}</b><br>Cantidad de Sitios: %{x}<br><br><b>Sitios Afectados:</b><br>%{customdata[0]}<extra></extra>')
        st.plotly_chart(fig_stopper_bar, use_container_width=True)
    else:
        st.info("No hay sitios en gestión activa para analizar stoppers.")
else:
    st.info("La columna 'Stopper' no se encontró en los datos.")

# --------------------------------------------------------
# 📊 Sección Forecast con pestañas
# --------------------------------------------------------

st.divider()
st.subheader("🔮 FORECAST")

tab1, tab2 = st.tabs(["FORECAST FIRMA", "FORECAST FIRMA ACUMULADO"])

# ---------------- TAB 1: Forecast Firma existente ----------------
with tab1:
    if 'Forecast Firma' in df_gestion_activa.columns and 'Forecast Móvil' in df_gestion_activa.columns:
        forecast_comp_df = df_gestion_activa.copy()
        forecast_comp_df = forecast_comp_df[forecast_comp_df['Estatus Limpio'] != 'Firmado']
        forecast_comp_df = forecast_comp_df.dropna(subset=['Forecast Firma', 'Forecast Móvil'])

        forecast_comp_df['WeekNum_Original'] = pd.to_numeric(forecast_comp_df['Forecast Firma'].str.extract(r'(\d+)')[0], errors='coerce')
        forecast_comp_df['WeekNum_Movil'] = pd.to_numeric(forecast_comp_df['Forecast Móvil'].str.extract(r'(\d+)')[0], errors='coerce')
        
        forecast_comp_df.dropna(subset=['WeekNum_Original', 'WeekNum_Movil'], inplace=True)
        forecast_comp_df[['WeekNum_Original', 'WeekNum_Movil']] = forecast_comp_df[['WeekNum_Original', 'WeekNum_Movil']].astype(int)

        forecast_comp_df['Variacion'] = forecast_comp_df['WeekNum_Movil'] - forecast_comp_df['WeekNum_Original']
        
        def get_status_and_color(v):
            if v > 0: return 'Retrasado', '#d93025'
            if v < 0: return 'Adelantado', '#1e8e3e'
            return 'En Fecha', '#1a73e8'

        forecast_comp_df[['Status', 'Color']] = forecast_comp_df['Variacion'].apply(get_status_and_color).apply(pd.Series)
        forecast_comp_df.sort_values(by=['WeekNum_Movil', 'Sitio'], ascending=[True, True], inplace=True)

        if forecast_comp_df.empty:
            st.info("No hay sitios con 'Forecast Firma' y 'Forecast Móvil' válidos para comparar.")
        else:
            fig = go.Figure()
            legend_added = set()

            for _, row in forecast_comp_df.iterrows():
                y_pos = row['Sitio']
                x_orig = row['WeekNum_Original']
                x_movil = row['WeekNum_Movil']
                color = row['Color']
                status = row['Status']

                show_legend = status not in legend_added
                if show_legend:
                    legend_added.add(status)

                if row['Variacion'] == 0:
                    fig.add_trace(go.Scatter(
                        x=[x_movil], y=[y_pos],
                        mode='markers+text',
                        text=[str(x_movil)],
                        textposition='middle right',
                        textfont=dict(color='DarkSlateGrey', size=12),
                        marker=dict(color=color, size=12, symbol='circle', line=dict(width=1, color='DarkSlateGrey')),
                        hoverinfo='text',
                        hovertext=f"<b>{row['Sitio']}</b><br>Forecast: W{x_movil}<br><b>(En Fecha)</b>",
                        name=status,
                        legendgroup=status,
                        showlegend=show_legend
                    ))
                else:
                    fig.add_shape(type='line', x0=x_orig, y0=y_pos, x1=x_movil, y1=y_pos,
                                  line=dict(color='rgba(128, 128, 128, 0.5)', width=1.5, dash='dot'))
                    fig.add_trace(go.Scatter(
                        x=[x_orig], y=[y_pos],
                        mode='markers+text',
                        text=[str(x_orig)],
                        textposition='middle left',
                        textfont=dict(color='grey', size=10),
                        marker=dict(color='grey', size=8, symbol='circle'),
                        hoverinfo='text',
                        hovertext=f"<b>{row['Sitio']}</b><br>F. Original: W{x_orig}",
                        showlegend=False
                    ))
                    variacion_str = f"+{row['Variacion']}" if row['Variacion'] > 0 else str(row['Variacion'])
                    hover_text_movil = f"<b>{row['Sitio']}</b><br>F. Móvil: W{x_movil}<br>F. Original: W{x_orig}<br>Variación: {variacion_str} semanas"
                    fig.add_trace(go.Scatter(
                        x=[x_movil], y=[y_pos],
                        mode='markers+text',
                        text=[str(x_movil)],
                        textposition='middle right',
                        textfont=dict(color='DarkSlateGrey', size=12),
                        marker=dict(color=color, size=12, symbol='circle', line=dict(width=1, color='DarkSlateGrey')),
                        hoverinfo='text',
                        hovertext=hover_text_movil,
                        name=status,
                        legendgroup=status,
                        showlegend=show_legend
                    ))

            fig.update_layout(
                yaxis_title=None,
                xaxis_title="Número de Semana del Año",
                height=200 + len(forecast_comp_df) * 40,
                yaxis=dict(type='category', categoryorder='array', categoryarray=forecast_comp_df['Sitio'].tolist()),
                margin=dict(l=250, r=40, t=80, b=40),
                plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text='')
            )
            
            current_week = datetime.now().isocalendar().week
            fig.add_vline(x=current_week, line_width=2, line_dash="dash", line_color="purple",
                          annotation_text="Semana Actual", annotation_position="top left", annotation_font_color="purple")

            st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("Para ver la comparación, asegúrese de que el archivo Excel contenga las columnas 'Forecast Firma' y 'Forecast Móvil'.")

# ---------------- TAB 2: Forecast Firma Acumulado ----------------


df_forecast = df_gestion_activa.copy()

df_forecast['Week_Forecast'] = pd.to_numeric(df_forecast['Forecast Firma'].str.extract(r'(\d+)')[0], errors='coerce')
df_forecast['Week_Real'] = pd.to_numeric(df_forecast['Week Firma'].str.extract(r'(\d+)')[0], errors='coerce')

df_forecast = df_forecast.dropna(subset=['Week_Forecast', 'Week_Real'])
df_forecast[['Week_Forecast', 'Week_Real']] = df_forecast[['Week_Forecast', 'Week_Real']].astype(int)

last_real_week = df_forecast['Week_Real'].max()

weeks_forecast = list(range(12, 40 + 1))
weeks_real = list(range(12, last_real_week + 1))

forecast_weekly = df_forecast.groupby('Week_Forecast').size().reindex(weeks_forecast, fill_value=0).tolist()
forecast_cum = pd.Series(forecast_weekly).cumsum().tolist()

real_weekly = df_forecast.groupby('Week_Real').size().reindex(weeks_real, fill_value=0).tolist()
real_cum = pd.Series(real_weekly).cumsum().tolist()

fig = go.Figure()

# Forecast acumulado (línea azul)
fig.add_trace(go.Scatter(
    x=weeks_forecast,
    y=forecast_cum,
    mode='lines+markers+text',
    name='Forecast Acumulado',
    line=dict(color='royalblue', width=2, dash='dash'),
    marker=dict(size=6, symbol='circle-open', line=dict(color='royalblue', width=2)),
    text=[str(v) if v != 0 else "" for v in forecast_cum],
    textposition="top center",
    textfont=dict(size=9, color="royalblue")
))

# Real acumulado (línea roja)
fig.add_trace(go.Scatter(
    x=weeks_real,
    y=real_cum,
    mode='lines+markers+text',
    name='Real Acumulado',
    line=dict(color='red', width=2),
    marker=dict(size=6, symbol='circle-open', line=dict(color='red', width=2)),
    text=[str(v) if v != 0 else "" for v in real_cum],
    textposition="top center",
    textfont=dict(size=9, color="red")
))

fig.update_layout(
    xaxis=dict(
        title="Semana",
        dtick=1,
        tickmode='linear',
        range=[12 - 0.5, 40 + 0.5],
        tickvals=list(range(12, 41)),
        ticktext=[f"W{w}" for w in range(12, 41)],
        gridcolor='rgba(200, 200, 200, 0.3)',
        showgrid=True
    ),
    yaxis=dict(title="Q Firmas", rangemode='tozero', gridcolor='rgba(200, 200, 200, 0.3)', showgrid=True),
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
    template="simple_white"
)

st.plotly_chart(fig, use_container_width=True)
# --------------------------------------------------------
# VISUALIZACIÓN DE CRONOGRAMA TSS
# --------------------------------------------------------
st.divider()
st.subheader("📅 Cronograma de TSS")

def parse_tss_date(value):
    if pd.isna(value):
        return None
    if isinstance(value, (datetime, pd.Timestamp)):
        return value
    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower.startswith('w'):
            try:
                week_num = int(value_lower.replace('w', ''))
                current_year = datetime.now().year
                return datetime.fromisocalendar(current_year, week_num, 1)
            except (ValueError, TypeError):
                return None
    return pd.to_datetime(value, errors='coerce')

if 'Fecha TSS' in df_gestion_activa.columns:
    tss_df = df_gestion_activa.dropna(subset=['Fecha TSS']).copy()
    tss_df['SortableDate'] = tss_df['Fecha TSS'].apply(parse_tss_date)
    tss_df = tss_df.dropna(subset=['SortableDate']).sort_values('SortableDate')

    expander_title = f"Ver Cronograma de TSS ({len(tss_df)} sitios con fecha)"
    with st.expander(expander_title):
        if not tss_df.empty:
            today = datetime.now().date()
            current_isocal = datetime.now().isocalendar()
            start_of_week = datetime.fromisocalendar(current_isocal.year, current_isocal.week, 1).date()
            end_of_week = datetime.fromisocalendar(current_isocal.year, current_isocal.week, 7).date()

            for _, row in tss_df.iterrows():
                site_name = row['Sitio']
                tss_date = row['SortableDate'].date()
                original_format = row['Fecha TSS']
                
                if isinstance(original_format, (datetime, pd.Timestamp)):
                    display_date = original_format.strftime('%d-%m-%Y')
                else:
                    display_date = str(original_format).strip()

                if tss_date < start_of_week:
                    status_icon = "✅"
                    status_text = "(Realizada)"
                elif start_of_week <= tss_date <= end_of_week:
                    status_icon = "🎯"
                    status_text = "(Semana Actual)"
                else: 
                    status_icon = "🗓️"
                    status_text = "(En Programación)"

                st.markdown(f"{status_icon} **{site_name}**: {display_date} {status_text}")
        else:
            st.info("No hay sitios en gestión activa con una fecha de TSS programada.")
else:
    st.info("La columna 'Fecha TSS' no se encontró en los datos.")

# --------------------------------------------------------
# MAPS
# --------------------------------------------------------
st.divider()
st.subheader("🌐 Georeferencia")
mapa_df = df_filtrado.dropna(subset=['Lat', 'Long'])
if not mapa_df.empty:
    fig_mapa = px.scatter_mapbox(mapa_df, lat="Lat", lon="Long", zoom=4, hover_name="Nombre Sitio", hover_data={"Comuna": True, "Gestor": True}, color_discrete_sequence=["mediumpurple"])
    fig_mapa.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_mapa, use_container_width=True, config={"scrollZoom": True})
else:
    st.info("No hay coordenadas disponibles para mostrar en el mapa.")
