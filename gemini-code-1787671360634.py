import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configuração da página
st.set_page_config(
    page_title="SERCOM | Dashboard Executivo Dark",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Personalizada - DARK MODE EXEC (Fundo Escuro Grafite #0E0B16)
st.markdown("""
    <style>
    /* Estilo Global Dark */
    .stApp {
        background-color: #0E0B16;
        color: #E2E8F0;
    }
    
    /* Cards Executivos */
    .kpi-card {
        background-color: #1A162B;
        border: 1px solid #2D2545;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        border-top: 3px solid #F58220;
    }
    .kpi-label {
        font-size: 0.8rem;
        font-weight: 600;
        color: #A0AEC0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-top: 4px;
        white-space: nowrap;
    }
    .kpi-sub {
        font-size: 0.75rem;
        color: #F58220;
        margin-top: 2px;
    }

    /* Container e Cabeçalho */
    .executive-header {
        background: linear-gradient(90deg, #1D0F38 0%, #0E0B16 100%);
        padding: 20px 24px;
        border-radius: 8px;
        border-left: 5px solid #F58220;
        margin-bottom: 24px;
    }
    .executive-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #FFFFFF;
        margin: 0;
    }
    .executive-subtitle {
        font-size: 0.85rem;
        color: #A0AEC0;
        margin-top: 4px;
    }
    
    /* Ajustes da Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #141021;
        border-right: 1px solid #2D2545;
    }
    
    /* Abas */
    button[data-baseweb="tab"] {
        color: #A0AEC0 !important;
        font-weight: 600;
    }
    button[aria-selected="true"] {
        color: #F58220 !important;
        border-bottom-color: #F58220 !important;
    }
    </style>
""", unsafe_allow_html=True)

# Função para carregar e tratar os dados
@st.cache_data
def load_data(file):
    df_capa = pd.read_excel(file, sheet_name='CAPA')
    
    summary_cols = ['Unnamed: 30', 'Unnamed: 31', 'Unnamed: 32', 'Unnamed: 33', 'Unnamed: 34', 'Unnamed: 35', 'Unnamed: 36']
    df_summary = df_capa[summary_cols].dropna(how='all')
    df_summary.columns = ['OPERACAO', 'TOTAL_RV', 'TOTAL_BH', 'RECEITA_LIQUIDA', 'CUSTO_OP', 'REPRESENTATIVIDADE', 'HC_ATIVOS']
    
    df_summary = df_summary[df_summary['OPERACAO'] != 'OPERAÇÃO'].reset_index(drop=True)
    
    cols_num = ['TOTAL_RV', 'TOTAL_BH', 'RECEITA_LIQUIDA', 'CUSTO_OP', 'HC_ATIVOS']
    for col in cols_num:
        df_summary[col] = pd.to_numeric(df_summary[col], errors='coerce').fillna(0)
    
    df_summary['OPERACAO'] = df_summary['OPERACAO'].astype(str).str.strip()
    
    df_summary['REPRESENTATIVIDADE_PCT'] = df_summary.apply(
        lambda row: (row['CUSTO_OP'] / row['RECEITA_LIQUIDA'] * 100) if row['RECEITA_LIQUIDA'] > 0 else 0, axis=1
    )
    
    df_summary['CUSTO_POR_HC'] = df_summary.apply(
        lambda row: (row['CUSTO_OP'] / row['HC_ATIVOS']) if row['HC_ATIVOS'] > 0 else 0, axis=1
    )
    
    return df_summary

# Carregamento dos dados
try:
    data = load_data('Analise colaboradores.xlsx')
except Exception:
    st.error("Por favor, verifique se o arquivo 'Analise colaboradores.xlsx' está na pasta.")
    st.stop()

# Sidebar - Upload e Filtros
st.sidebar.markdown("### ⚙️ Painel de Controle")
uploaded_file = st.sidebar.file_uploader("Substituir Planilha (.xlsx)", type=['xlsx'])
if uploaded_file is not None:
    data = load_data(uploaded_file)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Filtro Geral")
op_filter = st.sidebar.multiselect(
    "Operações Visíveis:",
    options=list(data['OPERACAO'].unique()),
    default=list(data['OPERACAO'].unique())
)

df_filtered = data[data['OPERACAO'].isin(op_filter)]

# Header
st.markdown("""
    <div class="executive-header">
        <div class="executive-title">Painel Executivo de Custos Operacionais</div>
        <div class="executive-subtitle">Análise Consolidada & Por Operação: Receita Líquida, Banco de Horas (BH) e Remuneração Variável (RV)</div>
    </div>
""", unsafe_allow_html=True)

# KPIs Consolidados do Filtro
t_rec = df_filtered['RECEITA_LIQUIDA'].sum()
t_custo = df_filtered['CUSTO_OP'].sum()
t_rv = df_filtered['TOTAL_RV'].sum()
t_bh = df_filtered['TOTAL_BH'].sum()
t_hc = df_filtered['HC_ATIVOS'].sum()
t_rep = (t_custo / t_rec * 100) if t_rec > 0 else 0

k1, k2, k3, k4, k5 = st.columns(5)

def fmt_brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

with k1:
    st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Receita Líquida</div><div class="kpi-value">{fmt_brl(t_rec)}</div></div>''', unsafe_allow_html=True)
with k2:
    st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Custo OP Total</div><div class="kpi-value">{fmt_brl(t_custo)}</div></div>''', unsafe_allow_html=True)
with k3:
    st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Total RV</div><div class="kpi-value">{fmt_brl(t_rv)}</div></div>''', unsafe_allow_html=True)
with k4:
    st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Total BH</div><div class="kpi-value">{fmt_brl(t_bh)}</div></div>''', unsafe_allow_html=True)
with k5:
    st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Representatividade</div><div class="kpi-value">{t_rep:.2f}%</div><div class="kpi-sub">Ref. Teórica: 3,0%</div></div>''', unsafe_allow_html=True)

st.write("")
st.write("")

# Abas do Dashboard
tab1, tab2, tab3 = st.tabs([
    "🔍 Visão Detalhada por Operação", 
    "📊 Comparativo & Representatividade (3,0%)", 
    "📋 Matriz Consolidada"
])

# ABA 1: VISÃO INDIVIDUAL POR OPERAÇÃO
with tab1:
    st.markdown("### 🔎 Detalhamento Individual da Operação")
    
    # Dropdown para selecionar a Operação
    selected_op = st.selectbox(
        "Selecione uma Operação para analisar em detalhe:",
        options=sorted(df_filtered['OPERACAO'].unique()),
        index=0
    )
    
    op_data = df_filtered[df_filtered['OPERACAO'] == selected_op].iloc[0]
    
    st.write("")
    
    # Cards da Operação Selecionada
    c1, c2, c3, c4, c5 = st.columns(5)
    
    op_rec = op_data['RECEITA_LIQUIDA']
    op_custo = op_data['CUSTO_OP']
    op_rv = op_data['TOTAL_RV']
    op_bh = op_data['TOTAL_BH']
    op_rep = op_data['REPRESENTATIVIDADE_PCT']
    op_hc = op_data['HC_ATIVOS']
    op_c_hc = op_data['CUSTO_POR_HC']
    
    status_color = "#34D399" if op_rep <= 3.0 else "#F58220"
    status_text = "DENTRO DA REF. (≤ 3.0%)" if op_rep <= 3.0 else "ACIMA DA REF. (> 3.0%)"
    if op_rec == 0:
        status_text = "SEM RECEITA REGISTRADA"
        status_color = "#A0AEC0"

    with c1:
        st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Receita Operação</div><div class="kpi-value">{fmt_brl(op_rec)}</div></div>''', unsafe_allow_html=True)
    with c2:
        st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Custo OP Operação</div><div class="kpi-value">{fmt_brl(op_custo)}</div></div>''', unsafe_allow_html=True)
    with c3:
        st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Representatividade</div><div class="kpi-value">{op_rep:.2f}%</div><div class="kpi-sub" style="color: {status_color}; font-weight: bold;">{status_text}</div></div>''', unsafe_allow_html=True)
    with c4:
        st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Headcount (HC)</div><div class="kpi-value">{int(op_hc)} Ativos</div></div>''', unsafe_allow_html=True)
    with c5:
        st.markdown(f'''<div class="kpi-card"><div class="kpi-label">Custo Médio / HC</div><div class="kpi-value">{fmt_brl(op_c_hc)}</div></div>''', unsafe_allow_html=True)

    st.write("")
    st.write("")
    
    # Gráficos da Operação
    g_op1, g_op2 = st.columns(2)
    
    with g_op1:
        st.markdown(f"#### Composição do Custo em **{selected_op}**")
        df_op_comp = pd.DataFrame({
            'Tipo': ['Remuneração Variável (RV)', 'Banco de Horas (BH)'],
            'Valor': [op_rv, op_bh]
        })
        if op_custo > 0:
            fig_op_pie = px.pie(
                df_op_comp,
                values='Valor',
                names='Tipo',
                color_discrete_sequence=['#6D28D9', '#F58220'],
                hole=0.5
            )
            fig_op_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#E2E8F0'),
                height=320
            )
            st.plotly_chart(fig_op_pie, use_container_width=True)
        else:
            st.info("Esta operação não possui Custo OP registrado.")
            
    with g_op2:
        st.markdown(f"#### Comparativo com Operações Semelhantes")
        df_same = df_filtered[df_filtered['RECEITA_LIQUIDA'] > 0].sort_values(by='CUSTO_OP', ascending=False).head(8)
        
        fig_comp_bar = px.bar(
            df_same,
            x='OPERACAO',
            y='CUSTO_OP',
            color='OPERACAO',
            color_discrete_map={selected_op: '#F58220'},
            color_discrete_sequence=['#3B176D']
        )
        fig_comp_bar.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#E2E8F0'),
            showlegend=False,
            height=320,
            xaxis_title="",
            yaxis_title="Custo OP (R$)"
        )
        st.plotly_chart(fig_comp_bar, use_container_width=True)

# ABA 2: COMPARATIVO GERAL
with tab2:
    st.markdown("### 📊 Comparativo Geral de Operações")
    
    col_a, col_b = st.columns([6, 4])
    
    with col_a:
        st.markdown("#### Ranking de Representatividade % (Com Ref. Teórica 3,0%)")
        df_rep = df_filtered[df_filtered['RECEITA_LIQUIDA'] > 0].sort_values(by='REPRESENTATIVIDADE_PCT', ascending=True)
        
        colors = ['#F58220' if val > 3.0 else '#6D28D9' for val in df_rep['REPRESENTATIVIDADE_PCT']]
        
        fig_rep = go.Figure()
        fig_rep.add_trace(go.Bar(
            y=df_rep['OPERACAO'],
            x=df_rep['REPRESENTATIVIDADE_PCT'],
            orientation='h',
            marker_color=colors,
            text=[f"{v:.2f}%".replace(".", ",") for v in df_rep['REPRESENTATIVIDADE_PCT']],
            textposition='outside'
        ))
        
        fig_rep.add_vline(x=3.0, line_dash="dash", line_color="#EF4444", annotation_text=" Ref. 3,0%", annotation_position="top right")
        
        fig_rep.update_layout(
            height=500,
            margin=dict(l=10, r=20, t=20, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#E2E8F0'),
            xaxis_title="Representatividade (%)",
            yaxis_title=""
        )
        st.plotly_chart(fig_rep, use_container_width=True)
        
    with col_b:
        st.markdown("#### Top 8 Custo Médio / HC (R$)")
        df_hc_sort = df_filtered[df_filtered['HC_ATIVOS'] > 0].sort_values(by='CUSTO_POR_HC', ascending=False).head(8)
        
        fig_hc_top = px.bar(
            df_hc_sort,
            x='CUSTO_POR_HC',
            y='OPERACAO',
            orientation='h',
            text_auto='.2f',
            color_discrete_sequence=['#F58220']
        )
        fig_hc_top.update_layout(
            height=500,
            margin=dict(l=10, r=20, t=20, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#E2E8F0'),
            xaxis_title="Custo / HC (R$)",
            yaxis_title="",
            yaxis=dict(autorange="reversed")
        )
        st.plotly_chart(fig_hc_top, use_container_width=True)

# ABA 3: MATRIZ COMPLETA
with tab3:
    st.markdown("### 📋 Matriz Consolidada de Dados")
    
    df_grid = df_filtered.copy()
    df_grid['RECEITA_LIQUIDA'] = df_grid['RECEITA_LIQUIDA'].apply(fmt_brl)
    df_grid['TOTAL_RV'] = df_grid['TOTAL_RV'].apply(fmt_brl)
    df_grid['TOTAL_BH'] = df_grid['TOTAL_BH'].apply(fmt_brl)
    df_grid['CUSTO_OP'] = df_grid['CUSTO_OP'].apply(fmt_brl)
    df_grid['REPRESENTATIVIDADE_PCT'] = df_grid['REPRESENTATIVIDADE_PCT'].apply(lambda x: f"{x:.2f}%".replace(".", ","))
    df_grid['CUSTO_POR_HC'] = df_grid['CUSTO_POR_HC'].apply(fmt_brl)

    df_grid = df_grid[['OPERACAO', 'RECEITA_LIQUIDA', 'TOTAL_RV', 'TOTAL_BH', 'CUSTO_OP', 'REPRESENTATIVIDADE_PCT', 'HC_ATIVOS', 'CUSTO_POR_HC']]
    df_grid.columns = ['Operação', 'Receita Líquida', 'Total RV', 'Total BH', 'Custo OP', 'Representatividade %', 'HCs Ativos', 'Custo / HC']

    st.dataframe(df_grid, use_container_width=True, hide_index=True)
