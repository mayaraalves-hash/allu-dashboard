import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SHEET_ID   = '1QdYSZhC77JkkyTTAImVWZiZiC_D6gl6qknlcG53Tuww'
SHEET_NAME = 'CONTROLE DE COMPRAS - CAPEX'
CREDS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'credenciais.json')
SCOPES     = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
]

# Cores da Allu
COR_PRIMARIA   = '#00C853'
COR_SECUNDARIA = '#1A1A1A'
COR_ACENTO     = '#69F0AE'
CORES_GRAFICOS = ['#00C853', '#69F0AE', '#00E676', '#B9F6CA', '#1B5E20', '#43A047', '#81C784']

st.set_page_config(
    page_title='Dashboard Compras CAPEX | Allu',
    page_icon='allu',
    layout='wide',
    initial_sidebar_state='collapsed',
)

st.markdown(f"""
<style>
    [data-testid="collapsedControl"] {{ display: none; }}
    section[data-testid="stSidebar"] {{ display: none; }}
    .stApp {{ background-color: #F7F8FA; font-family: 'Inter', sans-serif; }}

    /* header */
    .main-header {{
        background: white;
        border-bottom: 2px solid {COR_PRIMARIA};
        padding: 20px 28px 16px;
        border-radius: 8px;
        margin-bottom: 20px;
    }}
    .main-header h1 {{ color: #111; margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.3px; }}
    .main-header p  {{ color: #999; margin: 4px 0 0; font-size: 12px; }}

    /* filtros */
    .stExpander {{
        background: white !important;
        border: 1px solid #E8E8E8 !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        margin-bottom: 16px !important;
    }}
    .stExpander summary {{
        font-size: 13px !important;
        font-weight: 500 !important;
        color: #555 !important;
        padding: 10px 16px !important;
    }}

    /* multiselect */
    .stMultiSelect > div > div {{
        background: white !important;
        border: 1px solid #E0E0E0 !important;
        border-radius: 6px !important;
        min-height: 36px !important;
        box-shadow: none !important;
    }}
    .stMultiSelect > div > div:hover {{ border-color: {COR_PRIMARIA} !important; }}
    .stMultiSelect > div > div:focus-within {{ border-color: {COR_PRIMARIA} !important; box-shadow: 0 0 0 2px rgba(0,200,83,0.12) !important; }}
    .stMultiSelect label {{ font-size: 11px !important; font-weight: 600 !important; color: #999 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; }}
    .stMultiSelect [data-baseweb="tag"] {{ background: {COR_PRIMARIA} !important; color: white !important; border-radius: 4px !important; font-size: 11px !important; }}
    .stMultiSelect input::placeholder {{ color: #bbb !important; font-size: 13px !important; }}

    /* date input */
    .stDateInput label {{ font-size: 11px !important; font-weight: 600 !important; color: #999 !important; text-transform: uppercase !important; letter-spacing: 0.5px !important; }}
    .stDateInput > div > div {{ border: 1px solid #E0E0E0 !important; border-radius: 6px !important; background: white !important; }}
    .stDateInput > div > div:focus-within {{ border-color: {COR_PRIMARIA} !important; }}

    /* KPI cards */
    [data-testid="metric-container"] {{
        background: white;
        border-radius: 8px;
        padding: 16px !important;
        border: 1px solid #F0F0F0;
        border-top: 2px solid {COR_PRIMARIA};
    }}
    [data-testid="metric-container"] label {{ color: #999; font-size: 11px; text-transform: uppercase; letter-spacing: 0.4px; }}
    [data-testid="metric-container"] [data-testid="stMetricValue"] {{ color: #111; font-weight: 700; font-size: 22px; }}

    /* produto cards */
    .produto-card {{
        background: white;
        border-radius: 8px;
        padding: 14px 16px;
        border: 1px solid #F0F0F0;
        border-top: 2px solid {COR_PRIMARIA};
        height: 100%;
    }}
    .produto-card .prod-nome {{ font-weight: 600; font-size: 12px; color: #222; margin-bottom: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .produto-card .prod-forn {{ font-size: 11px; color: #aaa; margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
    .produto-card .prod-qtd {{ font-size: 24px; font-weight: 700; color: {COR_PRIMARIA}; line-height: 1; }}
    .produto-card .prod-qtd-label {{ font-size: 11px; color: #bbb; margin-top: 2px; }}
    .produto-card .prod-valor {{ font-size: 12px; color: #666; margin-top: 8px; }}

    /* abas */
    .stTabs [data-baseweb="tab-list"] {{ gap: 0; border-bottom: 1px solid #eee; background: white; border-radius: 8px 8px 0 0; padding: 0 16px; }}
    .stTabs [data-baseweb="tab"] {{ font-weight: 500; font-size: 14px; padding: 12px 16px; color: #999; border-bottom: 2px solid transparent; }}
    .stTabs [aria-selected="true"] {{ color: #111 !important; border-bottom: 2px solid {COR_PRIMARIA} !important; background: transparent !important; font-weight: 600 !important; }}

    /* botão */
    div.stButton > button {{ background: {COR_PRIMARIA}; color: white; border: none; border-radius: 6px; font-weight: 600; font-size: 13px; padding: 8px 18px; width: 100%; }}
    div.stButton > button:hover {{ background: #00A846; color: white; }}

    /* tabela e divisores */
    .stDataFrame {{ border-radius: 8px; overflow: hidden; border: 1px solid #F0F0F0; }}
    hr {{ border-color: #F0F0F0; margin: 16px 0; }}
</style>
""", unsafe_allow_html=True)


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def parse_currency(val):
    if val is None or val == '':
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(s)
    except Exception:
        return 0.0


def parse_int(val):
    if val is None or val == '':
        return 0
    try:
        return int(str(val).replace('.', '').replace(',', '').split('.')[0])
    except Exception:
        return 0


def fmt_brl(valor):
    return f'R$ {valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


# ─── DADOS ────────────────────────────────────────────────────────────────────

# Limites aprovados — usar nomes normalizados (após agrupamento)
LIMITES = {
    'GLOBAL DISTRIBUICAO (iPlace)': 6_000_000,
    'FAST SHOP S.A':                2_500_000,
    'FAST SHOP S.A.':               2_500_000,
}


@st.cache_data(ttl=300)
def load_sap_data():
    if 'gcp_service_account' in st.secrets:
        creds = Credentials.from_service_account_info(
            dict(st.secrets['gcp_service_account']), scopes=SCOPES
        )
    else:
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    ws     = client.open_by_key(SHEET_ID).worksheet('SAP_ABERTO')

    # Lê com valores brutos (sem formatação) para garantir números corretos
    raw = ws.get_all_values()
    if not raw:
        return pd.DataFrame()
    headers = [h.strip().upper() for h in raw[0]]
    df = pd.DataFrame(raw[1:], columns=headers)

    # Converte colunas numéricas: remove R$, pontos de milhar, troca vírgula por ponto
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df


@st.cache_data(ttl=300)
def load_data():
    # No Streamlit Cloud lê das secrets; localmente lê do arquivo
    if 'gcp_service_account' in st.secrets:
        creds = Credentials.from_service_account_info(
            dict(st.secrets['gcp_service_account']), scopes=SCOPES
        )
    else:
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client = gspread.authorize(creds)
    ws     = client.open_by_key(SHEET_ID).worksheet(SHEET_NAME)
    df     = pd.DataFrame(ws.get_all_records())

    df.columns = [c.strip().upper() for c in df.columns]

    for col in ['PREÇO TOTAL', 'PREÇO UNITÁRIO', 'VALOR PARCELAS']:
        if col in df.columns:
            df[col] = df[col].apply(parse_currency)

    for col in ['QUANTIDADE COMPRADA', 'QUANTIDADE RECEBIDA']:
        if col in df.columns:
            df[col] = df[col].apply(parse_int)

    if 'LEAD TIME' in df.columns:
        df['LEAD TIME'] = pd.to_numeric(
            df['LEAD TIME'].astype(str).str.replace(',', '.', regex=False),
            errors='coerce'
        )

    for col in ['DATA DA COMPRA', 'DATA DE RECEBIMENTO', 'PREVISÃO DE COMPRA']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], dayfirst=True, errors='coerce')

    if 'DATA DA COMPRA' in df.columns:
        df['ANO']     = df['DATA DA COMPRA'].dt.year
        df['ANO_MES'] = df['DATA DA COMPRA'].dt.to_period('M').astype(str)

    if 'FORNECEDOR' in df.columns:
        df = df[df['FORNECEDOR'].astype(str).str.strip() != '']

    return df


# ─── HEADER ───────────────────────────────────────────────────────────────────

col_titulo, col_btn = st.columns([6, 1])
with col_titulo:
    st.markdown("""
    <div class="main-header">
        <div>
            <h1>allu. &nbsp;|&nbsp; Dashboard Compras CAPEX</h1>
            <p>Atualização automática a cada 5 minutos</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_btn:
    st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)
    if st.button('Atualizar'):
        st.cache_data.clear()
        st.rerun()

# ─── CARREGAR DADOS ───────────────────────────────────────────────────────────

try:
    df = load_data()
except Exception as e:
    st.error(f'Erro ao carregar dados: {e}')
    st.stop()

if df.empty:
    st.warning('Nenhum dado encontrado na planilha.')
    st.stop()

# ─── FILTROS (lista suspensa — vazio = todos) ─────────────────────────────────

with st.expander('Filtros', expanded=False):
    st.caption('Deixe em branco para considerar todos. Selecione para filtrar.')

    # Linha 1: período com calendário
    fd1, fd2 = st.columns(2)
    data_min = df['DATA DA COMPRA'].min().date() if 'DATA DA COMPRA' in df.columns and df['DATA DA COMPRA'].notna().any() else None
    data_max = df['DATA DA COMPRA'].max().date() if 'DATA DA COMPRA' in df.columns and df['DATA DA COMPRA'].notna().any() else None
    with fd1:
        data_inicio = st.date_input('Data início', value=data_min, min_value=data_min, max_value=data_max, key='f_data_ini', format='DD/MM/YYYY')
    with fd2:
        data_fim = st.date_input('Data fim', value=data_max, min_value=data_min, max_value=data_max, key='f_data_fim', format='DD/MM/YYYY')

    st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

    # Linha 2: demais filtros
    fc1, fc2, fc3, fc4 = st.columns(4)

    fornecedores = sorted(df['FORNECEDOR'].dropna().unique().tolist()) if 'FORNECEDOR' in df.columns else []
    with fc1:
        forn_sel = st.multiselect('Fornecedor', fornecedores, default=[], placeholder='Todos', key='f_forn')

    filiais = sorted(df['FILIAL'].dropna().unique().tolist()) if 'FILIAL' in df.columns else []
    with fc2:
        filial_sel = st.multiselect('Filial', filiais, default=[], placeholder='Todos', key='f_filial')

    formas_pag = sorted(df['FORMA DE PAGAMENTO'].dropna().unique().tolist()) if 'FORMA DE PAGAMENTO' in df.columns else []
    with fc3:
        fp_sel = st.multiselect('Forma de Pagamento', formas_pag, default=[], placeholder='Todos', key='f_fp')

    anos = sorted(df['ANO'].dropna().unique().astype(int).tolist(), reverse=True) if 'ANO' in df.columns else []
    with fc4:
        ano_sel = st.multiselect('Ano', anos, default=[], placeholder='Todos', key='f_ano')

# Aplicar filtros — lista vazia significa "sem filtro" (mostra tudo)
df_f = df.copy()
if 'DATA DA COMPRA' in df_f.columns and data_min and data_max:
    df_f = df_f[
        (df_f['DATA DA COMPRA'].dt.date >= data_inicio) &
        (df_f['DATA DA COMPRA'].dt.date <= data_fim)
    ]
if ano_sel:
    df_f = df_f[df_f['ANO'].isin(ano_sel)]
if forn_sel:
    df_f = df_f[df_f['FORNECEDOR'].isin(forn_sel)]
if filial_sel:
    df_f = df_f[df_f['FILIAL'].isin(filial_sel)]
if fp_sel:
    df_f = df_f[df_f['FORMA DE PAGAMENTO'].isin(fp_sel)]

# ─── ABAS ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3 = st.tabs(['Visão Geral', 'Logística', 'Créditos em Aberto'])

# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════
with tab1:

    # ── KPIs gerais ──────────────────────────────────────────────────────────
    total_valor    = df_f['PREÇO TOTAL'].sum() if 'PREÇO TOTAL' in df_f.columns else 0
    total_qtd      = df_f['QUANTIDADE COMPRADA'].sum() if 'QUANTIDADE COMPRADA' in df_f.columns else 0
    n_fornecedores = df_f['FORNECEDOR'].nunique() if 'FORNECEDOR' in df_f.columns else 0
    # Lead time: apenas itens já recebidos (com DATA DE RECEBIMENTO preenchida)
    df_recebidos   = df_f[df_f['DATA DE RECEBIMENTO'].notna()] if 'DATA DE RECEBIMENTO' in df_f.columns else df_f
    lead_medio     = df_recebidos['LEAD TIME'].mean() if 'LEAD TIME' in df_recebidos.columns else None
    n_pedidos      = len(df_f)

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric('Volume Total', fmt_brl(total_valor))
    k2.metric('Qtd Comprada', f'{int(total_qtd):,}'.replace(',', '.'))
    k3.metric('Fornecedores', n_fornecedores)
    k4.metric('Pedidos', n_pedidos)
    k5.metric('Lead Time Médio', f'{lead_medio:.1f} dias' if lead_medio and not pd.isna(lead_medio) else 'N/A')

    st.markdown('<br>', unsafe_allow_html=True)

    # ── Cards por produto ─────────────────────────────────────────────────────
    if 'PRODUTO' in df_f.columns and 'QUANTIDADE COMPRADA' in df_f.columns:
        st.markdown('##### Resumo por Produto')

        top_produtos = (
            df_f.groupby(['PRODUTO', 'FORNECEDOR'])
            .agg(qtd=('QUANTIDADE COMPRADA', 'sum'), valor=('PREÇO TOTAL', 'sum'))
            .reset_index()
            .sort_values('qtd', ascending=False)
            .head(8)
        )

        cols_prod = st.columns(min(len(top_produtos), 4))
        for i, (_, row) in enumerate(top_produtos.iterrows()):
            with cols_prod[i % 4]:
                nome    = str(row['PRODUTO'])[:40]
                forn    = str(row['FORNECEDOR'])[:30]
                qtd     = int(row['qtd'])
                valor   = fmt_brl(row['valor'])
                qtd_fmt = f'{qtd:,}'.replace(',', '.')
                st.markdown(f"""
                <div class="produto-card">
                    <div class="prod-nome" title="{row['PRODUTO']}">{nome}</div>
                    <div class="prod-forn">{forn}</div>
                    <div class="prod-qtd">{qtd_fmt}</div>
                    <div class="prod-qtd-label">unidades compradas</div>
                    <div class="prod-valor">{valor}</div>
                </div>
                """, unsafe_allow_html=True)

        # segunda linha se houver mais de 4 produtos
        if len(top_produtos) > 4:
            st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
            cols_prod2 = st.columns(min(len(top_produtos) - 4, 4))
            for i, (_, row) in enumerate(top_produtos.iloc[4:].iterrows()):
                with cols_prod2[i % 4]:
                    nome  = str(row['PRODUTO'])[:40]
                    forn  = str(row['FORNECEDOR'])[:30]
                    qtd   = int(row['qtd'])
                    valor = fmt_brl(row['valor'])
                    qtd_fmt = f'{qtd:,}'.replace(',', '.')
                    st.markdown(f"""
                    <div class="produto-card">
                        <div class="prod-nome" title="{row['PRODUTO']}">{nome}</div>
                        <div class="prod-forn">{forn}</div>
                        <div class="prod-qtd">{qtd_fmt}</div>
                        <div class="prod-qtd-label">unidades compradas</div>
                        <div class="prod-valor">{valor}</div>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown('<br>', unsafe_allow_html=True)

    # ── Gráficos ──────────────────────────────────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        if 'FORNECEDOR' in df_f.columns and 'PREÇO TOTAL' in df_f.columns:
            by_forn = (
                df_f.groupby('FORNECEDOR')['PREÇO TOTAL']
                .sum().reset_index()
                .sort_values('PREÇO TOTAL', ascending=True)
                .tail(15)
            )
            fig = px.bar(
                by_forn, x='PREÇO TOTAL', y='FORNECEDOR', orientation='h',
                title='Volume por Fornecedor (R$)',
                labels={'PREÇO TOTAL': 'Total (R$)', 'FORNECEDOR': ''},
                color_discrete_sequence=[COR_PRIMARIA],
            )
            fig.update_layout(height=400, plot_bgcolor='white', paper_bgcolor='white',
                              title_font_color=COR_SECUNDARIA)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if 'FORMA DE PAGAMENTO' in df_f.columns and 'PREÇO TOTAL' in df_f.columns:
            by_fp = (
                df_f[df_f['FORMA DE PAGAMENTO'].astype(str).str.strip() != '']
                .groupby('FORMA DE PAGAMENTO')['PREÇO TOTAL']
                .sum().reset_index()
            )
            fig2 = px.pie(
                by_fp, values='PREÇO TOTAL', names='FORMA DE PAGAMENTO',
                title='Volume por Forma de Pagamento',
                color_discrete_sequence=CORES_GRAFICOS,
                hole=0.4,
            )
            fig2.update_layout(height=400, paper_bgcolor='white',
                               title_font_color=COR_SECUNDARIA)
            st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        if 'ANO_MES' in df_f.columns and 'PREÇO TOTAL' in df_f.columns:
            by_mes = (
                df_f.groupby('ANO_MES')['PREÇO TOTAL']
                .sum().reset_index()
                .sort_values('ANO_MES')
            )
            fig3 = px.bar(
                by_mes, x='ANO_MES', y='PREÇO TOTAL',
                title='Volume Mensal (R$)',
                labels={'ANO_MES': '', 'PREÇO TOTAL': 'Total (R$)'},
                color_discrete_sequence=[COR_PRIMARIA],
            )
            fig3.update_layout(height=350, plot_bgcolor='white', paper_bgcolor='white',
                               title_font_color=COR_SECUNDARIA)
            st.plotly_chart(fig3, use_container_width=True)

    with col4:
        if 'FORNECEDOR' in df_f.columns and 'QUANTIDADE COMPRADA' in df_f.columns:
            by_forn_q = (
                df_f.groupby('FORNECEDOR')['QUANTIDADE COMPRADA']
                .sum().reset_index()
                .sort_values('QUANTIDADE COMPRADA', ascending=True)
                .tail(15)
            )
            fig4 = px.bar(
                by_forn_q, x='QUANTIDADE COMPRADA', y='FORNECEDOR', orientation='h',
                title='Quantidade Comprada por Fornecedor',
                labels={'QUANTIDADE COMPRADA': 'Qtd', 'FORNECEDOR': ''},
                color_discrete_sequence=[COR_ACENTO],
            )
            fig4.update_layout(height=350, plot_bgcolor='white', paper_bgcolor='white',
                               title_font_color=COR_SECUNDARIA)
            st.plotly_chart(fig4, use_container_width=True)

    # Lead time — somente itens recebidos
    if 'FORNECEDOR' in df_recebidos.columns and 'LEAD TIME' in df_recebidos.columns:
        st.markdown('### Lead Time Médio por Fornecedor')
        lt_forn = (
            df_recebidos.groupby('FORNECEDOR')['LEAD TIME']
            .mean().dropna().round(1).reset_index()
            .sort_values('LEAD TIME', ascending=False)
        )
        lt_forn.columns = ['Fornecedor', 'Lead Time Médio (dias)']
        fig5 = px.bar(
            lt_forn, x='Fornecedor', y='Lead Time Médio (dias)',
            color='Lead Time Médio (dias)',
            color_continuous_scale=['#00C853', '#69F0AE', '#FFB347', '#D32F2F'],
        )
        fig5.update_layout(height=350, plot_bgcolor='white', paper_bgcolor='white',
                           coloraxis_showscale=False)
        st.plotly_chart(fig5, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — LOGÍSTICA
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('### Produtos a Chegar')

    hoje = pd.Timestamp.today().normalize()

    if 'DATA DE RECEBIMENTO' not in df_f.columns:
        st.info('Coluna "DATA DE RECEBIMENTO" não encontrada na planilha.')
    else:
        # Pendentes = quantidade recebida vazia ou zero
        pendentes = df_f[
            df_f['QUANTIDADE RECEBIDA'].isna() | (df_f['QUANTIDADE RECEBIDA'] == 0)
        ].copy() if 'QUANTIDADE RECEBIDA' in df_f.columns else df_f[df_f['DATA DE RECEBIMENTO'].isna()].copy()

        # Lead time médio: apenas itens recebidos do histórico completo
        df_hist_recebidos = df[df['DATA DE RECEBIMENTO'].notna()] if 'DATA DE RECEBIMENTO' in df.columns else df
        if 'LEAD TIME' in df_hist_recebidos.columns and 'FORNECEDOR' in df_hist_recebidos.columns:
            lt_medio = (
                df_hist_recebidos.groupby('FORNECEDOR')['LEAD TIME']
                .mean().round(1).reset_index()
            )
            lt_medio.columns = ['FORNECEDOR', 'LEAD TIME MÉDIO (dias)']
            pendentes = pendentes.merge(lt_medio, on='FORNECEDOR', how='left')

        if 'PREVISÃO DE COMPRA' in pendentes.columns:
            def status(row):
                prev = row.get('PREVISÃO DE COMPRA')
                if pd.isna(prev):
                    return '🟡 Sem previsão'
                return '🔴 Atrasado' if prev < hoje else '🟢 No prazo'
            pendentes['STATUS'] = pendentes.apply(status, axis=1)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric('Pedidos Pendentes', len(pendentes))
        qtd_pendente = int(pendentes['QUANTIDADE COMPRADA'].sum()) if 'QUANTIDADE COMPRADA' in pendentes.columns else 0
        k2.metric('Ativos a Chegar', f'{qtd_pendente:,}'.replace(',', '.'))
        atrasados = len(pendentes[pendentes.get('STATUS', pd.Series(dtype=str)) == '🔴 Atrasado']) if 'STATUS' in pendentes.columns else 0
        k3.metric('Atrasados', atrasados)
        valor_pendente = pendentes['PREÇO TOTAL'].sum() if 'PREÇO TOTAL' in pendentes.columns else 0
        k4.metric('Valor em Trânsito', fmt_brl(valor_pendente))

        st.divider()

        # Busca coluna de previsão por substring (ignora acentuação exata)
        COL_PREVISAO = next(
            (c for c in pendentes.columns if 'PREVIS' in c.upper()),
            None
        )

        COLS_LOG = [
            'STATUS', 'FILIAL', 'FORNECEDOR', 'PRODUTO',
            'DATA DA COMPRA',
        ]
        if COL_PREVISAO:
            COLS_LOG.append(COL_PREVISAO)
        COLS_LOG += ['QUANTIDADE COMPRADA', 'LEAD TIME MÉDIO (dias)']

        cols_show = [c for c in COLS_LOG if c in pendentes.columns]
        df_show   = pendentes[cols_show].copy()

        # Renomeia para exibição
        rename_map = {'DATA DA COMPRA': 'Data da Compra'}
        if COL_PREVISAO:
            rename_map[COL_PREVISAO] = 'Previsão de Entrega'
        df_show = df_show.rename(columns=rename_map)

        for dc in ['Data da Compra', 'Previsão de Entrega']:
            if dc in df_show.columns:
                df_show[dc] = pd.to_datetime(df_show[dc], errors='coerce').dt.strftime('%d/%m/%Y').fillna('-')

        if 'PREÇO TOTAL' in df_show.columns:
            df_show['PREÇO TOTAL'] = df_show['PREÇO TOTAL'].apply(
                lambda x: fmt_brl(x) if isinstance(x, float) else '-'
            )

        if 'STATUS' in df_show.columns:
            df_show = df_show.sort_values('STATUS')

        st.dataframe(df_show, use_container_width=True, hide_index=True)

        # Gráfico: Qtd a chegar por Filial + Fornecedor
        if 'FORNECEDOR' in pendentes.columns and 'FILIAL' in pendentes.columns and 'QUANTIDADE COMPRADA' in pendentes.columns:
            graf_forn = (
                pendentes.groupby(['FILIAL', 'FORNECEDOR'])['QUANTIDADE COMPRADA']
                .sum().reset_index()
                .sort_values('QUANTIDADE COMPRADA', ascending=False)
            )
            fig_p = px.bar(
                graf_forn, x='FORNECEDOR', y='QUANTIDADE COMPRADA', color='FILIAL',
                title='Qtd a Chegar por Fornecedor e Filial',
                labels={'QUANTIDADE COMPRADA': 'Qtd', 'FORNECEDOR': '', 'FILIAL': 'Filial'},
                color_discrete_sequence=CORES_GRAFICOS,
            )
            fig_p.update_traces(texttemplate='%{y}', textposition='outside')
            fig_p.update_layout(height=350, plot_bgcolor='white', paper_bgcolor='white',
                                title_font_color=COR_SECUNDARIA, uniformtext_minsize=10)
            st.plotly_chart(fig_p, use_container_width=True)

        # Gráfico: Qtd a chegar por Previsão de Entrega (linha do tempo)
        if COL_PREVISAO and 'QUANTIDADE COMPRADA' in pendentes.columns:
            graf_prev = pendentes.copy()
            graf_prev[COL_PREVISAO] = pd.to_datetime(graf_prev[COL_PREVISAO], dayfirst=True, errors='coerce')
            graf_prev = graf_prev[graf_prev[COL_PREVISAO].notna()]
            graf_prev['Previsão'] = graf_prev[COL_PREVISAO].dt.strftime('%d/%m/%Y')
            graf_prev = (
                graf_prev.groupby(['Previsão', COL_PREVISAO])['QUANTIDADE COMPRADA']
                .sum().reset_index()
                .sort_values(COL_PREVISAO)
            )
            fig_prev = px.bar(
                graf_prev, x='Previsão', y='QUANTIDADE COMPRADA',
                title='Qtd a Chegar por Previsão de Entrega',
                labels={'QUANTIDADE COMPRADA': 'Qtd', 'Previsão': ''},
                color_discrete_sequence=[COR_ACENTO],
            )
            fig_prev.update_traces(texttemplate='%{y}', textposition='outside')
            fig_prev.update_layout(height=350, plot_bgcolor='white', paper_bgcolor='white',
                                   title_font_color=COR_SECUNDARIA, uniformtext_minsize=10)
            st.plotly_chart(fig_prev, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# ABA 3 — CRÉDITOS EM ABERTO
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('### Créditos em Aberto por Fornecedor')

    try:
        df_sap = load_sap_data()
    except Exception as e:
        st.error(f'Erro ao carregar aba SAP_ABERTO: {e}')
        st.stop()

    # Filtra apenas Nota Fiscal de Entrada
    col_doc = next((c for c in ['DOCUMENTO', 'TIPO', 'TIPO DE DOCUMENTO'] if c in df_sap.columns), None)
    if col_doc:
        df_sap = df_sap[df_sap[col_doc].astype(str).str.strip() == 'Nota Fiscal de Entrada']

    # Identifica colunas — busca flexível por substring
    col_apagar  = next((c for c in df_sap.columns if 'VENCER' in c), None)
    col_forn    = next((c for c in df_sap.columns if c in ['FORNECEDOR', 'NOME FORNECEDOR']), None)
    col_vencido = next((c for c in df_sap.columns if 'VENCIDO' in c or 'ATRASADO' in c), None)

    if not col_apagar or not col_forn:
        st.warning('Colunas "Fornecedor" ou "A Pagar" não encontradas na aba SAP _ABERTO.')
    else:
        # Parse valores numéricos (formato brasileiro: 1.234,56)
        def parse_br(val):
            if val is None or str(val).strip() in ('', '-', '0'):
                return 0.0
            s = str(val).strip().replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
            try:
                return float(s)
            except Exception:
                return 0.0

        df_sap[col_apagar] = df_sap[col_apagar].apply(parse_br)
        if col_vencido:
            df_sap[col_vencido] = df_sap[col_vencido].apply(parse_br)

        # Normaliza nomes — agrupa todas as variações da Global em um único nome
        def normalizar_forn(nome):
            n = str(nome).upper()
            if 'GLOBAL DISTRIBUI' in n or 'GLOBAL DISTRIBU' in n:
                return 'GLOBAL DISTRIBUICAO (iPlace)'
            return nome
        df_sap[col_forn] = df_sap[col_forn].apply(normalizar_forn)

        # Agrupa por fornecedor
        agg = {col_apagar: 'sum'}
        if col_vencido:
            agg[col_vencido] = 'sum'
        creditos = df_sap.groupby(col_forn).agg(agg).reset_index()
        creditos.columns = ['Fornecedor', 'Limite Consumido'] + (['Vencido (Atrasado)'] if col_vencido else [])
        creditos = creditos[creditos['Limite Consumido'] > 0].sort_values('Limite Consumido', ascending=False)

        # Adiciona limites aprovados e calcula saldo
        creditos['Limite Aprovado'] = creditos['Fornecedor'].map(LIMITES)
        creditos['Saldo Disponível'] = creditos.apply(
            lambda r: r['Limite Aprovado'] - r['Limite Consumido']
            if pd.notna(r['Limite Aprovado']) else None, axis=1
        )

        # ── KPIs ──────────────────────────────────────────────────────────────
        total_consumido  = creditos['Limite Consumido'].sum()
        total_aprovado   = creditos['Limite Aprovado'].dropna().sum()
        total_saldo      = creditos['Saldo Disponível'].dropna().sum()
        total_vencido    = creditos['Vencido (Atrasado)'].sum() if 'Vencido (Atrasado)' in creditos.columns else 0

        k1, k2, k3, k4 = st.columns(4)
        k1.metric('Total em Aberto', fmt_brl(total_consumido))
        k2.metric('Limite Total Aprovado', fmt_brl(total_aprovado))
        k3.metric('Saldo Total Disponível', fmt_brl(total_saldo))
        k4.metric('Total Vencido', fmt_brl(total_vencido))

        st.divider()

        # ── Tabela ────────────────────────────────────────────────────────────
        df_display = creditos.copy()
        for col in ['Limite Consumido', 'Limite Aprovado', 'Saldo Disponível']:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(
                    lambda x: fmt_brl(x) if pd.notna(x) and x != 0 else '-'
                )
        if 'Vencido (Atrasado)' in df_display.columns:
            df_display['Vencido (Atrasado)'] = df_display['Vencido (Atrasado)'].apply(
                lambda x: fmt_brl(x) if x > 0 else '-'
            )

        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # ── Gráfico: consumido vs aprovado ────────────────────────────────────
        df_graf = creditos[creditos['Limite Aprovado'].notna()].copy()
        if not df_graf.empty:
            fig_c = go.Figure()
            fig_c.add_trace(go.Bar(
                name='Limite Consumido',
                x=df_graf['Fornecedor'],
                y=df_graf['Limite Consumido'],
                marker_color=COR_PRIMARIA,
            ))
            fig_c.add_trace(go.Bar(
                name='Saldo Disponível',
                x=df_graf['Fornecedor'],
                y=df_graf['Saldo Disponível'],
                marker_color='#E0E0E0',
            ))
            fig_c.update_layout(
                barmode='stack',
                title='Limite Aprovado vs Consumido',
                height=350,
                plot_bgcolor='white',
                paper_bgcolor='white',
                title_font_color=COR_SECUNDARIA,
                legend=dict(orientation='h', yanchor='bottom', y=1.02),
            )
            st.plotly_chart(fig_c, use_container_width=True)
