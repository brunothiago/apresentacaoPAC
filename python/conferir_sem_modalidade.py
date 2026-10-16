#!/usr/bin/env python3
"""Lista os contratos que caem em "Outras / sem modalidade" — para conferência.

Grava conferencia/sem_modalidade.txt (fora do git: dados por contrato, repositório público).
Uso (na raiz do projeto):
  uv run --with pandas --with openpyxl --with python-dotenv --with msoffcrypto-tool \
         python python/conferir_sem_modalidade.py
"""
import os
import sys

import pandas as pd

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import dados  # noqa: E402

SAIDA = os.path.join(RAIZ, 'conferencia', 'sem_modalidade.txt')

D = dados.load()
ext = D['extracao']
saci = D['saci'][D['saci']['mod'] == dados.OUTRAS].copy()
ogu = D['ogu'][D['ogu']['mod'] == dados.OUTRAS].copy()
# situação na apresentação: fora (bln_pac = NÃO no SACI) ou dentro
saci['na_apresentacao'] = saci.excl.map({True: 'fora (bln_pac = NÃO)', False: 'dentro'})
ogu['na_apresentacao'] = ogu.excl.map({True: 'fora (bln_pac = NÃO)', False: 'dentro'})

saci['vlr_investimento'] = saci.vlr_investimento.map(
    lambda v: '—' if pd.isna(v) else f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.'))
cols_saci = ['na_apresentacao', 'cod_tci', 'num_convenio', 'num_proposta_selecao_pac', 'dsc_fase_pac', 'txt_sigla_secretaria',
             'txt_uf', 'txt_municipio', 'txt_eixo', 'txt_subeixo', 'txt_modalidade', 'txt_fonte',
             'dsc_situacao_contrato_mcid', 'dsc_situacao_objeto_mcid', 'vlr_investimento']
cols_ogu = ['na_apresentacao', 'cod_tci_saci', 'num_convenio_saci', 'num_proposta_selecao_pac_saci', 'txt_uf_saci',
            'txt_modalidade_saci', 'dsc_situacao_contrato_mcid_saci', 'status_suspensiva_calc', 'fase_atual_calc']

# vazio vira "—" (senão o groupby descarta as linhas sem modalidade)
saci = saci[cols_saci].astype(object).where(saci[cols_saci].notna(), '—')
ogu = ogu[cols_ogu].astype(object).where(ogu[cols_ogu].notna(), '—')

pd.set_option('display.width', 400)
pd.set_option('display.max_colwidth', 40)
with open(SAIDA, 'w', encoding='utf-8') as f:
    f.write(f'Contratos em "Outras / sem modalidade" — extração {ext["extraido_em"]}\n')
    f.write('Regra: modalidade da base GM quando a proposta casa; senão a do SACI. Cai aqui quem não casa\n')
    f.write('com a base GM e não tem uma das 10 modalidades no SACI (vazia ou Assessoria Técnica HIS).\n\n')

    f.write(f'== SACI (view_mat_carteira_investimento) — {len(saci)} contratos\n\n')
    f.write(f'Sem número de proposta de seleção: {(saci.num_proposta_selecao_pac == "—").sum()}\n\n')
    resumo = saci.groupby(['na_apresentacao', 'txt_sigla_secretaria', 'txt_modalidade', 'txt_fonte', 'dsc_situacao_contrato_mcid']).size()
    f.write(resumo.rename('qtd').to_frame().to_string() + '\n\n')
    f.write(saci[cols_saci].sort_values(['na_apresentacao', 'txt_sigla_secretaria', 'txt_modalidade', 'cod_tci']).to_string(index=False) + '\n\n')

    f.write(f'== painelpac (OGU) — {len(ogu)} contratos (os mesmos do SACI, só OGU)\n\n')
    resumo = ogu.groupby(['na_apresentacao', 'txt_modalidade_saci', 'dsc_situacao_contrato_mcid_saci', 'status_suspensiva_calc']).size()
    f.write(resumo.rename('qtd').to_frame().to_string() + '\n\n')
    f.write(ogu[cols_ogu].sort_values(['na_apresentacao', 'cod_tci_saci']).to_string(index=False) + '\n')
print('escrito:', SAIDA, f'({len(saci)} SACI, {len(ogu)} painelpac)')
