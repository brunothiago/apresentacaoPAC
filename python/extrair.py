#!/usr/bin/env python3
"""Tira as fotos do banco que alimentam a apresentação — uma versão por extração.

A apresentação (build.py) lê só as fotos em data/ — não conecta no banco —, para o
index.html continuar autocontido e funcionando offline.

Três fontes, todas do banco `corporativo`:

| Foto                          | Origem                                          | Slides                      |
|-------------------------------|-------------------------------------------------|-----------------------------|
| base_unica_gm_<carimbo>.xlsx  | se_cgpac.tab_base_unica_gm (painelgm)           | Seleção, Contratação        |
| carteira_saci_<carimbo>.xlsx  | se_saci.view_mat_carteira_investimento          | Contratação, Execução       |
| painelpac_ogu_<carimbo>.xlsx  | consulta OGU do painelpac (QUERY do             | Suspensivas, Licitação      |
|                               | python/ogu/2_gerar_base_pc32.py, importada)     |                             |

- carteira SACI: fases "NOVO PAC - Seleção" e "NOVO PAC - Migrado", sem a SNH (o
  "NOVO PAC - MCMV" é todo da SNH e fica de fora, como na novopac-apresentacao);
- painelpac: a consulta é importada do próprio painelpac (pasta irmã ../painelpac, ou
  PAINELPAC_DIR no config.env), para os números baterem com o painel. Os status de prazo
  dela usam CURRENT_DATE, então valem para o dia da extração.

Carimbo <DDMMYYYY_HHMM> = hora da extração, o mesmo nas três fotos. Se uma fonte não mudou
desde a extração anterior (mesmo conteúdo), a foto anterior é reaproveitada em vez de gravar
outra igual. Cada extração entra em data/extracoes.json (carimbo, arquivos, linhas e a data
de atualização de cada fonte) — o build usa a mais recente.

As fotos vão protegidas por senha (SENHA_BASE_XLSX do config.env), com a criptografia
padrão do Excel: o repositório é público.

Uso:
  uv run --with pandas --with openpyxl --with sqlalchemy --with psycopg2-binary \
         --with python-dotenv --with msoffcrypto-tool python python/extrair.py
"""
import hashlib
import importlib.util
import io
import json
import os
import sys
from datetime import datetime

import msoffcrypto
import pandas as pd
from dotenv import load_dotenv
from msoffcrypto.format.ooxml import OOXMLFile
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

HERE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(HERE)
DATA = os.path.join(RAIZ, 'data')
REGISTRO = os.path.join(DATA, 'extracoes.json')

load_dotenv(os.path.join(HERE, 'config.env'))
SENHA = os.getenv('SENHA_BASE_XLSX')
if not SENHA:
    raise SystemExit('Defina SENHA_BASE_XLSX em python/config.env — as fotos vão com senha.')
PAINELPAC = os.path.abspath(os.getenv('PAINELPAC_DIR') or os.path.join(RAIZ, '..', 'painelpac'))

# ---------------------------------------------------------------- consultas
GM_COLUNAS = [
    'num_proposta_selecao', 'fonte', 'subfonte', 'regiao', 'uf', 'municipio', 'proponente',
    'vlr_portaria_total', 'vlr_portaria_ogu', 'vlr_portaria_fin', 'eixo', 'subeixo', 'modalidade',
    'grupo_modalidade', 'ano_selecao', 'status_selecao', 'tipo_financiamento', 'dte_carga',
]
SQL_GM = f'SELECT {", ".join(GM_COLUNAS)} FROM se_cgpac.tab_base_unica_gm ORDER BY id_linha'

SACI_COLUNAS = [
    'cod_tci', 'num_convenio', 'num_proposta_selecao_pac', 'dsc_fase_pac', 'txt_fonte',
    'txt_sigla_secretaria', 'txt_uf', 'txt_municipio', 'txt_eixo', 'txt_subeixo', 'txt_modalidade',
    'num_ano_instrumento', 'dte_assinatura_contrato', 'dsc_situacao_contrato_mcid',
    'dsc_situacao_objeto_mcid', 'dte_inicio_obra_mcid', 'dte_fim_obra_mcid', 'vlr_investimento',
    'vlr_repasse', 'vlr_contrapartida', 'vlr_empenhado', 'vlr_desembolsado', 'vlr_pago',
    'prc_execucao_fisica', 'prc_execucao_financ', 'prc_desembolsado', 'txt_motivo_paralisacao_mcid',
    'bln_carteira_ativa_mcid', 'dte_carga',
]
SQL_SACI = f"""
SELECT {", ".join(SACI_COLUNAS)}
FROM se_saci.view_mat_carteira_investimento
WHERE dsc_fase_pac IN ('NOVO PAC - Seleção', 'NOVO PAC - Migrado')
  AND coalesce(txt_sigla_secretaria, '') <> 'SNH'
ORDER BY cod_tci
"""

# colunas da consulta do painelpac que a apresentação usa
PAC_COLUNAS = [
    'cod_tci_saci', 'num_convenio_saci', 'num_proposta_selecao_pac_saci', 'txt_uf_saci',
    'txt_modalidade_saci', 'dsc_situacao_contrato_mcid_saci', 'dte_assinatura_contrato_saci',
    'vlr_repasse_saci', 'status_suspensiva_calc', 'vencimento_da_suspensiva_pbi',
    'dte_retirada_suspensiva_tgov', 'urgencia_suspensiva_calc', 'nivel_contrato_pc48_calc',
    'prazo_suspensiva_pc48_calc', 'prazo_suspensiva_pc48_prorrogado_calc',
    'status_prazo_suspensiva_pc48_calc', 'fase_atual_calc', 'dte_primeira_data_lae_tdb',
    'dte_publicacao_licitacao_tgov', 'dte_homologacao_licitacao_tgov', 'dte_vrpl_tdb', 'dte_aio_tdb',
    'dte_inicio_obra_mcid_saci', 'prazo_pub_licitacao_calc', 'prazo_homolog_licitacao_calc',
    'status_pub_licitacao_calc', 'status_homolog_licitacao_calc', 'status_regra_casa_civil_calc',
    'status_inicio_obra_calc',
]


def modulo_painelpac():
    """Importa a consulta OGU do painelpac sem rodar o ETL dele (o main() fica de fora)."""
    pasta = os.path.join(PAINELPAC, 'python', 'ogu')
    arquivo = os.path.join(pasta, '2_gerar_base_pc32.py')
    if not os.path.exists(arquivo):
        raise SystemExit(f'Não encontrei {arquivo} — ajuste PAINELPAC_DIR em python/config.env.')
    sys.path.insert(0, pasta)  # o módulo importa comparar_snapshots_base da mesma pasta
    spec = importlib.util.spec_from_file_location('painelpac_pc32', arquivo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- fotos
def sem_fuso(df):
    """O Excel não aceita data com fuso; tira o fuso das colunas de data/hora."""
    for c in df.columns:
        if isinstance(df[c].dtype, pd.DatetimeTZDtype):
            df[c] = df[c].dt.tz_localize(None)
    return df


def impressao(df):
    """Hash do conteúdo — o .xlsx cifrado muda a cada gravação, o conteúdo não."""
    return hashlib.sha256(df.to_csv(index=False).encode('utf-8')).hexdigest()[:16]


def gravar(df, nome, carimbo):
    """Grava data/<nome>_<carimbo>.xlsx já cifrado e confere que reabre com a senha."""
    saida = os.path.join(DATA, f'{nome}_{carimbo}.xlsx')
    buf = io.BytesIO()
    df.to_excel(buf, index=False, sheet_name=nome[:31])
    buf.seek(0)
    with open(saida, 'wb') as f:
        OOXMLFile(buf).encrypt(SENHA, f)
    with open(saida, 'rb') as f:
        protegido = msoffcrypto.OfficeFile(f)
        if not protegido.is_encrypted():
            raise SystemExit(f'ERRO: {saida} foi gravado sem senha — não publique este arquivo.')
        protegido.load_key(password=SENHA)
        aberto = io.BytesIO()
        protegido.decrypt(aberto)
    if len(pd.read_excel(aberto)) != len(df):
        raise SystemExit(f'ERRO: {saida} não reabriu com o mesmo conteúdo.')
    return os.path.basename(saida)


def data_iso(v):
    return None if v is None or pd.isna(v) else pd.Timestamp(v).strftime('%Y-%m-%d')


def main():
    url = URL.create(
        drivername='postgresql+psycopg2',
        username=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME'),
    )
    # sessão somente leitura: o script nunca altera o banco
    eng = create_engine(url, connect_args={'connect_timeout': 15,
                                           'options': '-c default_transaction_read_only=on'})
    pac = modulo_painelpac()
    agora = datetime.now()
    carimbo = f'{agora:%d%m%Y_%H%M}'

    print(f'Conectando em {url.host}:{url.port}/{url.database} ...')
    with eng.connect() as conn:
        gm = pd.read_sql(text(SQL_GM), conn)
        saci = pd.read_sql(text(SQL_SACI), conn)
        ogu = pd.read_sql(pac.QUERY, conn)
        frescor = {s['key']: s['updated_at'] for s in pac.fetch_source_freshness(conn)}

    faltam = set(PAC_COLUNAS) - set(ogu.columns)
    if faltam:
        raise SystemExit(f'A consulta do painelpac mudou — faltam colunas: {sorted(faltam)}')
    ogu = ogu[PAC_COLUNAS]

    registro = json.load(open(REGISTRO, encoding='utf-8')) if os.path.exists(REGISTRO) else []
    anterior = registro[-1] if registro else {'arquivos': {}, 'hash': {}}

    fotos = {'base_unica_gm': gm, 'carteira_saci': saci, 'painelpac_ogu': ogu}
    arquivos, hashes, linhas = {}, {}, {}
    for nome, df in fotos.items():
        df = sem_fuso(df)
        h = impressao(df)
        reaproveita = anterior['hash'].get(nome) == h and os.path.exists(
            os.path.join(DATA, anterior['arquivos'].get(nome, '')))
        arquivos[nome] = anterior['arquivos'][nome] if reaproveita else gravar(df, nome, carimbo)
        hashes[nome], linhas[nome] = h, len(df)
        print(f'  {nome}: {len(df)} linhas -> {arquivos[nome]}{" (sem mudança)" if reaproveita else ""}')

    entrada = {
        'carimbo': carimbo,
        'extraido_em': f'{agora:%Y-%m-%d %H:%M}',
        'arquivos': arquivos,
        'linhas': linhas,
        'hash': hashes,
        # data de atualização de cada fonte (a do painelpac vem da própria consulta dele)
        'atualizacao': {
            'base_unica_gm': data_iso(pd.to_datetime(gm.dte_carga).max()),
            'saci': data_iso(pd.to_datetime(saci.dte_carga).max()),
            'transferegov': frescor.get('transferegov'),
            'bdgestores': frescor.get('bdgestores'),
            'power_bi_caixa': frescor.get('power_bi_caixa'),
        },
    }
    if anterior.get('hash') == hashes:
        print('Nenhuma fonte mudou desde a extração anterior — registro mantido.')
        return
    registro.append(entrada)
    with open(REGISTRO, 'w', encoding='utf-8') as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(f'Extração {carimbo} registrada em data/extracoes.json')
    print('Atualização das fontes:', json.dumps(entrada['atualizacao'], ensure_ascii=False))


if __name__ == '__main__':
    main()
