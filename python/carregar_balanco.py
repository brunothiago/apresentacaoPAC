#!/usr/bin/env python3
"""Carrega o balanço do Governa (planilha "Export") para uma tabela no se_cgpac.

Usa a conexão e a regra de confirmação do painelgm (../painelgm/python/saci: conexao.py e
base_unica_db.confirmar): sem --confirmar não escreve nada, só mostra o que faria.

- colunas em snake_case (sem acento); o nome original de cada coluna vai no COMMENT da coluna;
- tipos: ID Governa bigint, datas date, colunas 100% numéricas double precision, o resto text;
- + dte_carga (data da carga) e txt_origem (arquivo de origem);
- confere linhas, IDs únicos e a soma das colunas numéricas contra a planilha;
- SELECT para os usuários de DB_USUARIOS_PERMISSAO (config.env do painelgm).

Uso (na raiz do apresentacaoPAC):
  uv run --with pandas --with openpyxl --with sqlalchemy --with psycopg2-binary --with python-dotenv \
      python python/carregar_balanco.py                  # simulação
  ... python python/carregar_balanco.py --confirmar      # executa
"""
import argparse
import os
import re
import sys
import unicodedata
from datetime import date

import pandas as pd
from sqlalchemy import text

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAINELGM = os.path.abspath(os.path.join(RAIZ, '..', 'painelgm', 'python', 'saci'))
sys.path.insert(0, PAINELGM)
from base_unica_db import confirmar  # noqa: E402
from conexao import criar_engine, descrever_conexao  # noqa: E402

PLANILHA = os.path.join(RAIZ, 'Base Balanço Governa jun 2026 - com inativas.xlsx')
ABA = 'Export'
SCHEMA = 'se_cgpac'
TABELA = 'balancojun2026_com_inativas'
COMPLETA = f'{SCHEMA}.{TABELA}'


def snake(nome, usados):
    s = unicodedata.normalize('NFKD', str(nome)).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9]+', '_', s).strip('_') or 'coluna'
    if s[0].isdigit():
        s = 'c_' + s
    s = s[:60]
    base, i = s, 2
    while s in usados:
        s = f'{base[:57]}_{i}'
        i += 1
    usados.add(s)
    return s


def tipo(serie):
    v = serie.dropna()
    if pd.api.types.is_datetime64_any_dtype(serie):
        return 'date'
    if len(v) and pd.api.types.is_numeric_dtype(serie):
        return 'double precision'
    return 'text'


def ler():
    df = pd.read_excel(PLANILHA, sheet_name=ABA, header=0)
    usados = set()
    cols = [(orig, snake(orig, usados)) for orig in df.columns]
    df.columns = [c for _, c in cols]
    tipos = {c: tipo(df[c]) for _, c in cols}
    tipos['id_governa'] = 'bigint'
    for c, t in tipos.items():
        if t == 'date':
            df[c] = pd.to_datetime(df[c], errors='coerce').dt.date
        elif t == 'text':
            df[c] = df[c].map(lambda x: None if pd.isna(x) else str(x))
    df['id_governa'] = pd.to_numeric(df['id_governa'], errors='raise').astype('Int64')
    df['dte_carga'] = date.today()
    df['txt_origem'] = os.path.basename(PLANILHA)
    return df, cols, tipos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--confirmar', action='store_true', help='executa de verdade')
    args = ap.parse_args()

    df, cols, tipos = ler()
    if df.id_governa.duplicated().any():
        sys.exit('ERRO: ID Governa duplicado na planilha.')
    numericas = [c for c, t in tipos.items() if t == 'double precision']
    somas = {c: float(df[c].sum()) for c in numericas}

    eng = criar_engine()
    with eng.connect() as conn:
        ja = conn.execute(text("SELECT to_regclass(:t)"), {'t': COMPLETA}).scalar()
    if ja:
        sys.exit(f'ERRO: {COMPLETA} já existe — nada foi feito.')

    contagem = pd.Series(tipos).value_counts().to_dict()
    plano = [
        f'Banco: {descrever_conexao()}',
        f'Planilha: {os.path.basename(PLANILHA)} (aba {ABA})',
        f'Criar {COMPLETA}: {len(df)} linhas, {len(cols)} colunas + dte_carga, txt_origem',
        f'Tipos: {contagem}',
        f'IDs Governa únicos: {df.id_governa.nunique()}',
        'Comentários: nome original de cada coluna (COMMENT ON COLUMN)',
        f'SELECT para: {os.getenv("DB_USUARIOS_PERMISSAO") or "(ninguém)"}',
    ]
    if not confirmar('CARGA DO BALANÇO DE JUNHO/2026 NO BANCO', plano, args.confirmar):
        return

    ddl = ',\n  '.join(f'"{c}" {tipos[c]}' for _, c in cols) + ',\n  dte_carga date NOT NULL,\n  txt_origem text'
    with eng.begin() as conn:
        conn.execute(text(f'CREATE TABLE {COMPLETA} (\n  {ddl},\n  PRIMARY KEY (id_governa)\n)'))
        df.to_sql(TABELA, conn, schema=SCHEMA, if_exists='append', index=False, method='multi', chunksize=300)
        conn.execute(text(f"COMMENT ON TABLE {COMPLETA} IS :c"),
                     {'c': f'Balanço Novo PAC junho/2026 (Governa), com inativas — {os.path.basename(PLANILHA)}, '
                           f'carregado em {date.today():%d/%m/%Y}'})
        for orig, c in cols:
            conn.execute(text(f'COMMENT ON COLUMN {COMPLETA}."{c}" IS :c'), {'c': str(orig)})
        # conferência dentro da transação: se não bater, nada fica gravado
        n = conn.execute(text(f'SELECT count(*) FROM {COMPLETA}')).scalar()
        if n != len(df):
            raise SystemExit(f'ERRO: gravou {n} linhas, esperava {len(df)} — desfeito.')
        for c, s in somas.items():
            sb = conn.execute(text(f'SELECT coalesce(sum("{c}"), 0) FROM {COMPLETA}')).scalar()
            if abs(float(sb) - s) > max(1e-6 * abs(s), 0.01):
                raise SystemExit(f'ERRO: soma de {c} difere (banco {sb} × planilha {s}) — desfeito.')
        for u in [u.strip() for u in (os.getenv('DB_USUARIOS_PERMISSAO') or '').split(',') if u.strip()]:
            conn.execute(text(f'GRANT SELECT ON {COMPLETA} TO "{u}"'))
    print(f'OK: {COMPLETA} — {len(df)} linhas; somas de {len(somas)} colunas numéricas conferidas.')


if __name__ == '__main__':
    main()
