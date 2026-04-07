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

tab1, tab2, tab3, tab4, tab5 = st.tabs(['Visão Geral', 'Logística', 'Créditos em Aberto', 'Histórico de Preços', 'Análises'])

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

        # MRR gerado: itens já recebidos, cruzados com ticket médio da aba MRR
        try:
            df_mrr_vg = load_mrr_data()
        except Exception:
            df_mrr_vg = pd.DataFrame()

        mrr_gerado = 0.0
        if not df_mrr_vg.empty and 'produto' in df_mrr_vg.columns and 'PRODUTO' in df_recebidos.columns:
            mrr_prods_vg = df_mrr_vg['produto'].tolist()
            mrr_map_vg   = df_mrr_vg.set_index('produto')['valor_mensal'].to_dict()

            def buscar_ticket_vg(nome):
                norm = _normalizar(nome)
                for p in mrr_prods_vg:
                    if _normalizar(p) == norm:
                        return mrr_map_vg[p]
                norm_lista = [_normalizar(p) for p in mrr_prods_vg]
                matches = difflib.get_close_matches(norm, norm_lista, n=1, cutoff=0.5)
                if matches:
                    return mrr_map_vg[mrr_prods_vg[norm_lista.index(matches[0])]]
                return 0.0

            qtd_col = 'QUANTIDADE RECEBIDA' if 'QUANTIDADE RECEBIDA' in df_recebidos.columns else 'QUANTIDADE COMPRADA'
            mrr_gerado = df_recebidos.apply(
                lambda r: buscar_ticket_vg(r['PRODUTO']) * r[qtd_col], axis=1
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
        k7.metric('Lead Time Médio', f'{lead_medio:.1f} dias' if lead_medio and not pd.isna(lead_medio) else 'N/A')
        k8.metric('MRR Gerado', fmt_brl(mrr_gerado))

        st.markdown('<br>', unsafe_allow_html=True)

        # ── Pedidos do período ────────────────────────────────────────────────────
        st.markdown('##### Pedidos do Período')
        cols_pedidos = ['DATA DA COMPRA', 'FORNECEDOR', 'PRODUTO', 'FILIAL',
                        'QUANTIDADE COMPRADA', 'PREÇO UNITÁRIO', 'PREÇO TOTAL', 'FORMA DE PAGAMENTO']
        cols_pedidos = [c for c in cols_pedidos if c in df_f.columns]
        df_ped = df_f[cols_pedidos].copy()
        if 'DATA DA COMPRA' in df_ped.columns:
            df_ped['DATA DA COMPRA'] = pd.to_datetime(df_ped['DATA DA COMPRA'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('-')
        for col in ['PREÇO UNITÁRIO', 'PREÇO TOTAL']:
            if col in df_ped.columns:
                df_ped[col] = df_ped[col].apply(fmt_brl)
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

    else:
        # ── Visão Recebimentos ────────────────────────────────────────────────
        df_recebidos = df_f[df_f['DATA DE RECEBIMENTO'].notna()] if 'DATA DE RECEBIMENTO' in df_f.columns else pd.DataFrame()

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

# ══════════════════════════════════════════════════════════════════════════════
# ABA 4 — HISTÓRICO DE PREÇOS
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('### Histórico de Preços por Modelo')

    colunas_hist = ['PRODUTO', 'FORNECEDOR', 'DATA DA COMPRA', 'PREÇO UNITÁRIO', 'FORMA DE PAGAMENTO', 'FILIAL']
    colunas_hist = [c for c in colunas_hist if c in df.columns]

    df_hist = df[colunas_hist].copy()
    df_hist = df_hist[df_hist['PRODUTO'].astype(str).str.strip() != '']

    if 'PREÇO UNITÁRIO' in df_hist.columns:
        df_hist = df_hist[df_hist['PREÇO UNITÁRIO'] > 0]

    if 'DATA DA COMPRA' in df_hist.columns:
        df_hist = df_hist.sort_values('DATA DA COMPRA', ascending=False)

    # ── Filtros ───────────────────────────────────────────────────────────────
    hf1, hf2 = st.columns(2)
    with hf1:
        produtos_lista = sorted(df_hist['PRODUTO'].dropna().unique().tolist())
        prod_sel = st.multiselect('Produto', produtos_lista, default=[], placeholder='Todos', key='hist_prod')
    with hf2:
        fp_lista = sorted(df_hist['FORMA DE PAGAMENTO'].dropna().unique().tolist()) if 'FORMA DE PAGAMENTO' in df_hist.columns else []
        fp_hist_sel = st.multiselect('Forma de Pagamento', fp_lista, default=[], placeholder='Todos', key='hist_fp')

    if prod_sel:
        df_hist = df_hist[df_hist['PRODUTO'].isin(prod_sel)]
    if fp_hist_sel:
        df_hist = df_hist[df_hist['FORMA DE PAGAMENTO'].isin(fp_hist_sel)]

    # ── Resumo: último preço e variação por modelo ────────────────────────────
    if 'PREÇO UNITÁRIO' in df_hist.columns and 'DATA DA COMPRA' in df_hist.columns:
        df_sorted = df_hist.sort_values('DATA DA COMPRA')

        # Para cada produto: linha do último preço e linha do menor preço
        def resumo_produto(g):
            ultima = g.iloc[-1]
            menor  = g.loc[g['PREÇO UNITÁRIO'].idxmin()]
            return pd.Series({
                'Fornecedor':        ultima.get('FORNECEDOR', '-'),
                'Ultima_Compra':     ultima.get('DATA DA COMPRA'),
                'Ultimo_Preco':      ultima.get('PREÇO UNITÁRIO'),
                'Ultimo_FP':         ultima.get('FORMA DE PAGAMENTO', '-'),
                'Menor_Preco':       menor.get('PREÇO UNITÁRIO'),
                'Menor_FP':          menor.get('FORMA DE PAGAMENTO', '-'),
                'Menor_Data':        menor.get('DATA DA COMPRA'),
                'Maior_Preco':       g['PREÇO UNITÁRIO'].max(),
                'Qtd_Compras':       len(g),
            })

        ultimo_preco = (
            df_sorted.groupby('PRODUTO')
            .apply(resumo_produto)
            .reset_index()
            .sort_values('Ultima_Compra', ascending=False)
        )

        ultimo_preco['Ultima_Compra'] = pd.to_datetime(ultimo_preco['Ultima_Compra']).dt.strftime('%d/%m/%Y')
        ultimo_preco['Menor_Data']    = pd.to_datetime(ultimo_preco['Menor_Data']).dt.strftime('%d/%m/%Y')
        for col in ['Ultimo_Preco', 'Menor_Preco', 'Maior_Preco']:
            ultimo_preco[col] = ultimo_preco[col].apply(fmt_brl)
        ultimo_preco.columns = [
            'Produto', 'Último Fornecedor', 'Última Compra',
            'Último Preço', 'Pagamento (último)',
            'Menor Preço', 'Pagamento (menor)', 'Data Menor Preço',
            'Maior Preço', 'Nº Compras',
        ]

        st.markdown('##### Resumo por Modelo')
        st.dataframe(ultimo_preco, use_container_width=True, hide_index=True)

        st.markdown('##### Todas as Compras')

    # ── Tabela completa ───────────────────────────────────────────────────────
    df_hist_show = df_hist.copy()
    if 'DATA DA COMPRA' in df_hist_show.columns:
        df_hist_show['DATA DA COMPRA'] = pd.to_datetime(df_hist_show['DATA DA COMPRA'], errors='coerce').dt.strftime('%d/%m/%Y').fillna('-')
    if 'PREÇO UNITÁRIO' in df_hist_show.columns:
        df_hist_show['PREÇO UNITÁRIO'] = df_hist_show['PREÇO UNITÁRIO'].apply(fmt_brl)

    df_hist_show = df_hist_show.rename(columns={
        'DATA DA COMPRA': 'Data da Compra',
        'PREÇO UNITÁRIO': 'Preço Unitário',
        'FORMA DE PAGAMENTO': 'Forma de Pagamento',
    })

    st.dataframe(df_hist_show, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# ABA 5 — ANÁLISES
# ══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.markdown('### Análises')
    with st.expander('Filtros', expanded=False):
        an_f1, an_f2 = st.columns(2)
        mes_inicio_an = hoje_date.replace(day=1)
        default_ini_an = max(mes_inicio_an, data_min) if data_min else mes_inicio_an
        if data_min and default_ini_an > hoje_date:
            default_ini_an = data_min
        with an_f1:
            an_data_inicio = st.date_input('Data início', value=default_ini_an, min_value=data_min, max_value=hoje_date, key='an_data_ini', format='DD/MM/YYYY')
        with an_f2:
            an_data_fim = st.date_input('Data fim', value=hoje_date, min_value=data_min, max_value=hoje_date, key='an_data_fim', format='DD/MM/YYYY')
        an_c1, an_c2, an_c3 = st.columns(3)
        with an_c1:
            an_forn = st.multiselect('Fornecedor', sorted(df['FORNECEDOR'].dropna().unique().tolist()) if 'FORNECEDOR' in df.columns else [], default=[], placeholder='Todos', key='an_forn')
        with an_c2:
            an_filial = st.multiselect('Filial', sorted(df['FILIAL'].dropna().unique().tolist()) if 'FILIAL' in df.columns else [], default=[], placeholder='Todos', key='an_filial')
        with an_c3:
            an_fp = st.multiselect('Forma de Pagamento', sorted(df['FORMA DE PAGAMENTO'].dropna().unique().tolist()) if 'FORMA DE PAGAMENTO' in df.columns else [], default=[], placeholder='Todos', key='an_fp')

    df_an = df.copy()
    if data_min:
        df_an = df_an[(df_an['DATA DA COMPRA'].dt.date >= an_data_inicio) & (df_an['DATA DA COMPRA'].dt.date <= an_data_fim)]
    if an_forn:
        df_an = df_an[df_an['FORNECEDOR'].isin(an_forn)]
    if an_filial:
        df_an = df_an[df_an['FILIAL'].isin(an_filial)]
    if an_fp:
        df_an = df_an[df_an['FORMA DE PAGAMENTO'].isin(an_fp)]

    col1, col2 = st.columns(2)

    with col1:
        if 'FORNECEDOR' in df_an.columns and 'PREÇO TOTAL' in df_an.columns:
            by_forn = (
                df_an.groupby('FORNECEDOR')['PREÇO TOTAL']
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
        if 'FORMA DE PAGAMENTO' in df_an.columns and 'PREÇO TOTAL' in df_an.columns:
            by_fp = (
                df_an[df_an['FORMA DE PAGAMENTO'].astype(str).str.strip() != '']
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
        if 'ANO_MES' in df_an.columns and 'PREÇO TOTAL' in df_an.columns:
            by_mes = (
                df_an.groupby('ANO_MES')['PREÇO TOTAL']
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
        if 'FORNECEDOR' in df_an.columns and 'QUANTIDADE COMPRADA' in df_an.columns:
            by_forn_q = (
                df_an.groupby('FORNECEDOR')['QUANTIDADE COMPRADA']
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
    df_recebidos_an = df_an[df_an['DATA DE RECEBIMENTO'].notna()] if 'DATA DE RECEBIMENTO' in df_an.columns else df_an
    if 'FORNECEDOR' in df_recebidos_an.columns and 'LEAD TIME' in df_recebidos_an.columns:
        st.markdown('##### Lead Time Médio por Fornecedor')
        lt_forn = (
            df_recebidos_an.groupby('FORNECEDOR')['LEAD TIME']
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

    # ── Forma de pagamento por mês ────────────────────────────────────────────
    if 'ANO_MES' in df_an.columns and 'FORMA DE PAGAMENTO' in df_an.columns and 'PREÇO TOTAL' in df_an.columns:
        st.markdown('##### Forma de Pagamento por Mês')
        fp_mes = (
            df_an[df_an['FORMA DE PAGAMENTO'].astype(str).str.strip() != '']
            .groupby(['ANO_MES', 'FORMA DE PAGAMENTO'])['PREÇO TOTAL']
            .sum().reset_index()
            .sort_values('ANO_MES', ascending=False)
        )
        # Pivot para tabela
        fp_pivot = fp_mes.pivot_table(index='ANO_MES', columns='FORMA DE PAGAMENTO', values='PREÇO TOTAL', aggfunc='sum', fill_value=0).reset_index()
        fp_pivot = fp_pivot.sort_values('ANO_MES', ascending=False)
        for col in fp_pivot.columns:
            if col != 'ANO_MES':
                fp_pivot[col] = fp_pivot[col].apply(lambda x: fmt_brl(x) if x > 0 else '-')
        fp_pivot = fp_pivot.rename(columns={'ANO_MES': 'Mês'})
        st.dataframe(fp_pivot, use_container_width=True, hide_index=True)

        # Gráfico
        fig_fp_mes = px.bar(
            fp_mes, x='ANO_MES', y='PREÇO TOTAL', color='FORMA DE PAGAMENTO',
            title='Volume por Forma de Pagamento e Mês',
            labels={'ANO_MES': '', 'PREÇO TOTAL': 'Total (R$)', 'FORMA DE PAGAMENTO': ''},
            color_discrete_sequence=CORES_GRAFICOS,
            barmode='group',
        )
        fig_fp_mes.update_layout(height=400, plot_bgcolor='white', paper_bgcolor='white',
                                  title_font_color='#1A1A1A',
                                  legend=dict(orientation='h', yanchor='bottom', y=1.02))
        st.plotly_chart(fig_fp_mes, use_container_width=True)
