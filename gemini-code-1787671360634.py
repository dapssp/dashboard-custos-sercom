import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA & TEMA CORPORATIVO
# ---------------------------------------------------------
st.set_page_config(
    page_title="SERCOM | Governança de Custos Operacionais",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS para Estética Executiva (Light Mode Corporativo / C-Level)
st.markdown("""
    <style>
    /* Reset & Background Geral */
    .stApp {
        background-color: #F4F6F9 !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #1E293B;
    }
    
    /* Header Principal Executivo */
    .exec-header {
        background: linear-gradient(135deg, #260E4C 0%, #3B176D 100%);
        padding: 24px 32px;
        border-radius: 12px;
        color: #FFFFFF;
        box-shadow: 0 4px 20px rgba(38, 14, 76, 0.15);
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .exec-title {
        font-size: 1.8rem;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin: 0;
        color: #FFFFFF;
    }
    .exec-subtitle {
        font-size: 0.95rem;
        color: #E2E8F0;
        font-weight: 300;
        margin-top: 4px;
    }
    .exec-badge {
        background: rgba(245, 130, 32, 0.2);
        border: 1px solid #F58220;
        color: #F58220;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }

    /* Cards de KPI Customizados (Sem Truncamento de Texto) */
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 18px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.03);
        border-top: 4px solid #3B176D;
        transition: transform 0.2s ease;
    }
    .kpi-card.accent {
        border-top: 4px solid #F58220;
    }
    .kpi-label {
        font-size: 0.78rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 1.35rem;
        font-weight: 700;
        color: #0F172A;
        line-height: 1.2;
        white-space: nowrap;
    }
    .kpi-sub {
        font-size: 0.75rem;
        color: #94A3B8;
        margin-top: 4px;
    }

    /* Cards de Seção/Gráfico */
    .chart-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
        margin-bottom: 20px;
    }
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #260E4C;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        border-bottom: 2px solid #F1F5F9;
        padding-bottom: 8px;
    }

    /* Ajuste de Abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #E2E8F0;
        padding: 4px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 6px;
        color: #475569;
        font-weight: 600;
        font-size: 0.88rem;
    }
    .stTabs [aria-selected="true"] {
        background-color: #3B176D !important;
        color: #FFFFFF !important;
    }

    /* Sidebar Customizada */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2E8F0;
    }
    </style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# 2. CARREGAMENTO E TRATAMENTO DOS DADOS
# ---------------------------------------------------------
@st.cache_data
def load_data(file_source):
    df_capa = pd.read_excel(file_source, sheet_name='CAPA')
    
    # Extração da Tabela Sumarizada
    summary_cols = ['Unnamed: 30', 'Unnamed: 31', 'Unnamed: 32', 'Unnamed: 33', 'Unnamed: 34', 'Unnamed: 35', 'Unnamed: 36']
    df_summary = df_capa[summary_cols].dropna(how='all')
    df_summary.columns = ['OPERACAO', 'TOTAL_RV', 'TOTAL_BH', 'RECEITA_LIQUIDA', 'CUSTO_OP', 'REPRESENTATIVIDADE', 'HC_ATIVOS']
    
    # Limpeza do cabeçalho original
    df_summary = df_summary[df_summary['OPERACAO'] != 'OPERAÇÃO'].reset_index(drop=True)
    
    # Conversões Numéricas
    cols_num = ['TOTAL_RV', 'TOTAL_BH', 'RECEITA_LIQUIDA', 'CUSTO_OP', 'HC_ATIVOS']
    for col in cols_num:
        df_summary[col] = pd.to_numeric(df_summary[col], errors='coerce').fillna(0)
    
    df_summary['OPERACAO'] = df_summary['OPERACAO'].astype(str).str.strip()
    
    # Recálculo preciso de % de Representatividade e Custo por HC
    df_summary['REPRESENTATIVIDADE_PCT'] = df_summary.apply(
        lambda r: (r['CUSTO_OP'] / r['RECEITA_LIQUIDA'] * 100) if r['RECEITA_LIQUIDA'] > 0 else 0, axis=1
    )
    df_summary['CUSTO_POR_HC'] = df_summary.apply(
        lambda r: (r['CUSTO_OP'] / r['HC_ATIVOS']) if r['HC_ATIVOS'] > 0 else 0, axis=1
    )
    df_summary['BH_POR_HC'] = df_summary.apply(
        lambda r: (r['TOTAL_BH'] / r['HC_ATIVOS']) if r['HC_ATIVOS'] > 0 else 0, axis=1
    )
    
    return df_summary

# ---------------------------------------------------------
# 3. NAVEGAÇÃO E FILTROS NA SIDEBAR
# ---------------------------------------------------------
st.sidebar.markdown("### SERCOM | BI Executivo")
st.sidebar.caption("Fotografia Gerencial de Custos")
st.sidebar.markdown("---")

uploaded_file = st.sidebar.file_uploader("Upload de Base (.xlsx)", type=['xlsx'])

if uploaded_file is not None:
    data = load_data(uploaded_file)
else:
    try:
        data = load_data('Analise colaboradores.xlsx')
    except Exception:
        st.error("Por favor, importe a planilha 'Analise colaboradores.xlsx'.")
        st.stop()

# Filtros Executivos
st.sidebar.markdown("#### Filtros da Análise")
eixo_view = st.sidebar.radio("Escopo de Visualização:", ["Todas as Operações", "Apenas Operações com Receita Líquida"])

if eixo_view == "Apenas Operações com Receita Líquida":
    data_scope = data[data['RECEITA_LIQUIDA'] > 0]
else:
    data_scope = data

selected_ops = st.sidebar.multiselect(
    "Filtrar por Operação:",
    options=list(data_scope['OPERACAO'].unique()),
    default=list(data_scope['OPERACAO'].unique())
)

df_filtered = data_scope[data_scope['OPERACAO'].isin(selected_ops)]

# ---------------------------------------------------------
# 4. HEADER EXECUTIVO
# ---------------------------------------------------------
st.markdown("""
    <div class="exec-header">
        <div>
            <div class="exec-title">Relatório Gerencial de Custos Operacionais</div>
            <div class="exec-subtitle">Análise Consolidada: Receita Líquida, Banco de Horas (BH) e Remuneração Variável (RV)</div>
        </div>
        <div class="exec-badge">BASE OFICIAL SERCOM</div>
    </div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. CARDS DE KPI EXECUTIVOS (FORMATADOS & SEM TRUNCAR)
# ---------------------------------------------------------
tot_rec = df_filtered['RECEITA_LIQUIDA'].sum()
tot_op = df_filtered['CUSTO_OP'].sum()
tot_rv = df_filtered['TOTAL_RV'].sum()
tot_bh = df_filtered['TOTAL_BH'].sum()
tot_hc = df_filtered['HC_ATIVOS'].sum()
rep_global = (tot_op / tot_rec * 100) if tot_rec > 0 else 0

def fmt_brl(val):
    return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Receita Líquida Total</div>
            <div class="kpi-value">{fmt_brl(tot_rec)}</div>
            <div class="kpi-sub">Escopo: {len(df_filtered)} Operações</div>
        </div>
    """, unsafe_allow_html=True)

with c2:
    st.markdown(f"""
        <div class="kpi-card accent">
            <div class="kpi-label">Custo OP Registrado</div>
            <div class="kpi-value">{fmt_brl(tot_op)}</div>
            <div class="kpi-sub">RV Total + BH Total</div>
        </div>
    """, unsafe_allow_html=True)

with c3:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Banco de Horas (BH)</div>
            <div class="kpi-value">{fmt_brl(tot_bh)}</div>
            <div class="kpi-sub">{(tot_bh/tot_op*100 if tot_op>0 else 0):.1f}% do Custo OP</div>
        </div>
    """, unsafe_allow_html=True)

with c4:
    st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Remuneração Variável</div>
            <div class="kpi-value">{fmt_brl(tot_rv)}</div>
            <div class="kpi-sub">{(tot_rv/tot_op*100 if tot_op>0 else 0):.1f}% do Custo OP</div>
        </div>
    """, unsafe_allow_html=True)

with c5:
    st.markdown(f"""
        <div class="kpi-card accent">
            <div class="kpi-label">Representatividade %</div>
            <div class="kpi-value">{rep_global:.2f}%</div>
            <div class="kpi-sub">Ref. Teórica: 3,00%</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 6. ESTRUTURA EM ABAS EXECUTIVAS
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    " Visão Geral & Proporcionalidade",
    " Ranking de Representatividade (Ref. 3.0%)",
    " Composição (BH vs. RV)",
    " Matriz Consolidada de Dados"
])

# ---------------------------------------------------------
# TAB 1: VISÃO GERAL & PROPORCIONALIDADE
# ---------------------------------------------------------
with tab1:
    g1, g2 = st.columns([6, 4])
    
    with g1:
        st.markdown('<div class="section-header">Receita Líquida vs. Custo OP Registrado por Operação</div>', unsafe_allow_html=True)
        
        df_top10 = df_filtered[df_filtered['RECEITA_LIQUIDA'] > 0].sort_values(by='RECEITA_LIQUIDA', ascending=False).head(10)
        
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=df_top10['OPERACAO'],
            y=df_top10['RECEITA_LIQUIDA'],
            name='Receita Líquida',
            marker_color='#3B176D',
            hovertemplate='<b>%{x}</b><br>Receita: R$ %{y:,.2f}<extra></extra>'
        ))
        fig1.add_trace(go.Bar(
            x=df_top10['OPERACAO'],
            y=df_top10['CUSTO_OP'],
            name='Custo OP (RV+BH)',
            marker_color='#F58220',
            hovertemplate='<b>%{x}</b><br>Custo OP: R$ %{y:,.2f}<extra></extra>'
        ))
        
        fig1.update_layout(
            barmode='group',
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(gridcolor='#E2E8F0')
        )
        st.plotly_chart(fig1, use_container_width=True)

    with g2:
        st.markdown('<div class="section-header">Distribuição do Custo OP por Headcount (R$/HC)</div>', unsafe_allow_html=True)
        
        df_hc = df_filtered[df_filtered['HC_ATIVOS'] > 0].sort_values(by='CUSTO_POR_HC', ascending=False).head(8)
        
        fig2 = px.bar(
            df_hc,
            x='CUSTO_POR_HC',
            y='OPERACAO',
            orientation='h',
            color_discrete_sequence=['#3B176D'],
            text_auto='.0f'
        )
        fig2.update_traces(textposition='outside')
        fig2.update_layout(
            height=380,
            margin=dict(l=10, r=20, t=20, b=10),
            xaxis_title="Custo OP por HC (R$)",
            yaxis_title="",
            yaxis=dict(autorange="reversed"),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig2, use_container_width=True)

# ---------------------------------------------------------
# TAB 2: RANKING DE REPRESENTATIVIDADE (REF 3.0%)
# ---------------------------------------------------------
with tab2:
    st.markdown('<div class="section-header">Percentual de Representatividade sobre a Receita Líquida</div>', unsafe_allow_html=True)
    st.caption("Nota Metodológica: O parâmetro de 3,0% é utilizado estritamente como linha teórica de referência gerencial para comparabilidade entre operações.")
    
    df_rep = df_filtered[df_filtered['RECEITA_LIQUIDA'] > 0].sort_values(by='REPRESENTATIVIDADE_PCT', ascending=True)
    
    colors = ['#F58220' if val > 3.0 else '#3B176D' for val in df_rep['REPRESENTATIVIDADE_PCT']]
    
    fig_rep = go.Figure()
    fig_rep.add_trace(go.Bar(
        y=df_rep['OPERACAO'],
        x=df_rep['REPRESENTATIVIDADE_PCT'],
        orientation='h',
        marker_color=colors,
        text=[f"{v:.2f}%".replace(".", ",") for v in df_rep['REPRESENTATIVIDADE_PCT']],
        textposition='outside'
    ))
    
    fig_rep.add_vline(
        x=3.0,
        line_dash="dash",
        line_color="#EF4444",
        line_width=2,
        annotation_text="Referência Teórica (3,0%)",
        annotation_position="top right"
    )
    
    fig_rep.update_layout(
        height=520,
        margin=dict(l=10, r=40, t=20, b=10),
        xaxis_title="Representatividade (%)",
        yaxis_title="",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig_rep, use_container_width=True)

# ---------------------------------------------------------
# TAB 3: COMPOSIÇÃO DE CUSTOS (BH vs RV)
# ---------------------------------------------------------
with tab3:
    c_left, c_right = st.columns(2)
    
    with c_left:
        st.markdown('<div class="section-header">Top Operações com Maior Lançamento de Banco de Horas (BH)</div>', unsafe_allow_html=True)
        df_bh_top = df_filtered.sort_values(by='TOTAL_BH', ascending=False).head(8)
        
        fig_bh = px.bar(
            df_bh_top,
            x='OPERACAO',
            y='TOTAL_BH',
            color_discrete_sequence=['#F58220'],
            text_auto='.2s'
        )
        fig_bh.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="",
            yaxis_title="Total BH (R$)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_bh, use_container_width=True)
        
    with c_right:
        st.markdown('<div class="section-header">Distribuição de Remuneração Variável (RV) Registrada</div>', unsafe_allow_html=True)
        df_rv_top = df_filtered[df_filtered['TOTAL_RV'] > 0].sort_values(by='TOTAL_RV', ascending=False)
        
        fig_rv = px.bar(
            df_rv_top,
            x='OPERACAO',
            y='TOTAL_RV',
            color_discrete_sequence=['#3B176D'],
            text_auto='.2s'
        )
        fig_rv.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=20, b=10),
            xaxis_title="",
            yaxis_title="Total RV (R$)",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_rv, use_container_width=True)

# ---------------------------------------------------------
# TAB 4: MATRIZ CONSOLIDADA DE DADOS
# ---------------------------------------------------------
with tab4:
    st.markdown('<div class="section-header">Matriz Gerencial Consolidada por Operação</div>', unsafe_allow_html=True)
    
    df_grid = df_filtered.copy()
    
    # Ordenação por Custo OP decrescente
    df_grid = df_grid.sort_values(by='CUSTO_OP', ascending=False)
    
    # Formatação das colunas para visualização executiva
    df_grid['RECEITA_LIQUIDA'] = df_grid['RECEITA_LIQUIDA'].apply(fmt_brl)
    df_grid['TOTAL_RV'] = df_grid['TOTAL_RV'].apply(fmt_brl)
    df_grid['TOTAL_BH'] = df_grid['TOTAL_BH'].apply(fmt_brl)
    df_grid['CUSTO_OP'] = df_grid['CUSTO_OP'].apply(fmt_brl)
    df_grid['CUSTO_POR_HC'] = df_grid['CUSTO_POR_HC'].apply(fmt_brl)
    df_grid['REPRESENTATIVIDADE_PCT'] = df_grid['REPRESENTATIVIDADE_PCT'].apply(lambda x: f"{x:.2f}%".replace(".", ","))
    
    df_grid = df_grid[['OPERACAO', 'RECEITA_LIQUIDA', 'TOTAL_RV', 'TOTAL_BH', 'CUSTO_OP', 'REPRESENTATIVIDADE_PCT', 'HC_ATIVOS', 'CUSTO_POR_HC']]
    df_grid.columns = ['Operação', 'Receita Líquida', 'Total RV', 'Total BH', 'Custo OP (RV+BH)', 'Representatividade (%)', 'HCs Ativos', 'Custo OP / HC']
    
    st.dataframe(df_grid, use_container_width=True, hide_index=True)
    
    # Botão de exportação
    csv_data = df_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Exportar Base Consolidada (CSV)",
        data=csv_data,
        file_name="SERCOM_Analise_Custos_Operacionais.csv",
        mime="text/csv"
    )
