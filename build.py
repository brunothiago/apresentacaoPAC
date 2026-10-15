#!/usr/bin/env python3
"""Gera index.html — apresentação "Novo PAC — MCid · Balanço da carteira" para a Secretaria-Executiva.

Caminho em cinco etapas, dois slides cada: Seleção → Suspensivas → Licitação → Contratação →
Execução. Layout e navegação da novopac-apresentacao (assets/), com os mesmos filtros de UF,
status (selecionadas / enquadradas) e ano, que valem para todos os slides.

Fontes (fotos do banco em data/, carga e regras em dados.py):
- Seleção: se_cgpac.tab_base_unica_gm (painelgm);
- Suspensivas e Licitação: consulta OGU do painelpac (status de prazo do dia da extração);
- Contratação: base GM (selecionadas) × se_saci.view_mat_carteira_investimento (contratos);
- Execução: se_saci.view_mat_carteira_investimento (Seleção + Migrado, sem cancelados).

> Não edite o index.html à mão: todo ajuste vai aqui, senão o próximo build desfaz.
"""
import json
import os
from datetime import datetime

import pandas as pd

import dados

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = f'{HERE}/index.html'
PDF_NAME = 'novopac-balanco-carteira.pdf'
VERSAO = '1.0'  # subir a cada commit que altere a apresentação
# histórico exibido no popup do "versão x.y" (encerramento) — acrescentar uma linha a cada versão
HISTORICO = [
    ('1.0', 'Primeira versão: seleção, suspensivas, licitação, contratação e execução.'),
]

D = dados.load()
EXT = D['extracao']
MODS = dados.MODS


def br(iso):
    return '—' if not iso else datetime.strptime(iso, '%Y-%m-%d').strftime('%d/%m/%Y')


def br_curta(iso):
    return '—' if not iso else datetime.strptime(iso, '%Y-%m-%d').strftime('%d/%m')


AT = EXT['atualizacao']
EXTRAIDO = datetime.strptime(EXT['extraido_em'], '%Y-%m-%d %H:%M')
HOJE = pd.Timestamp(EXTRAIDO.date())  # referência dos prazos: o dia da extração
DT_GM, DT_SACI = br(AT['base_unica_gm']), br(AT['saci'])
FONTES_PAC = (f'SACI {br_curta(AT["saci"])} · Transferegov {br_curta(AT["transferegov"])} · '
              f'Caixa {br_curta(AT["power_bi_caixa"])} · BDGestores {br_curta(AT["bdgestores"])}')
# "atualizado em" de cada slide (linha da tabela) — as datas de cada fonte vão no rodapé
AT_GM = f'Atualizado em <b>{DT_GM}</b>'
AT_SACI = f'Atualizado em <b>{DT_SACI}</b>'
AT_CT = f'Atualizado em <b>{br_curta(AT["base_unica_gm"])}</b> (GM) e <b>{br_curta(AT["saci"])}</b> (SACI)'
AT_PAC = f'Situação em <b>{EXTRAIDO:%d/%m/%Y}</b>'
SRC_GM = 'MCid · Portarias de seleção do Novo PAC (base única GM)'
SRC_PAC = f'painelpac ({FONTES_PAC})'
SRC_SACI = 'SACI (view_mat_carteira_investimento)'

# ---------------------------------------------------------------- linhas compactas
FONTE = {'FIN': 0, 'OGU': 1}
SIT_CT = ['Contratado - Normal', 'Contratado - Suspensiva', 'Contratado - Concluído',
          'Em Contratação', 'Cancelado ou Distratado']  # índice 5 = outros (TCE, liminar, prest. contas)
SIT_OBRA = {'Não iniciada': 0, 'Não cadastrada': 0, 'Cadastrada': 0, 'Sem informação': 0,
            'Em execução': 1, 'Paralisada': 2, 'Concluída': 3, 'Inacabada': 4,
            'Cancelada': 5, 'Inativada': 5}
FASES = ['SEM ANDAMENTO', 'SUSPENSIVA', 'SUSPENSIVA RETIRADA', 'LAE', 'PUBLICACAO LICITACAO',
         'HOMOLOGACAO', 'VRPL', 'AIO', 'OBRA INICIADA']
PRAZO = {'Concluída no prazo': 1, 'Concluída em atraso': 1, 'No prazo': 2, 'Próximos 30 dias': 3,
         'Vencida': 4}  # 0 = não se aplica / inconsistência
PC48 = {'No prazo': 1, 'Próximos 30 dias': 2, 'Vencida': 3}  # 0 = não se aplica
SUSP = {'RETIRADA': 0, 'PENDENTE': 1, 'SEM SUSPENSIVA': 2}


def num(v, casas=2):
    return None if pd.isna(v) else round(float(v), casas)


def idx_sit_ct(s):
    if s == 'Contratado - Suspensiva e Liminar':
        return 1
    return SIT_CT.index(s) if s in SIT_CT else 5


# seleção: [mod, fonte, uf, kind, ogu, fin, ano]  · kind 0 migrada · 1 selecionada · 2 enquadrada
SEL = []
for _, r in D['mig'].iterrows():
    SEL.append([MODS.index(r['mod']), FONTE.get(r.fonte, 2), r.uf, 0,
                num(r.vlr_portaria_ogu), num(r.vlr_portaria_fin), ''])
for _, r in D['sel'].iterrows():
    SEL.append([MODS.index(r['mod']), FONTE.get(r.fonte, 2), r.uf, 2 if r.status_selecao == 'enquadrada' else 1,
                num(r.vlr_portaria_ogu), num(r.vlr_portaria_fin), dados.ANO_LABEL[int(r.ano_selecao)]])

# contratos SACI: [mod, fonte, uf, kind, ano, sitContrato, sitObra, investimento, repasse, %fís, %fin]
CT = []
for _, r in D['saci'].iterrows():
    CT.append([MODS.index(r['mod']), FONTE.get(r.txt_fonte, 2), r.uf, int(r.kind), r.ano,
               idx_sit_ct(r.dsc_situacao_contrato_mcid), SIT_OBRA.get(r.dsc_situacao_objeto_mcid, 0),
               num(r.vlr_investimento) or 0, num(r.vlr_repasse) or 0,
               num(r.prc_execucao_fisica, 1), num(r.prc_execucao_financ, 1)])

# contratos OGU (painelpac): [mod, uf, kind, ano, repasse, cancelado, susp, pc48, tetoVencido,
#                             fase, pubLicitação, homLicitação, casaCivil]
OG = []
for _, r in D['ogu'].iterrows():
    teto = pd.to_datetime(r.prazo_suspensiva_pc48_prorrogado_calc, errors='coerce')
    OG.append([MODS.index(r['mod']), r.uf, int(r.kind), r.ano, num(r.vlr_repasse_saci),
               1 if r.dsc_situacao_contrato_mcid_saci == 'Cancelado ou Distratado' else 0,
               SUSP.get(r.status_suspensiva_calc, 2), PC48.get(r.status_prazo_suspensiva_pc48_calc, 0),
               1 if (r.status_suspensiva_calc == 'PENDENTE' and pd.notna(teto) and teto < HOJE) else 0,
               FASES.index(r.fase_atual_calc) if r.fase_atual_calc in FASES else 0,
               PRAZO.get(r.status_pub_licitacao_calc, 0), PRAZO.get(r.status_homolog_licitacao_calc, 0),
               1 if r.status_regra_casa_civil_calc == 'Cumpriu o prazo' else 0])

ANOS = sorted({r[6] for r in SEL if r[6]})
ufs = sorted(({r[2] for r in SEL} | {r[2] for r in CT} | {r[1] for r in OG}) - {'BR', ''})
uf_opts = '<option value="">Brasil — todas as UFs</option>' + ''.join(
    f'<option value="{u}">{u}</option>' for u in ufs)
print(f'seleção {len(SEL)} | contratos SACI {len(CT)} | contratos OGU painelpac {len(OG)} | UFs {len(ufs)}')

# ---------------------------------------------------------------- assets
DECK_CSS = open(f'{HERE}/assets/deck.css', encoding='utf-8').read()
DECK_JS = open(f'{HERE}/assets/deck-stage.js', encoding='utf-8').read().replace('</script', '<\\/script')
DECK_CHROME = open(f'{HERE}/assets/deck-chrome.html', encoding='utf-8').read()

EXTRA_CSS = """
  body{ margin:0; background:var(--navy); }
  /* ---- tabelas de dados ---- */
  table.data{ width:100%; border-collapse:collapse; }
  table.data th{ text-align:right; font-size:16px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--ink-soft); padding:0 18px 8px; border-bottom:2px solid var(--line-strong); line-height:1.2; vertical-align:bottom; }
  table.data th:first-child{ text-align:left; padding-left:0; }
  table.data thead tr.grp th{ text-align:center; border-bottom:1px solid var(--line-strong); padding-bottom:6px; color:var(--accent-deep); letter-spacing:.1em; }
  table.data thead tr.grp th.vazio{ border-bottom:0; }
  table.data td{ padding:5px 18px; border-bottom:1px solid var(--line); font-size:22px; color:var(--ink); font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; vertical-align:middle; }
  table.data td:first-child{ text-align:left; padding-left:0; font-weight:600; }
  table.data tr.tot td{ border-top:2px solid var(--line-strong); border-bottom:0; font-weight:800; color:var(--navy); }
  table.data td.empty{ text-align:center; font-weight:400; color:var(--ink-soft); padding:60px 0; }
  table.data td.hl{ color:var(--accent-deep); font-weight:700; }
  table.data td.alerta{ color:#9A383A; font-weight:700; }
  table.data td.zero{ color:var(--ink-soft); opacity:.55; }
  .body.tight{ padding-top:18px; }
  .title-block.tight{ margin-bottom:0; }
  .title-block{ flex:1 1 auto; min-width:0; }
  .ctrls{ flex:none; }
  .title-block .title{ font-size:48px; line-height:1.05; display:flex; align-items:center; gap:22px; }
  .etapa{ flex:none; display:inline-flex; flex-direction:column; align-items:center; justify-content:center; width:104px; height:74px; background:var(--accent); color:#fff; border-radius:2px; line-height:1; }
  .etapa .n{ font-size:30px; font-weight:800; }
  .etapa .t{ font-size:12px; font-weight:800; letter-spacing:.12em; text-transform:uppercase; margin-top:6px; }
  /* linha de metadados da tabela: atualização · contagem · recorte */
  .tmeta{ font-size:18px; color:var(--ink-soft); margin:0 0 10px; line-height:1.4; }
  .tmeta b{ color:var(--navy); font-weight:700; }
  .tmeta .sep{ margin:0 10px; opacity:.5; }
  .nota{ font-size:17px; color:var(--ink-soft); margin:8px 0 0; font-style:italic; line-height:1.35; }
  /* destaques (KPIs) */
  .kpis{ display:grid; grid-template-columns:repeat(4, 1fr); gap:22px; margin:0 0 14px; }
  .kpi{ background:var(--paper-2); border-left:5px solid var(--accent); padding:8px 20px 10px; }
  .kpi .kv{ font-size:40px; font-weight:800; color:var(--navy); letter-spacing:-.02em; font-variant-numeric:tabular-nums; line-height:1.1; }
  .kpi .kl{ font-size:16px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:var(--ink-soft); margin-top:4px; }
  .kpi.alerta{ border-left-color:#BC4749; }
  .kpi.alerta .kv{ color:#9A383A; }
  .kpi.ok{ border-left-color:#168821; }
  .kpi.ok .kv{ color:#0F5F18; }
  /* controles de filtro (UF + status + ano), numa linha só */
  .ctrls{ display:flex; flex-direction:column; align-items:flex-end; gap:10px; }
  .ufctl, .stctl{ display:flex; align-items:center; gap:12px; }
  .ufctl label, .stctl label{ font-size:18px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:var(--ink-soft); }
  .ufctl select{ font-family:'rawline','Raleway',sans-serif; font-size:20px; font-weight:600; color:var(--navy); background:#fff; border:1px solid var(--line-strong); border-radius:2px; padding:7px 12px; min-width:260px; cursor:pointer; }
  .ufctl select:focus{ outline:2px solid var(--blue); outline-offset:1px; }
  .ctrow{ display:flex; gap:18px; }
  .stgrp{ display:flex; border:1px solid var(--line-strong); border-radius:2px; overflow:hidden; }
  .stbtn{ font-family:'rawline','Raleway',sans-serif; font-size:18px; font-weight:700; letter-spacing:.02em; padding:8px 16px; background:#fff; color:var(--ink-soft); border:0; cursor:pointer; }
  .stbtn + .stbtn{ border-left:1px solid var(--line-strong); }
  .stbtn[aria-pressed="true"]{ background:var(--blue); color:#fff; }
  .stbtn:focus-visible{ outline:2px solid var(--blue); outline-offset:-2px; }
  .title-row{ display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; gap:40px; }
  @media print{ .ufctl select{ border:0; padding:0; } }
  /* cores por etapa (paleta da novopac-apresentacao) */
  .e1{ --accent:#1351B4; --accent-deep:#0C3C8F; }
  .e2{ --accent:#BC4749; --accent-deep:#9A383A; }
  .e3{ --accent:#B38600; --accent-deep:#8A6800; }
  .e4{ --accent:#0C7B93; --accent-deep:#08596B; }
  .e5{ --accent:#168821; --accent-deep:#0F5F18; }
  /* roteiro da capa */
  .roteiro{ display:flex; gap:0; margin-top:120px; }
  .roteiro .passo{ flex:1; border-top:4px solid var(--c); padding:18px 26px 0 0; }
  .roteiro .passo .pn{ font-size:22px; font-weight:800; color:var(--c); letter-spacing:.12em; }
  .roteiro .passo .pt{ font-size:32px; font-weight:700; color:#fff; margin-top:6px; }
  /* botões do rodapé de encerramento: exportar PDF e baixar as bases */
  .xlsxlink{ display:inline-flex; align-items:center; gap:10px; margin-left:18px;
    font-family:'rawline','Raleway',sans-serif; font-size:20px; font-weight:700;
    letter-spacing:.08em; text-transform:uppercase; color:var(--amber-bright);
    text-decoration:none; background:transparent; cursor:pointer;
    border:1px solid rgba(255,255,255,.32); border-radius:2px; padding:8px 14px;
    transition:background .15s, border-color .15s; }
  .xlsxlink:hover{ background:rgba(255,255,255,.10); border-color:var(--amber-bright); }
  .xlsxlink .lock{ width:15px; height:15px; margin-left:-2px; opacity:.85; }
  .xlsxlink svg{ width:18px; height:18px; fill:none; stroke:currentColor; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
  @media print{ .xlsxlink, .rotate-hint{ display:none !important; } }
  @media (hover: none), (pointer: coarse){ .deck-bar-zone{ display:none !important; } }
  .fsbtn{ display:none; position:fixed; z-index:2147483000;
    right:max(16px, env(safe-area-inset-right)); bottom:max(16px, env(safe-area-inset-bottom));
    width:54px; height:54px; border-radius:50%; border:1px solid rgba(255,255,255,.28);
    background:rgba(7,29,65,.55); backdrop-filter:blur(8px); cursor:pointer;
    align-items:center; justify-content:center; padding:0; }
  .fsbtn svg{ width:22px; height:22px; stroke:#fff; fill:none; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
  .fsbtn:active{ background:rgba(19,81,180,.75); }
  @media (hover: none), (pointer: coarse){ .fsbtn{ display:flex; } }
  @media print{ .fsbtn{ display:none !important; } }
  /* versão da apresentação (rodapés) */
  .ver{ font-size:18px; font-weight:600; letter-spacing:.06em; opacity:.72; margin-left:14px; white-space:nowrap; }
  .verwrap{ position:relative; display:inline-block; }
  .verlink{ background:none; border:0; padding:0; font-family:inherit; color:inherit; cursor:pointer; text-decoration:underline dotted; text-underline-offset:4px; }
  .verlink:hover{ opacity:1; color:var(--amber-bright); }
  .verlog{ position:absolute; bottom:calc(100% + 16px); right:0; width:640px; background:var(--navy-2); border:1px solid var(--line-dark); border-left:4px solid var(--amber-bright); padding:24px 28px; text-align:left; box-shadow:0 12px 40px rgba(0,0,0,.45); }
  .verlog h3{ margin:0 0 14px; font-size:16px; font-weight:700; letter-spacing:.12em; text-transform:uppercase; color:var(--amber-bright); }
  .verlog ul{ margin:0; padding:0; list-style:none; }
  .verlog li{ display:flex; gap:16px; font-size:18px; line-height:1.75; color:var(--paper); }
  .verlog li b{ flex:none; width:52px; color:var(--blue-soft); font-variant-numeric:tabular-nums; }
  @media print{ .verlog{ display:none !important; } }
  /* quadro de fontes e atualização (encerramento) */
  .fontes{ display:grid; grid-template-columns:repeat(2, minmax(0, 1fr)); gap:14px 60px; margin-top:70px; max-width:1500px; }
  .fontes div{ font-size:24px; color:var(--paper); border-left:3px solid var(--amber-bright); padding-left:18px; line-height:1.35; }
  .fontes b{ display:block; font-size:17px; letter-spacing:.12em; text-transform:uppercase; color:var(--blue-soft); }
"""

HEAD = f"""<!DOCTYPE html>
<html lang="pt-BR"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>Novo PAC — Balanço da carteira</title>
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Novo PAC">
<meta name="theme-color" content="#071D41">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="">
<!-- Tipografia oficial do Governo Federal (Padrão Digital de Governo — gov.br/ds) -->
<link rel="stylesheet" href="https://cdngovbr-ds.estaleiro.serpro.gov.br/design-system/fonts/rawline/css/rawline.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Raleway:ital,wght@0,300;0,400;0,500;0,600;0,700;0,800;1,300;1,400;1,500;1,600;1,700&display=swap">
<style>{DECK_CSS}
{EXTRA_CSS}</style>
</head>
<body>
"""

CHROME_TOP = """    <div class="top">
      <div class="eyebrow">Novo PAC — MCid · Balanço da carteira</div>
      <div class="brand"><span class="govbr">gov<b>.br</b></span><span class="div"></span><span class="min">Ministério das Cidades - DMP/SE</span></div>
    </div>
    <hr class="hr">
"""


def foot(fonte):
    return f"""    <hr class="hr">
    <div class="bot">
      <span class="org">Fonte: {fonte} · extração de {EXTRAIDO:%d/%m/%Y %H:%M}</span>
      <span style="display:inline-flex; align-items:baseline;"><span class="pageno"></span><span class="ver">versão {VERSAO}</span></span>
    </div>
"""


ETAPAS = {1: 'Seleção', 2: 'Suspensivas', 3: 'Licitação', 4: 'Contratação', 5: 'Execução'}


def cabecalho(colunas):
    """colunas: lista de rótulos ou de (grupo, [rótulos]) — grupos viram uma 2ª linha de cabeçalho."""
    if not any(isinstance(c, tuple) for c in colunas):
        return '<tr><th>Modalidade</th>' + ''.join(f'<th>{c}</th>' for c in colunas) + '</tr>'
    grp, sub = ['<th class="vazio"></th>'], ['<th>Modalidade</th>']
    for c in colunas:
        if isinstance(c, tuple):
            grp.append(f'<th colspan="{len(c[1])}">{c[0]}</th>')
            sub += [f'<th>{s}</th>' for s in c[1]]
        else:
            grp.append('<th class="vazio"></th>')
            sub.append(f'<th>{c}</th>')
    return '<tr class="grp">' + ''.join(grp) + '</tr><tr>' + ''.join(sub) + '</tr>'


def slide(etapa, n, titulo, tabela_id, colunas, legenda, atualizado, fonte, dek='', kpis=None, nota=''):
    dek_html = f'\n          <p class="dek" style="max-width:66ch; font-style:italic; font-size:23px; margin:6px 0 0 126px;">{dek}</p>' if dek else ''
    anos_btns = ''.join(f'<button type="button" class="stbtn anobtn" data-ano="{a}" aria-pressed="true">{a}</button>' for a in ANOS)
    kpi_html = ''
    if kpis:
        cards = ''.join(f'<div class="kpi{" " + k[2] if len(k) > 2 else ""}"><div class="kv" data-kpi="{tabela_id}:{i}">—</div><div class="kl">{k[0]}</div></div>'
                        for i, k in enumerate(kpis))
        kpi_html = f'\n        <div class="kpis">{cards}</div>'
    nota_html = f'\n        <p class="nota">{nota}</p>' if nota else ''
    return f"""
  <section class="p2 content e{etapa}" data-label="{ETAPAS[etapa]} {n}">
{CHROME_TOP}    <div class="body tight">
      <div class="title-row">
        <div class="title-block tight">
          <h2 class="title"><span class="etapa"><span class="n">0{etapa}</span><span class="t">{ETAPAS[etapa]}</span></span>{titulo}</h2>{dek_html}
        </div>
        <div class="ctrls">
          <div class="ufctl"><label for="{tabela_id}-uf">Recorte</label><select id="{tabela_id}-uf" class="ufsel">{uf_opts}</select></div>
          <div class="ctrow">
            <div class="stctl"><label>Status</label><div class="stgrp"><button type="button" class="stbtn" data-st="sel" aria-pressed="true">Selecionadas</button><button type="button" class="stbtn" data-st="enq" aria-pressed="true">Enquadradas</button></div></div>
            <div class="stctl anoctl"><label>Ano</label><div class="stgrp">{anos_btns}</div></div>
          </div>
        </div>
      </div>
      <div class="col grow" style="justify-content:flex-start;">{kpi_html}
        <p class="tmeta">{atualizado}<span class="sep">·</span>{legenda}<span class="sep">·</span>Status: <b class="stname">selecionadas + enquadradas</b><span class="sep">·</span>Anos: <b class="anoname">todos</b><span class="sep">·</span>Recorte: <b class="ufname">Brasil</b></p>
        <table class="data dense" id="{tabela_id}">
          <thead>{cabecalho(colunas)}</thead>
          <tbody></tbody>
        </table>{nota_html}
      </div>
    </div>
{foot(fonte)}  </section>
"""


HISTORICO_LI = '\n'.join(f'            <li><b>{v}</b>{t}</li>' for v, t in HISTORICO)
XLSX = EXT['arquivos']

SLIDES = f"""
<deck-stage width="1920" height="1080" no-rail="">

  <!-- ============ CAPA ============ -->
  <section class="p2 dark cover" data-label="Capa" style="position:relative; overflow:hidden; z-index:0;">
    <svg class="covernet" viewBox="0 0 460 900" fill="none" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <g stroke="var(--blue-soft)" stroke-width="1.6" stroke-linecap="round">
        <line x1="120" y1="150" x2="300" y2="100"></line><line x1="300" y1="100" x2="390" y2="270"></line>
        <line x1="120" y1="150" x2="230" y2="310"></line><line x1="230" y1="310" x2="390" y2="270"></line>
        <line x1="230" y1="310" x2="95" y2="370"></line><line x1="230" y1="310" x2="330" y2="480"></line>
        <line x1="330" y1="480" x2="390" y2="270"></line><line x1="330" y1="480" x2="300" y2="670"></line>
        <line x1="230" y1="310" x2="185" y2="550"></line><line x1="185" y1="550" x2="110" y2="650"></line>
        <line x1="185" y1="550" x2="300" y2="670"></line><line x1="300" y1="670" x2="250" y2="810"></line>
        <line x1="110" y1="650" x2="250" y2="810"></line>
      </g>
      <g fill="var(--blue-soft)">
        <circle cx="120" cy="150" r="5"></circle><circle cx="390" cy="270" r="5"></circle><circle cx="95" cy="370" r="5"></circle>
        <circle cx="330" cy="480" r="5"></circle><circle cx="185" cy="550" r="5"></circle><circle cx="110" cy="650" r="5"></circle><circle cx="250" cy="810" r="5"></circle>
      </g>
      <g fill="var(--amber-bright)">
        <circle cx="300" cy="100" r="6.5"></circle><circle cx="230" cy="310" r="8"></circle><circle cx="300" cy="670" r="6.5"></circle>
      </g>
    </svg>
    <div class="top">
      <div class="eyebrow" style="letter-spacing:.2em;">Programa de Aceleração do Crescimento</div>
      <div class="brand">
        <span class="govbr" style="color:#fff;">gov<b style="color:var(--amber-bright);">.br</b></span>
        <span class="div"></span>
        <span class="min">Ministério das Cidades - DMP/SE</span>
      </div>
    </div>
    <hr class="hr">
    <div class="body" style="justify-content:center; padding-top:0;">
      <div class="label" style="color:var(--amber-bright); margin-bottom:30px;">Secretaria-Executiva</div>
      <h1 style="font-size:140px; font-weight:800; line-height:.98; letter-spacing:-.03em; margin:0; max-width:20ch;">Novo PAC<span style="color:var(--blue-soft); font-weight:500;"> — MCid</span></h1>
      <p style="font-family:'Raleway',sans-serif; font-style:italic; font-weight:500; font-size:38px; line-height:1.4; color:var(--paper); margin:60px 0 0; max-width:48ch;">Balanço da carteira — da seleção à execução das obras.</p>
      <div class="roteiro">
        <div class="passo" style="--c:#6FA8F0;"><div class="pn">01</div><div class="pt">Seleção</div></div>
        <div class="passo" style="--c:#E48587;"><div class="pn">02</div><div class="pt">Suspensivas</div></div>
        <div class="passo" style="--c:#E5B400;"><div class="pn">03</div><div class="pt">Licitação</div></div>
        <div class="passo" style="--c:#5BC0D6;"><div class="pn">04</div><div class="pt">Contratação</div></div>
        <div class="passo" style="--c:#54C264;"><div class="pn">05</div><div class="pt">Execução</div></div>
      </div>
    </div>
    <hr class="hr">
    <div class="bot" style="border-top:0; padding-top:18px;">
      <span class="org" style="color:var(--paper);">Ministério das Cidades - DMP/SE</span>
      <div style="flex: 1;"></div>
      <span class="org" style="color:var(--paper);">Extração de {EXTRAIDO:%d/%m/%Y %H:%M}<span class="ver">versão {VERSAO}</span></span>
    </div>
  </section>

{slide(1, 1, 'Carteira de seleções do Novo PAC', 't-sel1',
       ['Qtd. FIN', 'Qtd. OGU', 'Total', 'Valor OGU<br>(R$ mi)', 'Valor FIN<br>(R$ mi)', 'Valor total<br>(R$ mi)'],
       'Contagem: migradas + novas seleções', AT_GM, SRC_GM,
       kpis=[('Propostas',), ('Valor total',), ('OGU',), ('Financiamento',)])}
{slide(1, 2, 'Novas seleções por ano', 't-sel2',
       [('Quantidade', ANOS + ['Total']), ('Valor (R$ mi)', ANOS + ['Total'])],
       'Contagem: novas seleções, sem migradas', AT_GM, SRC_GM,
       dek='Portarias de 2023, 2025 e 2026 — selecionadas e enquadradas/habilitadas.')}
{slide(2, 1, 'Cláusulas suspensivas — OGU', 't-susp1',
       ['Contratos<br>OGU', 'Com<br>suspensiva', 'Retiradas', 'Pendentes', '% retirada', 'Repasse<br>pendente (R$ mi)'],
       'Contagem: contratos OGU do Novo PAC Seleção (sem SNH), sem cancelados', AT_PAC, SRC_PAC,
       kpis=[('Com suspensiva',), ('Retiradas', '', 'ok'), ('Pendentes', '', 'alerta'), ('Repasse pendente',)])}
{slide(2, 2, 'Prazo das suspensivas pendentes', 't-susp2',
       ['Pendentes', ('Prazo inicial (PC 48/2026)', ['No prazo', 'Vence em<br>30 dias', 'Vencido']), 'Teto da<br>prorrogação<br>vencido', 'Sem prazo<br>calculado'],
       'Contagem: suspensivas pendentes (OGU)', AT_PAC, SRC_PAC,
       kpis=[('Pendentes',), ('Prazo inicial vencido', '', 'alerta'), ('Teto da prorrogação vencido', '', 'alerta'), ('Vencem em 30 dias',)],
       nota=f'Prazo contado da assinatura (PC 48/2026, art. 12): 6, 8 ou 10 meses conforme o nível do contrato; prorrogação única até 8, 12 ou 14 meses. Situação em {EXTRAIDO:%d/%m/%Y}.')}
{slide(3, 1, 'Etapa atual dos contratos OGU', 't-lic1',
       ['Sem<br>registro', 'Em<br>suspensiva', 'Suspensiva<br>retirada/LAE', 'Edital<br>publicado', 'Licitação<br>homologada', 'VRPL /<br>AIO', 'Obra<br>iniciada', 'Total'],
       'Contagem: contratos OGU do Novo PAC Seleção, sem cancelados — etapa mais avançada', AT_PAC, SRC_PAC,
       kpis=[('Aguardando licitação',), ('Edital publicado',), ('Homologada até AIO',), ('Obra iniciada', '', 'ok')])}
{slide(3, 2, 'Prazos da licitação — art. 36-A', 't-lic2',
       [('Publicação do edital', ['Publicado', 'No prazo', 'Vence em<br>30 dias', 'Vencido']), ('Homologação', ['Homologada', 'No prazo', 'Vence em<br>30 dias', 'Vencido'])],
       'Contagem: contratos OGU assinados após a PC 72/2025, com LAE', AT_PAC, SRC_PAC,
       dek='Publicação em até 60 dias da LAE e homologação em até 120 dias da publicação — data-limite de 30/10/2026.',
       nota=f'Prazos vencidos ou vencendo antes de 30/10/2026 passam para 30/10/2026 (regra do painelpac). Situação em {EXTRAIDO:%d/%m/%Y}.')}
{slide(4, 1, 'Selecionado × contratado', 't-ct1',
       ['Seleções', 'Contratos<br>assinados', 'Em<br>contratação', 'Cancelados /<br>distratados', '% assinado', 'Investimento<br>assinado (R$ mi)'],
       'Contagem: novas seleções (GM) × contratos do Novo PAC Seleção (SACI)', AT_CT, 'base única GM e ' + SRC_SACI,
       kpis=[('Seleções',), ('Contratos assinados', '', 'ok'), ('% assinado',), ('Investimento assinado',)],
       nota='Uma linha por fonte nas duas bases: proposta com OGU e FIN conta uma vez em cada fonte.')}
{slide(4, 2, 'Situação dos contratos assinados', 't-ct2',
       ['Normal', 'Suspensiva', 'Concluído', 'Outros*', 'Total', 'Qtd. OGU', 'Qtd. FIN', 'Repasse /<br>financ. (R$ mi)'],
       'Contagem: contratos assinados do Novo PAC Seleção (SACI)', AT_SACI, SRC_SACI,
       kpis=[('Assinados',), ('Normal', '', 'ok'), ('Em suspensiva', '', 'alerta'), ('Repasse / financiamento',)],
       nota='* Outros: em TCE, liminar e em prestação de contas.')}
{slide(5, 1, 'Situação das obras', 't-ex1',
       ['Não<br>iniciada', 'Em<br>execução', 'Paralisada', 'Concluída', 'Inacabada', 'Total', '% concluída'],
       'Contagem: contratos do Novo PAC Seleção + Migrado (SACI), sem cancelados', AT_SACI, SRC_SACI,
       kpis=[('Em execução',), ('Paralisadas', '', 'alerta'), ('Concluídas', '', 'ok'), ('Não iniciadas',)])}
{slide(5, 2, 'Execução média e paralisações', 't-ex2',
       [('% físico médio', ['Novas<br>seleções', 'Migradas', 'Total']), '% financeiro<br>médio', 'Paralisadas', 'Investimento<br>paralisado (R$ mi)', 'Concluídas'],
       'Médias: obras em execução ou paralisadas (média simples por contrato)', AT_SACI, SRC_SACI,
       kpis=[('% físico médio',), ('% financeiro médio',), ('Paralisadas', '', 'alerta'), ('Investimento paralisado', '', 'alerta')])}

  <!-- ============ ENCERRAMENTO ============ -->
  <section class="p2 dark" data-label="Encerramento">
    <div class="top">
      <div class="eyebrow">Novo PAC — MCid · Balanço da carteira</div>
      <div class="brand"><span class="govbr">gov<b>.br</b></span><span class="div"></span><span class="min">Ministério das Cidades - DMP/SE</span></div>
    </div>
    <hr class="hr">
    <div class="body" style="justify-content:center; padding-top:0;">
      <h2 style="font-size:120px; font-weight:800; letter-spacing:-.03em; margin:0; line-height:.95;">Obrigado.</h2>
      <p style="font-family:'Raleway',sans-serif; font-style:italic; font-weight:500; font-size:38px; line-height:1.42; color:var(--paper); margin:60px 0 0; max-width:48ch;">Novo PAC — Ministério das Cidades.</p>
      <div class="fontes">
        <div><b>Seleção</b>Base única GM (se_cgpac) · atualizada em {DT_GM}</div>
        <div><b>Contratação e execução</b>SACI — view_mat_carteira_investimento · {DT_SACI}</div>
        <div><b>Suspensivas e licitação</b>painelpac — {FONTES_PAC}</div>
        <div><b>Extração do banco</b>{EXTRAIDO:%d/%m/%Y às %H:%M}</div>
      </div>
    </div>
    <hr class="hr">
    <div class="bot" style="border-top:0; padding-top:18px;">
      <span class="org" style="color:var(--paper);">Ministério das Cidades - DMP/SE</span>
      <div style="flex: 1;"></div>
      <span class="org" style="color:var(--paper);">Extração de {EXTRAIDO:%d/%m/%Y}<span class="verwrap"><button type="button" class="ver verlink" id="verBtn" aria-haspopup="dialog" aria-expanded="false" title="Ver histórico de atualizações">versão {VERSAO}</button>
        <div class="verlog" id="verLog" role="dialog" aria-label="Histórico de atualizações" hidden>
          <h3>Atualizações da apresentação</h3>
          <ul>
{HISTORICO_LI}
          </ul>
        </div></span></span>
      <a class="xlsxlink" href="{PDF_NAME}" download title="Baixar o PDF da apresentação (um slide por página) — com filtros aplicados, o PDF é gerado refletindo os filtros">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 21V3h9l5 5v13z"></path><path d="M14 3v6h6"></path></svg>
        <span class="pdftxt">Exportar PDF</span>
      </a>
      <a class="xlsxlink" href="data/{XLSX['base_unica_gm']}" download title="Base de seleção (base única GM) — arquivo protegido por senha">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12"></path><path d="M7 10l5 5 5-5"></path><path d="M4 19h16"></path></svg>
        Seleção
        <svg class="lock" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2"></rect><path d="M8 10V7a4 4 0 0 1 8 0v3"></path></svg>
      </a>
      <a class="xlsxlink" href="data/{XLSX['carteira_saci']}" download title="Carteira do SACI (Novo PAC Seleção + Migrado) — arquivo protegido por senha">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12"></path><path d="M7 10l5 5 5-5"></path><path d="M4 19h16"></path></svg>
        SACI
        <svg class="lock" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2"></rect><path d="M8 10V7a4 4 0 0 1 8 0v3"></path></svg>
      </a>
      <a class="xlsxlink" href="data/{XLSX['painelpac_ogu']}" download title="Base OGU do painelpac (suspensivas e licitação) — arquivo protegido por senha">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 3v12"></path><path d="M7 10l5 5 5-5"></path><path d="M4 19h16"></path></svg>
        Painelpac
        <svg class="lock" viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="10" width="16" height="11" rx="2"></rect><path d="M8 10V7a4 4 0 0 1 8 0v3"></path></svg>
      </a>
    </div>
  </section>

</deck-stage>

<!-- popup do histórico de atualizações (versão no rodapé do encerramento) -->
<script>
(function () {{
  var btn = document.getElementById('verBtn');
  var log = document.getElementById('verLog');
  if (!btn || !log) return;
  function setOpen(open) {{
    log.hidden = !open;
    btn.setAttribute('aria-expanded', String(open));
  }}
  btn.addEventListener('click', function (e) {{
    e.stopPropagation();
    setOpen(log.hidden);
  }});
  document.addEventListener('click', function (e) {{
    if (!log.hidden && !log.contains(e.target)) setOpen(false);
  }});
  document.addEventListener('keydown', function (e) {{
    if (e.key === 'Escape' && !log.hidden) setOpen(false);
  }});
}})();
</script>

<!-- tela cheia no toque (iPhone/iPad): esconde a interface do navegador -->
<button type="button" class="fsbtn" id="fsBtn" aria-label="Tela cheia" title="Tela cheia">
  <svg id="fsBtnIco" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9V5a1 1 0 0 1 1-1h4M20 9V5a1 1 0 0 0-1-1h-4M4 15v4a1 1 0 0 0 1 1h4M20 15v4a1 1 0 0 1-1 1h-4"></path></svg>
</button>
<script>
(function () {{
  var b = document.getElementById('fsBtn');
  var ico = document.getElementById('fsBtnIco');
  var el = document.documentElement;
  var req = el.requestFullscreen || el.webkitRequestFullscreen;
  if (!req) {{ b.style.display = 'none'; return; }}
  function fsEl() {{ return document.fullscreenElement || document.webkitFullscreenElement; }}
  function sync() {{
    ico.innerHTML = fsEl()
      ? '<path d="M9 4v3a2 2 0 0 1-2 2H4M20 9h-3a2 2 0 0 1-2-2V4M9 20v-3a2 2 0 0 0-2-2H4M15 20v-3a2 2 0 0 1 2-2h3"/>'
      : '<path d="M4 9V5a1 1 0 0 1 1-1h4M20 9V5a1 1 0 0 0-1-1h-4M4 15v4a1 1 0 0 0 1 1h4M20 15v4a1 1 0 0 1-1 1h-4"/>';
  }}
  b.addEventListener('click', function () {{
    if (fsEl()) (document.exitFullscreen || document.webkitExitFullscreen).call(document);
    else req.call(el);
  }});
  document.addEventListener('fullscreenchange', sync);
  document.addEventListener('webkitfullscreenchange', sync);
}})();
</script>
"""

APP_JS = r"""
// ===== dados e filtros (UF, status e ano) — valem para todos os slides =====
const MODS = __MODS__;
const ANOS = __ANOS__;
// seleção (base GM): [mod, fonte, uf, kind, ogu, fin, ano] · fonte 0 FIN · 1 OGU
// kind 0 migrada · 1 selecionada · 2 enquadrada · ano '' = migrada / sem ano
const SEL = __SEL__;
// contratos SACI: [mod, fonte, uf, kind, ano, sitContrato, sitObra, investimento, repasse, %fís, %fin]
// sitContrato 0 normal · 1 suspensiva · 2 concluído · 3 em contratação · 4 cancelado · 5 outros
// sitObra 0 não iniciada · 1 em execução · 2 paralisada · 3 concluída · 4 inacabada · 5 cancelada
const CT = __CT__;
// contratos OGU (painelpac): [mod, uf, kind, ano, repasse, cancelado, susp, pc48, tetoVencido,
//   fase, pub, hom, casaCivil] · susp 0 retirada · 1 pendente · 2 sem · pc48 0 n/a · 1 no prazo ·
//   2 ≤30 dias · 3 vencido · fase = índice em FASES · pub/hom 0 n/a · 1 concluída · 2 no prazo ·
//   3 ≤30 dias · 4 vencida
const OG = __OG__;

// posição de uf / kind / ano em cada fonte
const SRC = {
  sel: { rows: SEL, uf: 2, kind: 3, ano: 6 },
  ct:  { rows: CT,  uf: 2, kind: 3, ano: 4 },
  og:  { rows: OG,  uf: 1, kind: 2, ano: 3 },
};

const fmtInt = new Intl.NumberFormat('pt-BR');
const fmtMi = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmtBi = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const fmtPct = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const I = (v) => fmtInt.format(v);
const M = (v) => fmtMi.format(v / 1e6);
const B = (v) => 'R$ ' + fmtBi.format(v / 1e9) + ' bi';
const P = (a, b) => (b ? fmtPct.format(100 * a / b) + '%' : '—');
const H = (v) => [I(v), v ? 'hl' : 'zero'];      // destaque
const A = (v) => [I(v), v ? 'alerta' : 'zero'];  // alerta
const media = (s, n) => (n ? fmtPct.format(s / n) + '%' : '—');

// célula: string ou [string, classe]
const TABLES = [
  { id: 't-sel1', parts: [{ src: 'sel', add: (a, r) => {
      a.n++; if (r[1] === 0) a.qf++; else if (r[1] === 1) a.qo++;
      a.ogu += r[4]; a.fin += r[5]; } }],
    init: () => ({ n: 0, qf: 0, qo: 0, ogu: 0, fin: 0 }),
    cols: (a) => [I(a.qf), I(a.qo), H(a.n), M(a.ogu), M(a.fin), [M(a.ogu + a.fin), 'hl']],
    kpis: (t) => [I(t.n), B(t.ogu + t.fin), B(t.ogu), B(t.fin)] },

  { id: 't-sel2', parts: [{ src: 'sel', keep: (r) => r[3] >= 1, add: (a, r) => {
      a.n++; a.q[r[6]] = (a.q[r[6]] || 0) + 1; a.v[r[6]] = (a.v[r[6]] || 0) + r[4] + r[5]; a.vt += r[4] + r[5]; } }],
    init: () => ({ n: 0, q: {}, v: {}, vt: 0 }),
    cols: (a) => ANOS.map((y) => anoOn(y) ? I(a.q[y] || 0) : ['—', 'zero']).concat([H(a.n)])
      .concat(ANOS.map((y) => anoOn(y) ? M(a.v[y] || 0) : ['—', 'zero'])).concat([[M(a.vt), 'hl']]) },

  { id: 't-susp1', parts: [{ src: 'og', keep: (r) => !r[5], add: (a, r) => {
      a.n++; if (r[6] === 0) a.ret++; if (r[6] === 1) { a.pen++; a.vpen += r[4]; } } }],
    init: () => ({ n: 0, ret: 0, pen: 0, vpen: 0 }),
    cols: (a) => [I(a.n), H(a.ret + a.pen), I(a.ret), A(a.pen),
                  P(a.ret, a.ret + a.pen), M(a.vpen)],
    kpis: (t) => [I(t.ret + t.pen), I(t.ret) + ' · ' + P(t.ret, t.ret + t.pen), I(t.pen), B(t.vpen)] },

  { id: 't-susp2', parts: [{ src: 'og', keep: (r) => !r[5] && r[6] === 1, add: (a, r) => {
      a.n++; a.p[r[7]]++; if (r[8]) a.teto++; } }],
    init: () => ({ n: 0, p: [0, 0, 0, 0], teto: 0 }),
    cols: (a) => [H(a.n), I(a.p[1]), I(a.p[2]), A(a.p[3]),
                  A(a.teto), I(a.p[0])],
    kpis: (t) => [I(t.n), I(t.p[3]), I(t.teto), I(t.p[2])] },

  { id: 't-lic1', parts: [{ src: 'og', keep: (r) => !r[5], add: (a, r) => {
      a.n++; const f = r[9];
      // FASES: 0 sem andamento · 1 suspensiva · 2 susp. retirada · 3 LAE · 4 publicação ·
      //        5 homologação · 6 VRPL · 7 AIO · 8 obra iniciada
      const c = [0, 1, 2, 2, 3, 4, 5, 5, 6][f]; a.f[c]++; } }],
    init: () => ({ n: 0, f: [0, 0, 0, 0, 0, 0, 0] }),
    cols: (a) => a.f.map((v, i) => i === 6 ? H(v) : I(v)).concat([H(a.n)]),
    kpis: (t) => [I(t.f[0] + t.f[1] + t.f[2]), I(t.f[3]), I(t.f[4] + t.f[5]), I(t.f[6]) + ' · ' + P(t.f[6], t.n)] },

  { id: 't-lic2', parts: [{ src: 'og', keep: (r) => !r[5] && (r[10] || r[11]), add: (a, r) => {
      a.n++; if (r[10]) a.p[r[10]]++; if (r[11]) a.h[r[11]]++; } }],
    init: () => ({ n: 0, p: [0, 0, 0, 0, 0], h: [0, 0, 0, 0, 0] }),
    cols: (a) => [H(a.p[1]), I(a.p[2]), I(a.p[3]), A(a.p[4]),
                  H(a.h[1]), I(a.h[2]), I(a.h[3]), A(a.h[4])] },

  { id: 't-ct1', parts: [
      { src: 'sel', keep: (r) => r[3] >= 1, add: (a, r) => { a.n++; a.sel++; } },
      { src: 'ct', keep: (r) => r[3] >= 1, add: (a, r) => {
          a.n++; const s = r[5];
          if (s === 3) a.emc++; else if (s === 4) a.canc++; else { a.ass++; a.inv += r[7]; } } }],
    init: () => ({ n: 0, sel: 0, ass: 0, emc: 0, canc: 0, inv: 0 }),
    cols: (a) => [I(a.sel), H(a.ass), I(a.emc), I(a.canc), P(a.ass, a.sel), M(a.inv)],
    kpis: (t) => [I(t.sel), I(t.ass), P(t.ass, t.sel), B(t.inv)] },

  { id: 't-ct2', parts: [{ src: 'ct', keep: (r) => r[3] >= 1 && r[5] !== 3 && r[5] !== 4, add: (a, r) => {
      a.n++; a.s[r[5] === 5 ? 3 : r[5]]++;
      if (r[1] === 1) a.qo++; else if (r[1] === 0) a.qf++; a.rep += r[8]; } }],
    init: () => ({ n: 0, s: [0, 0, 0, 0], qo: 0, qf: 0, rep: 0 }),
    cols: (a) => [I(a.s[0]), A(a.s[1]), I(a.s[2]), I(a.s[3]), H(a.n),
                  I(a.qo), I(a.qf), M(a.rep)],
    kpis: (t) => [I(t.n), I(t.s[0]), I(t.s[1]), B(t.rep)] },

  { id: 't-ex1', parts: [{ src: 'ct', keep: (r) => r[5] !== 4 && r[6] !== 5, add: (a, r) => {
      a.n++; a.o[r[6]]++; } }],
    init: () => ({ n: 0, o: [0, 0, 0, 0, 0] }),
    cols: (a) => [I(a.o[0]), I(a.o[1]), A(a.o[2]), I(a.o[3]), I(a.o[4]),
                  H(a.n), P(a.o[3], a.n)],
    kpis: (t) => [I(t.o[1]), I(t.o[2]), I(t.o[3]) + ' · ' + P(t.o[3], t.n), I(t.o[0])] },

  { id: 't-ex2', parts: [{ src: 'ct', keep: (r) => r[5] !== 4 && r[6] !== 5, add: (a, r) => {
      a.n++;
      if (r[6] === 2) { a.par++; a.vpar += r[7]; }
      if (r[6] === 3) a.conc++;
      if ((r[6] === 1 || r[6] === 2)) {
        if (r[9] !== null) { const k = r[3] === 0 ? 'm' : 's'; a.fs[k] += r[9]; a.fn[k]++; }
        if (r[10] !== null) { a.fis += r[10]; a.fin_n++; }
      } } }],
    init: () => ({ n: 0, par: 0, vpar: 0, conc: 0, fs: { s: 0, m: 0 }, fn: { s: 0, m: 0 }, fis: 0, fin_n: 0 }),
    cols: (a) => [media(a.fs.s, a.fn.s), media(a.fs.m, a.fn.m), [media(a.fs.s + a.fs.m, a.fn.s + a.fn.m), 'hl'],
                  media(a.fis, a.fin_n), A(a.par), M(a.vpar), I(a.conc)],
    kpis: (t) => [media(t.fs.s + t.fs.m, t.fn.s + t.fn.m), media(t.fis, t.fin_n), I(t.par), B(t.vpar)] },
];

const state = { uf: '', sel: true, enq: true, anos: {} };
ANOS.forEach((a) => { state.anos[a] = true; });
const anoFiltrado = () => ANOS.some((a) => !state.anos[a]);
const anoOn = (y) => !!state.anos[y];

// filtros comuns: UF, status (migradas contam como selecionadas) e ano (com recorte de ano,
// migradas e linhas sem ano saem da conta)
function passa(s, r) {
  if (state.uf && r[s.uf] !== state.uf) return false;
  if (!(r[s.kind] <= 1 ? state.sel : state.enq)) return false;
  if (anoFiltrado() && !state.anos[r[s.ano]]) return false;
  return true;
}

function td(c) {
  return Array.isArray(c) ? '<td class="' + c[1] + '">' + c[0] + '</td>' : '<td>' + c + '</td>';
}

function render() {
  for (const t of TABLES) {
    const acc = MODS.map(() => t.init());
    const tot = t.init();
    for (const p of t.parts) {
      const s = SRC[p.src];
      for (const r of s.rows) {
        if (p.keep && !p.keep(r)) continue;
        if (!passa(s, r)) continue;
        p.add(acc[r[0]], r);
        p.add(tot, r);
      }
    }
    const body = [];
    acc.forEach((a, i) => { if (a.n) body.push('<tr><td>' + MODS[i] + '</td>' + t.cols(a).map(td).join('') + '</tr>'); });
    const tb = document.querySelector('#' + t.id + ' tbody');
    const ncols = document.querySelectorAll('#' + t.id + ' thead tr:last-child th').length;
    if (!body.length) {
      tb.innerHTML = '<tr><td class="empty" colspan="' + ncols + '">Sem registros neste recorte.</td></tr>';
    } else {
      body.push('<tr class="tot"><td>TOTAL</td>' + t.cols(tot).map((c) => td(Array.isArray(c) ? c[0] : c)).join('') + '</tr>');
      tb.innerHTML = body.join('');
    }
    if (t.kpis) t.kpis(tot).forEach((v, i) => {
      const el = document.querySelector('[data-kpi="' + t.id + ':' + i + '"]');
      if (el) el.textContent = tot.n ? v : '—';
    });
  }
  const stname = state.sel && state.enq ? 'selecionadas + enquadradas'
    : (state.sel ? 'somente selecionadas' : 'somente enquadradas');
  const anosOn = ANOS.filter((a) => state.anos[a]);
  const anoname = anosOn.length === ANOS.length ? 'todos' : anosOn.join(' + ') + ' (sem migradas)';
  document.querySelectorAll('.ufname').forEach((el) => { el.textContent = state.uf || 'Brasil'; });
  document.querySelectorAll('.stname').forEach((el) => { el.textContent = stname; });
  document.querySelectorAll('.anoname').forEach((el) => { el.textContent = anoname; });
  document.querySelectorAll('select.ufsel').forEach((el) => { el.value = state.uf; });
  document.querySelectorAll('.stbtn:not(.anobtn)').forEach((el) => {
    el.setAttribute('aria-pressed', String(state[el.dataset.st]));
  });
  document.querySelectorAll('.anobtn').forEach((el) => {
    el.setAttribute('aria-pressed', String(!!state.anos[el.dataset.ano]));
  });
}

(function () {
  const params = new URLSearchParams(location.search);
  let uf = (params.get('uf') || '').toUpperCase().trim();
  if (uf && !document.querySelector('select.ufsel option[value="' + uf + '"]')) uf = '';
  state.uf = uf;
  const st = (params.get('status') || '').toLowerCase().trim();
  if (st === 'sel') state.enq = false; else if (st === 'enq') state.sel = false;
  const anoParam = (params.get('ano') || '').trim();
  if (anoParam) {
    const pedidos = anoParam.split(',').map((a) => a.trim()).filter((a) => ANOS.includes(a));
    if (pedidos.length) ANOS.forEach((a) => { state.anos[a] = pedidos.includes(a); });
  }
  render();
  document.querySelectorAll('select.ufsel').forEach((el) => {
    el.addEventListener('change', function () { state.uf = this.value; render(); });
  });
  document.querySelectorAll('.stbtn:not(.anobtn)').forEach((el) => {
    el.addEventListener('click', function () {
      const k = this.dataset.st, other = k === 'sel' ? 'enq' : 'sel';
      if (state[k] && !state[other]) return; // pelo menos um status ativo
      state[k] = !state[k];
      render();
    });
  });
  document.querySelectorAll('.anobtn').forEach((el) => {
    el.addEventListener('click', function () {
      const a = this.dataset.ano;
      const ligados = ANOS.filter((y) => state.anos[y]);
      if (state.anos[a] && ligados.length === 1) return; // pelo menos um ano ativo
      state.anos[a] = !state.anos[a];
      render();
    });
  });

  // ---- Exportar PDF: com filtros aplicados, gera e baixa o PDF refletindo os filtros ----
  // Sem filtros, baixa o PDF pré-gerado (vetorial, leve). Com recorte ativo, cada slide é
  // rasterizado em 1920×1080 com html2canvas e adicionado a um jsPDF; se algo falhar,
  // cai para window.print() (@page já é paisagem).
  function carregarScript(src) {
    return new Promise(function (res, rej) {
      const s = document.createElement('script');
      s.src = src; s.onload = res; s.onerror = rej;
      document.head.appendChild(s);
    });
  }
  async function capturarSlide(secao) {
    const wrap = document.createElement('div');
    wrap.style.cssText = 'position:fixed; left:-20000px; top:0; width:1920px; height:1080px; overflow:hidden; background:#fff; z-index:-1;';
    const clone = secao.cloneNode(true);
    clone.removeAttribute('data-deck-active');
    clone.style.position = 'relative';
    clone.style.inset = 'auto';
    clone.style.width = '1920px';
    clone.style.height = '1080px';
    clone.style.boxSizing = 'border-box';
    clone.style.visibility = 'visible';
    clone.style.opacity = '1';
    const selO = secao.querySelectorAll('select');
    clone.querySelectorAll('select').forEach((s, i) => { s.value = selO[i].value; });
    const svgO = secao.querySelectorAll('svg, svg *');
    clone.querySelectorAll('svg, svg *').forEach((el, i) => {
      ['stroke', 'fill'].forEach((p) => {
        if ((el.getAttribute(p) || '').indexOf('var(') !== -1) {
          el.setAttribute(p, getComputedStyle(svgO[i])[p]);
        }
      });
    });
    clone.querySelectorAll('.xlsxlink').forEach((el) => el.remove());
    const net = clone.querySelector('.covernet');
    if (net) {
      net.setAttribute('width', 884);
      net.setAttribute('height', 1080);
      const img = document.createElement('img');
      img.style.cssText = 'position:absolute; top:0; right:0; height:100%; width:46%; opacity:.42; z-index:0;';
      const carregou = new Promise((res) => { img.onload = res; img.onerror = res; });
      img.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(new XMLSerializer().serializeToString(net));
      net.replaceWith(img);
      Array.from(clone.children).forEach((ch) => {
        if (ch !== img) { if (!ch.style.position) ch.style.position = 'relative'; ch.style.zIndex = '1'; }
      });
      await carregou;
    }
    wrap.appendChild(clone);
    document.body.appendChild(wrap);
    try {
      return await html2canvas(clone, { scale: 1, width: 1920, height: 1080, logging: false, backgroundColor: null });
    } finally {
      wrap.remove();
    }
  }
  let gerandoPdf = false;
  async function gerarPdfFiltrado(link) {
    if (gerandoPdf) return;
    gerandoPdf = true;
    const txt = link.querySelector('.pdftxt');
    const antes = txt ? txt.textContent : '';
    try {
      if (!window.html2canvas) await carregarScript('assets/html2canvas.min.js');
      if (!window.jspdf) await carregarScript('assets/jspdf.umd.min.js');
      const secoes = Array.from(document.querySelectorAll('deck-stage > section'))
        .filter((s) => !s.hasAttribute('data-deck-skip'));
      const pdf = new window.jspdf.jsPDF({ orientation: 'landscape', unit: 'px', format: [1920, 1080], compress: true, hotfixes: ['px_scaling'] });
      for (let i = 0; i < secoes.length; i++) {
        if (txt) txt.textContent = 'Gerando PDF… ' + (i + 1) + '/' + secoes.length;
        const canvas = await capturarSlide(secoes[i]);
        if (i) pdf.addPage([1920, 1080], 'landscape');
        pdf.addImage(canvas.toDataURL('image/jpeg', 0.92), 'JPEG', 0, 0, 1920, 1080);
      }
      const partes = ['novopac-balanco-carteira', (state.uf || 'brasil').toLowerCase()];
      if (!(state.sel && state.enq)) partes.push(state.sel ? 'selecionadas' : 'enquadradas');
      const anosOn = ANOS.filter((a) => state.anos[a]);
      if (anosOn.length !== ANOS.length) partes.push(anosOn.join('-'));
      pdf.save(partes.join('_') + '.pdf');
    } catch (err) {
      window.print();
    } finally {
      if (txt) txt.textContent = antes;
      gerandoPdf = false;
    }
  }
  const pdfLink = document.querySelector('a.xlsxlink[href$=".pdf"]');
  if (pdfLink) {
    pdfLink.addEventListener('click', function (e) {
      const filtrado = state.uf !== '' || !state.sel || !state.enq || ANOS.some((a) => !state.anos[a]);
      if (!filtrado) return;
      e.preventDefault();
      gerarPdfFiltrado(pdfLink);
    });
  }

  // ---- navegação: setas ↑/↓ e rolagem do mouse também passam os slides ----
  const stage = document.querySelector('deck-stage');
  const menu = document.getElementById('deckMenu');
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    if (!stage || !stage.next) return;
    if (menu && menu.hasAttribute('data-open')) return;
    const tag = (e.target && e.target.tagName) || '';
    if (tag === 'SELECT' || tag === 'INPUT' || tag === 'TEXTAREA') return;
    e.preventDefault();
    if (e.key === 'ArrowDown') stage.next(); else stage.prev();
  });
  let ultimoAvanco = 0, acumulado = 0;
  window.addEventListener('wheel', function (e) {
    if (!stage || !stage.next) return;
    if (menu && menu.hasAttribute('data-open')) return;
    const agora = Date.now();
    if (agora - ultimoAvanco < 400) { acumulado = 0; return; }
    if ((acumulado > 0) !== (e.deltaY > 0)) acumulado = 0;
    acumulado += e.deltaY;
    if (Math.abs(acumulado) < 60) return;
    if (acumulado > 0) stage.next(); else stage.prev();
    acumulado = 0; ultimoAvanco = agora;
  }, { passive: true });
})();
"""


def js(v):
    return json.dumps(v, ensure_ascii=False, separators=(',', ':'))


app_js = (APP_JS.replace('__MODS__', js(MODS)).replace('__ANOS__', js(ANOS))
          .replace('__SEL__', js(SEL)).replace('__CT__', js(CT)).replace('__OG__', js(OG)))

html = (HEAD + SLIDES
        + '\n<script>\n' + DECK_JS + '\n</script>\n'
        + '<script>\n' + app_js + '\n</script>\n'
        + DECK_CHROME + '\n</body></html>\n')

open(OUT, 'w', encoding='utf-8').write(html)
print('escrito:', OUT, f'({len(html)/1024:.0f} KB)')

# ---------------- PDF pré-gerado (um slide por página, paisagem 1920×1080) ----------------
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
pdf_out = f'{HERE}/{PDF_NAME}'
if os.path.exists(CHROME) and os.getenv('SEM_PDF') != '1':
    import subprocess
    r = subprocess.run(
        [CHROME, '--headless=new', '--disable-gpu', '--virtual-time-budget=8000',
         '--no-pdf-header-footer', f'--print-to-pdf={pdf_out}', f'file://{OUT}'],
        capture_output=True, timeout=180)
    if r.returncode == 0 and os.path.exists(pdf_out):
        print('PDF gerado:', pdf_out, f'({os.path.getsize(pdf_out)//1024} KB)')
    else:
        print('AVISO: geração do PDF falhou (código', r.returncode, ') — link do slide ficará quebrado até regenerar')
elif not os.path.exists(CHROME):
    aviso = 'mantido o PDF anterior' if os.path.exists(pdf_out) else 'PDF não gerado; link ficará quebrado'
    print(f'AVISO: Chrome não encontrado — {aviso}')
