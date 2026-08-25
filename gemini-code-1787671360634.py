import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# ==========================================
# CONFIGURAÇÃO DA APLICAÇÃO & DESIGN SYSTEM
# ==========================================
st.set_page_config(
    page_title="SERCOM | Executive AI Cost Center Analytics",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Senior Dark Mode (Paleta Roxo Royal #0E0B16 + Laranja SERCOM #F58220)
st.markdown("""
    <style>
    /* Estilo Global Dark */
    .stApp {
        background-color: #0E0B16;
        color: #E2E8F0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Header Principal com Badge de IA */
    .senior-header {
        background: linear-gradient(135deg, #1D0F38 0%, #120A24 100%);
        padding: 22px 28px;
        border-radius: 12px;
        border: 1px solid #2D2545;
        border-left: 6px solid #F58220;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
    }
    .senior-title {
        font-size: 1.6rem;
        font-weight: 800;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .senior-subtitle {
        font-size: 0.85rem;
        color: #94A3B8;
        margin-top: 6px;
    }
    .ai-badge {
        background: linear-gradient(90deg, #F58220 0%, #E65100 100%);
        color: #FFFFFF;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.8px;
    }

    /* Cards de KPI Reativos */
    div[data-testid="stMetric"] {
        background-color: #161224 !important;
        border: 1px solid #2B2240 !important;
        border-radius: 10px !important;
        padding: 14px 18px !important;
        border-top: 3px solid #F58220 !important;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4) !important;
        transition: transform 0.2s ease;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        border-color: #F58220 !important;
    }
    div[data-testid="stMetricLabel"] p {
        color: #94A3B8 !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #FFFFFF !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
    }
    div[data-testid="stMetricDelta"] {
        color: #F58220 !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
    }

    /* AI Insight Box */
    .ai-insight-card {
        background: linear-gradient(135deg, #1A102F 0%, #0F0A1C 100%);
        border: 1px solid #3B176D;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        border-left: 4px solid #8B5CF6;
    }
    
    /* Abas */
    button[data-baseweb="tab"] {
        color: #94A3B8 !important;
        font-weight: 600;
        font-size: 0.9rem;
    }
    button[aria-selected="true"] {
        color: #F58220 !important;
        border-bottom-color: #F58220 !important;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #120D1F;
        border-right: 1px solid #231B36;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# PIPELINE ETL AUTOMÁTICO (SELF-HEALING)
# ==========================================
class DataPipeline:
    """Pipeline para parsing, limpeza, resiliência de schemas e consolidação."""
    
    @staticmethod
    @st.cache_data(ttl=600)
    def process_excel(file_path_or_buffer):
        xls = pd.ExcelFile(file_path_or_buffer)
        
        # Estratégia 1: Extrair Resumo Consolidado da Capa (se disponível)
        if 'CAPA' in xls.sheet_names:
            df_capa = pd.read_excel(file_path_or_buffer, sheet_name='CAPA')
            
            # Algoritmo de Varredura Dinâmica para localizar a Tabela Gerencial
            summary_cols = ['Unnamed: 30', 'Unnamed: 31', 'Unnamed: 32', 'Unnamed: 33', 'Unnamed: 34', 'Unnamed: 35', 'Unnamed: 36']
            if set(summary_cols).issubset(df_capa.columns):
                df_summary = df_capa[summary_cols].dropna(how='all').copy()
                df_summary.columns = ['OPERACAO', 'TOTAL_RV', 'TOTAL_BH', 'RECEITA_LIQUIDA', 'CUSTO_OP', 'REPRESENTATIVIDADE', 'HC_ATIVOS']
                df_summary = df_summary[df_summary['OPERACAO'] != 'OPERAÇÃO'].reset_index(drop=True)
                
                # Coerção de tipos de dados numéricos
                num_cols = ['TOTAL_RV', 'TOTAL_BH', 'RECEITA_LIQUIDA', 'CUSTO_OP', 'HC_ATIVOS']
                for c in num_cols:
                    df_summary[c] = pd.to_numeric(df_summary[c], errors='coerce').fillna(0)
                
                df_summary['OPERACAO'] = df_summary['OPERACAO'].astype(str).str.strip()
                
                # Recálculo sintético de garantia
                df_summary['REPRESENTATIVIDADE_PCT'] = df_summary.apply(
                    lambda r: (r['CUSTO_OP'] / r['RECEITA_LIQUIDA'] * 100) if r['RECEITA_LIQUIDA'] > 0 else 0, axis=1
                )
                df_summary['CUSTO_POR_HC'] = df_summary.apply(
                    lambda r: (r['CUSTO_OP'] / r['HC_ATIVOS']) if r['HC_ATIVOS'] > 0 else 0, axis=1
                )
                
                return df_summary

        # Fallback de Segurança: Agregação em tempo real das abas brutas se a Capa falhar
        st.warning("⚠️ Módulo de Fallback Ativado: Processando dados brutos diretamente das abas operacionais...")
        return DataPipeline._reconstruct_from_raw(xls)

    @staticmethod
    def _reconstruct_from_raw(xls):
        # Leitura da Base de Horas
        df_bh = pd.read_excel(xls, sheet_name='BASE DE HORAS')
        grp_bh = df_bh.groupby('Descricao')['valor'].sum().reset_index()
        grp_bh.columns = ['OPERACAO', 'TOTAL_BH']
        
        # Leitura dos Ativos
        df_hc = pd.read_excel(xls, sheet_name='ATIVOS E DEMITIDOS')
        grp_hc = df_hc[df_hc['STATUS_ST'] == 'ATIVO'].groupby('DESC_CC')['MATRICULA'].nunique().reset_index()
        grp_hc.columns = ['OPERACAO', 'HC_ATIVOS']
        
        # Merge de contingência
        merged = pd.merge(grp_bh, grp_hc, on='OPERACAO', how='outer').fillna(0)
        merged['TOTAL_RV'] = 0.0
        merged['RECEITA_LIQUIDA'] = 0.0
        merged['CUSTO_OP'] = merged['TOTAL_BH'] + merged['TOTAL_RV']
        merged['REPRESENTATIVIDADE_PCT'] = 0.0
        merged['CUSTO_POR_HC'] = merged.apply(lambda r: (r['CUSTO_OP'] / r['HC_ATIVOS']) if r['HC_ATIVOS'] > 0 else 0, axis=1)
        
        return merged

# ==========================================
# AGENTE DE INTELIGÊNCIA ARTIFICIAL (AI ENGINE)
# ==========================================
class AIAgentEngine:
    """Motor de análise preditiva e geração de insights executivos via LLM."""
    
    @staticmethod
    def generate_executive_insights(df_filtered, api_key=None):
        total_rec = df_filtered['RECEITA_LIQUIDA'].sum()
        total_custo = df_filtered['CUSTO_OP'].sum()
        rep_geral = (total_custo / total_rec * 100) if total_rec > 0 else 0
        acima_ref = df_filtered[df_filtered['REPRESENTATIVIDADE_PCT'] > 3.0]['OPERACAO'].tolist()
        top_custo_op = df_filtered.sort_values(by='CUSTO_OP', ascending=False).iloc[0]['OPERACAO'] if len(df_filtered) > 0 else "N/A"
        
        # Prompt heurístico estruturado para IA
        prompt = f"""
        Como um especialista senior em Control Desk, FP&A e Business Intelligence da SERCOM, analise estes dados de fechamento:
        - Receita Líquida Total: R$ {total_rec:,.2f}
        - Custo Operacional Total (RV + BH): R$ {total_custo:,.2f}
        - Representatividade Média do Custo sobre a Receita: {rep_geral:.2f}% (Benchmark Referência: 3,0%)
        - Operações que excederam o Benchmark de 3,0%: {', '.join(acima_ref) if acima_ref else 'Nenhuma'}
        - Maior Custo Operacional Absoluto: {top_custo_op}

        Gere um parecer executivo neutro, direto e de alto nível em 3 tópicos curtos:
        1. Resumo da Exposição Financeira
        2. Destaques de Proporcionalidade (Referência Teórica 3,0%)
        3. Ponto de Atenção para Tomada de Decisão Gerencial
        """
        
        # Tenta integração com API da OpenAI se fornecida, caso contrário usa síntese local determinística
        if api_key and len(api_key) > 10:
            try:
                import openai
                client = openai.OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300
                )
                return response.choices[0].message.content
            except Exception as e:
                return f"⚠️ Erro ao consultar a API do LLM: {str(e)}. Exibindo síntese determinística da IA."
        
        # Síntese determinística nativa da IA (sem necessidade de API key)
        return f"""
        **1. Exposição Financeira Global:** O custo operacional consolidado é de **R$ {total_custo:,.2f}**, representando **{rep_geral:.2f}%** da Receita Líquida Total de R$ {total_rec:,.2f}.
        
        **2. Proporcionalidade vs Benchmark (3,0%):** Foram identificadas **{len(acima_ref)} operações** com representatividade superior ao marco teórico de 3,0%, com destaque para a concentração de volume na operação **{top_custo_op}**.
        
        **3. Ponto de Atenção Executivo:** Recomenda-se acompanhamento pontual da variação do Banco de Horas (BH) nas contas que superam a meta teórica para avaliar a distribuição de horas por operador sem comprometer a margem das operações.
        """

# ==========================================
# CARREGAMENTO DE DADOS & INTERFACE
# ==========================================
file_name = 'Analise colaboradores.xlsx'

# Sidebar do Dev Senior
st.sidebar.markdown("### 🛠️ Dev & AI Management")
st.sidebar.caption("Pipeline Status: **ONLINE (v2.4-ai)**")

uploaded_file = st.sidebar.file_uploader("📥 Alimentar Nova Base (.xlsx)", type=['xlsx'])
target_file = uploaded_file if uploaded_file else file_name

# Configuração da API Key de IA (Opcional)
openai_key = st.sidebar.text_input("🔑 OpenAI API Key (Opcional p/ LLM):", type="password", help="Insira sua chave para ativar insights dinâmicos GPT-4. Se vazio, a IA usará seu algoritmo nativo.")

try:
    data = DataPipeline.process_excel(target_file)
except Exception as e:
    st.error(f"Erro crítico no processamento do arquivo: {str(e)}")
    st.stop()

# Filtro Multiselect
st.sidebar.markdown("---")
st.sidebar.markdown("### 🎯 Filtro de Escopo")
all_ops = sorted(data['OPERACAO'].unique())
selected_ops = st.sidebar.multiselect("Selecione Operações:", options=all_ops, default=all_ops)

df_filtered = data[data['OPERACAO'].isin(selected_ops)]

# Header Executivo
st.markdown("""
    <div class="senior-header">
        <div class="senior-title">
            SERCOM Executive Cost Center Analytics 
            <span class="ai-badge">AI Engine Active</span>
        </div>
        <div class="senior-subtitle">
            Arquitetura de BI Resiliente | Monitoramento de Receita Líquida, Banco de Horas (BH) e Remuneração Variável (RV)
        </div>
    </div>
""", unsafe_allow_html=True)

# KPIs Consolidados
t_rec = df_filtered['RECEITA_LIQUIDA'].sum()
t_custo = df_filtered['CUSTO_OP'].sum()
t_rv = df_filtered['TOTAL_RV'].sum()
t_bh = df_filtered['TOTAL_BH'].sum()
t_rep = (t_custo / t_rec * 100) if t_rec > 0 else 0

def fmt_brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

k1, k2, k3, k4, k5 = st.columns(5)
with k1: st.metric("Receita Líquida", fmt_brl(t_rec))
with k2: st.metric("Custo OP Total", fmt_brl(t_custo))
with k3: st.metric("Total RV Registrada", fmt_brl(t_rv))
with k4: st.metric("Total BH Registrado", fmt_brl(t_bh))
with k5: st.metric("Representatividade", f"{t_rep:.2f}%".replace(".", ","), delta="Ref. Teórica: 3,0%")

st.write("")

# Módulo de Análise Inteligente de IA (AI Insights)
with st.expander("🤖 **AI Executive Summary & Diagnóstico Preditivo**", expanded=True):
    col_ai_1, col_ai_2 = st.columns([8, 2])
    with col_ai_1:
        ai_insights = AIAgentEngine.generate_executive_insights(df_filtered, openai_key)
        st.markdown(f'<div class="ai-insight-card">{ai_insights}</div>', unsafe_allow_html=True)
    with col_ai_2:
        st.markdown("##### AI Controls")
        if st.button("🔄 Regenerar Análise", use_container_width=True):
            st.rerun()
        
        # Download do relatório em JSON
        json_data = df_filtered.to_json(orient="records")
        st.download_button(
            label="📥 Exportar Data Set (JSON)",
            data=json_data,
            file_name="sercom_cost_center_ai.json",
            mime="application/json",
            use_container_width=True
        )

# Abas de Análise
tab1, tab2, tab3 = st.tabs([
    "🔍 Ficha Detalhada por Operação", 
    "📊 Benchmarking & Proporcionalidade (3,0%)", 
    "📋 Matriz Consolidada de Dados"
])

# ABA 1: DRILL-DOWN POR OPERAÇÃO
with tab1:
    st.markdown("### 🔎 Análise Individualizada de Operação")
    selected_op = st.selectbox("Selecione a Operação para Drill-down:", options=sorted(df_filtered['OPERACAO'].unique()), index=0)
    
    op_row = df_filtered[df_filtered['OPERACAO'] == selected_op].iloc[0]
    
    op_rec = op_row['RECEITA_LIQUIDA']
    op_custo = op_row['CUSTO_OP']
    op_rv = op_row['TOTAL_RV']
    op_bh = op_row['TOTAL_BH']
    op_rep = op_row['REPRESENTATIVIDADE_PCT']
    op_hc = op_row['HC_ATIVOS']
    op_c_hc = op_row['CUSTO_POR_HC']
    
    delta_str = "≤ 3.0% (Dentro da Meta)" if op_rep <= 3.0 else "> 3.0% (Acima da Ref.)"
    if op_rec == 0: delta_str = "Sem Receita Registrada"

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.metric("Receita da Operação", fmt_brl(op_rec))
    with c2: st.metric("Custo OP Operação", fmt_brl(op_custo))
    with c3: st.metric("Representatividade %", f"{op_rep:.2f}%".replace(".", ","), delta=delta_str)
    with c4: st.metric("Headcount (HC)", f"{int(op_hc)} Colaboradores")
    with c5: st.metric("Custo Médio / HC", fmt_brl(op_c_hc))

    st.write("")
    g1, g2 = st.columns(2)
    with g1:
        st.markdown(f"#### Decomposição do Custo em **{selected_op}**")
        if op_custo > 0:
            fig_pie = px.pie(
                names=['Remuneração Variável (RV)', 'Banco de Horas (BH)'],
                values=[op_rv, op_bh],
                color_discrete_sequence=['#8B5CF6', '#F58220'],
                hole=0.55
            )
            fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'), height=320)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("Operação sem registro de Custo OP.")
            
    with g2:
        st.markdown(f"#### Comparativo de Custo OP com Operações Pares")
        df_peers = df_filtered[df_filtered['RECEITA_LIQUIDA'] > 0].sort_values(by='CUSTO_OP', ascending=False).head(8)
        fig_peers = px.bar(
            df_peers,
            x='OPERACAO',
            y='CUSTO_OP',
            color='OPERACAO',
            color_discrete_map={selected_op: '#F58220'},
            color_discrete_sequence=['#3B176D']
        )
        fig_peers.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'), showlegend=False, height=320)
        st.plotly_chart(fig_peers, use_container_width=True)

# ABA 2: BENCHMARKING
with tab2:
    st.markdown("### 📊 Benchmarking & Exposição Financeira")
    ba, bb = st.columns([6, 4])
    
    with ba:
        st.markdown("#### Representatividade % vs. Benchmark Teórico (3,0%)")
        df_rep = df_filtered[df_filtered['RECEITA_LIQUIDA'] > 0].sort_values(by='REPRESENTATIVIDADE_PCT', ascending=True)
        colors = ['#F58220' if val > 3.0 else '#8B5CF6' for val in df_rep['REPRESENTATIVIDADE_PCT']]
        
        fig_rep = go.Figure(go.Bar(
            y=df_rep['OPERACAO'],
            x=df_rep['REPRESENTATIVIDADE_PCT'],
            orientation='h',
            marker_color=colors,
            text=[f"{v:.2f}%".replace(".", ",") for v in df_rep['REPRESENTATIVIDADE_PCT']],
            textposition='outside'
        ))
        fig_rep.add_vline(x=3.0, line_dash="dash", line_color="#EF4444", annotation_text=" Ref. Teórica (3,0%)", annotation_position="top right")
        fig_rep.update_layout(height=520, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'))
        st.plotly_chart(fig_rep, use_container_width=True)
        
    with bb:
        st.markdown("#### Top 8 Custo Médio por Headcount (R$/HC)")
        df_hc_top = df_filtered[df_filtered['HC_ATIVOS'] > 0].sort_values(by='CUSTO_POR_HC', ascending=False).head(8)
        fig_hc = px.bar(
            df_hc_top,
            x='CUSTO_POR_HC',
            y='OPERACAO',
            orientation='h',
            text_auto='.2f',
            color_discrete_sequence=['#F58220']
        )
        fig_hc.update_layout(height=520, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#E2E8F0'), yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_hc, use_container_width=True)

# ABA 3: TABELA AUDITÁVEL
with tab3:
    st.markdown("### 📋 Tabela Gerencial Auditável")
    
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
