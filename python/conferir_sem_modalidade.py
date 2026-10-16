#!/usr/bin/env python3
"""Lista, para verificação manual, os itens sem modalidade que estão FORA da apresentação pela exceção provisória.

Grava conferencia/sem_modalidade.txt (fora do git: dados por contrato). Usa a última extração (dados.load()):
  1. contratos do SACI (Novo PAC Seleção / Migrado, sem SNH, bln_pac = SIM) em "Outras / sem modalidade";
  2. itens do balanço Governa sem contrato no SACI (sem SNH, ativos, em obra/concluídos) sem modalidade.
Os que saíram por bln_pac = NÃO ficam num resumo à parte.

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


def br(v):
    return '—' if pd.isna(v) else f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def txt(v):
    return '—' if v is None or pd.isna(v) or str(v).strip() == '' else str(v)


def dt(v):
    return '—' if pd.isna(v) else f'{pd.Timestamp(v):%d/%m/%Y}'


D = dados.load()
ext = D['extracao']
s, o, bx = D['saci'], D['ogu'], D['bx']
og = o.set_index('cod_tci_saci')
fora = s[s.semmod].sort_values(['txt_sigla_secretaria', 'txt_fonte', 'txt_uf', 'cod_tci'])
bfora = bx[bx['mod'] == dados.OUTRAS].sort_values(['secretaria', 'modalidade', 'uf', 'id_governa'])
bln = s[s.excl]

L = [
    'EXCEÇÃO PROVISÓRIA — itens sem modalidade fora da apresentação (para verificação manual)',
    f'Extração {ext["extraido_em"]} · SACI {ext["atualizacao"]["saci"]} · balanço {ext["atualizacao"].get("balanco")}',
    '',
    'Critério: caem em "Outras / sem modalidade" quando não casam com a base GM (sem proposta de seleção ligada)',
    'e a modalidade do SACI / do balanço não é uma das 10 da apresentação. Enquanto a exceção valer, saem de',
    'todos os slides; as notas de rodapé dizem quantos saíram em cada recorte.',
    '',
    f'1) CONTRATOS DO SACI — {len(fora)} contratos · repasse R$ {br(fora.vlr_repasse.sum())}',
    '',
]
res = fora.groupby([fora.txt_sigla_secretaria.fillna('—'), fora.txt_fonte, fora.txt_modalidade.fillna('(vazia)'),
                    fora.dsc_situacao_contrato_mcid]).agg(qtd=('cod_tci', 'size'), repasse=('vlr_repasse', 'sum'))
res['repasse'] = res.repasse.map(br)
L += [res.to_string(), '']
for i, (_, r) in enumerate(fora.iterrows(), 1):
    p = og.loc[r.cod_tci] if r.cod_tci in og.index else None
    etapa = f' · suspensiva {p.status_suspensiva_calc} · etapa {p.fase_atual_calc}' if p is not None else ''
    L += [
        f'{i:2d}. [ ] TCI {r.cod_tci} · convênio {txt(r.num_convenio)} · {txt(r.txt_municipio)}/{txt(r.txt_uf)} · {txt(r.txt_sigla_secretaria)} · {r.txt_fonte}',
        f'      fase {r.dsc_fase_pac} · eixo {txt(r.txt_eixo)} · subeixo {txt(r.txt_subeixo)} · modalidade SACI {txt(r.txt_modalidade)}',
        f'      contrato {r.dsc_situacao_contrato_mcid} (assinado {dt(r.dte_assinatura_contrato)}) · obra {txt(r.dsc_situacao_objeto_mcid)}{etapa}',
        f'      repasse R$ {br(r.vlr_repasse)} · investimento R$ {br(r.vlr_investimento)} · proposta de seleção {txt(r.num_proposta_selecao_pac)}',
        f'      https://saci.cidades.gov.br/contratos/{r.cod_tci}',
        '      modalidade correta: ____________________________',
        '',
    ]

L += [f'2) ITENS DO BALANÇO GOVERNA SEM CONTRATO NO SACI — {len(bfora)} itens · total previsto Novo PAC R$ {br(bfora.vlr.sum())}', '']
for i, (_, r) in enumerate(bfora.iterrows(), 1):
    L += [
        f'{i:2d}. [ ] ID Governa {int(r.id_governa)} · {txt(r.secretaria)} · {txt(r.uf)} · fonte {txt(r.fonte)}',
        f'      modalidade no balanço: {txt(r.modalidade)} · subeixo {txt(r.subeixo)}',
        f'      fase {txt(r.fase)} · execução física {br(r["exec"])}% · total previsto R$ {br(r.vlr)} · sistema {txt(r.sistema_de_referencia)}',
        '      modalidade correta: ____________________________',
        '',
    ]

L += [f'3) PARA REFERÊNCIA — {len(bln)} contratos fora por bln_pac = NÃO no SACI (regra permanente, não é a exceção)', '']
r3 = bln.groupby([bln.txt_sigla_secretaria.fillna('—'), bln.bln_emenda.fillna('—'), bln.dsc_situacao_contrato_mcid]).size().rename('qtd')
L += [r3.to_frame().to_string(), '']

os.makedirs(os.path.dirname(SAIDA), exist_ok=True)
open(SAIDA, 'w', encoding='utf-8').write('\n'.join(L))
print('escrito:', SAIDA, f'({len(fora)} contratos SACI + {len(bfora)} itens do balanço)')
