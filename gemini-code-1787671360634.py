import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="SERCOM | Dashboard Executivo de Custos",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Personalizada (Roxo Royal #3B176D & Laranja #F58220)
st.markdown("""
    <style>
    .main {
        background-color: #FAFAFA;
    }
    .stApp header {
        background-color: transparent;
    }
    div[data-testid="metric-container"] {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        padding: 15px 20px;
        border-radius: 10px;
        border-left: 5px solid #3B176D;
        box-shadow: 0px 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="metric-container"] label {
        color: #4B5563 !important;
        font-weight: 600;
        font-size: 0.85rem;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #3B176D !important;
        font-weight: 700;
        font-size: 1.6rem;
    }
    .stButton>button {
        background-color: #3B176D;
        color: white;
        border-radius: 6px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #F58220;
        color: white;
    }
    h1, h2, h3 {
        color: #3B176D;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# Função para carregar e tratar os dados
@st.cache_data
def load_data(file):
    df_capa = pd.read_excel(file, sheet_name='CAPA')
    
    # Localizar a tabela sumarizada na aba CAPA
    # As colunas começam na linha 4 (índice 4) da coluna Unnamed: 30 em diante
    summary_cols = ['Unnamed: 30', 'Unnamed: 31', 'Unnamed: 32', 'Unnamed: 33', 'Unnamed: 34', 'Unnamed: 35', 'Unnamed: 36']
    df_summary = df_capa[summary_cols].dropna(how='all')
    
    # Definir cabeçalho
    df_summary.columns = ['OPERACAO', 'TOTAL_RV', 'TOTAL_BH', 'RECEITA_LIQUIDA', 'CUSTO_OP', 'REPRESENTATIVIDADE', 'HC_ATIVOS']
    
    # Remover linha do cabeçalho original se existir
    df_summary = df_summary[df_summary['OPERACAO'] != 'OPERAÇÃO'].reset_index(drop=True)
    
    # Converter colunas numéricas
    cols_num = ['TOTAL_RV', 'TOTAL_BH', 'RECEITA_LIQUIDA', 'CUSTO_OP', 'HC_ATIVOS']
    for col in cols_num:
        df_summary[col] = pd.to_numeric(df_summary[col], errors='coerce').fillna(0)
    
    # Tratar representatividade
    df_summary['REPRESENTATIVIDADE_PCT'] = df_summary.apply(
        lambda row: (row['CUSTO_OP'] / row['RECEITA_LIQUIDA'] * 100) if row['RECEITA_LIQUIDA'] > 0 else 0, axis=1
    )
    
    # Limpar nomes das operações
    df_summary['OPERACAO'] = df_summary['OPERACAO'].astype(str).str.strip()
    
    # Custo por HC
    df_summary['CUSTO_POR_HC'] = df_summary.apply(
        lambda row: (row['CUSTO_OP'] / row['HC_ATIVOS']) if row['HC_ATIVOS'] > 0 else 0, axis=1
    )
    
    return df_summary

# Barra Lateral (Sidebar)
st.sidebar.image("https://www.sercom.com.br/wp-content/uploads/2021/08/logo-sercom.png", width=180)
st.sidebar.title(" Painel de Controle")
st.sidebar.write("---")

uploaded_file = st.sidebar.file_uploader("📂 Importar nova planilha (.xlsx)", type=['xlsx'])

if uploaded_file is not None:
    data = load_data(uploaded_file)
else:
    try:
        data = load_data('Analise colaboradores.xlsx')
    except Exception as e:
        st.error("Por favor, faça o upload da planilha 'Analise colaboradores.xlsx' na barra lateral.")
        st.stop()

# Filtros na Sidebar
st.sidebar.subheader("Filtros Executivos")
op_filter = st.sidebar.multiselect(
    "Selecione as Operações:",
    options=list(data['OPERACAO'].unique()),
    default=list(data['OPERACAO'].unique())
)

df_filtered = data[data['OPERACAO'].isin(op_filter)]

# Header da Página
st.title("📊 Painel Executivo de Custos Operacionais")
st.caption("Visão Transparente e Comparativa: Receita Líquida, Banco de Horas (BH) e Remuneração Variável (RV)")
st.write("---")

# KPI Cards principais
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

total_receita = df_filtered['RECEITA_LIQUIDA'].sum()
total_custo = df_filtered['CUSTO_OP'].sum()
total_rv = df_filtered['TOTAL_RV'].sum()
total_bh = df_filtered['TOTAL_BH'].sum()
total_hc = df_filtered['HC_ATIVOS'].sum()
rep_geral = (total_custo / total_receita * 100) if total_receita > 0 else 0

with kpi1:
    st.metric("Receita Líquida Total", f"R$ {total_receita:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
with kpi2:
    st.metric("Custo OP Total", f"R$ {total_custo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
with kpi3:
    st.metric("Total RV Registrada", f"R$ {total_rv:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
with kpi4:
    st.metric("Total BH Registrado", f"R$ {total_bh:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
with kpi5:
    st.metric("Representatividade %", f"{rep_geral:.2f}%".replace(".", ","))

st.write("---")

# Layout de Gráficos - Linha 1
col_g1, col_g2 = st.columns([6, 4])

# Gráfico 1: Ranking de Representatividade x Ref Teórica de 3%
with col_g1:
    st.subheader("🎯 Representatividade % vs. Meta Teórica (3,0%)")
    
    df_rep = df_filtered[df_filtered['RECEITA_LIQUIDA'] > 0].sort_values(by='REPRESENTATIVIDADE_PCT', ascending=True)
    
    colors = ['#F58220' if val > 3.0 else '#3B176D' for val in df_rep['REPRESENTATIVIDADE_PCT']]
    
    fig_rep = go.Figure()
    fig_rep.add_trace(go.Bar(
        y=df_rep['OPERACAO'],
        x=df_rep['REPRESENTATIVIDADE_PCT'],
        orientation='h',
        marker_color=colors,
        text=[f"{v:.1f}%".replace(".", ",") for v in df_rep['REPRESENTATIVIDADE_PCT']],
        textposition='outside'
    ))
    
    # Adicionar Linha de Referência de 3%
    fig_rep.add_vline(x=3.0, line_dash="dash", line_color="#EF4444", annotation_text=" Ref. Teórica (3.0%)", annotation_position="top right")
    
    fig_rep.update_layout(
        height=450,
        margin=dict(l=10, r=20, t=30, b=10),
        xaxis_title="Representatividade (%)",
        yaxis_title="",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_rep, use_container_width=True)

# Gráfico 2: Composição do Custo OP (RV vs BH)
with col_g2:
    st.subheader("🧩 Composição de Custos (RV vs BH)")
    
    comp_df = pd.DataFrame({
        'Categoria': ['Remuneração Variável (RV)', 'Banco de Horas (BH)'],
        'Valor': [total_rv, total_bh]
    })
    
    fig_pie = px.pie(
        comp_df,
        values='Valor',
        names='Categoria',
        color_discrete_sequence=['#3B176D', '#F58220'],
        hole=0.4
    )
    fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#FFFFFF', width=2)))
    fig_pie.update_layout(
        height=450,
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.write("---")

# Layout de Gráficos - Linha 2
col_g3, col_g4 = st.columns(2)

# Gráfico 3: Top Operações por Receita Líquida vs Custo OP
with col_g3:
    st.subheader("💰 Receita Líquida vs. Custo OP (Top Operações)")
    df_top_rec = df_filtered[df_filtered['RECEITA_LIQUIDA'] > 0].sort_values(by='RECEITA_LIQUIDA', ascending=False).head(10)
    
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        x=df_top_rec['OPERACAO'],
        y=df_top_rec['RECEITA_LIQUIDA'],
        name='Receita Líquida',
        marker_color='#3B176D'
    ))
    fig_bar.add_trace(go.Bar(
        x=df_top_rec['OPERACAO'],
        y=df_top_rec['CUSTO_OP'],
        name='Custo OP',
        marker_color='#F58220'
    ))
    fig_bar.update_layout(
        barmode='group',
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# Gráfico 4: Custo Médio por Colaborador (HC)
with col_g4:
    st.subheader("👥 Custo OP Médio por Headcount (R$/HC)")
    df_hc_cost = df_filtered[df_filtered['HC_ATIVOS'] > 0].sort_values(by='CUSTO_POR_HC', ascending=False).head(10)
    
    fig_hc = px.bar(
        df_hc_cost,
        x='OPERACAO',
        y='CUSTO_POR_HC',
        text_auto='.2f',
        color_discrete_sequence=['#3B176D']
    )
    fig_hc.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=30, b=10),
        xaxis_title="",
        yaxis_title="R$ / HC Activo",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_hc, use_container_width=True)

st.write("---")

# Tabela Interativa de Dados
st.subheader("📋 Tabela Consolidada de Operações")
st.write("Consulte e ordene os indicadores consolidados de cada operação:")

# Formatação da Tabela para apresentação
df_display = df_filtered.copy()
df_display['RECEITA_LIQUIDA'] = df_display['RECEITA_LIQUIDA'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
df_display['TOTAL_RV'] = df_display['TOTAL_RV'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
df_display['TOTAL_BH'] = df_display['TOTAL_BH'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
df_display['CUSTO_OP'] = df_display['CUSTO_OP'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
df_display['REPRESENTATIVIDADE_PCT'] = df_display['REPRESENTATIVIDADE_PCT'].apply(lambda x: f"{x:.2f}%".replace(".", ","))
df_display['CUSTO_POR_HC'] = df_display['CUSTO_POR_HC'].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

df_display = df_display[['OPERACAO', 'RECEITA_LIQUIDA', 'TOTAL_RV', 'TOTAL_BH', 'CUSTO_OP', 'REPRESENTATIVIDADE_PCT', 'HC_ATIVOS', 'CUSTO_POR_HC']]
df_display.columns = ['Operação', 'Receita Líquida', 'Total RV', 'Total BH', 'Custo OP', 'Representatividade %', 'HCs Ativos', 'Custo / HC']

st.dataframe(df_display, use_container_width=True, hide_index=True)