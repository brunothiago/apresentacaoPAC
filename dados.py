"""Carga das fotos do banco para o build.py — a extração mais recente de data/extracoes.json.

As fotos vão protegidas por senha (SENHA_BASE_XLSX em python/config.env); aqui elas são
decifradas em memória, sem gravar cópia aberta em disco.

Regras de recorte:
- seleção (se_cgpac.tab_base_unica_gm): as mesmas da novopac-apresentacao — migradas =
  'retomada'; seleções = 'selecionada' ou 'enquadrada'; 'substituída' fica de fora; as 2
  propostas MCMV FNHIS ficam de fora; ano_selecao 2023 conta como 2024;
- contratos (SACI e painelpac): ano de seleção e status vêm da base GM pelo número da
  proposta (num_proposta_selecao_pac = num_proposta_selecao). Quem não casa usa o ano do
  instrumento (ou da assinatura) e conta como selecionada; sem nenhum ano, fica sem ano
  (só aparece com todos os anos ligados, como as migradas);
- modalidade: a da base GM quando casa; senão a do SACI, com a grafia da base GM. O que não
  é uma das 10 modalidades (Assessoria Técnica HIS, sem modalidade) vai para "Outras";
- valor das migradas: o da base GM (vlr_portaria_ogu + vlr_portaria_fin da retomada com o mesmo
  cod_tci) — a parte pós-2023, repasse vigente menos o desembolsado até 31/12/2022 (regra do
  painelgm). Sem correspondência, vlr_gm fica vazio e o build usa o valor do SACI.
"""
import io
import json
import os
import unicodedata

import msoffcrypto
import pandas as pd
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
REGISTRO = f'{HERE}/data/extracoes.json'

OUTRAS = 'Outras / sem modalidade'
MODS = [
    'Abastecimento de Água - Rural',
    'Abastecimento de Água - Urbano',
    'Contenção de Encostas',
    'Drenagem Urbana',
    'Esgotamento Sanitário',
    'Mobilidade: Médias e Grandes Cidades',
    'Regularização Fundiária',
    'Renovação de Frota',
    'Resíduos Sólidos',
    'Urbanização de Favelas',
    OUTRAS,
]
LABELS = {'Médias e Grandes Cidades': 'Mobilidade: Médias e Grandes Cidades'}
MCMV = ('MCMV FNHIS', 'MCMV FNHIS SUB50')
STATUS = {'retomada', 'selecionada', 'enquadrada', 'substituída'}
SELECOES = ('selecionada', 'enquadrada')
# ano_selecao -> rótulo de exibição (igual à novopac-apresentacao: a portaria de 2024 é "2023")
ANO_LABEL = {2023: '2023', 2024: '2023', 2025: '2025', 2026: '2026'}


def _chave(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return ' '.join(s.lower().split())


_MOD_POR_CHAVE = {_chave(m): m for m in MODS}
_MOD_POR_CHAVE.update({_chave(k): v for k, v in LABELS.items()})


def modalidade(nome):
    if nome is None or pd.isna(nome):
        return OUTRAS
    return _MOD_POR_CHAVE.get(_chave(nome), OUTRAS)


def extracao():
    """Última entrada de data/extracoes.json."""
    if not os.path.exists(REGISTRO):
        raise SystemExit('Sem data/extracoes.json — rode python/extrair.py')
    return json.load(open(REGISTRO, encoding='utf-8'))[-1]


def abrir(nome_arquivo):
    """DataFrame da foto, decifrando com a senha se estiver protegida."""
    caminho = f'{HERE}/data/{nome_arquivo}'
    with open(caminho, 'rb') as f:
        arquivo = msoffcrypto.OfficeFile(f)
        if not arquivo.is_encrypted():
            return pd.read_excel(caminho)
        load_dotenv(f'{HERE}/python/config.env')
        senha = os.getenv('SENHA_BASE_XLSX')
        if not senha:
            raise SystemExit(f'{nome_arquivo} está protegida por senha — '
                             'defina SENHA_BASE_XLSX em python/config.env.')
        aberto = io.BytesIO()
        try:
            arquivo.load_key(password=senha)
            arquivo.decrypt(aberto)
        except Exception as e:
            raise SystemExit(f'Não consegui abrir {nome_arquivo} com a SENHA_BASE_XLSX: {e}')
    return pd.read_excel(aberto)


def _selecao(gm):
    desconhecidos = set(gm.status_selecao.dropna()) - STATUS
    if desconhecidos or gm.status_selecao.isna().any():
        raise SystemExit(f'status_selecao inesperado: {sorted(desconhecidos) or "vazio"}')
    for c in ('vlr_portaria_total', 'vlr_portaria_ogu', 'vlr_portaria_fin'):
        gm[c] = pd.to_numeric(gm[c], errors='coerce').fillna(0)
    gm['uf'] = gm.uf.fillna('').astype(str).str.strip().str.upper()
    gm['mod'] = gm.modalidade.map(modalidade)
    gm['chave'] = gm.num_proposta_selecao.astype(str).str.strip()
    return gm


def _ano_status(df, col_proposta, fonte, col_ano_inst, col_assinatura, migrado, gm):
    """kind (0 migrado · 1 selecionada · 2 enquadrada), rótulo do ano e modalidade GM.

    Casa por proposta + fonte (a mesma proposta pode ter linha OGU selecionada e linha FIN
    enquadrada); sem a fonte correspondente, casa só pela proposta.
    """
    gm = gm[gm.status_selecao != 'substituída']
    chave = df[col_proposta].astype(str).str.strip()
    chave_fonte = chave + '|' + fonte.astype(str).str.strip().str.upper()
    por_fonte = gm.assign(k=gm.chave + '|' + gm.fonte.astype(str).str.strip().str.upper()) \
                  .drop_duplicates('k').set_index('k')
    por_prop = gm.drop_duplicates('chave').set_index('chave')

    def buscar(col):
        return chave_fonte.map(por_fonte[col]).fillna(chave.map(por_prop[col]))

    st, ano, mod_gm = buscar('status_selecao'), buscar('ano_selecao'), buscar('mod')
    # sem casamento: ano do instrumento (ou da assinatura)
    ano_inst = pd.to_numeric(df[col_ano_inst], errors='coerce') if col_ano_inst else None
    ano_ass = pd.to_datetime(df[col_assinatura], errors='coerce').dt.year
    ano_fb = ano_inst.fillna(ano_ass) if ano_inst is not None else ano_ass
    ano = ano.fillna(ano_fb)
    kind = st.map({'enquadrada': 2}).fillna(1).astype(int).where(~migrado, 0)
    rotulo = ano.map(lambda a: '' if pd.isna(a) else ANO_LABEL.get(int(a), '2023' if a < 2023 else ''))
    rotulo = rotulo.where(~migrado, '')
    return kind, rotulo, mod_gm, st.notna()


def load():
    ext = extracao()
    arq = ext['arquivos']

    gm = _selecao(abrir(arq['base_unica_gm']))
    mig = gm[gm.status_selecao == 'retomada'].copy()
    sel = gm[gm.status_selecao.isin(SELECOES) & ~gm.modalidade.isin(MCMV)].copy()
    sel['ano_selecao'] = sel.ano_selecao.astype(int).replace({2023: 2024})
    for d in (mig, sel):
        fora = set(d['mod']) - set(MODS[:-1])
        if fora:
            raise SystemExit(f'modalidade da base GM fora da lista: {sorted(fora)}')

    saci = abrir(arq['carteira_saci'])
    if saci.cod_tci.duplicated().any():
        raise SystemExit('cod_tci duplicado na carteira do SACI')
    saci['uf'] = saci.txt_uf.fillna('').astype(str).str.strip().str.upper()
    migr = saci.dsc_fase_pac.eq('NOVO PAC - Migrado')
    kind, ano, mod_gm, casou = _ano_status(saci, 'num_proposta_selecao_pac', saci.txt_fonte,
                                           'num_ano_instrumento', 'dte_assinatura_contrato', migr, gm)
    saci['kind'], saci['ano'], saci['casou_gm'] = kind, ano, casou
    saci['mod'] = mod_gm.fillna(saci.txt_modalidade.map(modalidade))
    # valor das migradas pela base GM (pós-2023), casando a retomada pelo cod_tci
    tci = lambda c: c.astype(str).str.strip()
    vgm = (mig.assign(t=tci(mig.cod_tci), v=mig.vlr_portaria_ogu + mig.vlr_portaria_fin)
              .loc[lambda d: mig.cod_tci.notna()].groupby('t').v.sum())
    saci['vlr_gm'] = tci(saci.cod_tci).map(vgm).where(migr)
    for c in ('vlr_investimento', 'vlr_repasse', 'vlr_desembolsado', 'prc_execucao_fisica',
              'prc_execucao_financ'):
        saci[c] = pd.to_numeric(saci[c], errors='coerce')

    ogu = abrir(arq['painelpac_ogu'])
    ogu = ogu.drop_duplicates('cod_tci_saci')
    ogu['uf'] = ogu.txt_uf_saci.fillna('').astype(str).str.strip().str.upper()
    kind, ano, mod_gm, _ = _ano_status(ogu, 'num_proposta_selecao_pac_saci',
                                       pd.Series('OGU', index=ogu.index), None,
                                       'dte_assinatura_contrato_saci',
                                       pd.Series(False, index=ogu.index), gm)
    ogu['kind'], ogu['ano'] = kind, ano
    ogu['mod'] = mod_gm.fillna(ogu.txt_modalidade_saci.map(modalidade))
    ogu['vlr_repasse_saci'] = pd.to_numeric(ogu.vlr_repasse_saci, errors='coerce').fillna(0)
    ogu['dt_alinhamento'] = pd.to_datetime(ogu.alinhamento_suspensivas_0826, errors='coerce')

    return {'sel': sel, 'mig': mig, 'saci': saci, 'ogu': ogu, 'extracao': ext}
