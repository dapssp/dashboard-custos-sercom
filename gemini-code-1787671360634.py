import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import os
import json
import re
from typing import Optional


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="SERCOM | Executive Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CORES
# ============================================================

BG = "#0E0B16"
CARD = "#161224"
PURPLE = "#3B176D"
PURPLE_LIGHT = "#8B5CF6"
ORANGE = "#F58220"
WHITE = "#FFFFFF"
GRAY = "#94A3B8"
BORDER = "#2B2240"


# ============================================================
# CSS
# ============================================================

st.markdown(
    f"""
    <style>

    .stApp {{
        background-color: {BG};
        color: {WHITE};
    }}

    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }}

    .senior-header {{
        background: linear-gradient(
            135deg,
            #1D0F38 0%,
            #120A24 100%
        );

        padding: 25px 30px;
        border-radius: 14px;
        border-left: 6px solid {ORANGE};
        margin-bottom: 25px;
    }}

    .senior-title {{
        color: {WHITE};
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 5px;
    }}

    .senior-subtitle {{
        color: {GRAY};
        font-size: 0.95rem;
    }}

    div[data-testid="stMetric"] {{
        background-color: {CARD} !important;
        border: 1px solid {BORDER} !important;
        border-radius: 12px !important;
        padding: 16px 18px !important;
        border-top: 3px solid {ORANGE} !important;
    }}

    div[data-testid="stMetricLabel"] p {{
        color: {GRAY} !important;
        font-size: 0.75rem !important;
        font-weight: 700 !important;
    }}

    div[data-testid="stMetricValue"] div {{
        color: {WHITE} !important;
        font-size: 1.3rem !important;
        font-weight: 800 !important;
    }}

    .ai-box {{
        background: linear-gradient(
            135deg,
            #1D0F38,
            #161224
        );

        border: 1px solid #4C2A78;
        border-left: 5px solid {PURPLE_LIGHT};
        border-radius: 12px;
        padding: 22px;
        margin-top: 15px;
        margin-bottom: 25px;
    }}

    .ai-title {{
        color: {PURPLE_LIGHT};
        font-size: 1.1rem;
        font-weight: 800;
        margin-bottom: 12px;
    }}

    .ai-text {{
        color: #E2E8F0;
        line-height: 1.7;
        font-size: 0.95rem;
    }}

    .attention {{
        background-color: #241A16;
        border-left: 4px solid {ORANGE};
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def normalize_text(text):
    """Normaliza texto para facilitar identificação de colunas."""

    if text is None:
        return ""

    text = str(text).strip().upper()

    replacements = {
        "Á": "A",
        "À": "A",
        "Ã": "A",
        "Â": "A",
        "É": "E",
        "Ê": "E",
        "Í": "I",
        "Ó": "O",
        "Ô": "O",
        "Õ": "O",
        "Ú": "U",
        "Ç": "C"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^A-Z0-9]+", "_", text)

    return text.strip("_")


def clean_numeric(series):
    """
    Converte valores financeiros/númericos de forma resiliente.
    """

    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce").fillna(0)

    s = (
        series
        .astype(str)
        .str.strip()
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.replace("%", "", regex=False)
    )

    return pd.to_numeric(s, errors="coerce").fillna(0)


def find_column(df, possible_names):
    """
    Localiza uma coluna mesmo que o Excel tenha pequenas
    diferenças de nomenclatura.
    """

    normalized = {
        normalize_text(col): col
        for col in df.columns
    }

    for name in possible_names:

        key = normalize_text(name)

        if key in normalized:
            return normalized[key]

    # tentativa por aproximação
    for norm_col, original_col in normalized.items():

        for name in possible_names:

            norm_name = normalize_text(name)

            if norm_name in norm_col or norm_col in norm_name:
                return original_col

    return None


# ============================================================
# LEITURA DO EXCEL
# ============================================================

@st.cache_data
def load_excel(file_bytes):

    excel = pd.ExcelFile(io.BytesIO(file_bytes))

    sheets = excel.sheet_names

    # --------------------------------------------------------
    # 1. Tenta CAPA
    # --------------------------------------------------------

    if "CAPA" in sheets:

        raw = pd.read_excel(
            io.BytesIO(file_bytes),
            sheet_name="CAPA",
            header=None
        )

        # procura uma linha contendo OPERAÇÃO
        header_row = None

        for i in range(min(len(raw), 50)):

            row = raw.iloc[i].astype(str).str.upper()

            if row.str.contains("OPERA", na=False).any():

                header_row = i
                break

        if header_row is not None:

            df = pd.read_excel(
                io.BytesIO(file_bytes),
                sheet_name="CAPA",
                header=header_row
            )

            df.columns = [
                normalize_text(c)
                for c in df.columns
            ]

            required = {
                "OPERACAO": [
                    "OPERACAO",
                    "OPERAÇÃO"
                ],

                "TOTAL_RV": [
                    "TOTAL_RV",
                    "TOTAL RV",
                    "RV"
                ],

                "TOTAL_BH": [
                    "TOTAL_BH",
                    "TOTAL BH",
                    "BH"
                ],

                "RECEITA_LIQUIDA": [
                    "RECEITA_LIQUIDA",
                    "RECEITA LIQUIDA",
                    "RECEITA"
                ],

                "CUSTO_OP": [
                    "CUSTO_OP",
                    "CUSTO OP"
                ],

                "HC_ATIVOS": [
                    "QUANTIDADE_HCS_ATIVOS",
                    "HC_ATIVOS",
                    "HEADCOUNT",
                    "HC"
                ]
            }

            result = {}

            for target, options in required.items():

                col = find_column(df, options)

                if col:
                    result[target] = df[col]

            # Se encontrou o essencial
            if (
                "OPERACAO" in result
                and "TOTAL_RV" in result
                and "TOTAL_BH" in result
                and "RECEITA_LIQUIDA" in result
            ):

                final = pd.DataFrame(result)

                # ------------------------------------------------
                # Limpeza
                # ------------------------------------------------

                final["OPERACAO"] = (
                    final["OPERACAO"]
                    .astype(str)
                    .str.strip()
                )

                final = final[
                    ~final["OPERACAO"]
                    .str.upper()
                    .isin([
                        "",
                        "NAN",
                        "TOTAL",
                        "TOTAL GERAL",
                        "OPERACAO"
                    ])
                ]

                # ------------------------------------------------
                # Valores
                # ------------------------------------------------

                for col in [
                    "TOTAL_RV",
                    "TOTAL_BH",
                    "RECEITA_LIQUIDA",
                    "CUSTO_OP",
                    "HC_ATIVOS"
                ]:

                    if col in final:
                        final[col] = clean_numeric(final[col])

                # ------------------------------------------------
                # Cálculos
                # ------------------------------------------------

                # Sempre recalcula Custo OP para garantir
                # consistência com a regra de negócio.

                final["CUSTO_OP"] = (
                    final["TOTAL_RV"] +
                    final["TOTAL_BH"]
                )

                final["REPRESENTATIVIDADE_PCT"] = np.where(
                    final["RECEITA_LIQUIDA"] > 0,
                    (
                        final["CUSTO_OP"] /
                        final["RECEITA_LIQUIDA"]
                    ) * 100,
                    0
                )

                final["CUSTO_POR_HC"] = np.where(
                    final.get("HC_ATIVOS", 0) > 0,
                    final["CUSTO_OP"] /
                    final["HC_ATIVOS"],
                    0
                )

                return final, sheets

    raise ValueError(
        "Não foi possível identificar uma tabela gerencial válida na aba CAPA."
    )


# ============================================================
# MOTOR DE INSIGHTS SEM IA
# ============================================================

def generate_rule_based_insights(df):

    if df.empty:
        return "Não existem dados suficientes para gerar o parecer."

    total_rv = df["TOTAL_RV"].sum()
    total_bh = df["TOTAL_BH"].sum()
    receita = df["RECEITA_LIQUIDA"].sum()
    custo = df["CUSTO_OP"].sum()

    representatividade = (
        custo / receita * 100
        if receita > 0
        else 0
    )

    # --------------------------------------------------------
    # Ranking BH
    # --------------------------------------------------------

    top_bh = (
        df.sort_values(
            "TOTAL_BH",
            ascending=False
        )
        .head(3)
    )

    # --------------------------------------------------------
    # Ranking RV
    # --------------------------------------------------------

    top_rv = (
        df.sort_values(
            "TOTAL_RV",
            ascending=False
        )
        .head(3)
    )

    # --------------------------------------------------------
    # Maior representatividade
    # --------------------------------------------------------

    top_rep = (
        df.sort_values(
            "REPRESENTATIVIDADE_PCT",
            ascending=False
        )
        .head(3)
    )

    # --------------------------------------------------------
    # Construção do parecer
    # --------------------------------------------------------

    texto = []

    texto.append(
        f"O cenário consolidado apresenta Receita Líquida "
        f"de R$ {receita:,.2f}, com Custo Operacional "
        f"de R$ {custo:,.2f}."
    )

    texto.append(
        f"A representatividade consolidada do Custo Operacional "
        f"corresponde a {representatividade:.2f}% da Receita Líquida, "
        f"considerando a referência teórica de 3,0%."
    )

    texto.append(
        f"O total registrado de Remuneração Variável é de "
        f"R$ {total_rv:,.2f}, enquanto o Banco de Horas "
        f"representa R$ {total_bh:,.2f}."
    )

    # --------------------------------------------------------
    # BH
    # --------------------------------------------------------

    if len(top_bh) > 0:

        nomes = ", ".join(
            top_bh["OPERACAO"].head(3).tolist()
        )

        texto.append(
            f"Em relação ao Banco de Horas, as maiores "
            f"concentrações financeiras estão associadas a: "
            f"{nomes}."
        )

    # --------------------------------------------------------
    # RV
    # --------------------------------------------------------

    if len(top_rv) > 0:

        nomes = ", ".join(
            top_rv["OPERACAO"].head(3).tolist()
        )

        texto.append(
            f"Para Remuneração Variável, os maiores valores "
            f"registrados concentram-se em: {nomes}."
        )

    # --------------------------------------------------------
    # Representatividade
    # --------------------------------------------------------

    if len(top_rep) > 0:

        partes = []

        for _, row in top_rep.iterrows():

            partes.append(
                f"{row['OPERACAO']} "
                f"({row['REPRESENTATIVIDADE_PCT']:.2f}%)"
            )

        texto.append(
            "As maiores representatividades observadas são: "
            + ", ".join(partes)
            + "."
        )

    texto.append(
        "A análise é exclusivamente descritiva e considera "
        "os valores disponibilizados no arquivo, sem inferir "
        "a procedência ou a necessidade dos valores registrados."
    )

    return " ".join(texto)


# ============================================================
# GEMINI
# ============================================================

def get_gemini_key():

    try:

        if "GEMINI_API_KEY" in st.secrets:
            return st.secrets["GEMINI_API_KEY"]

    except Exception:
        pass

    return os.getenv("GEMINI_API_KEY")


def generate_gemini_insights(df):

    api_key = get_gemini_key()

    if not api_key:
        return None

    try:

        from google import genai

        client = genai.Client(
            api_key=api_key
        )

        # ----------------------------------------------------
        # Resumo numérico enviado ao modelo
        # ----------------------------------------------------

        data = df.copy()

        numeric_cols = [
            "TOTAL_RV",
            "TOTAL_BH",
            "RECEITA_LIQUIDA",
            "CUSTO_OP",
            "REPRESENTATIVIDADE_PCT",
            "HC_ATIVOS",
            "CUSTO_POR_HC"
        ]

        for col in numeric_cols:

            if col in data:
                data[col] = pd.to_numeric(
                    data[col],
                    errors="coerce"
                ).fillna(0)

        payload = {
            "total_operacoes": int(len(data)),
            "receita_liquida": float(
                data["RECEITA_LIQUIDA"].sum()
            ),
            "total_rv": float(
                data["TOTAL_RV"].sum()
            ),
            "total_bh": float(
                data["TOTAL_BH"].sum()
            ),
            "custo_operacional": float(
                data["CUSTO_OP"].sum()
            ),
            "representatividade_consolidada": float(
                (
                    data["CUSTO_OP"].sum() /
                    data["RECEITA_LIQUIDA"].sum() *
                    100
                )
                if data["RECEITA_LIQUIDA"].sum() > 0
                else 0
            ),
            "operacoes": data.to_dict(
                orient="records"
            )
        }

        prompt = f"""
Você é um analista executivo de planejamento financeiro
da SERCOM.

Analise exclusivamente os dados abaixo.

OBJETIVO:
Produzir um parecer executivo curto, objetivo e
estritamente descritivo.

REGRAS IMPORTANTES:

1. Não afirmar que qualquer valor é errado.
2. Não afirmar que qualquer valor é indevido.
3. Não afirmar que qualquer valor é irregular.
4. Não afirmar fraude.
5. Não afirmar que BH ou RV deveria ser reduzido.
6. Não propor cortes.
7. Não questionar a validade dos critérios utilizados.
8. Não inventar informações.
9. Não criar números que não estejam nos dados.
10. A referência de 3% é apenas uma META TEÓRICA.
11. Sempre analisar Custo Operacional junto da Receita Líquida.
12. O Custo Operacional é:
    TOTAL RV + TOTAL BH.
13. Representatividade:
    CUSTO OP / RECEITA LÍQUIDA * 100.

Dê atenção especial à quantidade e concentração de
Banco de Horas.

Analise:

- Receita Líquida;
- RV;
- BH;
- Custo Operacional;
- Representatividade;
- concentração por operação;
- custo por HC;
- maiores exposições;
- operações próximas ou acima da referência teórica de 3%.

Utilize linguagem executiva.

Use expressões como:

"valor registrado"
"cenário observado"
"exposição financeira"
"concentração"
"representatividade"
"ponto de atenção"

Estrutura da resposta:

1. VISÃO EXECUTIVA
2. BANCO DE HORAS
3. REMUNERAÇÃO VARIÁVEL
4. CUSTO X RECEITA
5. PRINCIPAIS PONTOS DE ATENÇÃO

Não faça recomendações de redução.

DADOS:

{json.dumps(payload, ensure_ascii=False, default=float)}
"""

        response = client.models.generate_content(
            model="gemini-3-flash-preview",
            contents=prompt
        )

        return response.text

    except Exception as e:

        st.session_state["ai_error"] = str(e)

        return None


# ============================================================
# UPLOAD
# ============================================================

st.markdown(
    """
    <div class="senior-header">

        <div class="senior-title">
            SERCOM | Executive Analytics
        </div>

        <div class="senior-subtitle">
            Análise Executiva de Custos Operacionais
            • Banco de Horas • RV • Receita Líquida
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


uploaded_file = st.file_uploader(
    "Carregar arquivo Excel",
    type=["xlsx"]
)


if uploaded_file:

    try:

        file_bytes = uploaded_file.getvalue()

        df, sheets = load_excel(file_bytes)

        st.success(
            f"Arquivo carregado com sucesso • "
            f"{len(df)} operações identificadas"
        )

        # ====================================================
        # SIDEBAR
        # ====================================================

        st.sidebar.header("Filtros")

        operacoes = sorted(
            df["OPERACAO"].dropna().unique().tolist()
        )

        selected_operations = st.sidebar.multiselect(
            "Operações",
            operacoes,
            default=operacoes
        )

        filtered_df = df[
            df["OPERACAO"].isin(
                selected_operations
            )
        ].copy()

        # ====================================================
        # KPIs
        # ====================================================

        receita = filtered_df["RECEITA_LIQUIDA"].sum()
        rv = filtered_df["TOTAL_RV"].sum()
        bh = filtered_df["TOTAL_BH"].sum()
        custo = filtered_df["CUSTO_OP"].sum()

        representatividade = (
            custo / receita * 100
            if receita > 0
            else 0
        )

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "RECEITA LÍQUIDA",
            f"R$ {receita:,.0f}"
        )

        col2.metric(
            "TOTAL RV",
            f"R$ {rv:,.0f}"
        )

        col3.metric(
            "TOTAL BH",
            f"R$ {bh:,.0f}"
        )

        col4.metric(
            "CUSTO OP",
            f"R$ {custo:,.0f}"
        )

        col5.metric(
            "REPRESENTATIVIDADE",
            f"{representatividade:.2f}%"
        )

        st.divider()

        # ====================================================
        # IA
        # ====================================================

        st.subheader("🤖 Parecer Executivo")

        generate_ai = st.button(
            "Gerar análise executiva",
            type="primary"
        )

        if generate_ai:

            with st.spinner(
                "Analisando dados e construindo parecer executivo..."
            ):

                # Primeiro tenta Gemini
                ai_text = generate_gemini_insights(
                    filtered_df
                )

                # Fallback automático
                if not ai_text:

                    ai_text = generate_rule_based_insights(
                        filtered_df
                    )

                    source = "Motor analítico interno"

                else:

                    source = "Gemini"

                st.session_state["ai_text"] = ai_text
                st.session_state["ai_source"] = source

        if "ai_text" in st.session_state:

            st.markdown(
                f"""
                <div class="ai-box">

                    <div class="ai-title">
                        PARECER EXECUTIVO
                    </div>

                    <div class="ai-text">
                        {st.session_state["ai_text"]}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

            st.caption(
                f"Fonte da análise: "
                f"{st.session_state.get('ai_source', '')}"
            )

        # ====================================================
        # GRÁFICO REPRESENTATIVIDADE
        # ====================================================

        st.subheader(
            "Representatividade do Custo Operacional"
        )

        chart_df = (
            filtered_df
            .sort_values(
                "REPRESENTATIVIDADE_PCT",
                ascending=True
            )
        )

        fig = px.bar(
            chart_df,
            x="REPRESENTATIVIDADE_PCT",
            y="OPERACAO",
            orientation="h",
            text="REPRESENTATIVIDADE_PCT"
        )

        fig.add_vline(
            x=3,
            line_dash="dash",
            line_color=ORANGE,
            annotation_text="Referência teórica: 3%"
        )

        fig.update_traces(
            marker_color=PURPLE_LIGHT,
            texttemplate="%{text:.2f}%",
            textposition="outside"
        )

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font_color=WHITE,
            xaxis_title="Representatividade (%)",
            yaxis_title="",
            margin=dict(
                l=10,
                r=40,
                t=30,
                b=20
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ====================================================
        # BH
        # ====================================================

        st.subheader(
            "Banco de Horas — Concentração"
        )

        bh_df = (
            filtered_df[
                [
                    "OPERACAO",
                    "TOTAL_BH",
                    "HC_ATIVOS"
                ]
            ]
            .sort_values(
                "TOTAL_BH",
                ascending=False
            )
        )

        fig_bh = px.bar(
            bh_df,
            x="OPERACAO",
            y="TOTAL_BH",
            text="TOTAL_BH"
        )

        fig_bh.update_traces(
            marker_color=ORANGE
        )

        fig_bh.update_layout(
            template="plotly_dark",
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font_color=WHITE,
            xaxis_title="",
            yaxis_title="Total BH"
        )

        st.plotly_chart(
            fig_bh,
            use_container_width=True
        )

        # ====================================================
        # RV
        # ====================================================

        st.subheader(
            "Remuneração Variável — Distribuição"
        )

        rv_df = (
            filtered_df
            .sort_values(
                "TOTAL_RV",
                ascending=False
            )
        )

        fig_rv = px.bar(
            rv_df,
            x="OPERACAO",
            y="TOTAL_RV",
            text="TOTAL_RV"
        )

        fig_rv.update_traces(
            marker_color=PURPLE_LIGHT
        )

        fig_rv.update_layout(
            template="plotly_dark",
            paper_bgcolor=BG,
            plot_bgcolor=BG,
            font_color=WHITE,
            xaxis_title="",
            yaxis_title="Total RV"
        )

        st.plotly_chart(
            fig_rv,
            use_container_width=True
        )

        # ====================================================
        # TABELA
        # ====================================================

        st.subheader(
            "Visão Consolidada"
        )

        display_df = filtered_df.copy()

        display_df[
            "REPRESENTATIVIDADE"
        ] = display_df[
            "REPRESENTATIVIDADE_PCT"
        ].map(
            lambda x: f"{x:.2f}%"
        )

        display_df[
            "CUSTO_POR_HC"
        ] = display_df[
            "CUSTO_POR_HC"
        ].map(
            lambda x: f"R$ {x:,.2f}"
        )

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )

        # ====================================================
        # DOWNLOAD
        # ====================================================

        csv = filtered_df.to_csv(
            index=False
        ).encode("utf-8-sig")

        st.download_button(
            "Baixar dados filtrados",
            csv,
            "sercom_analytics.csv",
            "text/csv"
        )

    except Exception as e:

        st.error(
            "Não foi possível processar o arquivo."
        )

        with st.expander(
            "Detalhes técnicos"
        ):
            st.exception(e)

else:

    st.info(
        "Carregue um arquivo Excel para iniciar a análise."
    )
