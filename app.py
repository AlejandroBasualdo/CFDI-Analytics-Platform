import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import text
from src.database import engine, SessionLocal, Factura, AlertaAuditoria, get_stats
from src.etl import ejecutar_pipeline
from src.anomaly import detectar_anomalias
from src.classifier import clasificar_todas_las_facturas
from src.conciliacion import conciliar
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="CFDI Analytics Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* Fondo principal - Negro industrial carbón */
.stApp { background-color: #0D1117; }

/* Sidebar - Gris azulado oscuro */
section[data-testid="stSidebar"] { 
    background-color: #161B22; 
    border-right: 1px solid #30363D; 
}

/* Header */
header[data-testid="stHeader"] { background-color: #0D1117; }

/* Tipografía principal - Blanco grisáceo */
h1, h2, h3, h4 { color: #E6EDF3 !important; font-weight: 600; }
p, label, span, .stMarkdown { color: #8B949E; }

/* Métricas - Tarjetas oscuras con acentos */
[data-testid="metric-container"] {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
[data-testid="stMetricValue"] { 
    font-size: 26px !important; 
    color: #58A6FF !important; 
    font-weight: 700;
    text-shadow: 0 0 10px rgba(88, 166, 255, 0.3);
}
[data-testid="stMetricLabel"] { 
    font-size: 11px !important; 
    color: #6E7681 !important; 
    text-transform: uppercase; 
    letter-spacing: 0.08em;
}

/* Botones - Estilo industrial */
.stButton button {
    background: #161B22 !important;
    color: #E6EDF3 !important;
    border: 1px solid #30363D !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    width: 100% !important;
    padding: 10px 16px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease;
}
.stButton button:hover { 
    background: #21262D !important; 
    border-color: #58A6FF !important;
    box-shadow: 0 0 12px rgba(88, 166, 255, 0.2);
}

/* Divisores */
hr { border-color: #30363D !important; }
.stDivider { border-color: #30363D; }

/* DataFrames - Fondo oscuro con texto claro */
[data-testid="stDataFrame"] { background: #161B22 !important; border: 1px solid #30363D; border-radius: 8px; }
iframe { color-scheme: dark !important; }
.stDataFrame * { color: #E6EDF3 !important; }
.stDataFrame th { background-color: #21262D !important; color: #58A6FF !important; font-weight: 600; }
.stDataFrame td { border-bottom: 1px solid #30363D; }

/* Selectbox y otros inputs */
.stSelectbox > div > div { 
    background-color: #161B22; 
    border: 1px solid #30363D; 
    color: #E6EDF3; 
}
.stSelectbox > div > div:hover { border-color: #58A6FF; }

/* Spinner y carga */
.stSpinner > div > div { border-color: #58A6FF !important; }

/* Alertas y mensajes */
.stSuccess { background-color: rgba(63, 185, 80, 0.15); border: 1px solid #3FB950; border-radius: 8px; }
.stInfo { background-color: rgba(88, 166, 255, 0.15); border: 1px solid #58A6FF; border-radius: 8px; }
.stWarning { background-color: rgba(210, 153, 34, 0.15); border: 1px solid #D29922; border-radius: 8px; }

/* Scrollbar personalizada */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: #0D1117; }
::-webkit-scrollbar-thumb { background: #21262D; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #6E7681; }
</style>
""", unsafe_allow_html=True)

LAYOUT = dict(
    paper_bgcolor="#161B22",
    plot_bgcolor="#161B22",
    font=dict(color="#E6EDF3", size=12),
    margin=dict(l=20, r=20, t=30, b=20),
    height=320,
    xaxis=dict(
        gridcolor="#21262D",
        linecolor="#30363D",
        zerolinecolor="#30363D"
    ),
    yaxis=dict(
        gridcolor="#21262D",
        linecolor="#30363D",
        zerolinecolor="#30363D"
    )
)

def get_df(query: str) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)

with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:8px 0 4px;'>
        <svg width="32" height="32" viewBox="0 0 42 42" fill="none">
            <rect width="42" height="42" rx="8" fill="#58A6FF"/>
            <text x="21" y="27" text-anchor="middle" fill="white" font-size="14" font-weight="bold">CF</text>
        </svg>
        <p style='color:#E6EDF3; font-size:14px; font-weight:600; margin:6px 0 0;'>CFDI Analytics</p>
        <p style='color:#6E7681; font-size:11px; margin:2px 0 0;'>Aceros del Norte S.A. de C.V.</p>
    </div>
    """, unsafe_allow_html=True)
    st.divider()

    if st.button("Ejecutar pipeline ETL"):
        with st.spinner("Procesando CFDIs..."):
            ejecutar_pipeline()
            st.success("Pipeline completado")

    if st.button("Detectar anomalías"):
        with st.spinner("Analizando con Isolation Forest..."):
            detectar_anomalias()
            st.success("Detección completada")

    if st.button("Clasificar conceptos"):
        with st.spinner("Clasificando con NLP..."):
            clasificar_todas_las_facturas()
            st.success("Clasificación completada")

    if st.button("Conciliación bancaria"):
        with st.spinner("Conciliando..."):
            conciliar()
            st.success("Conciliación completada")

    st.divider()
    st.markdown("<p style='color:#6E7681; font-size:11px; line-height:1.8;'>Motor: PostgreSQL 18<br>ML: Isolation Forest<br>NLP: spaCy ES<br>Conciliación: FuzzyWuzzy</p>", unsafe_allow_html=True)

st.markdown("""
<div style='display:flex; align-items:center; gap:14px; margin-bottom:8px;'>
    <svg width="40" height="40" viewBox="0 0 42 42" fill="none">
        <rect width="42" height="42" rx="8" fill="#58A6FF"/>
        <text x="21" y="27" text-anchor="middle" fill="white" font-size="14" font-weight="bold">CF</text>
    </svg>
    <div>
        <h2 style='margin:0; color:#E6EDF3; font-size:24px; font-weight:600;'>CFDI Analytics Platform</h2>
        <p style='margin:0; color:#6E7681; font-size:13px;'>Sistema integral de facturación electrónica · Aceros del Norte S.A. de C.V. · RFC: ANO850312AB1</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.divider()

stats = get_stats()
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total CFDIs", f"{stats['total_facturas']:,}")
col2.metric("Válidas", f"{stats['validas']:,}")
col3.metric("Inválidas", f"{stats['invalidas']:,}")
col4.metric("Anomalías", f"{stats['anomalias']:,}")
col5.metric("Total facturado", f"${stats['total_mxn']:,.0f}")

st.divider()

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("#### Gasto mensual por periodo")
    df_mes = get_df("""
        SELECT
            SUBSTRING(fecha, 1, 7) as mes,
            SUM(total) as total_mes,
            COUNT(*) as num_facturas
        FROM facturas
        GROUP BY mes
        ORDER BY mes
    """)
    if not df_mes.empty:
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=df_mes["mes"], y=df_mes["total_mes"],
            marker_color="#58A6FF", name="Total MXN"
        ))
        fig1.update_layout(**LAYOUT)
        fig1.update_xaxes(showgrid=False, linecolor="#30363D", tickfont=dict(color="#8B949E"))
        fig1.update_yaxes(showgrid=True, gridcolor="#21262D", linecolor="#30363D", tickfont=dict(color="#8B949E"))
        st.plotly_chart(fig1, use_container_width=True)

with col_b:
    st.markdown("#### Top 5 proveedores por monto")
    df_prov = get_df("""
        SELECT receptor_nombre, SUM(total) as total_proveedor
        FROM facturas
        GROUP BY receptor_nombre
        ORDER BY total_proveedor DESC
        LIMIT 5
    """)
    if not df_prov.empty:
        fig2 = px.bar(
            df_prov, x="total_proveedor", y="receptor_nombre",
            orientation="h",
            color_discrete_sequence=["#F78166"]
        )
        fig2.update_layout(**LAYOUT)
        fig2.update_xaxes(showgrid=True, gridcolor="#21262D", linecolor="#30363D", tickfont=dict(color="#8B949E"))
        fig2.update_yaxes(showgrid=False, linecolor="#30363D", tickfont=dict(color="#8B949E"))
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

col_c, col_d = st.columns(2)

with col_c:
    st.markdown("#### Distribución por categoría contable")
    df_cat = get_df("""
        SELECT categoria_concepto, COUNT(*) as total,
               SUM(total) as monto_total
        FROM facturas
        WHERE categoria_concepto IS NOT NULL
        GROUP BY categoria_concepto
        ORDER BY total DESC
    """)
    if not df_cat.empty:
        fig3 = px.pie(
            df_cat, values="total", names="categoria_concepto",
            color_discrete_sequence=["#58A6FF","#F78166","#3FB950","#D29922","#A371F7","#F85149","#79C0FF"]
        )
        fig3.update_layout(**LAYOUT)
        st.plotly_chart(fig3, use_container_width=True)

with col_d:
    st.markdown("#### Facturas por método de pago")
    df_mp = get_df("""
        SELECT
            CASE metodo_pago
                WHEN 'PUE' THEN 'Pago en una exhibición'
                WHEN 'PPD' THEN 'Pago en parcialidades'
                ELSE metodo_pago
            END as metodo,
            COUNT(*) as total
        FROM facturas
        GROUP BY metodo_pago
    """)
    if not df_mp.empty:
        fig4 = px.pie(
            df_mp, values="total", names="metodo",
            color_discrete_sequence=["#58A6FF", "#F78166"]
        )
        fig4.update_layout(**LAYOUT)
        st.plotly_chart(fig4, use_container_width=True)

st.divider()
st.markdown("#### Alertas de auditoría")

df_alertas = get_df("""
    SELECT tipo_alerta, descripcion, severidad,
           creado_en, uuid_factura
    FROM alertas_auditoria
    ORDER BY creado_en DESC
    LIMIT 20
""")

if not df_alertas.empty:
    col_fil1, col_fil2 = st.columns(2)
    with col_fil1:
        severidad_filter = st.selectbox(
            "Filtrar por severidad",
            ["Todas", "ALTA", "MEDIA", "BAJA"]
        )
    with col_fil2:
        tipo_filter = st.selectbox(
            "Filtrar por tipo",
            ["Todos", "MONTO_ATIPICO", "HORARIO_INUSUAL", "PATRON_ANOMALO", "DUPLICADO"]
        )

    df_filtrado = df_alertas.copy()
    if severidad_filter != "Todas":
        df_filtrado = df_filtrado[df_filtrado["severidad"] == severidad_filter]
    if tipo_filter != "Todos":
        df_filtrado = df_filtrado[df_filtrado["tipo_alerta"] == tipo_filter]

    df_filtrado["creado_en"] = pd.to_datetime(df_filtrado["creado_en"]).dt.strftime("%Y-%m-%d %H:%M")
    df_filtrado.columns = ["Tipo", "Descripción", "Severidad", "Fecha", "UUID"]
    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
else:
    st.info("No hay alertas. Ejecuta la detección de anomalías primero.")

st.divider()
st.markdown("#### Últimas facturas procesadas")
df_facturas = get_df("""
    SELECT folio, receptor_nombre, concepto_descripcion,
           total, categoria_concepto, es_valido, es_anomalia, fecha
    FROM facturas
    ORDER BY creado_en DESC
    LIMIT 20
""")
if not df_facturas.empty:
    df_facturas["fecha"] = pd.to_datetime(df_facturas["fecha"]).dt.strftime("%Y-%m-%d")
    df_facturas["total"] = df_facturas["total"].apply(lambda x: f"${x:,.2f}")
    df_facturas.columns = ["Folio", "Proveedor", "Concepto", "Total", "Categoría", "Válida", "Anomalía", "Fecha"]
    st.dataframe(df_facturas, use_container_width=True, hide_index=True)