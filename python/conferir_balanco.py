#!/usr/bin/env python3
"""Conciliação balanço Governa × carteira da apresentação — grava conferencia/balanco_conciliacao.txt.

Fora do git (dados por contrato). Usa a última extração (dados.load()).
Uso: uv run --with pandas --with openpyxl --with python-dotenv --with msoffcrypto-tool \
         python python/conferir_balanco.py
"""
import os
import sys

import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import dados  # noqa: E402

D = dados.load()
ext = D['extracao']
bal = dados.abrir(ext['arquivos']['balanco_governa'])
s, bx = D['saci'], D['bx']
bal['g'] = bal.fase.map(dados.bal_grupo).map({3: 'concluída', 1: 'em execução', 2: 'paralisada', 0: 'outras'})
idg = pd.to_numeric(s.id_governa, errors='coerce')


def onde(r):
    if r.id_governa in set(idg.dropna()):
        return '1 contrato da carteira (SACI)'
    if r.secretaria == 'SNH':
        return '2 SNH (fora da carteira)'
    if r.status_do_id != 'Ativo':
        return '3 inativo'
    return '4 sem contrato no SACI (entra como item do balanço)'


bal['onde'] = bal.apply(onde, axis=1)
a = s[~s.dsc_situacao_contrato_mcid.isin(['Em Contratação', 'Cancelado ou Distratado'])]
gb = a.bal_g.map({3: 'concluída', 1: 'em execução', 2: 'paralisada', 0: 'outra / sem balanço'})
os.makedirs(os.path.join(RAIZ, 'conferencia'), exist_ok=True)
saida = os.path.join(RAIZ, 'conferencia', 'balanco_conciliacao.txt')
with open(saida, 'w', encoding='utf-8') as f:
    f.write(f'Balanço Governa ({ext["atualizacao"].get("balanco")}) × carteira — extração {ext["extraido_em"]}\n\n')
    f.write('1) Balanço: grupo de fase × onde está\n')
    f.write(pd.crosstab(bal.onde, bal.g, margins=True).to_string() + '\n\n')
    f.write('2) Contratos assinados do SACI: situação da obra no SACI × grupo no balanço\n')
    f.write(pd.crosstab([a.dsc_fase_pac, a.dsc_situacao_objeto_mcid.fillna('(vazio)')], gb, margins=True).to_string() + '\n\n')
    f.write('3) Itens do balanço sem contrato no SACI (sem SNH, ativos, em obra/concluídos)\n')
    f.write(bx.groupby(['secretaria', 'modalidade', 'fase']).size().rename('qtd').to_frame().to_string() + '\n')
print('escrito:', saida)
