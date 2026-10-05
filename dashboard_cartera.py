import streamlit as st
import pandas as pd
import plotly.express as px
from matplotlib.colors import LinearSegmentedColormap
import os
from datetime import datetime
import pytz

# --- VARIABLES GLOBALES Y COLORES NEUTROS ---
MESES_ES = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
            7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}

COLORES_NEUTROS = ['#2A4B7C', '#5072A7', '#D4A373', '#E76F51', '#5F9EA0', '#E9C46A', '#6D6875', '#8F979C']
CMAP_NEUTRO = LinearSegmentedColormap.from_list('neutro', ['#F8F9FA', '#2A4B7C'])

ESTILO_CENTRADO = [
    {'selector': 'th', 'props': [('text-align', 'center')]},
    {'selector': 'td', 'props': [('text-align', 'center')]}
]


def formato_millones(valor):
    if pd.isna(valor):
        return "$0.00"
    if abs(valor) >= 1000000:
        return f"${valor / 1000000:,.1f} M"
    else:
        return f"${valor:,.2f}"


def col_excel(letra):
    letra = letra.upper()
    numero = 0
    for c in letra:
        numero = numero * 26 + (ord(c) - 64)
    return numero - 1


def calcular_comision(row, col_monto, col_clave, col_transp):
    try:
        transp = str(row[col_transp]).strip().lower()
        monto = float(str(row[col_monto]).replace('$', '').replace(',', '')) if pd.notna(row[col_monto]) else 0.0
        clave = str(row[col_clave]).strip().lower()

        if 'coordinadora' in transp:
            if 'efectivo' in clave or 'pse' in clave:
                if monto <= 229000:
                    return 5474.0
                else:
                    return monto * 0.02
            elif 'tarjeta' in clave:
                if monto <= 136000:
                    return 4641.0
                else:
                    return monto * 0.0265
            else:
                return monto * 0.02
        elif 'servientrega' in transp:
            return monto * 0.012
        elif 'domina' in transp:
            return monto * 0.018
        elif 'xcargo' in transp or 'x cargo' in transp:
            return monto * 0.015
        elif 'moova' in transp:
            return monto * 0.02
        else:
            return 0.0
    except:
        return 0.0


st.set_page_config(page_title="Dashboard Cartera COD", layout="wide")

# --- ESTILOS CSS Y OCULTAMIENTO DE MARCAS DE AGUA ---
st.markdown("""
    <style>
    /* Centrado de textos y métricas */
    h1, h2, h3 { text-align: center !important; }
    [data-testid="stMetricValue"], [data-testid="stMetricLabel"] {
        text-align: center !important;
        justify-content: center !important;
        display: flex;
    }

    /* TRUCO CSS: Ocultar publicidad de Streamlit */
    footer {visibility: hidden;} 
    .viewerBadge_container {display: none !important;} 
    #MainMenu {visibility: visible;} 

    /* Ocultar el botón de 'Deploy' de la parte superior derecha */
    .stDeployButton {display: none !important;} 
    </style>
""", unsafe_allow_html=True)

# --- BRANDING CORPORATIVO DAFITI ---
st.markdown(
    "<h1 style='text-align: center; color: #000000; margin-top: -35px; font-size: 45px; font-weight: 900; letter-spacing: 2px;'>DAFITI</h1>",
    unsafe_allow_html=True)
st.markdown(
    "<h2 style='margin-top: -15px; margin-bottom: 5px; text-align: center; font-size: 24px; color: #2A4B7C;'>📊 Dashboard Integral de Gestión de Cartera COD</h2>",
    unsafe_allow_html=True)

# --- PANTALLA DE INICIO AMIGABLE (SESSION STATE) ---
if 'app_iniciada' not in st.session_state:
    st.session_state['app_iniciada'] = False

if not st.session_state['app_iniciada']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.info(
        "👋 ¡Hola! El servidor está listo. Por favor, presiona el botón para cargar la base de datos y comenzar a analizar la información.")

    col_vacia1, col_boton, col_vacia2 = st.columns([1, 2, 1])
    with col_boton:
        if st.button("🚀 Cargar Dashboard de Cartera", use_container_width=True):
            st.session_state['app_iniciada'] = True
            st.rerun()

    st.stop()

# --- LECTURA DE FECHA Y ACTUALIZACIÓN ---
archivo_a_leer = "base_principal.parquet"

try:
    timestamp_modificacion = os.path.getmtime(archivo_a_leer)
    zona_colombia = pytz.timezone('America/Bogota')
    fecha_colombia = datetime.fromtimestamp(timestamp_modificacion, tz=zona_colombia)
    fecha_actualizacion = fecha_colombia.strftime('%d/%m/%Y %I:%M %p')
except Exception:
    timestamp_modificacion = 0
    fecha_actualizacion = "Desconocida"

st.markdown(
    f"<p style='text-align: center; color: gray; font-size: 14px; margin-top: -10px;'>Última actualización de datos: <b>{fecha_actualizacion}</b></p>",
    unsafe_allow_html=True)


@st.cache_data(show_spinner="⚡ Descomprimiendo y construyendo visualizaciones...")
def cargar_datos(timestamp_cache):
    if not os.path.exists("base_principal.parquet"):
        raise FileNotFoundError("El archivo base_principal.parquet no se encontró en el servidor.")

    df = pd.read_parquet("base_principal.parquet")

    try:
        df_comisiones = pd.read_parquet("comisiones.parquet")
    except FileNotFoundError:
        df_comisiones = pd.DataFrame()

    col_orden = df.columns[0]
    col_item = df.columns[1]
    col_fecha = df.columns[2]
    col_estado = df.columns[3]
    col_ciudad = df.columns[5]
    col_valor = df.columns[6]
    col_marca = df.columns[10]
    col_guia = df.columns[16]
    col_recaudo = df.columns[21]
    col_transp = df.columns[23]
    col_fecha_rec = df.columns[25]
    col_tipo = df.columns[33]
    col_obs = df.columns[34]
    col_rango = df.columns[col_excel('AF')]

    df[col_valor] = pd.to_numeric(df[col_valor].astype(str).str.replace(r'[\$,\s]', '', regex=True),
                                  errors='coerce').fillna(0)
    df[col_recaudo] = pd.to_numeric(df[col_recaudo].astype(str).str.replace(r'[\$,\s]', '', regex=True),
                                    errors='coerce').fillna(0)

    df[col_fecha] = pd.to_datetime(df[col_fecha], errors='coerce')
    df[col_fecha_rec] = pd.to_datetime(df[col_fecha_rec], errors='coerce')
    df['Dias_Recaudo'] = (df[col_fecha_rec] - df[col_fecha]).dt.days

    df['Año'] = df[col_fecha].dt.year
    df['Mes_Num'] = df[col_fecha].dt.month
    df['Mes'] = df['Mes_Num'].map(MESES_ES)

    df[col_estado] = df[col_estado].astype(str).str.strip().str.lower()
    df[col_obs] = df[col_obs].astype(str).str.strip().str.lower()
    df[col_transp] = df[col_transp].astype(str).str.strip().str.title().replace('Nan', 'Sin Asignar')
    df[col_tipo] = df[col_tipo].fillna('Sin Asignar')
    df[col_rango] = df[col_rango].fillna('Sin Rango')

    estados_devolucion = ['canceled', 'rejected_after_delivery_failed']
    df['Es_Devolucion'] = df[col_estado].isin(estados_devolucion)
    df['Deuda_Transportes'] = df[col_obs].isin(
        ['3. enviar a transportes', '7. enviar a cedi-marketplace', '4. en procesamiento'])
    df['Deuda_Transportadora'] = df[col_obs].isin(['2. enviar a transportadora'])
    df['Es_Deuda_Total'] = df['Deuda_Transportes'] | df['Deuda_Transportadora']

    cols_float = df.select_dtypes(include=['float64']).columns
    df[cols_float] = df[cols_float].astype('float32')

    cols_int = df.select_dtypes(include=['int64']).columns
    df[cols_int] = df[cols_int].astype('int32')

    columnas_categoria = [col_ciudad, col_marca, col_transp, col_tipo, col_rango, 'Mes']
    for col in columnas_categoria:
        if col in df.columns:
            df[col] = df[col].astype('category')

    columnas_utiles = [
        col_orden, col_item, col_fecha, col_guia, col_valor, col_marca, col_ciudad,
        col_transp, col_tipo, col_recaudo, col_rango, 'Dias_Recaudo', 'Año', 'Mes_Num',
        'Mes', 'Es_Devolucion', 'Deuda_Transportes', 'Deuda_Transportadora', 'Es_Deuda_Total'
    ]
    df = df[columnas_utiles]

    if not df_comisiones.empty:
        idx_fecha_com = col_excel('G')
        idx_monto_com = col_excel('E')
        idx_clave_com = col_excel('I')
        idx_transp_com = col_excel('F')

        try:
            col_fecha_com = df_comisiones.columns[idx_fecha_com]
            col_monto_com = df_comisiones.columns[idx_monto_com]
            col_clave_com = df_comisiones.columns[idx_clave_com]
            col_transp_com = df_comisiones.columns[idx_transp_com]

            df_comisiones[col_fecha_com] = pd.to_datetime(df_comisiones[col_fecha_com], errors='coerce')
            df_comisiones['Año'] = df_comisiones[col_fecha_com].dt.year
            df_comisiones['Mes_Num'] = df_comisiones[col_fecha_com].dt.month
            df_comisiones['Mes'] = df_comisiones['Mes_Num'].map(MESES_ES)

            df_comisiones['Valor_Comision'] = df_comisiones.apply(
                lambda row: calcular_comision(row, col_monto_com, col_clave_com, col_transp_com), axis=1
            )
            df_comisiones['Transportadora_Limpia'] = df_comisiones[col_transp_com].astype(str).str.strip().str.title()

            cols_float_com = df_comisiones.select_dtypes(include=['float64']).columns
            df_comisiones[cols_float_com] = df_comisiones[cols_float_com].astype('float32')

            columnas_cat_com = ['Mes', 'Transportadora_Limpia']
            for col in columnas_cat_com:
                if col in df_comisiones.columns:
                    df_comisiones[col] = df_comisiones[col].astype('category')

            df_comisiones = df_comisiones[df_comisiones['Valor_Comision'] > 0]

        except IndexError:
            df_comisiones = pd.DataFrame()
    else:
        df_comisiones = pd.DataFrame()

    return df, col_orden, col_item, col_fecha, col_guia, col_valor, col_marca, col_ciudad, col_transp, col_tipo, col_recaudo, col_rango, df_comisiones


try:
    df_principal, col_orden, col_item, col_fecha, col_guia, col_valor, col_marca, col_ciudad, col_transp, col_tipo, col_recaudo, col_rango, df_comisiones = cargar_datos(
        timestamp_modificacion)
except Exception as e:
    st.error(f"🚨 Error: No se encontraron los archivos Parquet. Detalle: {e}")
    st.stop()

# --- 3. BARRA DE FILTROS SUPERIOR ---
st.markdown(
    "<h4 style='margin-top: 0px; margin-bottom: 10px; text-align: center; font-size: 16px;'>🔍 Filtros de Búsqueda</h4>",
    unsafe_allow_html=True)

if 'filtro_anio' not in st.session_state:
    st.session_state['filtro_anio'] = 'Todos'
if 'filtro_mes' not in st.session_state:
    st.session_state['filtro_mes'] = 'Todos'
if 'filtro_transp' not in st.session_state:
    st.session_state['filtro_transp'] = 'Todas'


def reset_filtros():
    st.session_state['filtro_anio'] = 'Todos'
    st.session_state['filtro_mes'] = 'Todos'
    st.session_state['filtro_transp'] = 'Todas'


lista_anios = sorted(df_principal['Año'].dropna().unique())
df_meses_unicos = df_principal[['Mes_Num', 'Mes']].dropna().drop_duplicates().sort_values('Mes_Num')
lista_meses = df_meses_unicos['Mes'].tolist()

# --- FILTRO DE LIMPIEZA PARA EL MENÚ DESPLEGABLE ---
transportadoras_crudas = df_principal[col_transp].dropna().unique()

# Aquí expandimos las palabras basura para atrapar todos los errores
palabras_basura = ['n/a', '_', 'canceled', 'closed', 'clarify', 'return', 'cruce', 'factura', 'fve', '&',
                   'transferencia']

lista_transp_limpia = [
    t for t in transportadoras_crudas
    if not any(basura in str(t).lower() for basura in palabras_basura)
]
lista_transp = sorted(lista_transp_limpia)

col_f1, col_f2, col_f3, col_f4 = st.columns(4)

with col_f1:
    anio_seleccionado = st.selectbox("Selecciona un Año", ["Todos"] + list(lista_anios), key='filtro_anio')
with col_f2:
    mes_seleccionado = st.selectbox("Selecciona un Mes", ["Todos"] + lista_meses, key='filtro_mes')
with col_f3:
    transp_seleccionada = st.selectbox("Selecciona Transportadora", ["Todas"] + lista_transp, key='filtro_transp')
with col_f4:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("🔄 Limpiar Filtros", on_click=reset_filtros, width="stretch")

st.divider()

# Filtrado por máscaras booleanas
mask_principal = pd.Series(True, index=df_principal.index)
if anio_seleccionado != "Todos":
    mask_principal = mask_principal & (df_principal['Año'] == anio_seleccionado)
if mes_seleccionado != "Todos":
    mask_principal = mask_principal & (df_principal['Mes'] == mes_seleccionado)
if transp_seleccionada != "Todas":
    mask_principal = mask_principal & (df_principal[col_transp] == transp_seleccionada)
df_filtrado = df_principal[mask_principal]

if not df_comisiones.empty:
    mask_com = pd.Series(True, index=df_comisiones.index)
    if anio_seleccionado != "Todos":
        mask_com = mask_com & (df_comisiones['Año'] == anio_seleccionado)
    if mes_seleccionado != "Todos":
        mask_com = mask_com & (df_comisiones['Mes'] == mes_seleccionado)
    if transp_seleccionada != "Todas":
        mask_com = mask_com & (df_comisiones['Transportadora_Limpia'] == transp_seleccionada)
    df_com_filt = df_comisiones[mask_com]
else:
    df_com_filt = df_comisiones

# Variables compartidas
total_ordenes = df_filtrado[col_orden].nunique()
total_devoluciones = df_filtrado.loc[df_filtrado['Es_Devolucion'], col_valor].sum()
df_ventas_totales = df_filtrado
ventas_totales = df_ventas_totales[col_valor].sum()
df_guias = df_filtrado.drop_duplicates(subset=[col_guia])
total_recaudo = df_guias[col_recaudo].sum()
tasa_devolucion = (total_devoluciones / ventas_totales * 100) if ventas_totales > 0 else 0
total_comision = df_com_filt['Valor_Comision'].sum() if not df_com_filt.empty else 0.0

# --- IMPLEMENTACIÓN DE PESTAÑAS (TABS) ---
tab_resumen, tab_transp, tab_cartera, tab_comp = st.tabs([
    "📊 Resumen General",
    "🚚 Transportadoras",
    "⚠️ Cartera Pendiente",
    "📅 Comparativos y Tops"
])

# --- PESTAÑA 1: RESUMEN GENERAL ---
with tab_resumen:
    st.markdown("<h3 style='margin-top: 0px; margin-bottom: 0px;'>📈 Indicadores Generales</h3>", unsafe_allow_html=True)
    if not df_filtrado.empty and pd.notna(df_filtrado[col_fecha].min()):
        f_min = df_filtrado[col_fecha].min().strftime('%d/%m/%Y')
        f_max = df_filtrado[col_fecha].max().strftime('%d/%m/%Y')
        st.markdown(
            f"<p style='text-align: center; color: gray; font-size: 15px; margin-top: 5px; margin-bottom: 15px;'>Periodo analizado: <b>{f_min} al {f_max}</b></p>",
            unsafe_allow_html=True)
    else:
        st.markdown(
            "<p style='text-align: center; color: gray; font-size: 15px; margin-top: 5px; margin-bottom: 15px;'>Periodo analizado: Sin datos</p>",
            unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric(label="Ventas Totales", value=formato_millones(ventas_totales))
    col2.metric(label="Total Recaudo", value=formato_millones(total_recaudo))
    col3.metric(label="Devoluciones (Valor)", value=formato_millones(total_devoluciones))
    st.write("")
    col4, col5, col6 = st.columns(3)
    col4.metric(label="Total Comisión", value=formato_millones(total_comision))
    col5.metric(label="Total Órdenes", value=f"{total_ordenes:,.0f}")
    col6.metric(label="Tasa Devolución", value=f"{tasa_devolucion:.1f}%")

    st.divider()

    st.subheader("📅 Desempeño Comparativo por Año")
    mask_comp = pd.Series(True, index=df_principal.index)
    if mes_seleccionado != "Todos":
        mask_comp = mask_comp & (df_principal['Mes'] == mes_seleccionado)
    if anio_seleccionado != "Todos":
        mask_comp = mask_comp & (df_principal['Año'] != anio_seleccionado)
    if transp_seleccionada != "Todas":
        mask_comp = mask_comp & (df_principal[col_transp] == transp_seleccionada)

    df_comparativo = df_principal[mask_comp]

    if not df_comparativo.empty:
        df_guias_comparativo = df_comparativo.drop_duplicates(subset=[col_guia])
        kpis_anio = df_comparativo.groupby('Año', observed=True).agg(
            Total_Ordenes=(col_orden, 'nunique'),
            Total_Devoluciones=(col_valor, lambda x: x[df_comparativo.loc[x.index, 'Es_Devolucion']].sum()),
            Ventas_Totales=(col_valor, 'sum')
        )
        recaudo_anio = df_guias_comparativo.groupby('Año', observed=True)[col_recaudo].sum().rename('Total_Recaudo')

        if not df_comisiones.empty:
            mask_com_comp = pd.Series(True, index=df_comisiones.index)
            if mes_seleccionado != "Todos":
                mask_com_comp = mask_com_comp & (df_comisiones['Mes'] == mes_seleccionado)
            if anio_seleccionado != "Todos":
                mask_com_comp = mask_com_comp & (df_comisiones['Año'] != anio_seleccionado)
            if transp_seleccionada != "Todas":
                mask_com_comp = mask_com_comp & (df_comisiones['Transportadora_Limpia'] == transp_seleccionada)

            df_com_comp = df_comisiones[mask_com_comp]
            comision_anio = df_com_comp.groupby('Año', observed=True)['Valor_Comision'].sum().rename('Total_Comision')
        else:
            comision_anio = pd.Series(0, index=kpis_anio.index, name='Total_Comision')

        kpis_anio = kpis_anio.join(recaudo_anio).join(comision_anio).reset_index()
        tabla_kpis_centrada = kpis_anio.style.format({
            'Año': '{:.0f}', 'Total_Ordenes': '{:,.0f}', 'Total_Devoluciones': '${:,.2f}',
            'Ventas_Totales': '${:,.2f}', 'Total_Recaudo': '${:,.2f}', 'Total_Comision': '${:,.2f}'
        }).set_properties(**{'text-align': 'center'}).set_table_styles(ESTILO_CENTRADO)

        st.dataframe(tabla_kpis_centrada, width="stretch", hide_index=True)

    st.divider()

    if not df_filtrado.empty:
        df_tipo = df_filtrado[~df_filtrado['Es_Devolucion']].groupby(col_tipo, observed=True)[
            col_valor].sum().reset_index()
        if df_tipo[col_valor].sum() > 0:
            df_tipo['Porcentaje'] = (df_tipo[col_valor] / df_tipo[col_valor].sum()) * 100
            df_tipo['Texto'] = df_tipo.apply(lambda x: f"{x[col_tipo]}: {x['Porcentaje']:.1f}%", axis=1)
            df_tipo['Agrupador'] = "Distribución"

            fig_tipo = px.bar(
                df_tipo, x=col_valor, y='Agrupador', color=col_tipo, orientation='h', text='Texto',
                color_discrete_sequence=[COLORES_NEUTROS[0], COLORES_NEUTROS[2], COLORES_NEUTROS[4]]
            )
            fig_tipo.update_traces(textposition='inside', textfont_size=14, insidetextanchor='middle')
            fig_tipo.update_layout(
                barmode='stack', showlegend=False, height=90,
                margin=dict(t=0, b=0, l=0, r=0),
                xaxis=dict(showgrid=False, showticklabels=False, zeroline=False, title=""),
                yaxis=dict(showgrid=False, showticklabels=False, zeroline=False, title="")
            )
            st.markdown(
                "<br><p style='text-align: center; color: gray; font-size: 14px; margin-bottom: -5px;'>Composición de Ventas por Tipo</p>",
                unsafe_allow_html=True)
            st.plotly_chart(fig_tipo, width="stretch")

    st.divider()
    st.subheader("⚖️ Comparativo de Ventas Totales vs Recaudo")
    col_graf1, col_graf2 = st.columns(2)
    if not df_filtrado.empty:
        with col_graf1:
            st.markdown("<h4 style='text-align: center; font-size: 18px;'>Por Rango</h4>", unsafe_allow_html=True)
            df_ventas_rango = df_ventas_totales.groupby(col_rango, observed=True)[col_valor].sum().reset_index(
                name='Ventas_Totales')
            df_recaudo_rango = df_guias.groupby(col_rango, observed=True)[col_recaudo].sum().reset_index(name='Recaudo')
            df_rango = pd.merge(df_ventas_rango, df_recaudo_rango, on=col_rango, how='outer').fillna(0)
            df_rango_melt = df_rango.melt(id_vars=col_rango, value_vars=['Ventas_Totales', 'Recaudo'],
                                          var_name='Métrica', value_name='Monto')
            df_rango_melt['Etiqueta'] = df_rango_melt['Monto'].apply(lambda x: formato_millones(x))

            fig_rango = px.bar(
                df_rango_melt, x=col_rango, y='Monto', color='Métrica', barmode='group', text='Etiqueta',
                color_discrete_sequence=[COLORES_NEUTROS[0], COLORES_NEUTROS[2]], hover_data={'Monto': ':$,.0f'}
            )
            fig_rango.update_traces(textposition='outside', textfont_size=10)
            fig_rango.update_layout(xaxis_title="Rangos", yaxis_title="Monto ($)", hovermode="x unified",
                                    legend_title="")
            st.plotly_chart(fig_rango, width="stretch")

        with col_graf2:
            st.markdown("<h4 style='text-align: center; font-size: 18px;'>Por Transportadora</h4>",
                        unsafe_allow_html=True)
            df_ventas_transp = df_ventas_totales.groupby(col_transp, observed=True)[col_valor].sum().reset_index(
                name='Ventas_Totales')
            df_recaudo_transp = df_guias.groupby(col_transp, observed=True)[col_recaudo].sum().reset_index(
                name='Recaudo')
            df_transp_comp = pd.merge(df_ventas_transp, df_recaudo_transp, on=col_transp, how='outer').fillna(0)
            df_transp_melt = df_transp_comp.melt(id_vars=col_transp, value_vars=['Ventas_Totales', 'Recaudo'],
                                                 var_name='Métrica', value_name='Monto')
            df_transp_melt['Etiqueta'] = df_transp_melt['Monto'].apply(lambda x: formato_millones(x))

            fig_transp = px.bar(
                df_transp_melt, x=col_transp, y='Monto', color='Métrica', barmode='group', text='Etiqueta',
                color_discrete_sequence=[COLORES_NEUTROS[0], COLORES_NEUTROS[2]], hover_data={'Monto': ':$,.0f'}
            )
            fig_transp.update_traces(textposition='outside', textfont_size=10)
            fig_transp.update_layout(xaxis_title="Transportadoras", yaxis_title="Monto ($)", hovermode="x unified",
                                     legend_title="")
            st.plotly_chart(fig_transp, width="stretch")

# --- PESTAÑA 2: TRANSPORTADORAS ---
with tab_transp:
    st.header("🔥 Matriz por Transportadora")
    if not df_filtrado.empty:
        resumen_transp = df_filtrado.groupby(col_transp, observed=True).agg(
            Ordenes=(col_orden, 'nunique'),
            Devoluciones=(col_valor, lambda x: x[df_filtrado.loc[x.index, 'Es_Devolucion']].sum()),
            Ventas_Totales=(col_valor, 'sum')
        ).reset_index().sort_values(by='Ventas_Totales', ascending=False).reset_index(drop=True)

        tabla_coloreada = resumen_transp.style.background_gradient(cmap=CMAP_NEUTRO, subset=['Ordenes', 'Devoluciones',
                                                                                             'Ventas_Totales']).format({
            'Devoluciones': '${:,.2f}', 'Ventas_Totales': '${:,.2f}'
        }).set_properties(**{'text-align': 'center'}).set_table_styles(ESTILO_CENTRADO)
        st.dataframe(tabla_coloreada, width="stretch", hide_index=True)

    st.divider()
    st.header("⏱️ Análisis de Días de Recaudo")
    df_tiempos = df_filtrado[df_filtrado['Dias_Recaudo'] >= 0]
    if not df_tiempos.empty:
        st.metric(label="Promedio Global de Recaudo (Días)", value=f"{df_tiempos['Dias_Recaudo'].mean():.1f} días")

        st.write("**Promedio de Días por Transportadora (General)**")
        df_tiempos_transp = df_tiempos.groupby(col_transp, observed=True)[
            'Dias_Recaudo'].mean().reset_index().sort_values(by='Dias_Recaudo', ascending=True)
        fig_tiempos = px.bar(df_tiempos_transp, x='Dias_Recaudo', y=col_transp, orientation='h',
                             color_discrete_sequence=[COLORES_NEUTROS[0]], text='Dias_Recaudo')
        fig_tiempos.update_traces(texttemplate='%{text:.1f}', textposition='outside')
        fig_tiempos.update_layout(xaxis_title="Días Promedio", yaxis_title="")
        st.plotly_chart(fig_tiempos, width="stretch")

        st.write("**Tendencia de Días de Recaudo (Mes a Mes por Transportadora)**")
        lista_transp_disponibles = sorted(df_tiempos[col_transp].dropna().unique())
        transp_seleccionadas = st.multiselect("Filtra Transportadoras específicas para ver su tendencia:",
                                              options=lista_transp_disponibles, default=[])

        df_tendencia_dias = df_tiempos.groupby(['Año', 'Mes_Num', 'Mes', col_transp], observed=True)[
            'Dias_Recaudo'].mean().reset_index().sort_values(by=['Año', 'Mes_Num'])
        if transp_seleccionadas:
            df_tendencia_dias = df_tendencia_dias[df_tendencia_dias[col_transp].isin(transp_seleccionadas)]

        df_tendencia_dias['Periodo'] = df_tendencia_dias['Mes'].astype(str) + "<br>" + df_tendencia_dias['Año'].astype(
            str)
        fig_tendencia_dias = px.line(
            df_tendencia_dias, x='Periodo', y='Dias_Recaudo', color=col_transp, markers=True,
            color_discrete_sequence=COLORES_NEUTROS, hover_name=col_transp,
            hover_data={'Año': False, 'Mes': False, 'Periodo': False, col_transp: False, 'Dias_Recaudo': ':.1f'}
        )
        orden_periodos = \
        df_tendencia_dias[['Año', 'Mes_Num', 'Periodo']].drop_duplicates().sort_values(['Año', 'Mes_Num'])[
            'Periodo'].tolist()
        fig_tendencia_dias.update_xaxes(type='category', categoryorder='array', categoryarray=orden_periodos)
        fig_tendencia_dias.update_layout(xaxis_title="", yaxis_title="Días Promedio", hovermode="x unified")
        st.plotly_chart(fig_tendencia_dias, width="stretch")

    st.divider()
    st.header("💸 Análisis de Comisiones por Transportadora")
    if not df_com_filt.empty:
        periodos = df_com_filt[['Año', 'Mes_Num']].drop_duplicates().sort_values(by=['Año', 'Mes_Num'],
                                                                                 ascending=False).head(6)
        df_com_filt_6m = pd.merge(df_com_filt, periodos, on=['Año', 'Mes_Num'], how='inner')

        st.subheader("📉 Tendencia (Últimos 6 meses)")
        tendencia_com = df_com_filt_6m.groupby(['Año', 'Mes_Num', 'Mes', 'Transportadora_Limpia'], observed=True)[
            'Valor_Comision'].sum().reset_index()
        tendencia_com = tendencia_com.sort_values(by=['Año', 'Mes_Num'])
        tendencia_com['Periodo'] = tendencia_com['Mes'].astype(str) + "<br>" + tendencia_com['Año'].astype(str)

        fig_com = px.line(
            tendencia_com, x='Periodo', y='Valor_Comision', color='Transportadora_Limpia', markers=True,
            color_discrete_sequence=COLORES_NEUTROS,
            hover_data={'Año': False, 'Mes': False, 'Periodo': False, 'Valor_Comision': ':$,.0f'}
        )
        orden_periodos_com = \
        tendencia_com[['Año', 'Mes_Num', 'Periodo']].drop_duplicates().sort_values(['Año', 'Mes_Num'])[
            'Periodo'].tolist()

        fig_com.update_xaxes(type='category', categoryorder='array', categoryarray=orden_periodos_com, tickangle=-45)
        fig_com.update_layout(xaxis_title="", yaxis_title="Comisión ($)", hovermode="x unified",
                              legend_title="Transportadora")
        st.plotly_chart(fig_com, width="stretch")

        st.write("")

        st.subheader("🧮 Matriz Mensual")
        matriz_com = df_com_filt_6m.pivot_table(index='Transportadora_Limpia', columns=['Año', 'Mes_Num'],
                                                values='Valor_Comision', aggfunc='sum', fill_value=0, observed=True)

        matriz_com.columns = [f"{MESES_ES[mes]} {anio}" for anio, mes in matriz_com.columns]
        matriz_com['Total Comisión'] = matriz_com.sum(axis=1)
        matriz_com = matriz_com.sort_values(by='Total Comisión', ascending=False)

        matriz_com.index.name = 'Transportadora'
        matriz_com = matriz_com.reset_index()

        columnas_numericas = matriz_com.columns[1:]
        matriz_com_centrada = matriz_com.style.background_gradient(cmap=CMAP_NEUTRO, subset=columnas_numericas) \
            .format({col: "${:,.0f}" for col in columnas_numericas}) \
            .set_properties(**{'text-align': 'center'}) \
            .set_table_styles(ESTILO_CENTRADO)

        st.dataframe(matriz_com_centrada, width="stretch", hide_index=True)
    else:
        st.info("Los filtros seleccionados no arrojaron datos de comisiones.")

# --- PESTAÑA 3: CARTERA PENDIENTE ---
with tab_cartera:
    st.header("⚠️ Cartera Pendiente COD")
    deuda_transportadora = df_filtrado.loc[df_filtrado['Deuda_Transportadora'], col_valor].sum()
    deuda_transportes = df_filtrado.loc[df_filtrado['Deuda_Transportes'], col_valor].sum()
    deuda_total = deuda_transportadora + deuda_transportes

    col_d1, col_d2, col_d3 = st.columns(3)
    col_d1.metric("Total Transportadora", value=formato_millones(deuda_transportadora))
    col_d2.metric("Total Transportes", value=formato_millones(deuda_transportes))
    col_d3.metric("Gran Total Pendiente", value=formato_millones(deuda_total))
    st.write("")

    subtab_transp, subtab_interna = st.tabs(["Transportadora", "Área Transportes (Interno)"])


    def mostrar_matriz_deuda(df_datos, filtro_columna):
        df_deuda = df_datos[df_datos[filtro_columna] == True]
        if not df_deuda.empty:
            matriz = df_deuda.pivot_table(index=col_transp, columns=['Año', 'Mes_Num'], values=col_valor, aggfunc='sum',
                                          fill_value=0, observed=True)
            matriz.columns = pd.MultiIndex.from_tuples([(str(anio), MESES_ES[mes]) for anio, mes in matriz.columns],
                                                       names=["Año", "Mes"])
            matriz[('Total', 'Deuda')] = matriz.sum(axis=1)
            matriz = matriz.sort_values(by=('Total', 'Deuda'), ascending=False)
            matriz_centrada = matriz.style.background_gradient(cmap=CMAP_NEUTRO, subset=matriz.columns[:-1]).format(
                "${:,.2f}").set_properties(**{'text-align': 'center'}).set_table_styles(ESTILO_CENTRADO)
            st.dataframe(matriz_centrada, width="stretch")
        else:
            st.success("No hay dinero pendiente en esta categoría.")


    with subtab_transp:
        st.subheader("Pendiente por la Transportadora")
        mostrar_matriz_deuda(df_filtrado, 'Deuda_Transportadora')
    with subtab_interna:
        st.subheader("Pendiente por Transportes")
        mostrar_matriz_deuda(df_filtrado, 'Deuda_Transportes')

    st.divider()
    st.header("📋 Detalle de Guías Pendientes de Pago")
    df_detalle_deuda = df_filtrado[df_filtrado['Es_Deuda_Total'] == True]

    if not df_detalle_deuda.empty:
        columnas_solicitadas = [col_orden, col_item, col_fecha, col_guia, col_valor, col_marca, col_ciudad, col_transp,
                                col_tipo]
        tabla_final_pendientes = df_detalle_deuda[columnas_solicitadas].copy()
        tabla_final_pendientes[col_guia] = tabla_final_pendientes[col_guia].astype(str)
        tabla_final_pendientes[col_orden] = tabla_final_pendientes[col_orden].astype(str)
        tabla_final_pendientes[col_item] = tabla_final_pendientes[col_item].astype(str)
        tabla_final_pendientes[col_fecha] = tabla_final_pendientes[col_fecha].dt.strftime('%Y-%m-%d')
        tabla_final_centrada = tabla_final_pendientes.style.set_properties(**{'text-align': 'center'}).set_table_styles(
            ESTILO_CENTRADO)
        st.dataframe(tabla_final_centrada, width="stretch", hide_index=True)

        csv_detalle = tabla_final_pendientes.to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Descargar Detalle en Excel/CSV", data=csv_detalle,
                           file_name="Detalle_Guias_Pendientes.csv", mime="text/csv")
    else:
        st.success("No existen guías pendientes de pago en el periodo seleccionado.")

# --- PESTAÑA 4: COMPARATIVOS Y TOPS ---
with tab_comp:
    st.subheader("📑 Consolidado Financiero Mensual")
    st.write("Esta tabla cruza las Ventas Totales, el Recaudo y las Comisiones generadas mes a mes.")

    if not df_filtrado.empty:
        df_v = df_ventas_totales.groupby(['Año', 'Mes_Num', 'Mes'], observed=True)[col_valor].sum().reset_index(
            name='Ventas Totales')
        df_r = df_guias.groupby(['Año', 'Mes_Num', 'Mes'], observed=True)[col_recaudo].sum().reset_index(name='Recaudo')

        if not df_com_filt.empty:
            df_c = df_com_filt.groupby(['Año', 'Mes_Num', 'Mes'], observed=True)['Valor_Comision'].sum().reset_index(
                name='Comisión')
        else:
            df_c = pd.DataFrame(columns=['Año', 'Mes_Num', 'Mes', 'Comisión'])

        df_consolidado = pd.merge(df_v, df_r, on=['Año', 'Mes_Num', 'Mes'], how='outer')
        df_consolidado = pd.merge(df_consolidado, df_c, on=['Año', 'Mes_Num', 'Mes'], how='outer').fillna(0)
        df_consolidado = df_consolidado.sort_values(by=['Año', 'Mes_Num'])

        columnas_mostrar = ['Año', 'Mes', 'Ventas Totales', 'Recaudo', 'Comisión']
        df_consolidado_mostrar = df_consolidado[columnas_mostrar]

        tabla_consolidada_estilo = df_consolidado_mostrar.style.format({
            'Ventas Totales': '${:,.0f}', 'Recaudo': '${:,.0f}', 'Comisión': '${:,.0f}'
        }).set_properties(**{'text-align': 'center'}).set_table_styles(ESTILO_CENTRADO)

        st.dataframe(tabla_consolidada_estilo, width="stretch", hide_index=True)

    st.divider()
    st.subheader("📊 Comparativo de Ventas Totales (Año vs Año)")
    if not df_ventas_totales.empty:
        ventas_mes = df_ventas_totales.groupby(['Mes_Num', 'Mes', 'Año'], observed=True)[col_valor].sum().reset_index(
            name='Ventas_Totales')
        df_grafica = ventas_mes.sort_values(by=['Año', 'Mes_Num'])
        df_grafica['Año'] = df_grafica['Año'].astype(str)

        fig = px.line(df_grafica, x='Mes', y='Ventas_Totales', color='Año', markers=True,
                      color_discrete_sequence=[COLORES_NEUTROS[0], COLORES_NEUTROS[3]],
                      hover_data={'Año': False, 'Mes': False, 'Ventas_Totales': ':$,.0f'})

        fig.update_xaxes(categoryorder='array', categoryarray=list(MESES_ES.values()))
        fig.update_layout(xaxis_title="", yaxis_title="Ventas Totales", hovermode="x unified")
        st.plotly_chart(fig, width="stretch")

    st.divider()
    st.header("🏆 Tops de Desempeño (Ventas Totales)")
    col_top1, col_top2 = st.columns(2)
    with col_top1:
        st.subheader("Top 10 Ciudades")
        df_top_ciudades = df_ventas_totales.groupby(col_ciudad, observed=True)[col_valor].sum().nlargest(
            10).reset_index().sort_values(by=col_valor, ascending=True)
        df_top_ciudades['Etiqueta'] = df_top_ciudades[col_valor].apply(lambda x: formato_millones(x))
        fig_ciudades = px.bar(df_top_ciudades, x=col_valor, y=col_ciudad, orientation='h', text='Etiqueta',
                              color_discrete_sequence=[COLORES_NEUTROS[0]])
        fig_ciudades.update_traces(textposition='outside')
        fig_ciudades.update_layout(xaxis_title="Ventas Totales ($)", yaxis_title="")
        st.plotly_chart(fig_ciudades, width="stretch")

    with col_top2:
        st.subheader("Top 10 Marcas")
        df_top_marcas = df_ventas_totales.groupby(col_marca, observed=True)[col_valor].sum().nlargest(
            10).reset_index().sort_values(by=col_valor, ascending=True)
        df_top_marcas['Etiqueta'] = df_top_marcas[col_valor].apply(lambda x: formato_millones(x))
        fig_marcas = px.bar(df_top_marcas, x=col_valor, y=col_marca, orientation='h', text='Etiqueta',
                            color_discrete_sequence=[COLORES_NEUTROS[1]])
        fig_marcas.update_traces(textposition='outside')
        fig_marcas.update_layout(xaxis_title="Ventas Totales ($)", yaxis_title="")
        st.plotly_chart(fig_marcas, width="stretch")