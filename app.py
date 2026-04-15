import os
import unicodedata
import difflib
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
def load_mrr_data():
    if 'gcp_service_account' in st.secrets:
        creds = Credentials.from_service_account_info(
            dict(st.secrets['gcp_service_account']), scopes=SCOPES
        )
    else:
        creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    client   = gspread.authorize(creds)
    planilha = client.open_by_key(SHEET_ID)
    # Busca a aba MRR pelo gid fixo (798865343) — nova aba sempre atualizada
    ws = next(
        (s for s in planilha.worksheets() if s.id == 798865343),
        None
    )
    # Fallback: busca pelo título caso o gid mude
    if ws is None:
        ws = next(
            (s for s in planilha.worksheets() if s.title.strip().upper() == 'MRR'),
            None
        )
    if ws is None:
        nomes = [s.title for s in planilha.worksheets()]
        raise ValueError(f'Aba MRR não encontrada. Abas disponíveis: {nomes}')
    raw = ws.get_all_values()
    if not raw:
        return pd.DataFrame()
    headers = [h.strip().lower() for h in raw[0]]
    df = pd.DataFrame(raw[1:], columns=headers)
    df.columns = [c.strip() for c in df.columns]
    # Usa apenas o mês mais recente disponível
    if 'mes' in df.columns:
        df['mes'] = df['mes'].astype(str).str.strip()
        mes_max = df['mes'].max()
        df = df[df['mes'] == mes_max]
    if 'valor_mensal' in df.columns:
        df['valor_mensal'] = df['valor_mensal'].apply(parse_currency)
    return df


def _normalizar(texto):
    """Remove acentos e deixa minúsculo para comparação aproximada."""
    return unicodedata.normalize('NFKD', str(texto).lower()).encode('ascii', 'ignore').decode()


def match_mrr(produto, mrr_produtos):
    """Retorna o nome mais próximo da lista mrr_produtos, ou None se distância > limiar."""
    norm_prod  = _normalizar(produto)
    norm_lista = [_normalizar(p) for p in mrr_produtos]
    matches    = difflib.get_close_matches(norm_prod, norm_lista, n=1, cutoff=0.6)
    if not matches:
        return None
    idx = norm_lista.index(matches[0])
    return mrr_produtos[idx]


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

    # Converte coluna de previsão independente do nome exato
    col_prev = next((c for c in df.columns if 'PREVIS' in c.upper()), None)
    if col_prev and col_prev not in ['DATA DA COMPRA', 'DATA DE RECEBIMENTO', 'PREVISÃO DE COMPRA']:
        df[col_prev] = pd.to_datetime(df[col_prev], dayfirst=True, errors='coerce')

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

# ─── VALORES BASE ─────────────────────────────────────────────────────────────
data_min  = df['DATA DA COMPRA'].min().date() if 'DATA DA COMPRA' in df.columns and df['DATA DA COMPRA'].notna().any() else None
hoje_date = pd.Timestamp.today().date()

# ─── ABAS ─────────────────────────────────────────────────────────────────────

tab1, tab2 = st.tabs(['Visão Geral', 'Logística'])

# ══════════════════════════════════════════════════════════════════════════════
# ABA 1 — VISÃO GERAL
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    # ── Filtros da aba ────────────────────────────────────────────────────────
    with st.expander('Filtros', expanded=True):
        st.caption('Deixe em branco para considerar todos.')
        vg_f1, vg_f2 = st.columns(2)
        mes_inicio_vg = hoje_date.replace(day=1)
        default_ini_vg = max(mes_inicio_vg, data_min) if data_min else mes_inicio_vg
        if data_min and default_ini_vg > hoje_date:
            default_ini_vg = data_min
        with vg_f1:
            vg_data_inicio = st.date_input('Data início', value=default_ini_vg, min_value=data_min, max_value=hoje_date, key='vg_data_ini', format='DD/MM/YYYY')
        with vg_f2:
            vg_data_fim = st.date_input('Data fim', value=hoje_date, min_value=data_min, max_value=hoje_date, key='vg_data_fim', format='DD/MM/YYYY')
        vg_c1, vg_c2, vg_c3 = st.columns(3)
        with vg_c1:
            vg_forn = st.multiselect('Fornecedor', sorted(df['FORNECEDOR'].dropna().unique().tolist()) if 'FORNECEDOR' in df.columns else [], default=[], placeholder='Todos', key='vg_forn')
        with vg_c2:
            vg_filial = st.multiselect('Filial', sorted(df['FILIAL'].dropna().unique().tolist()) if 'FILIAL' in df.columns else [], default=[], placeholder='Todos', key='vg_filial')
        with vg_c3:
            vg_fp = st.multiselect('Forma de Pagamento', sorted(df['FORMA DE PAGAMENTO'].dropna().unique().tolist()) if 'FORMA DE PAGAMENTO' in df.columns else [], default=[], placeholder='Todos', key='vg_fp')

    # Aplicar filtros
    df_f = df.copy()
    if data_min:
        df_f = df_f[(df_f['DATA DA COMPRA'].dt.date >= vg_data_inicio) & (df_f['DATA DA COMPRA'].dt.date <= vg_data_fim)]
    if vg_forn:
        df_f = df_f[df_f['FORNECEDOR'].isin(vg_forn)]
    if vg_filial:
        df_f = df_f[df_f['FILIAL'].isin(vg_filial)]
    if vg_fp:
        df_f = df_f[df_f['FORMA DE PAGAMENTO'].isin(vg_fp)]

    # ── Toggle Compras / Recebimentos ─────────────────────────────────────────
    visao_sel = st.radio('Visualizar', ['Compras', 'Recebimentos'], horizontal=True, key='vg_visao')

    if visao_sel == 'Compras':
        # ── KPIs gerais ──────────────────────────────────────────────────────────
        total_valor    = df_f['PREÇO TOTAL'].sum() if 'PREÇO TOTAL' in df_f.columns else 0
        total_qtd      = df_f['QUANTIDADE COMPRADA'].sum() if 'QUANTIDADE COMPRADA' in df_f.columns else 0
        n_fornecedores = df_f['FORNECEDOR'].nunique() if 'FORNECEDOR' in df_f.columns else 0
        # Lead time: apenas itens já recebidos (com DATA DE RECEBIMENTO preenchida)
        df_recebidos   = df_f[df_f['DATA DE RECEBIMENTO'].notna()] if 'DATA DE RECEBIMENTO' in df_f.columns else df_f
        lead_medio     = df_recebidos['LEAD TIME'].mean() if 'LEAD TIME' in df_recebidos.columns else None
        n_pedidos      = len(df_f)

        # MRR: carrega tickets
        try:
            df_mrr_vg = load_mrr_data()
        except Exception:
            df_mrr_vg = pd.DataFrame()

        def _buscar_ticket(nome, prods, mapa):
            norm = _normalizar(nome)
            norms = [_normalizar(p) for p in prods]
            if norm in norms:
                return mapa[prods[norms.index(norm)]]
            m = difflib.get_close_matches(norm, norms, n=1, cutoff=0.5)
            return mapa[prods[norms.index(m[0])]] if m else 0.0

        mrr_realizado = 0.0
        mrr_previsto  = 0.0

        if not df_mrr_vg.empty and 'produto' in df_mrr_vg.columns:
            _prods = df_mrr_vg['produto'].tolist()
            _mapa  = df_mrr_vg.set_index('produto')['valor_mensal'].to_dict()

            # MRR Realizado: compras do período já recebidas (DATA DE RECEBIMENTO preenchida)
            if 'PRODUTO' in df_recebidos.columns:
                qtd_col = 'QUANTIDADE RECEBIDA' if 'QUANTIDADE RECEBIDA' in df_recebidos.columns else 'QUANTIDADE COMPRADA'
                mrr_realizado = df_recebidos.apply(
                    lambda r: _buscar_ticket(r['PRODUTO'], _prods, _mapa) * r[qtd_col], axis=1
                ).sum()

            # MRR Previsto: compras do período ainda em trânsito (sem data de recebimento)
            df_transit = df_f[df_f['DATA DE RECEBIMENTO'].isna()] if 'DATA DE RECEBIMENTO' in df_f.columns else pd.DataFrame()
            if not df_transit.empty and 'PRODUTO' in df_transit.columns and 'QUANTIDADE COMPRADA' in df_transit.columns:
                mrr_previsto = df_transit.apply(
                    lambda r: _buscar_ticket(r['PRODUTO'], _prods, _mapa) * r['QUANTIDADE COMPRADA'], axis=1
                ).sum()

        qtd_recebida = int(df_recebidos['QUANTIDADE RECEBIDA'].sum()) if 'QUANTIDADE RECEBIDA' in df_recebidos.columns else 0
        qtd_pendente = int(total_qtd) - qtd_recebida

        k1, k2, k3, k4 = st.columns(4)
        k1.metric('Volume Total', fmt_brl(total_valor))
        k2.metric('Qtd Comprada', f'{int(total_qtd):,}'.replace(',', '.'))
        k3.metric('Qtd Recebida', f'{qtd_recebida:,}'.replace(',', '.'))
        k4.metric('Qtd Pendente', f'{qtd_pendente:,}'.replace(',', '.'))

        k5, k6, k7, k8 = st.columns(4)
        k5.metric('Fornecedores', n_fornecedores)
        k6.metric('Pedidos', n_pedidos)
        k7.metric('MRR Realizado', fmt_brl(mrr_realizado))
        k8.metric('MRR Previsto', fmt_brl(mrr_previsto))

        st.markdown('<br>', unsafe_allow_html=True)

        # ── Pedidos do período ────────────────────────────────────────────────────
        st.markdown('##### Pedidos do Período')
        cols_pedidos = ['DATA DA COMPRA', 'FORNECEDOR', 'PRODUTO', 'FILIAL',
                        'QUANTIDADE COMPRADA', 'PREÇO UNITÁRIO', 'PREÇO TOTAL', 'FORMA DE PAGAMENTO']
        cols_pedidos = [c for c in cols_pedidos if c in df_f.columns]
        df_ped = df_f[cols_pedidos].copy()

        # MRR por linha
        if not df_mrr_vg.empty and 'produto' in df_mrr_vg.columns and 'PRODUTO' in df_ped.columns:
            _mrr_prods = df_mrr_vg['produto'].tolist()
            _mrr_map   = df_mrr_vg.set_index('produto')['valor_mensal'].to_dict()
            _mrr_norms = [_normalizar(p) for p in _mrr_prods]
            def _ticket_linha(nome):
                n = _normalizar(nome)
                if n in _mrr_norms:
                    return _mrr_map[_mrr_prods[_mrr_norms.index(n)]]
                m = difflib.get_close_matches(n, _mrr_norms, n=1, cutoff=0.5)
                return _mrr_map[_mrr_prods[_mrr_norms.index(m[0])]] if m else 0.0
            qtd_col_ped = 'QUANTIDADE COMPRADA'
            df_ped['MRR'] = df_ped.apply(
                lambda r: _ticket_linha(r['PRODUTO']) * r[qtd_col_ped]
                if qtd_col_ped in df_ped.columns else 0.0, axis=1
            )

        if 'DATA DA COMPRA' in df_ped.columns:
            df_ped['DATA DA COMPRA'] = pd.to_datetime(df_ped['DATA DA COMPRA'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('-')
        for col in ['PREÇO UNITÁRIO', 'PREÇO TOTAL']:
            if col in df_ped.columns:
                df_ped[col] = df_ped[col].apply(fmt_brl)
        if 'MRR' in df_ped.columns:
            df_ped['MRR'] = df_ped['MRR'].apply(lambda x: fmt_brl(x) if x > 0 else '-')
        df_ped = df_ped.sort_values('DATA DA COMPRA', ascending=False) if 'DATA DA COMPRA' in df_ped.columns else df_ped
        st.dataframe(df_ped, use_container_width=True, hide_index=True)

        st.markdown('<br>', unsafe_allow_html=True)

        # ── Histórico de compras por mês (sem filtro, a partir de nov/25) ─────────
        if 'ANO_MES' in df.columns:
            st.markdown('##### Histórico de Compras')
            df_hist_geral = df[df['ANO_MES'] >= '2025-11'].copy()

            # Calcula MRR por item recebido (usa quantidade recebida × ticket médio)
            if not df_mrr_vg.empty and 'produto' in df_mrr_vg.columns and 'PRODUTO' in df_hist_geral.columns:
                mrr_prods_h  = df_mrr_vg['produto'].tolist()
                mrr_map_h    = df_mrr_vg.set_index('produto')['valor_mensal'].to_dict()
                norm_lista_h = [_normalizar(p) for p in mrr_prods_h]

                def ticket_hist(nome):
                    norm = _normalizar(nome)
                    if norm in norm_lista_h:
                        return mrr_map_h[mrr_prods_h[norm_lista_h.index(norm)]]
                    m = difflib.get_close_matches(norm, norm_lista_h, n=1, cutoff=0.5)
                    return mrr_map_h[mrr_prods_h[norm_lista_h.index(m[0])]] if m else 0.0

                qtd_col_h = 'QUANTIDADE RECEBIDA' if 'QUANTIDADE RECEBIDA' in df_hist_geral.columns else 'QUANTIDADE COMPRADA'
                df_hist_geral['_mrr'] = df_hist_geral.apply(
                    lambda r: ticket_hist(r['PRODUTO']) * r[qtd_col_h]
                    if pd.notna(r[qtd_col_h]) and r[qtd_col_h] > 0 else 0.0, axis=1
                )
            else:
                df_hist_geral['_mrr'] = 0.0

            hist = (
                df_hist_geral.groupby('ANO_MES')
                .agg(
                    Quantidade=('QUANTIDADE COMPRADA', 'sum'),
                    Custo_Total=('PREÇO TOTAL', 'sum'),
                    Pedidos=('ANO_MES', 'count'),
                    MRR_Total=('_mrr', 'sum'),
                )
                .reset_index()
                .sort_values('ANO_MES', ascending=False)
            )
            hist['Custo Total'] = hist['Custo_Total'].apply(fmt_brl)
            hist['MRR Gerado']  = hist['MRR_Total'].apply(fmt_brl)
            hist['Quantidade']  = hist['Quantidade'].apply(lambda x: f'{int(x):,}'.replace(',', '.'))
            hist = hist.rename(columns={'ANO_MES': 'Mês', 'Pedidos': 'Nº Pedidos'})
            hist = hist[['Mês', 'Nº Pedidos', 'Quantidade', 'Custo Total', 'MRR Gerado']]
            st.dataframe(hist, use_container_width=True, hide_index=True)

        st.markdown('<br>', unsafe_allow_html=True)

        # ── Resumo por produto × mês ──────────────────────────────────────────
        if 'PRODUTO' in df.columns and 'ANO_MES' in df.columns and 'QUANTIDADE COMPRADA' in df.columns:
            st.markdown('##### Volume de Compras por Produto e Mês')
            df_resumo = df[df['ANO_MES'] >= '2025-11'].copy()

            pivot = (
                df_resumo.groupby(['PRODUTO', 'ANO_MES'])['QUANTIDADE COMPRADA']
                .sum()
                .reset_index()
                .pivot_table(index='PRODUTO', columns='ANO_MES', values='QUANTIDADE COMPRADA', aggfunc='sum', fill_value=0)
            )
            pivot.columns.name = None
            pivot = pivot.reset_index()

            # Renomeia colunas de mês para formato legível (2025-11 → Nov/25)
            def fmt_mes(m):
                try:
                    return pd.Period(m, 'M').strftime('%b/%y').capitalize()
                except Exception:
                    return m
            pivot = pivot.rename(columns={c: fmt_mes(c) for c in pivot.columns if c != 'PRODUTO'})

            # Adiciona coluna Total
            mes_cols = [c for c in pivot.columns if c != 'PRODUTO']
            pivot['Total'] = pivot[mes_cols].sum(axis=1)
            pivot = pivot.sort_values('Total', ascending=False)

            # Formata números
            for c in mes_cols + ['Total']:
                pivot[c] = pivot[c].apply(lambda x: f'{int(x):,}'.replace(',', '.') if x > 0 else '-')

            pivot = pivot.rename(columns={'PRODUTO': 'Produto'})
            st.dataframe(pivot, use_container_width=True, hide_index=True)

    else:
        # ── Visão Recebimentos — filtra por DATA DE RECEBIMENTO no período ────
        if 'DATA DE RECEBIMENTO' in df.columns:
            df_recebidos = df[df['DATA DE RECEBIMENTO'].notna()].copy()
            df_recebidos = df_recebidos[
                (df_recebidos['DATA DE RECEBIMENTO'].dt.date >= vg_data_inicio) &
                (df_recebidos['DATA DE RECEBIMENTO'].dt.date <= vg_data_fim)
            ]
            if vg_forn:
                df_recebidos = df_recebidos[df_recebidos['FORNECEDOR'].isin(vg_forn)]
            if vg_filial:
                df_recebidos = df_recebidos[df_recebidos['FILIAL'].isin(vg_filial)]
            if vg_fp:
                df_recebidos = df_recebidos[df_recebidos['FORMA DE PAGAMENTO'].isin(vg_fp)]
        else:
            df_recebidos = pd.DataFrame()

        # MRR gerado (recebimentos)
        try:
            df_mrr_vg = load_mrr_data()
        except Exception:
            df_mrr_vg = pd.DataFrame()

        mrr_gerado_rec = 0.0
        if not df_recebidos.empty and not df_mrr_vg.empty and 'produto' in df_mrr_vg.columns and 'PRODUTO' in df_recebidos.columns:
            mrr_prods_vg = df_mrr_vg['produto'].tolist()
            mrr_map_vg   = df_mrr_vg.set_index('produto')['valor_mensal'].to_dict()

            def buscar_ticket_rec(nome):
                norm = _normalizar(nome)
                for p in mrr_prods_vg:
                    if _normalizar(p) == norm:
                        return mrr_map_vg[p]
                norm_lista = [_normalizar(p) for p in mrr_prods_vg]
                matches = difflib.get_close_matches(norm, norm_lista, n=1, cutoff=0.5)
                if matches:
                    return mrr_map_vg[mrr_prods_vg[norm_lista.index(matches[0])]]
                return 0.0

            qtd_col_r = 'QUANTIDADE RECEBIDA' if 'QUANTIDADE RECEBIDA' in df_recebidos.columns else 'QUANTIDADE COMPRADA'
            mrr_gerado_rec = df_recebidos.apply(
                lambda r: buscar_ticket_rec(r['PRODUTO']) * r[qtd_col_r], axis=1
            ).sum()

        qtd_recebida_r = int(df_recebidos['QUANTIDADE RECEBIDA'].sum()) if not df_recebidos.empty and 'QUANTIDADE RECEBIDA' in df_recebidos.columns else 0
        n_forn_rec     = df_recebidos['FORNECEDOR'].nunique() if not df_recebidos.empty and 'FORNECEDOR' in df_recebidos.columns else 0
        n_ped_rec      = len(df_recebidos)

        kr1, kr2, kr3, kr4 = st.columns(4)
        kr1.metric('Qtd Recebida', f'{qtd_recebida_r:,}'.replace(',', '.'))
        kr2.metric('MRR Gerado', fmt_brl(mrr_gerado_rec))
        kr3.metric('Fornecedores', n_forn_rec)
        kr4.metric('Nº Pedidos Recebidos', n_ped_rec)

        st.markdown('<br>', unsafe_allow_html=True)

        if df_recebidos.empty:
            st.info('Nenhum item recebido no período selecionado.')
        else:
            # Cards por produto
            if 'PRODUTO' in df_recebidos.columns and 'QUANTIDADE RECEBIDA' in df_recebidos.columns:
                st.markdown('##### Itens Recebidos no Período')
                qtd_col_rec = 'QUANTIDADE RECEBIDA'
                recebidos_prod = (
                    df_recebidos.groupby(['PRODUTO', 'FORNECEDOR'])
                    .agg(qtd=(qtd_col_rec, 'sum'), valor=('PREÇO TOTAL', 'sum'))
                    .reset_index()
                    .sort_values('qtd', ascending=False)
                )

                if not df_mrr_vg.empty and 'produto' in df_mrr_vg.columns:
                    mrr_prods_vg2 = df_mrr_vg['produto'].tolist()
                    mrr_map_vg2   = df_mrr_vg.set_index('produto')['valor_mensal'].to_dict()
                    def ticket_rec(nome):
                        norm = _normalizar(nome)
                        for p in mrr_prods_vg2:
                            if _normalizar(p) == norm:
                                return mrr_map_vg2[p]
                        nl = [_normalizar(p) for p in mrr_prods_vg2]
                        m  = difflib.get_close_matches(norm, nl, n=1, cutoff=0.5)
                        return mrr_map_vg2[mrr_prods_vg2[nl.index(m[0])]] if m else 0.0
                    recebidos_prod['ticket'] = recebidos_prod['PRODUTO'].apply(ticket_rec)
                    recebidos_prod['mrr']    = recebidos_prod['ticket'] * recebidos_prod['qtd']
                else:
                    recebidos_prod['ticket'] = 0.0
                    recebidos_prod['mrr']    = 0.0

                def render_cards(df_cards):
                    cols_c = st.columns(min(len(df_cards), 4))
                    for i, (_, row) in enumerate(df_cards.iterrows()):
                        with cols_c[i % 4]:
                            nome    = str(row['PRODUTO'])[:40]
                            forn    = str(row['FORNECEDOR'])[:30]
                            qtd_fmt = f'{int(row["qtd"]):,}'.replace(',', '.')
                            mrr_str = fmt_brl(row['mrr']) if row['mrr'] > 0 else '-'
                            st.markdown(f"""
                            <div class="produto-card">
                                <div class="prod-nome" title="{row['PRODUTO']}">{nome}</div>
                                <div class="prod-forn">{forn}</div>
                                <div class="prod-qtd">{qtd_fmt}</div>
                                <div class="prod-qtd-label">unidades recebidas</div>
                                <div class="prod-valor">MRR: {mrr_str}</div>
                            </div>
                            """, unsafe_allow_html=True)

                for chunk_start in range(0, len(recebidos_prod), 4):
                    chunk = recebidos_prod.iloc[chunk_start:chunk_start + 4]
                    render_cards(chunk)
                    if chunk_start + 4 < len(recebidos_prod):
                        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

            st.markdown('<br>', unsafe_allow_html=True)

            # Tabela de itens recebidos
            st.markdown('##### Detalhamento de Recebimentos')
            cols_rec = ['DATA DE RECEBIMENTO', 'PRODUTO', 'FORNECEDOR', 'FILIAL', 'QUANTIDADE RECEBIDA', 'PREÇO TOTAL']
            cols_rec = [c for c in cols_rec if c in df_recebidos.columns]
            df_rec_show = df_recebidos[cols_rec].copy()
            if 'DATA DE RECEBIMENTO' in df_rec_show.columns:
                df_rec_show['DATA DE RECEBIMENTO'] = pd.to_datetime(df_rec_show['DATA DE RECEBIMENTO'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('-')
            if 'PREÇO TOTAL' in df_rec_show.columns:
                df_rec_show['PREÇO TOTAL'] = df_rec_show['PREÇO TOTAL'].apply(fmt_brl)
            df_rec_show = df_rec_show.sort_values('DATA DE RECEBIMENTO', ascending=False) if 'DATA DE RECEBIMENTO' in df_rec_show.columns else df_rec_show
            st.dataframe(df_rec_show, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# ABA 2 — LOGÍSTICA
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('### Pedidos em Aberto')

    hoje = pd.Timestamp.today().normalize()

    # Filtros internos da logística
    log_c1, log_c2 = st.columns(2)
    with log_c1:
        log_forn = st.multiselect('Fornecedor', sorted(df['FORNECEDOR'].dropna().unique().tolist()) if 'FORNECEDOR' in df.columns else [], default=[], placeholder='Todos', key='log_forn')
    with log_c2:
        log_filial = st.multiselect('Filial', sorted(df['FILIAL'].dropna().unique().tolist()) if 'FILIAL' in df.columns else [], default=[], placeholder='Todos', key='log_filial')

    if 'DATA DE RECEBIMENTO' not in df.columns:
        st.info('Coluna "DATA DE RECEBIMENTO" não encontrada na planilha.')
    else:
        # Pendentes = sem data de recebimento E sem quantidade recebida (pedidos em aberto)
        mask_sem_recebimento = df['DATA DE RECEBIMENTO'].isna()
        if 'QUANTIDADE RECEBIDA' in df.columns:
            mask_sem_recebimento = mask_sem_recebimento & (df['QUANTIDADE RECEBIDA'].isna() | (df['QUANTIDADE RECEBIDA'] == 0))
        pendentes = df[mask_sem_recebimento].copy()
        if log_forn:
            pendentes = pendentes[pendentes['FORNECEDOR'].isin(log_forn)]
        if log_filial:
            pendentes = pendentes[pendentes['FILIAL'].isin(log_filial)]

        # Lead time médio: apenas itens recebidos do histórico completo
        df_hist_recebidos = df[df['DATA DE RECEBIMENTO'].notna()] if 'DATA DE RECEBIMENTO' in df.columns else df
        if 'LEAD TIME' in df_hist_recebidos.columns and 'FORNECEDOR' in df_hist_recebidos.columns:
            lt_medio = (
                df_hist_recebidos.groupby('FORNECEDOR')['LEAD TIME']
                .mean().round(1).reset_index()
            )
            lt_medio.columns = ['FORNECEDOR', 'LEAD TIME MÉDIO (dias)']
            pendentes = pendentes.merge(lt_medio, on='FORNECEDOR', how='left')

        # Busca coluna de previsão por substring (ignora nome exato)
        COL_PREVISAO_STATUS = next(
            (c for c in pendentes.columns if 'PREVIS' in c.upper()),
            None
        )
        if COL_PREVISAO_STATUS:
            pendentes[COL_PREVISAO_STATUS] = pd.to_datetime(
                pendentes[COL_PREVISAO_STATUS], dayfirst=True, errors='coerce'
            )
            def status(row):
                prev = row.get(COL_PREVISAO_STATUS)
                if pd.isnull(prev):
                    return 'Sem previsão'
                return 'Atrasado' if prev < hoje else 'No prazo'
            pendentes['STATUS'] = pendentes.apply(status, axis=1)

        # ── Cruzamento com MRR ───────────────────────────────────────────────
        df_mrr = pd.DataFrame()
        mrr_erro = None
        try:
            df_mrr = load_mrr_data()
        except Exception as e:
            mrr_erro = str(e)

        if mrr_erro:
            st.warning(f'MRR: {mrr_erro}')

        if not df_mrr.empty and 'produto' in df_mrr.columns and 'PRODUTO' in pendentes.columns:
            # Normaliza nomes da aba MRR para comparação
            mrr_produtos = df_mrr['produto'].tolist()
            mrr_map = df_mrr.set_index('produto')['valor_mensal'].to_dict()

            def buscar_ticket(nome_capex):
                norm = _normalizar(nome_capex)
                # 1. Tenta match exato normalizado
                for p in mrr_produtos:
                    if _normalizar(p) == norm:
                        return p
                # 2. Tenta match aproximado com cutoff 0.5
                norm_lista = [_normalizar(p) for p in mrr_produtos]
                matches = difflib.get_close_matches(norm, norm_lista, n=1, cutoff=0.5)
                if matches:
                    return mrr_produtos[norm_lista.index(matches[0])]
                return None

            pendentes['_prod_match'] = pendentes['PRODUTO'].apply(buscar_ticket)
            pendentes['TICKET MÉDIO'] = pendentes['_prod_match'].map(mrr_map)
            pendentes['MRR PREVISTO'] = pendentes.apply(
                lambda r: r['TICKET MÉDIO'] * r['QUANTIDADE COMPRADA']
                if pd.notna(r.get('TICKET MÉDIO')) else None, axis=1
            )
            pendentes.drop(columns=['_prod_match'], inplace=True)

        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric('Pedidos Pendentes', len(pendentes))
        qtd_pendente = int(pendentes['QUANTIDADE COMPRADA'].sum()) if 'QUANTIDADE COMPRADA' in pendentes.columns else 0
        k2.metric('Ativos a Chegar', f'{qtd_pendente:,}'.replace(',', '.'))
        atrasados = int((pendentes['STATUS'] == 'Atrasado').sum()) if 'STATUS' in pendentes.columns else 0
        k3.metric('Pedidos Atrasados', atrasados)
        df_atrasados = pendentes[pendentes['STATUS'] == 'Atrasado'] if 'STATUS' in pendentes.columns else pd.DataFrame()
        qtd_atrasada = int(df_atrasados['QUANTIDADE COMPRADA'].sum()) if 'QUANTIDADE COMPRADA' in df_atrasados.columns and not df_atrasados.empty else 0
        k4.metric('Ativos Atrasados', f'{qtd_atrasada:,}'.replace(',', '.'))
        valor_pendente = pendentes['PREÇO TOTAL'].sum() if 'PREÇO TOTAL' in pendentes.columns else 0
        k5.metric('Valor em Trânsito', fmt_brl(valor_pendente))
        mrr_previsto = pendentes['MRR PREVISTO'].sum() if 'MRR PREVISTO' in pendentes.columns else 0
        k6.metric('MRR Previsto', fmt_brl(mrr_previsto))

        st.divider()

        # ── Resumo por modelo ────────────────────────────────────────────────
        if 'PRODUTO' in pendentes.columns and 'QUANTIDADE COMPRADA' in pendentes.columns:
            st.markdown('##### Volume por Modelo')
            resumo_modelo = (
                pendentes.groupby('PRODUTO')
                .agg(
                    qtd_total=('QUANTIDADE COMPRADA', 'sum'),
                    pedidos=('PRODUTO', 'count'),
                    mrr_total=('MRR PREVISTO', 'sum') if 'MRR PREVISTO' in pendentes.columns else ('QUANTIDADE COMPRADA', 'sum'),
                )
                .reset_index()
                .sort_values('qtd_total', ascending=False)
            )
            resumo_modelo.columns = ['Produto', 'Qtd Total', 'Pedidos', 'MRR Previsto']
            resumo_modelo['MRR Previsto'] = resumo_modelo['MRR Previsto'].apply(
                lambda x: fmt_brl(x) if pd.notna(x) and x > 0 else '-'
            )
            resumo_modelo['Qtd Total'] = resumo_modelo['Qtd Total'].apply(
                lambda x: f'{int(x):,}'.replace(',', '.')
            )
            st.dataframe(resumo_modelo, use_container_width=True, hide_index=True)
            st.markdown('##### Pedidos Detalhados')

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
        COLS_LOG += ['QUANTIDADE COMPRADA', 'TICKET MÉDIO', 'MRR PREVISTO', 'LEAD TIME MÉDIO (dias)']

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
        for col_val in ['TICKET MÉDIO', 'MRR PREVISTO']:
            if col_val in df_show.columns:
                df_show[col_val] = df_show[col_val].apply(
                    lambda x: fmt_brl(x) if pd.notna(x) and x != 0 else '-'
                )

        # Ordena: Atrasado primeiro, depois No prazo, Sem previsão por último
        if 'STATUS' in df_show.columns:
            ordem = {'Atrasado': 0, 'No prazo': 1, 'Sem previsão': 2}
            df_show['_ord'] = df_show['STATUS'].map(ordem).fillna(3)
            df_show = df_show.sort_values('_ord').drop(columns=['_ord'])

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

