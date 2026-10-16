#!/usr/bin/env python3
"""Gera index.html — apresentação "Novo PAC — MCid · Balanço da carteira" para a Secretaria-Executiva.

Caminho em cinco etapas, dois slides cada: Seleção → Suspensivas → Licitação → Contratação →
Execução. Layout e navegação da novopac-apresentacao (assets/), com filtros de UF, fonte
(OGU / FIN) e ano em todos os slides; o de status (selecionadas / enquadradas) só na seleção.

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
VERSAO = '1.23'  # subir a cada commit que altere a apresentação
# histórico exibido no popup do "versão x.y" (encerramento) — acrescentar uma linha a cada versão
HISTORICO = [
    ('1.0', 'Primeira versão: seleção, suspensivas, licitação, contratação e execução.'),
    ('1.1', 'Status só na seleção; filtro OGU/FIN; anos curtos; notas de conciliação; suspensivas reestruturadas.'),
    ('1.2', 'Numeração 1.1…5.2; slide 1.1 com % e filtro de origem; novo slide 4.3 — da seleção à obra.'),
    ('1.3', 'Slide 4.3: filtro de origem (migradas / novas) e critério de conclusão ≥ 95% de execução física.'),
    ('1.4', 'Migradas pelo valor da base GM (pós-2023) no 4.3 e no 5.2; novo slide 2.3 — alinhamento das suspensivas (DMP 08/2026).'),
    ('1.5', 'Slide 4.3 animado: o todo das seleções se quebra em contratos, obras iniciadas e concluídas.'),
    ('1.6', 'Balanço Governa jun/2026 como 2ª fonte da situação das obras (4.3, 5.1, 5.2); numeração N/total.'),
    ('1.7', 'Notas do 2.1 e do 3.1: cadeia das seleções OGU até os contratos OGU do painelpac.'),
    ('1.8', 'Slide 1.2 vira o painel de quadrados (waffle) por modalidade e fonte, no lugar da tabela por ano.'),
    ('1.9', 'Sai o slide de prazos das suspensivas (PC 48); o alinhamento das suspensivas passa a ser o 2.2.'),
    ('1.10', 'Slide 1.2: seletores Quantidade/Valor e Total/% e animação de preenchimento no painel de quadrados.'),
    ('1.11', 'Saem os contratos com fase Novo PAC mas bln_pac = NÃO no SACI (emendas e ações estratégicas); notas citam.'),
    ('1.12', 'Slide 1.2: animação de preenchimento mais lenta e visível.'),
    ('1.13', 'Trilha das etapas na linha de baixo de cada slide: a etapa atual em destaque, as demais como marca d\'água.'),
    ('1.14', 'A mesma trilha das etapas também na linha de cima dos slides.'),
    ('1.15', 'Slide 2.2: mais espaço entre as linhas das modalidades.'),
    ('1.16', 'Slide 3.2 vira a régua do prazo da licitação (antes × agora, 1 ponto = 1 contrato), com Quantidade/Valor.'),
    ('1.17', 'Exceção provisória: contratos e itens sem modalidade saem das contas; notas citam quantos.'),
    ('1.18', 'Slide 1.2: ícones das modalidades nos cartões do painel de quadrados.'),
    ('1.19', 'Slide 1.2: ícone no canto superior direito do cartão, maior.'),
    ('1.20', 'Slide 1.2: ícone das modalidades ainda maior.'),
    ('1.21', 'Slide 2.2: clicar numa bolinha abre a lista dos contratos do grupo, com link para o SACI.'),
    ('1.22', 'Extração de 16/10: 55 contratos da SNP saíram da fase Novo PAC no SACI (já estavam fora das contas).'),
    ('1.23', 'Slide 1.2: ícones de Renovação de Frota (ônibus) e Regularização Fundiária; ícones em cinza, azul só OGU, verde só FIN.'),
]

D = dados.load()
EXT = D['extracao']
MODS = dados.MODS

# ícones das modalidades (data/Icones, brancos sobre transparente): embutidos em base64 para o index.html
# continuar autocontido; aparecem num círculo na cor da etapa (cartões do 1.2)
import base64
ICONES_ARQ = {
    'Abastecimento de Água - Rural': 'abastecimento-de-agua-rural',
    'Abastecimento de Água - Urbano': 'abastecimento-de-agua-urbano',
    'Contenção de Encostas': 'contencao-de-encostas',
    'Drenagem Urbana': 'drenagem-urbana',
    'Esgotamento Sanitário': 'esgotamento-sanitario',
    'Mobilidade: Médias e Grandes Cidades': 'mobilidade-medias-e-grandes-cidades',
    'Regularização Fundiária': 'regularizacao-fundiaria',
    'Renovação de Frota': 'renovacao-de-frota',
    'Resíduos Sólidos': 'residuos-solidos',
    'Urbanização de Favelas': 'urbanizacao-de-favelas',
}
ICONES = []
for m in MODS:  # SVG (desenhados no padrão de traço branco) tem preferência sobre PNG
    base = f'{HERE}/data/Icones/{ICONES_ARQ.get(m, "-")}'
    tipo = next((t for t in ('svg', 'png') if os.path.exists(f'{base}.{t}')), None)
    mime = {'svg': 'image/svg+xml', 'png': 'image/png'}.get(tipo)
    ICONES.append(f'data:{mime};base64,' + base64.b64encode(open(f'{base}.{tipo}', 'rb').read()).decode() if tipo else '')


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
DT_BAL = br(AT.get('balanco'))
SRC_EXEC = f'SACI (view_mat_carteira_investimento) e Balanço Governa ({DT_BAL})'

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


# propostas: seleções OGU novas × contratos OGU do painelpac (a relação é N:N — a base GM repete propostas
# e há propostas com mais de um contrato, por recontratação ou divisão)
_prop = lambda x: x.astype(str).str.strip()
PROP_SEL_OGU = set(_prop(D['sel'].loc[D['sel'].fonte == 'OGU', 'num_proposta_selecao']))
PROP_CT_OGU = set(_prop(D['ogu'].num_proposta_selecao_pac_saci.dropna()))

# seleção: [mod, fonte, uf, kind, ogu, fin, ano, tem contrato OGU (só nas novas OGU)]
#           kind 0 migrada · 1 selecionada · 2 enquadrada
SEL = []
for _, r in D['mig'].iterrows():
    SEL.append([MODS.index(r['mod']), FONTE.get(r.fonte, 2), r.uf, 0,
                num(r.vlr_portaria_ogu), num(r.vlr_portaria_fin), '', 0])
for _, r in D['sel'].iterrows():
    SEL.append([MODS.index(r['mod']), FONTE.get(r.fonte, 2), r.uf, 2 if r.status_selecao == 'enquadrada' else 1,
                num(r.vlr_portaria_ogu), num(r.vlr_portaria_fin), dados.ANO_LABEL[int(r.ano_selecao)],
                1 if r.fonte == 'OGU' and str(r.num_proposta_selecao).strip() in PROP_CT_OGU else 0])

# contratos SACI: [mod, fonte, uf, kind, ano, sitContrato, sitObra, investimento, repasse, %fís, %fin,
#                  valor GM da migrada (pós-2023) ou None, grupo no balanço, % físico no balanço,
#                  fora: 1 bln_pac = NÃO · 2 sem modalidade (exceção provisória)]
# grupo no balanço: 0 outra fase / sem balanço · 1 em execução · 2 paralisada · 3 concluída
CT = []
for _, r in D['saci'].iterrows():
    CT.append([MODS.index(r['mod']), FONTE.get(r.txt_fonte, 2), r.uf, int(r.kind), r.ano,
               idx_sit_ct(r.dsc_situacao_contrato_mcid), SIT_OBRA.get(r.dsc_situacao_objeto_mcid, 0),
               num(r.vlr_investimento) or 0, num(r.vlr_repasse) or 0,
               num(r.prc_execucao_fisica), num(r.prc_execucao_financ), num(r.vlr_gm),
               int(r.bal_g), num(r.bal_exec), 1 if r.excl else 2 if r.semmod else 0])

# itens do balanço sem contrato na carteira (sem SNH, ativos, em obra ou concluídos): mesmo formato do CT,
# como novas seleções sem ano, situação da obra pelo balanço e valor pelo total previsto no Novo PAC
BX = []
for _, r in D['bx'].iterrows():
    BX.append([MODS.index(r['mod']), FONTE.get(r.fonte, 2), r.uf, 1, '', 0, {1: 1, 2: 2, 3: 3}[int(r.g)],
               num(r.vlr) or 0, num(r.vlr) or 0, num(r['exec']), None, None, int(r.g), num(r['exec']), 2 if r['mod'] == dados.OUTRAS else 0])

# contratos OGU (painelpac): [mod, uf, kind, ano, repasse, cancelado, susp, pc48, tetoVencido,
#                             fase, pubLicitação, homLicitação, casaCivil, data alinhada DMP 08/26,
#                             ligado a seleção OGU nova, em contratação, fora das contas, convênio, município, TCI]
_mun_saci = D['saci'].set_index('cod_tci').txt_municipio
OG = []
for _, r in D['ogu'].iterrows():
    teto = pd.to_datetime(r.prazo_suspensiva_pc48_prorrogado_calc, errors='coerce')
    OG.append([MODS.index(r['mod']), r.uf, int(r.kind), r.ano, num(r.vlr_repasse_saci),
               1 if r.dsc_situacao_contrato_mcid_saci == 'Cancelado ou Distratado' else 0,
               SUSP.get(r.status_suspensiva_calc, 2), PC48.get(r.status_prazo_suspensiva_pc48_calc, 0),
               1 if (r.status_suspensiva_calc == 'PENDENTE' and pd.notna(teto) and teto < HOJE) else 0,
               FASES.index(r.fase_atual_calc) if r.fase_atual_calc in FASES else 0,
               PRAZO.get(r.status_pub_licitacao_calc, 0), PRAZO.get(r.status_homolog_licitacao_calc, 0),
               1 if r.status_regra_casa_civil_calc == 'Cumpriu o prazo' else 0,
               '' if pd.isna(r.dt_alinhamento) else f'{r.dt_alinhamento:%Y-%m-%d}',
               1 if str(r.num_proposta_selecao_pac_saci).strip() in PROP_SEL_OGU else 0,
               1 if r.dsc_situacao_contrato_mcid_saci == 'Em Contratação' else 0, 1 if r.excl else 2 if r.semmod else 0,
               str(r.num_convenio_saci or ''), str(_mun_saci.get(r.cod_tci_saci, '') or ''), r.cod_tci_saci])

# régua do prazo da licitação (3.2, porte do regua-licitacao.js do painelpac): contratos OGU em
# "Contratado - Normal" — [mod, uf, kind, ano, repasse, fora do PAC, prazo legal pub (LAE+60), prazo efetivo pub,
#  edital publicado, prazo legal hom (pub+120), prazo efetivo hom, homologada, assinatura, convênio, município, TCI]
_iso = lambda v: '' if pd.isna(v) else f'{pd.Timestamp(v):%Y-%m-%d}'
_mun = D['saci'].set_index('cod_tci').txt_municipio
RG = []
for _, r in D['ogu'][D['ogu'].dsc_situacao_contrato_mcid_saci == 'Contratado - Normal'].iterrows():
    RG.append([MODS.index(r['mod']), r.uf, int(r.kind), r.ano, num(r.vlr_repasse_saci), 1 if r.excl else 2 if r.semmod else 0,
               _iso(r.prazo_pub_licitacao_36a_calc), _iso(r.prazo_pub_licitacao_calc), 0 if pd.isna(r.dte_publicacao_licitacao_tgov) else 1,
               _iso(r.prazo_homolog_licitacao_120d), _iso(r.prazo_homolog_licitacao_calc), 0 if pd.isna(r.dte_homologacao_licitacao_tgov) else 1,
               _iso(r.dte_assinatura_contrato_saci), str(r.num_convenio_saci or ''), str(_mun.get(r.cod_tci_saci, '') or ''), r.cod_tci_saci])

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
  .nota b{ font-style:normal; color:var(--navy); }
  /* quadro da conta (nota do 3.1): aparece ao passar o mouse ou com foco */
  .nota{ position:relative; }  /* o quadro abre ancorado no início da nota, onde quer que o link caia */
  .conta{ position:static; font-style:normal; font-weight:700; color:var(--accent-deep); border-bottom:1px dotted currentColor; cursor:help; white-space:nowrap; }
  .conta-pop{ display:none; position:absolute; left:0; bottom:calc(100% + 10px); z-index:20; width:640px; white-space:normal;
    background:#fff; border:1px solid var(--line-strong); border-left:4px solid var(--accent); border-radius:6px;
    box-shadow:0 10px 30px rgba(7,29,65,.18); padding:12px 16px 10px; color:var(--ink); }
  .conta:hover .conta-pop, .conta:focus .conta-pop, .conta:focus-within .conta-pop{ display:block; }
  .conta-t{ display:block; font-size:14px; letter-spacing:.08em; text-transform:uppercase; color:var(--ink-soft); margin-bottom:6px; }
  .conta-pop table{ width:100%; border-collapse:collapse; font-size:16px; font-variant-numeric:tabular-nums; }
  .conta-pop td{ padding:3px 0; font-weight:500; color:var(--ink); }
  .conta-pop td:last-child{ text-align:right; padding-left:16px; white-space:nowrap; font-weight:700; color:var(--navy); }
  .conta-pop tr.sub td{ border-top:1px solid var(--line); font-weight:700; }
  .conta-pop tr.tot td{ border-top:2px solid var(--line-strong); font-weight:800; color:var(--navy); }
  .conta-pop tr:first-child td{ border-top:0; }
  @media print{ .conta-pop{ display:none !important; } }
  .rodape-row{ display:flex; justify-content:space-between; align-items:flex-start; gap:40px; margin-top:8px; }
  .rodape-row .nota{ margin:0; padding-top:4px; }
  .rodape-ctl{ flex:none; }
  .rodape-ctl.col{ display:flex; flex-direction:column; align-items:flex-end; gap:6px; }
  /* trilha das etapas (linha de baixo): a etapa do slide na cor dela, as demais como marca d'água */
  .trilha{ display:flex; gap:18px; align-items:center; height:16px; }
  .tr-seg{ flex:1; display:flex; align-items:center; gap:10px; opacity:.2; }
  .tr-seg span{ font-size:12.5px; font-weight:800; letter-spacing:.14em; text-transform:uppercase; color:var(--ink-soft); white-space:nowrap; }
  .tr-seg i{ flex:1; height:2px; background:var(--line-strong); border-radius:2px; }
  .tr-seg.on{ opacity:1; }
  .tr-seg.on span{ color:var(--accent); }
  .tr-seg.on i{ height:3px; background:var(--accent); }
  .trilha + .bot{ border-top:0; padding-top:10px; }
  .top.com-trilha{ padding-bottom:8px; }
  .trilha + .body.tight{ padding-top:10px; }  /* devolve o espaço que a trilha de cima ocupa */
  .pagetot{ font-size:var(--t-foot); font-weight:700; letter-spacing:.08em; color:var(--ink-soft); opacity:.6; font-variant-numeric:tabular-nums; }
  /* gráfico de blocos (4.3): uma barra por etapa, altura proporcional ao 1º bloco */
  .funil{ position:relative; display:grid; grid-template-columns:1fr 150px 1fr 150px 1fr 150px 1fr; height:528px; margin-top:4px; }
  .fbloco{ display:flex; flex-direction:column; justify-content:flex-end; min-width:0; }
  /* coluna: barra na base, sombra tracejada na altura das seleções e rótulos acima da barra */
  .fcol{ position:relative; height:430px; }
  .fbar, .fghost{ position:absolute; left:22px; right:22px; bottom:0; }
  .fbar{ background:var(--accent); border-radius:4px 4px 0 0; transition:height .7s cubic-bezier(.65,0,.35,1); }
  .fghost{ border:2px dashed var(--accent); border-bottom:0; border-radius:4px 4px 0 0; opacity:.35; transition:height .7s cubic-bezier(.65,0,.35,1), opacity .4s; }
  .flab{ position:absolute; left:0; right:0; transition:bottom .7s cubic-bezier(.65,0,.35,1); }
  .fval{ font-size:46px; font-weight:800; color:var(--navy); text-align:center; letter-spacing:-.02em; font-variant-numeric:tabular-nums; line-height:1.05; }
  .fsec{ font-size:19px; color:var(--ink-soft); text-align:center; margin:2px 0 0; font-variant-numeric:tabular-nums; }
  .fseta{ transition:opacity .45s ease, transform .45s ease; }
  .fseta.oculta{ opacity:0; transform:translateX(-14px); }
  .funil.sem-trans *{ transition:none !important; }
  .freplay{ position:absolute; top:-4px; right:0; z-index:2; font-family:'rawline','Raleway',sans-serif; font-size:15px; font-weight:700;
    letter-spacing:.06em; color:var(--ink-soft); background:#fff; border:1px solid var(--line-strong); border-radius:2px; padding:5px 10px; cursor:pointer; }
  .freplay:hover{ color:var(--accent-deep); border-color:var(--accent); }
  @media print{ .freplay{ display:none !important; } .funil *{ transition:none !important; } }
  @media (prefers-reduced-motion: reduce){ .funil *{ transition:none !important; } }
  .fbase{ border-top:2px solid var(--line-strong); padding-top:10px; text-align:center; height:96px; box-sizing:border-box; }
  .fnome{ font-size:24px; font-weight:700; color:var(--navy); }
  .fdet{ font-size:16px; color:var(--ink-soft); margin-top:4px; line-height:1.3; font-variant-numeric:tabular-nums; }
  .fseta{ align-self:end; margin-bottom:120px; text-align:center; color:var(--ink-soft); }
  .fseta .pc{ font-size:28px; font-weight:800; color:var(--accent-deep); font-variant-numeric:tabular-nums; }
  .fseta svg{ display:block; margin:4px auto; width:90px; height:18px; stroke:var(--ink-soft); fill:none; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
  #t-ex1 td, #t-ex2 td{ padding-top:2px; padding-bottom:2px; }  /* 12 linhas + nota no 5.1 e 5.2 */
  /* 1.2 · painel de quadrados (waffle) */
  .waf{ display:flex; flex-direction:column; gap:14px; }
  .waf-top{ display:grid; grid-template-columns:250px 1fr 380px; gap:30px; align-items:center; }
  .waf-tot .n{ font-size:60px; font-weight:800; color:var(--navy); letter-spacing:-.02em; line-height:1; font-variant-numeric:tabular-nums; }
  .waf-tot .l{ font-size:16px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--ink-soft); margin-top:6px; }
  .waf-bar{ display:flex; height:46px; border-radius:6px; overflow:hidden; background:#E5E9F0; }
  .waf-seg{ display:flex; align-items:center; justify-content:center; color:#fff; font-size:19px; white-space:nowrap; font-variant-numeric:tabular-nums; }
  .waf-seg b{ font-weight:800; margin-right:8px; letter-spacing:.04em; }
  .waf-seg.ogu{ background:#2563EB; } .waf-seg.fin{ background:#16A34A; }
  .waf-bar-leg{ display:flex; justify-content:space-between; font-size:17px; color:var(--ink-soft); margin-top:6px; font-variant-numeric:tabular-nums; }
  .waf-bar-leg b{ color:var(--navy); }
  .waf-bar-leg[hidden]{ display:none; }
  .waf i, .waf-leg i{ display:inline-block; flex:none; width:13px; height:13px; border-radius:3px; margin-right:7px; vertical-align:-1px; }
  .waf-leg{ font-size:16px; color:var(--ink-soft); display:flex; flex-wrap:wrap; gap:6px 16px; justify-content:flex-end; }
  .waf-leg .esc{ width:100%; text-align:right; font-weight:700; color:var(--navy); }
  .waf-grid{ display:grid; grid-template-columns:repeat(5, minmax(0, 1fr)); gap:14px; }
  .waf-card{ background:#fff; border:1px solid var(--line); border-radius:8px; box-shadow:0 1px 4px rgba(7,29,65,.06); padding:10px 14px 12px; }
  .waf-nome{ font-size:16px; font-weight:800; color:var(--navy); line-height:1.2; min-height:39px; letter-spacing:.01em; display:flex; align-items:flex-start; justify-content:space-between; gap:10px; }
  /* os PNG têm ~25% de margem transparente: a imagem é maior que o círculo e o excesso fica cortado */
  .waf-ico{ flex:none; width:54px; height:54px; margin:-4px -6px -14px 0;  /* margem negativa: não empurra os quadrados */ border-radius:50%; background:#344054; display:inline-flex; align-items:center; justify-content:center; overflow:hidden; transition:background .3s; }
  .waf.so-ogu .waf-ico{ background:#2563EB; }  /* fonte só OGU: a cor do OGU */
  .waf.so-fin .waf-ico{ background:#16A34A; }  /* fonte só FIN: a cor do FIN */
  .waf-ico img{ width:64px; height:64px; display:block; flex:none; }
  .waf-corpo{ display:flex; gap:12px; align-items:flex-start; margin-top:6px; }
  .waf-svg{ flex:none; display:block; }
  .waf-num{ flex:1; min-width:0; font-variant-numeric:tabular-nums; }
  .waf-num.rs .q{ font-size:25px; white-space:nowrap; }
  .waf-num.rs .f{ font-size:14px; }
  .waf-num.rs .f span{ font-size:12.5px; }
  .waf-tot.rs .n{ font-size:46px; }
  .waf-num .q{ font-size:32px; font-weight:800; color:var(--navy); line-height:1; letter-spacing:-.02em; }
  .waf-num .ql{ font-size:13px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--ink-soft); margin:3px 0 10px; }
  .waf-num .f{ font-size:15px; color:var(--ink-soft); line-height:1.5; white-space:nowrap; display:flex; align-items:center; }
  .waf-num .f b{ color:var(--navy); margin:0 4px; }
  .waf-num .f span{ font-size:14px; margin-left:auto; padding-left:6px; }
  .waf-cap{ font-size:12px; color:var(--ink-soft); }
  .waf.anim .wq{ animation:wq .7s cubic-bezier(.2,.7,.3,1) both; transform-box:fill-box; transform-origin:center; }
  .waf.anim .waf-seg{ animation:wseg 1.8s cubic-bezier(.65,0,.35,1) both; transform-origin:left center; }
  .waf.anim .waf-seg.fin{ animation-delay:.5s; }
  @keyframes wq{ from{ opacity:0; transform:scale(.25); } to{ opacity:1; transform:none; } }
  @keyframes wseg{ from{ transform:scaleX(0); } to{ transform:none; } }
  @media print{ .waf.anim *{ animation:none !important; } }
  @media (prefers-reduced-motion: reduce){ .waf.anim *{ animation:none !important; } }
  .waf-fin{ display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; }
  .waf-fin div{ background:var(--paper-2); border-radius:8px; padding:8px 18px; display:flex; justify-content:space-between; align-items:baseline; }
  .waf-fin span{ font-size:15px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--ink-soft); }
  .waf-fin b{ font-size:26px; font-weight:800; color:var(--navy); font-variant-numeric:tabular-nums; }
  .waf-fin .t b{ color:var(--accent-deep); }
  /* 3.2 · régua do prazo da licitação */
  .rg-regra{ margin:2px 0 10px; }
  .rg-kicker{ display:block; font-size:13px; font-weight:800; letter-spacing:.12em; text-transform:uppercase; color:var(--ink-soft); margin-bottom:6px; }
  .rg-trilha{ display:flex; align-items:center; gap:6px; }
  .rg-etapa{ flex:none; font-size:15px; font-weight:700; padding:5px 10px; border-radius:3px; color:#fff; white-space:nowrap; }
  .rg-etapa.escuro{ background:#344054; } .rg-etapa.verde{ background:#1F7A4D; } .rg-etapa.azul{ background:#1351B4; }
  .rg-trecho{ flex:1; min-width:0; display:flex; flex-direction:column; align-items:center; font-size:13px; color:var(--ink-soft); line-height:1.15; }
  .rg-trecho b{ font-weight:800; color:var(--navy); white-space:nowrap; } .rg-trecho em{ font-style:normal; font-size:12px; }
  .rg-trecho i{ display:block; width:100%; height:2px; margin:2px 0; background:#1F7A4D; }
  .rg-trecho.azul i{ background:#1351B4; } .rg-trecho.neutro i{ background:var(--line-strong); }
  .rg-cab{ display:flex; justify-content:space-between; align-items:baseline; gap:20px; margin-bottom:4px; }
  .rg-cab h3{ margin:0; font-size:20px; font-weight:800; color:var(--navy); }
  .rg-leg{ display:flex; gap:18px; font-size:15px; color:var(--ink-soft); }
  .rg-leg i{ display:inline-block; width:12px; height:12px; border-radius:50%; margin-right:6px; vertical-align:-1px; }
  .rg-corpo{ display:grid; grid-template-columns:auto 110px auto; justify-content:center; align-items:end; gap:24px; }
  .rg-tit{ font-size:14px; font-weight:800; letter-spacing:.06em; text-transform:uppercase; color:var(--ink-soft); margin-bottom:4px; }
  .rg-colunas{ display:flex; align-items:flex-end; gap:14px; min-height:250px; }
  .rg-col{ display:flex; flex-direction:column; align-items:center; }
  .rg-n{ font-size:15px; font-weight:800; color:var(--navy); font-variant-numeric:tabular-nums; margin-bottom:3px; white-space:nowrap; }
  .rg-pilha{ display:flex; flex-wrap:wrap-reverse; justify-content:center; align-items:center; gap:4px; }
  .rg-base{ width:100%; min-width:30px; height:2px; background:var(--line-strong); margin-top:4px; }
  .rg-lab{ font-size:13px; font-weight:700; color:var(--ink-soft); margin-top:3px; white-space:nowrap; }
  .rg-col.dest .rg-lab{ color:#B45309; } .rg-col.dest .rg-base{ background:#B45309; height:3px; }
  .rg-dot{ display:inline-block; border-radius:50%; flex:none; }
  .rg-dot.anel{ box-shadow:0 0 0 2px #fff, 0 0 0 4px #B42318; }
  .rg-obs{ font-size:13px; color:var(--ink-soft); margin-top:6px; } .rg-obs .rg-dot{ width:11px; height:11px; margin:0 8px 0 4px; vertical-align:-1px; }
  .rg-seta{ align-self:center; color:var(--ink-soft); } .rg-seta svg{ width:100px; height:22px; stroke:var(--ink-soft); fill:none; stroke-width:2; }
  .rg-comps{ display:grid; grid-template-columns:1fr 1fr; gap:30px; margin-top:12px; }
  .rg-comp-t{ font-size:14px; font-weight:800; letter-spacing:.04em; color:var(--navy); margin-bottom:4px; }
  .rg-barra{ display:grid; grid-template-columns:56px 1fr; align-items:center; gap:8px; margin-top:4px; font-size:14px; color:var(--ink-soft); }
  .rg-trilho{ display:flex; gap:2px; height:24px; border-radius:3px; overflow:hidden; background:#EEF1F5; }
  .rg-seg{ display:flex; align-items:center; justify-content:center; color:#fff; font-size:13px; font-weight:800; min-width:0; overflow:hidden; white-space:nowrap; }
  .alin{ margin-top:4px; position:relative; }
  .aln-b{ cursor:pointer; outline:none; }
  .aln-b:hover circle:first-of-type, .aln-b:focus circle:first-of-type{ fill-opacity:1; }
  .aln-b.sel circle:first-of-type{ fill:#0C3C8F; fill-opacity:1; stroke:#071D41; stroke-width:3; }
  .aln-dica{ margin-left:auto; font-style:italic; }
  .aln-lista{ position:absolute; top:36px; right:0; z-index:30; width:640px; max-height:440px; display:flex; flex-direction:column;
    background:#fff; border:1px solid var(--line-strong); border-left:4px solid var(--accent); border-radius:6px; box-shadow:0 12px 34px rgba(7,29,65,.2); }
  .aln-lista[hidden]{ display:none; }
  .aln-lista.esq{ right:auto; left:260px; }  /* bolinha à direita: quadro à esquerda (depois dos rótulos) */
  .aln-l-cab{ display:flex; justify-content:space-between; align-items:flex-start; gap:12px; padding:12px 16px 8px; border-bottom:1px solid var(--line); }
  .aln-l-cab b{ display:block; font-size:18px; color:var(--navy); }
  .aln-l-cab span{ font-size:15px; color:var(--ink-soft); }
  .aln-fechar{ border:0; background:none; font-size:28px; line-height:1; color:var(--ink-soft); cursor:pointer; padding:0 4px; }
  .aln-l-corpo{ overflow:auto; padding:4px 16px 10px; }
  .aln-l-corpo table{ width:100%; border-collapse:collapse; font-size:15px; font-variant-numeric:tabular-nums; }
  .aln-l-corpo th{ text-align:left; font-size:12px; letter-spacing:.08em; text-transform:uppercase; color:var(--ink-soft); padding:6px 8px 4px 0; position:sticky; top:0; background:#fff; }
  .aln-l-corpo td{ padding:4px 8px 4px 0; border-top:1px solid var(--line); color:var(--ink); white-space:nowrap; }
  .aln-l-corpo td:nth-child(4){ text-align:right; } .aln-l-corpo th:nth-child(4){ text-align:right; }
  .aln-l-corpo a{ color:#1351B4; font-weight:700; text-decoration:none; }
  .aln-st{ display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; }
  .aln-st.pend{ background:#1351B4; } .aln-st.ret{ background:#168821; } .aln-st.canc{ background:#98A2B3; }
  @media print{ .aln-lista, .aln-dica{ display:none !important; } }
  .alin svg{ display:block; width:100%; height:auto; }
  .alin-leg{ display:flex; gap:28px; font-size:16px; color:var(--ink-soft); margin-top:6px; }
  .alin-leg i{ display:inline-block; vertical-align:-3px; margin-right:8px; }
  .alin-leg .lg-dot{ width:16px; height:16px; border-radius:50%; background:#1351B4; opacity:.85; }
  .alin-leg .lg-ring{ width:12px; height:12px; border-radius:50%; border:3px solid #168821; }
  .alin-leg .lg-hoje{ width:0; height:16px; border-left:2px dashed #BC4749; }
  .fseta .lb{ font-size:14px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; }
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
  .stbtn.fixo{ background:var(--paper-2); color:var(--navy); cursor:default; }
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
"""


def chrome_top(etapa):
    """cabeçalho dos slides de conteúdo: a linha de baixo do cabeçalho também é a trilha das etapas."""
    return CHROME_TOP.replace('<div class="top">', '<div class="top com-trilha">') + f'    {trilha(etapa)}\n'


def trilha(etapa):
    """linha de baixo como trilha das 5 etapas (como o roteiro da capa): a do slide em destaque, as outras apagadas."""
    segs = ''.join(f'<div class="tr-seg{" on" if i == etapa else ""}"><span>0{i} {nome}</span><i></i></div>'
                   for i, nome in ETAPAS.items())
    return f'<div class="trilha" aria-label="Etapa {etapa} de 5">{segs}</div>'


def foot(fonte, etapa=None):
    linha = trilha(etapa) if etapa else '<hr class="hr">'
    return f"""    {linha}
    <div class="bot">
      <span class="org">Fonte: {fonte} · extração de {EXTRAIDO:%d/%m/%Y %H:%M}</span>
      <span style="display:inline-flex; align-items:baseline;"><span class="pageno"></span><span class="pagetot">/__NSLIDES__</span><span class="ver">versão {VERSAO}</span></span>
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


def grupo(rotulo, botoes):
    """caixa de botões no padrão dos filtros: botoes = [(classe extra, atributos, texto, ligado)]."""
    bts = ''.join(f'<button type="button" class="stbtn{" " + cl if cl else ""}" {at} aria-pressed="{str(on).lower()}">{tx}</button>'
                  for cl, at, tx, on in botoes)
    return f'<div class="stctl"><label>{rotulo}</label><div class="stgrp">{bts}</div></div>'


def radio(rotulo, chave, opcoes):
    """seletor exclusivo (state[chave] = valor): opcoes = [(valor, texto)]; o 1º é o padrão."""
    return grupo(rotulo, [('rdbtn', f'data-k="{chave}" data-v="{v}"', tx, i == 0) for i, (v, tx) in enumerate(opcoes)])


def cabeca(etapa, n, titulo, tid, dek='', status=False, so_ogu=False, origem=None, extra='', ori_on=(True, True)):
    """abertura do slide: selo + título + controles (origem, UF, status, fonte, ano e uma linha extra).

    status: filtro selecionadas/enquadradas (só nos slides de seleção); so_ogu: base só de OGU
    (painelpac) — o filtro de fonte vira etiqueta fixa; origem: filtro migradas/novas — None desliga,
    senão é o prefixo das chaves de estado (state.<prefixo>mig / state.<prefixo>nov), para cada slide ter
    o seu; ori_on: estado inicial dos dois botões."""
    dek_html = f'\n          <p class="dek" style="max-width:66ch; font-style:italic; font-size:23px; margin:6px 0 0 126px;">{dek}</p>' if dek else ''
    ano_ctl = grupo('Ano', [('anobtn', f'data-ano="{a}" title="{a}"', a[2:], True) for a in ANOS])
    ori_ctl = grupo('Origem', [('oribtn', f'data-ori="{origem}mig"', 'Migradas', ori_on[0]),
                               ('oribtn', f'data-ori="{origem}nov"', 'Novas', ori_on[1])]) if origem is not None else ''
    st_ctl = grupo('Status', [('', 'data-st="sel"', 'Selecionadas', True),
                              ('', 'data-st="enq"', 'Enquadradas', True)]) if status else ''
    fon_ctl = ('<div class="stctl"><label>Fonte</label><div class="stgrp"><span class="stbtn fixo">OGU</span></div></div>'
               if so_ogu else grupo('Fonte', [('fonbtn', 'data-fon="ogu"', 'OGU', True),
                                              ('fonbtn', 'data-fon="fin"', 'FIN', True)]))
    extra_html = f'\n          <div class="ctrow">{extra}</div>' if extra else ''
    return f"""
  <section class="p2 content e{etapa}" data-label="{etapa}.{n} {ETAPAS[etapa]}">
{chrome_top(etapa)}    <div class="body tight">
      <div class="title-row">
        <div class="title-block tight">
          <h2 class="title"><span class="etapa"><span class="n">{etapa}.{n}</span><span class="t">{ETAPAS[etapa]}</span></span>{titulo}</h2>{dek_html}
        </div>
        <div class="ctrls">
          <div class="ctrow">{ori_ctl}<div class="ufctl"><label for="{tid}-uf">Recorte</label><select id="{tid}-uf" class="ufsel">{uf_opts}</select></div></div>
          <div class="ctrow">
            {st_ctl}{fon_ctl}{ano_ctl}
          </div>{extra_html}
        </div>
      </div>
      <div class="col grow" style="justify-content:flex-start;">"""


def tmeta(atualizado, legenda, status=False, so_ogu=False, origem=None, ori_txt='migradas + novas'):
    partes = [atualizado, legenda]
    if origem is not None:
        partes.append(f'Origem: <b class="oriname{origem}">{ori_txt}</b>')
    if status:
        partes.append('Status: <b class="stname">selecionadas + enquadradas</b>')
    partes.append('Fonte: <b>OGU</b>' if so_ogu else 'Fonte: <b class="fonname">OGU + FIN</b>')
    partes += ['Anos: <b class="anoname">todos</b>', 'Recorte: <b class="ufname">Brasil</b>']
    return '<p class="tmeta">' + '<span class="sep">·</span>'.join(partes) + '</p>'


def cartoes(tid, kpis):
    """linha de destaques (KPIs): kpis = [(rótulo, '', classe opcional)], preenchidos pelo JS."""
    if not kpis:
        return ''
    cards = ''.join(f'<div class="kpi{" " + k[2] if len(k) > 2 else ""}"><div class="kv" data-kpi="{tid}:{i}">—</div><div class="kl">{k[0]}</div></div>'
                    for i, k in enumerate(kpis))
    return f'\n        <div class="kpis">{cards}</div>'


def slide(etapa, n, titulo, tabela_id, colunas, legenda, atualizado, fonte, dek='', kpis=None, nota='',
          status=False, so_ogu=False, origem=None, rodape='', extra=''):
    """slide de tabela; rodape: controles exibidos à direita da nota (ex.: valores × %)."""
    kpi_html = cartoes(tabela_id, kpis)
    nota_html = f'<p class="nota">{nota}</p>' if nota else '<p class="nota"></p>'
    nota_html = (f'\n        <div class="rodape-row">{nota_html}<div class="rodape-ctl">{rodape}</div></div>' if rodape
                 else (f'\n        {nota_html}' if nota else ''))
    return (cabeca(etapa, n, titulo, tabela_id, dek, status, so_ogu, origem, extra=extra)
            + f"""{kpi_html}
        {tmeta(atualizado, legenda, status, so_ogu, origem)}
        <table class="data dense" id="{tabela_id}">
          <thead>{cabecalho(colunas)}</thead>
          <tbody></tbody>
        </table>{nota_html}
      </div>
    </div>
{foot(fonte, etapa)}  </section>
""")


# seletor da fonte da situação das obras (4.3, 5.1, 5.2): o padrão soma o balanço do Governa
SIT_OBRA = lambda: radio('Situação da obra', 'sitobra', [('bal', 'SACI + balanço'), ('saci', 'Só SACI')])


def slide_transicao(etapa, n, titulo, legenda, atualizado, fonte, dek='', nota=''):
    """gráfico de blocos (funil) da seleção à obra — montado no render() do JS.

    Origem própria (prefixo 'g'): começa só com as novas seleções, como o slide 4.1."""
    extra = radio('Medida', 'med', [('qtd', 'Quantidade'), ('valor', 'Valor')]) + radio('Exibir', 'modo', [('tot', 'Total'), ('pct', '%')])
    criterio = radio('Concluídas', 'c95', [('0', 'Pela situação'), ('1', '+ obras com ≥ 95% físico')])
    return (cabeca(etapa, n, titulo, 'g-funil', dek, origem='g', extra=extra, ori_on=(False, True))
            + f"""
        {tmeta(atualizado, legenda, origem='g', ori_txt='somente novas')}
        <div class="funil" id="g-funil"></div>
        <div class="rodape-row"><p class="nota">{nota}</p><div class="rodape-ctl col">{SIT_OBRA()}{criterio}</div></div>
      </div>
    </div>
{foot(fonte, etapa)}  </section>
""")


def slide_waffle(etapa, n, titulo, legenda, atualizado, fonte, dek=''):
    """painel de quadrados (waffle) por modalidade × fonte — montado no render() do JS; mesmos filtros do 1.1."""
    extra = (radio('Medida', 'wmed', [('qtd', 'Quantidade'), ('valor', 'Valor')])
             + radio('Exibir', 'wmodo', [('tot', 'Total'), ('pct', '%')]))
    return (cabeca(etapa, n, titulo, 'g-waf', dek, status=True, origem='', extra=extra)
            + f"""
        {tmeta(atualizado, legenda, status=True, origem='')}
        <div class="waf" id="g-waf"></div>
        <p class="nota"><span data-ref="waf"></span></p>
      </div>
    </div>
{foot(fonte, etapa)}  </section>
""")


def slide_regua(etapa, n, titulo, legenda, atualizado, fonte):
    """régua do prazo da licitação (art. 36-A) — regra estática + pontos e barras montados no render() do JS."""
    extra = radio('Medida', 'rmed', [('qtd', 'Quantidade'), ('valor', 'Valor')])
    passo = lambda t, cls: f'<span class="rg-etapa {cls}">{t}</span>'
    trecho = lambda p, b, cls: f'<span class="rg-trecho {cls}"><b>{p}</b><i></i><em>{b}</em></span>'
    regra = ('<div class="rg-regra"><span class="rg-kicker">A regra · art. 36-A da PC 32/2024 (incluído pela PC 48/2026)</span>'
             '<div class="rg-trilha">' + passo('LAE', 'escuro') + trecho('até 60 dias', 'caput', 'verde') + passo('Edital publicado', 'verde')
             + trecho('até 120 dias', '§ 1º', 'verde') + passo('Licitação homologada', 'verde') + trecho('VRPL', '', 'neutro')
             + passo('AIO', 'azul') + trecho('10 dias úteis', '§ 4º', 'azul') + passo('Ordem de serviço', 'azul') + '</div></div>')
    return (cabeca(etapa, n, titulo, 'g-regua', so_ogu=True, extra=extra)
            + f"""
        {tmeta(atualizado, legenda, so_ogu=True)}
        {regra}
        <div class="rg" id="g-regua"></div>
        <p class="nota"><span data-ref="reg"></span></p>
      </div>
    </div>
{foot(fonte, etapa)}  </section>
""")


def slide_alinhamento(etapa, n, titulo, legenda, atualizado, fonte, dek='', kpis=None):
    """linha do tempo do alinhamento das suspensivas (gráfico do painelpac) — montada no render() do JS."""
    extra = (radio('Tamanho', 'aln', [('vlr', 'Repasse'), ('n', 'Contratos')])
             + radio('Mostrar', 'alnp', [('todos', 'Todos'), ('pend', 'Só pendentes')]))
    return (cabeca(etapa, n, titulo, 'g-alin', dek, so_ogu=True, extra=extra)
            + f"""{cartoes('g-alin', kpis)}
        {tmeta(atualizado, legenda, so_ogu=True)}
        <div class="alin" id="g-alin"></div>
        <p class="nota"><span data-ref="aln"></span></p>
      </div>
    </div>
{foot(fonte, etapa)}  </section>
""")


BALANCO_NOME = 'se_cgpac.balancojun2026_com_inativas'
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

{slide(1, 1, 'Carteira de seleções', 't-sel1',
       ['Qtd. FIN', 'Qtd. OGU', 'Total', 'Valor OGU<br>(R$ mi)', 'Valor FIN<br>(R$ mi)', 'Valor total<br>(R$ mi)'],
       'Contagem: migradas + novas seleções', AT_GM, SRC_GM,
       kpis=[('Propostas',), ('Valor total',), ('OGU',), ('Financiamento',)], status=True, origem='',
       nota='<span data-ref="sel1"></span>',
       rodape=radio('Exibir', 'pct1', [('0', 'Valores'), ('1', '% do total')]))}
{slide_waffle(1, 2, 'Carteira do Novo PAC por Modalidade', 'Contagem: migradas + novas seleções', AT_GM, SRC_GM,
       dek='Distribuição das seleções por fonte de recursos.')}
{slide(2, 1, 'Cláusulas suspensivas — OGU', 't-susp1',
       ['Sem<br>suspensiva', ('Com cláusula suspensiva', ['Retiradas', 'Pendentes', 'Subtotal']), 'Total<br>contratos OGU', '% retirada', 'Repasse<br>pendente (R$ mi)'],
       'Contagem: contratos OGU do Novo PAC Seleção (sem SNH), sem cancelados', AT_PAC, SRC_PAC,
       dek='Contratos OGU = sem suspensiva + suspensiva retirada + suspensiva pendente.',
       kpis=[('Contratos OGU',), ('Com suspensiva',), ('Retiradas', '', 'ok'), ('Pendentes', '', 'alerta')],
       nota='% retirada = retiradas ÷ contratos com cláusula suspensiva. <span data-ref="susp1"></span>', so_ogu=True)}
{slide_alinhamento(2, 2, 'Alinhamento das suspensivas',
       'Contagem: contratos OGU com data alinhada pela DMP (08/2026)', AT_PAC, SRC_PAC,
       dek='Datas de retirada pactuadas pela DMP (08/2026), por modalidade.')}
{slide(3, 1, 'Etapa atual dos contratos OGU', 't-lic1',
       ['Sem<br>registro', 'Em<br>suspensiva', 'Suspensiva<br>retirada/LAE', 'Edital<br>publicado', 'Licitação<br>homologada', 'VRPL /<br>AIO', 'Obra<br>iniciada', 'Total'],
       'Contagem: contratos OGU do Novo PAC Seleção, sem cancelados — etapa mais avançada', AT_PAC, SRC_PAC,
       kpis=[('Aguardando licitação',), ('Edital publicado',), ('Homologada até AIO',), ('Obra iniciada', '', 'ok')], so_ogu=True,
       nota='<span data-ref="lic1"></span>')}
{slide_regua(3, 2, 'Régua do prazo: antes × agora',
       'Contagem: contratos OGU em Contratado - Normal, sem edital publicado', AT_PAC, SRC_PAC)}
{slide(4, 1, 'Selecionado × contratado', 't-ct1',
       ['Seleções', 'Contratos<br>assinados', 'Em<br>contratação', 'Cancelados /<br>distratados', '% assinado', 'Investimento<br>assinado (R$ mi)'],
       'Contagem: novas seleções (GM) × contratos do Novo PAC Seleção (SACI)', AT_CT, 'base única GM e ' + SRC_SACI,
       kpis=[('Seleções',), ('Contratos assinados', '', 'ok'), ('% assinado',), ('Investimento assinado',)],
       nota='<span data-ref="ct1"></span> Proposta com OGU e FIN conta uma vez em cada fonte.')}
{slide(4, 2, 'Situação dos contratos assinados', 't-ct2',
       ['Normal', 'Suspensiva', 'Concluído', 'Outros*', 'Total', 'Qtd. OGU', 'Qtd. FIN', 'Repasse /<br>financ. (R$ mi)'],
       'Contagem: contratos assinados do Novo PAC Seleção (SACI)', AT_SACI, SRC_SACI,
       kpis=[('Assinados',), ('Normal', '', 'ok'), ('Em suspensiva', '', 'alerta'), ('Repasse / financiamento',)],
       nota='* Outros: em TCE, liminar e em prestação de contas.')}
{slide_transicao(4, 3, 'Da seleção à obra',
       'Contagem: seleções (GM) × contratos do Novo PAC Seleção / Migrado (SACI)', AT_CT, f'base GM, SACI e Balanço Governa ({DT_BAL})',
       dek='Quanto das seleções já virou contrato assinado, obra iniciada e obra concluída.',
       nota='<span data-ref="g43"></span> Valor: seleções pela portaria; contratos pelo repasse do SACI. '
            'Setas: conversão sobre o bloco anterior.')}
{slide(5, 1, 'Situação das obras', 't-ex1',
       ['Não<br>iniciada', 'Em<br>execução', 'Paralisada', 'Concluída', 'Inacabada', 'Total', '% concluída'],
       'Contagem: contratos do Novo PAC Seleção + Migrado (SACI), sem cancelados', AT_SACI, SRC_EXEC,
       kpis=[('Em execução',), ('Paralisadas', '', 'alerta'), ('Concluídas', '', 'ok'), ('Não iniciadas',)],
       nota='<span data-ref="ex1"></span>', extra=SIT_OBRA())}
{slide(5, 2, 'Execução média e paralisações', 't-ex2',
       [('% físico médio', ['Novas<br>seleções', 'Migradas', 'Total']), '% financeiro<br>médio', 'Paralisadas', 'Investimento<br>paralisado (R$ mi)', 'Concluídas'],
       'Médias: obras em execução ou paralisadas (média simples por contrato)', AT_SACI, SRC_EXEC, extra=SIT_OBRA(),
       kpis=[('% físico médio',), ('% financeiro médio',), ('Paralisadas', '', 'alerta'), ('Investimento paralisado', '', 'alerta')],
       nota='<span data-ref="ex2"></span>')}

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
        <div><b>Situação das obras (2ª fonte)</b>Balanço Governa — {BALANCO_NOME} · referência {DT_BAL}</div>
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
// ===== dados e filtros: UF, fonte e ano em todos os slides; status só nas tabelas de seleção =====
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
// régua do 3.2 (contratos OGU em Contratado - Normal)
const RG = __RG__;
// ícones das modalidades (data URI, na ordem de MODS)
const ICONES = __ICONES__;
// itens do balanço sem contrato na carteira (mesmo formato do CT; sem SNH, ativos)
const BX = __BX__;

// posição de uf / kind / ano / fonte em cada base (OG é todo OGU: sem filtro de fonte)
const SRC = {
  sel: { rows: SEL, uf: 2, kind: 3, ano: 6, fon: 1 },
  ct:  { rows: CT,  uf: 2, kind: 3, ano: 4, fon: 1, ex: 14 },
  bx:  { rows: BX,  uf: 2, kind: 3, ano: 4, fon: 1, ex: 14 },
  og:  { rows: OG,  uf: 1, kind: 2, ano: 3, ex: 16 },
  rg:  { rows: RG,  uf: 1, kind: 2, ano: 3, ex: 5 },
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
// situação da obra efetiva: com "SACI + balanço", a fase do balanço completa a do SACI — concluída se
// qualquer das duas disser; senão a do SACI se a obra já começou; senão a do balanço (em execução/paralisada)
const comBal = () => state.sitobra === 'bal';
function sitObra(r) {
  const s = r[6];
  if (!comBal() || r[12] === 0) return s;
  if (r[12] === 3) return 3;
  if (s >= 1 && s <= 4) return s;
  return r[12] === 1 ? 1 : 2;
}
// % físico para o critério de 95%: o maior entre SACI e balanço (com o balanço ligado)
const fisico = (r) => (comBal() && r[13] !== null ? Math.max(r[9] ?? 0, r[13]) : r[9]);
// valor do contrato: migrada pelo valor da base GM (pós-2023) quando houver; senão o campo do SACI
const vMig = (r, i) => (r[3] === 0 && r[11] !== null ? r[11] : r[i]);
const BM = (v) => (Math.abs(v) >= 1e9 ? B(v) : 'R$ ' + fmtBi.format(v / 1e6) + ' mi');  // bi ou mi

// 5.2: médias de execução das obras em execução ou paralisadas (situação efetiva); % físico do SACI e,
// nos itens só do balanço, o do balanço
function exAdd(a, r) {
  const o = sitObra(r);
  a.n++;
  if (o === 2) { a.par++; a.vpar += vMig(r, 7); }
  if (o === 3) a.conc++;
  if (o === 1 || o === 2) {
    const f = r[9] !== null ? r[9] : (comBal() ? r[13] : null);
    if (f !== null) { const k = r[3] === 0 ? 'm' : 's'; a.fs[k] += f; a.fn[k]++; }
    if (r[10] !== null) { a.fis += r[10]; a.fin_n++; }
  }
}

// célula: string ou [string, classe]
const TABLES = [
  { id: 't-sel1', status: true, origem: true, pctHead: true, parts: [{ src: 'sel', add: (a, r) => {
      a.n++; if (r[1] === 0) a.qf++; else if (r[1] === 1) a.qo++;
      if (r[3] === 0) a.mig++; else a.nov++;
      a.ogu += r[4]; a.fin += r[5]; } }],
    init: () => ({ n: 0, qf: 0, qo: 0, mig: 0, nov: 0, ogu: 0, fin: 0 }),
    // "% do total": participação da modalidade no total de cada coluna
    cols: (a, t) => state.pct1 === '1'
      ? [P(a.qf, t.qf), P(a.qo, t.qo), [P(a.n, t.n), 'hl'], P(a.ogu, t.ogu), P(a.fin, t.fin),
         [P(a.ogu + a.fin, t.ogu + t.fin), 'hl']]
      : [I(a.qf), I(a.qo), H(a.n), M(a.ogu), M(a.fin), [M(a.ogu + a.fin), 'hl']],
    kpis: (t) => [I(t.n), B(t.ogu + t.fin), B(t.ogu), B(t.fin)] },

  { id: 't-susp1', parts: [{ src: 'og', keep: (r) => !r[5], add: (a, r) => {
      a.n++;
      if (r[6] === 0) a.ret++; else if (r[6] === 1) { a.pen++; a.vpen += r[4]; } else a.sem++; } }],
    init: () => ({ n: 0, sem: 0, ret: 0, pen: 0, vpen: 0 }),
    // sem + retiradas + pendentes = total
    cols: (a) => [I(a.sem), I(a.ret), A(a.pen), I(a.ret + a.pen), H(a.n),
                  P(a.ret, a.ret + a.pen), M(a.vpen)],
    kpis: (t) => [I(t.n), I(t.ret + t.pen), I(t.ret) + ' · ' + P(t.ret, t.ret + t.pen), I(t.pen)] },

  { id: 't-lic1', parts: [{ src: 'og', keep: (r) => !r[5], add: (a, r) => {
      a.n++; const f = r[9];
      // FASES: 0 sem andamento · 1 suspensiva · 2 susp. retirada · 3 LAE · 4 publicação ·
      //        5 homologação · 6 VRPL · 7 AIO · 8 obra iniciada
      const c = [0, 1, 2, 2, 3, 4, 5, 5, 6][f]; a.f[c]++; } }],
    init: () => ({ n: 0, f: [0, 0, 0, 0, 0, 0, 0] }),
    cols: (a) => a.f.map((v, i) => i === 6 ? H(v) : I(v)).concat([H(a.n)]),
    kpis: (t) => [I(t.f[0] + t.f[1] + t.f[2]), I(t.f[3]), I(t.f[4] + t.f[5]), I(t.f[6]) + ' · ' + P(t.f[6], t.n)] },

  { id: 't-ct1', parts: [
      { src: 'sel', keep: (r) => r[3] >= 1, add: (a, r) => { a.n++; a.sel++; } },
      // migradas: só para a nota de conciliação (não entram na tabela)
      { src: 'sel', keep: (r) => r[3] === 0, add: (a) => { a.mig++; } },
      { src: 'ct', keep: (r) => r[3] >= 1, add: (a, r) => {
          a.n++; const s = r[5];
          if (s === 3) a.emc++; else if (s === 4) a.canc++; else { a.ass++; a.inv += r[7]; } } }],
    init: () => ({ n: 0, sel: 0, mig: 0, ass: 0, emc: 0, canc: 0, inv: 0 }),
    cols: (a) => [I(a.sel), H(a.ass), I(a.emc), I(a.canc), P(a.ass, a.sel), M(a.inv)],
    kpis: (t) => [I(t.sel), I(t.ass), P(t.ass, t.sel), B(t.inv)] },

  { id: 't-ct2', parts: [{ src: 'ct', keep: (r) => r[3] >= 1 && r[5] !== 3 && r[5] !== 4, add: (a, r) => {
      a.n++; a.s[r[5] === 5 ? 3 : r[5]]++;
      if (r[1] === 1) a.qo++; else if (r[1] === 0) a.qf++; a.rep += r[8]; } }],
    init: () => ({ n: 0, s: [0, 0, 0, 0], qo: 0, qf: 0, rep: 0 }),
    cols: (a) => [I(a.s[0]), A(a.s[1]), I(a.s[2]), I(a.s[3]), H(a.n),
                  I(a.qo), I(a.qf), M(a.rep)],
    kpis: (t) => [I(t.n), I(t.s[0]), I(t.s[1]), B(t.rep)] },

  { id: 't-ex1', parts: [{ src: 'ct', keep: (r) => r[5] !== 4 && sitObra(r) !== 5, add: (a, r) => {
      const o = sitObra(r);
      a.n++; a.o[o]++; if (r[3] === 0) a.mig++; else a.sel++;
      if (o === 3) { if (r[6] === 3) a.cs++; else a.cb++; }   // concluída pelo SACI · só pelo balanço
      if (r[12] === 3) a.balc++; } },                          // concluídas no balanço (contratos ligados)
      { src: 'bx', keep: () => comBal(), add: (a, r) => {
        a.n++; a.o[r[6]]++; a.bx++; if (r[6] === 3) { a.cx++; a.balc++; } } }],
    init: () => ({ n: 0, o: [0, 0, 0, 0, 0], sel: 0, mig: 0, bx: 0, cs: 0, cb: 0, cx: 0, balc: 0 }),
    cols: (a) => [I(a.o[0]), I(a.o[1]), A(a.o[2]), I(a.o[3]), I(a.o[4]),
                  H(a.n), P(a.o[3], a.n)],
    kpis: (t) => [I(t.o[1]), I(t.o[2]), I(t.o[3]) + ' · ' + P(t.o[3], t.n), I(t.o[0])] },

  { id: 't-ex2', parts: [{ src: 'ct', keep: (r) => r[5] !== 4 && sitObra(r) !== 5, add: (a, r) => exAdd(a, r) },
      { src: 'bx', keep: () => comBal(), add: (a, r) => { exAdd(a, r); a.bx++; } }],
    init: () => ({ n: 0, par: 0, vpar: 0, conc: 0, fs: { s: 0, m: 0 }, fn: { s: 0, m: 0 }, fis: 0, fin_n: 0, bx: 0 }),
    cols: (a) => [media(a.fs.s, a.fn.s), media(a.fs.m, a.fn.m), [media(a.fs.s + a.fs.m, a.fn.s + a.fn.m), 'hl'],
                  media(a.fis, a.fin_n), A(a.par), M(a.vpar), I(a.conc)],
    kpis: (t) => [media(t.fs.s + t.fs.m, t.fn.s + t.fn.m), media(t.fis, t.fin_n), I(t.par), B(t.vpar)] },
];

// cadeia seleções OGU (GM) → contratos OGU do painelpac, com os filtros de UF e ano
// contratos fora das contas, no recorte — para as notas: código 1 = bln_pac NÃO no SACI ·
// 2 = sem modalidade (exceção provisória); BX = itens do balanço sem contrato no SACI
function exclCt(keep, cod = 1, rows = CT, src = SRC.ct) {
  let n = 0;
  for (const r of rows) if (r[src.ex] === cod && keep(r) && passa(src, r, { excl: true })) n++;
  return n;
}
const SEMMOD = ' (exceção provisória, a revisar)';

function quadroOgu(c) {
    const L = (txt, v, tipo) => '<tr class="' + (tipo || '') + '"><td>' + txt + '</td><td>' + v + '</td></tr>';
    const quadro = '<span class="conta-pop" role="tooltip"><b class="conta-t">Das seleções OGU aos contratos do slide</b><table>'
      + L('Seleções OGU (slide 1.1)', I(c.sel), 'tot')
      + L('− migradas: o painelpac é só o Novo PAC Seleção', '− ' + I(c.mig))
      + L('− novas seleções ainda sem contrato', '− ' + I(c.semCt))
      + L('= novas seleções OGU com contrato', I(c.comCt), 'sub')
      + L('→ contratos dessas seleções (há propostas com mais de um)', I(c.lig))
      + L('+ contratos sem proposta de seleção ligada', '+ ' + I(c.semProp))
      + L('= contratos OGU no painelpac', I(c.ct), 'sub')
      + L('− fase Novo PAC mas bln_pac = NÃO no SACI (emendas e ações estratégicas)', '− ' + I(c.excl))
      + L('− sem modalidade' + SEMMOD, '− ' + I(c.semmod))
      + L('− cancelados / distratados', '− ' + I(c.canc))
      + L('= contratos deste slide (inclui ' + I(c.emc) + ' em contratação)', I(c.ativos), 'tot')
      + '</table></span>';
    return '<span class="conta" tabindex="0">ver a conta passo a passo ⓘ' + quadro + '</span>';
}

function cadeiaOgu() {
  const t = {}, c = { sel: 0, mig: 0, nov: 0, comCt: 0, semCt: 0, ct: 0, lig: 0, semProp: 0, canc: 0, emc: 0, ativos: 0, excl: 0, semmod: 0 };
  for (const r of SEL) {
    if (r[1] !== 1 || r[3] === 2 || !passa(SRC.sel, r, t)) continue;  // seleções OGU (selecionadas + migradas)
    c.sel++;
    if (r[3] === 0) c.mig++; else { c.nov++; if (r[7]) c.comCt++; else c.semCt++; }
  }
  for (const r of OG) {
    if (!passa(SRC.og, r, { excl: true })) continue;
    c.ct++; if (r[14]) c.lig++; else c.semProp++;
    if (r[16] === 1) c.excl++; else if (r[16] === 2) c.semmod++; else if (r[5]) c.canc++; else { c.ativos++; if (r[15]) c.emc++; }
  }
  return c;
}

// notas de conciliação entre slides: [data-ref] ← html calculado com os totais de cada tabela
const SEMANO = ' Com recorte de ano, as migradas (legado, sem ano de seleção) ficam fora.';
const REFS = {
  sel1: (T) => '<b>' + I(T['t-sel1'].n) + '</b> propostas = <b>' + I(T['t-sel1'].nov)
    + '</b> novas seleções + <b>' + I(T['t-sel1'].mig)
    + '</b> migradas (legado).' + (anoFiltrado() ? SEMANO : ''),
  waf: (T) => 'Mesmo recorte do 1.1: <b>' + I(T['t-sel1'].n) + '</b> propostas (<b>' + I(T['t-sel1'].nov) + '</b> novas + <b>'
    + I(T['t-sel1'].mig) + '</b> migradas). '
    + (state.wmed === 'valor'
      ? 'Quadrado = R$ ' + I(WAF.un / 1e6) + ' mi da portaria (escala única, ajustada ao recorte); '
      : 'Quadrado = 10 propostas; ')
    + 'o último é parcial; cinza = posição livre (70 por modalidade).'
    + (state.wmodo === 'pct' ? ' Em %: número grande = participação na carteira; OGU/FIN = % na modalidade.' : '')
    + (anoFiltrado() ? SEMANO : ''),
  ct1: (T) => 'Seleções = as <b>' + I(T['t-ct1'].sel) + '</b> novas seleções do slide 1.1'
    + (state.sel && state.enq ? '' : ' (selecionadas + enquadradas)')
    + '; as <b>' + I(T['t-ct1'].mig) + '</b> migradas (legado) entram direto na execução (slides 5.1 e 5.2).'
    + (exclCt((r) => r[3] >= 1) ? ' Sem os <b>' + I(exclCt((r) => r[3] >= 1)) + '</b> contratos com bln_pac = NÃO no SACI' : '')
    + (exclCt((r) => r[3] >= 1, 2) ? ' e os <b>' + I(exclCt((r) => r[3] >= 1, 2)) + '</b> sem modalidade' + SEMMOD : '') + '.',
  g43: () => (state.gmig && state.gnov ? 'Migradas + novas seleções (migradas sem ano: saem com recorte de ano).'
    : state.gmig ? 'Só as migradas (sem ano: com recorte de ano o gráfico fica vazio).'
    : 'Só as novas seleções, como no 4.1.')
    + (comBal() ? ' Obra: SACI + balanço jun/26, com <b>' + I(FUN.bx) + '</b> itens só no balanço (valor: total previsto Novo PAC).' : '')
    + (state.c95 === '1' ? ' Concluídas: + iniciadas com ≥ 95% físico' + (comBal() ? ' (SACI ou balanço)' : '') + '.' : '')
    + (state.gmig ? ' Migradas pelo valor da base GM (pós-2023).' : '')
    + ' Sem itens sem modalidade' + SEMMOD + '.',
  reg: () => 'Contratos OGU em Contratado - Normal (como no painelpac). Prazo efetivo = o maior entre o legal e 30/10/2026; '
    + 'antes × agora na data da extração. Ficam de fora <b>' + I(RGN.pc72) + '</b> sem prazo (PC 72, assinados antes de 21/10/2025), <b>'
    + I(RGN.semLae) + '</b> sem LAE' + (RGN.excl ? ', <b>' + I(RGN.excl) + '</b> com bln_pac = NÃO' : '')
    + (RGN.semmod ? ' e <b>' + I(RGN.semmod) + '</b> sem modalidade' : '') + '. Clique num ponto para abrir no SACI.',
  aln: () => !ALN.n ? 'Nenhum contrato com data alinhada neste recorte.'
    : (state.alnp === 'pend' ? 'Só pendentes. ' : '') + '<b>' + I(ALN.n) + '</b> com data alinhada = <b>' + I(ALN.pc)
      + '</b> pendentes + <b>' + I(ALN.ret) + '</b> já retiradas' + (ALN.canc ? ' + <b>' + I(ALN.canc) + '</b> cancelado(s)' : '')
      + ' (a data vale mesmo após a retirada). As <b>' + I(ALN.pc + ALN.ps) + '</b> pendentes do 2.1 = <b>' + I(ALN.pc)
      + '</b> com data + <b>' + I(ALN.ps) + '</b> fora do alinhamento de 08/2026.',
  ex1: (T) => {
    const t = T['t-ex1'];
    let s = 'Total = <b>' + I(t.sel) + '</b> Novo PAC Seleção + <b>' + I(t.mig) + '</b> migrados'
      + (comBal() && t.bx ? ' + <b>' + I(t.bx) + '</b> itens só no balanço' : '') + ', sem cancelados'
      + (anoFiltrado() ? ' (com recorte de ano, migrados e itens do balanço saem)' : '')
      + (exclCt((r) => r[5] !== 4) ? ', sem os <b>' + I(exclCt((r) => r[5] !== 4)) + '</b> com bln_pac = NÃO' : '')
      + (exclCt((r) => r[5] !== 4, 2) + (comBal() ? exclCt(() => true, 2, BX, SRC.bx) : 0)
        ? ' e sem <b>' + I(exclCt((r) => r[5] !== 4, 2) + (comBal() ? exclCt(() => true, 2, BX, SRC.bx) : 0)) + '</b> sem modalidade' + SEMMOD : '') + '.';
    if (comBal()) s += ' Concluídas <b>' + I(t.o[3]) + '</b> = <b>' + I(t.cs) + '</b> no SACI + <b>' + I(t.cb)
      + '</b> só no balanço jun/26 + <b>' + I(t.cx) + '</b> do balanço sem contrato no SACI (frota privada e outros); '
      + 'o balanço sem SNH tem <b>' + I(t.balc) + '</b> — a diferença são obras concluídas no SACI após junho.';
    return s;
  },
  // 2.1 / 3.1: das seleções OGU (1.1) aos contratos OGU do painelpac, em cadeia
  // 3.1: nota curta + quadro da conta (aparece ao passar o mouse) — das seleções OGU aos contratos do slide
  lic1: () => {
    const c = cadeiaOgu();
    return 'De <b>' + I(c.sel) + '</b> seleções OGU (slide 1.1) a <b>' + I(c.ativos) + '</b> contratos OGU: migradas, seleções sem contrato, '
      + 'bln_pac = NÃO, sem modalidade e cancelados saem; contratos sem proposta ligada entram. ' + quadroOgu(c);
  },
  susp1: () => { const c = cadeiaOgu(); return 'Base: <b>' + I(c.ativos) + '</b> contratos OGU do painelpac, sem cancelados e sem os <b>'
    + I(c.excl) + '</b> com bln_pac = NÃO e dos <b>' + I(c.semmod) + '</b> sem modalidade' + SEMMOD + '. ' + quadroOgu(c); },
  ex2: (T) => 'Investimento paralisado: migradas pelo valor da base GM (pós-2023); demais pelo investimento do SACI'
    + (comBal() ? '. Situação da obra pelo SACI + balanço jun/26 (+ <b>' + I(T['t-ex2'].bx) + '</b> itens do balanço sem contrato no SACI, '
      + 'com o % físico do balanço).' : '.'),
};

// filtros (liga/desliga) e seletores exclusivos (pct1: tabela 1.1 em % · med/modo: gráfico 4.3)
// origem: mig/nov no slide 1.1 · gmig/gnov no gráfico 4.3 (começa só com as novas) · c95: no 4.3,
// conta como concluída também a obra iniciada com ≥ 95% de execução física
const state = { uf: '', sel: true, enq: true, ogu: true, fin: true, mig: true, nov: true,
                gmig: false, gnov: true, anos: {}, pct1: '0', med: 'qtd', modo: 'tot', c95: '0', aln: 'vlr',
                sitobra: 'bal', alnp: 'todos', wmed: 'qtd', wmodo: 'tot', rmed: 'qtd' };
const PAR = { sel: 'enq', enq: 'sel', ogu: 'fin', fin: 'ogu', mig: 'nov', nov: 'mig', gmig: 'gnov', gnov: 'gmig' };
const ORIGENS = ['', 'g'];  // prefixos das chaves de origem
ANOS.forEach((a) => { state.anos[a] = true; });
const anoFiltrado = () => ANOS.some((a) => !state.anos[a]);
const anoOn = (y) => !!state.anos[y];

// filtros comuns: UF, fonte (fonte desconhecida só com as duas ligadas), ano (com recorte de
// ano, migradas e linhas sem ano saem da conta) e, só nas tabelas de seleção, status
// (migradas contam como selecionadas); origem (migradas / novas) só onde a tabela pede
function passa(s, r, t) {
  // fora do PAC pelo próprio SACI (fase Novo PAC mas bln_pac = NÃO): só entra quando a nota pede (t.excl)
  if (s.ex !== undefined && r[s.ex] && !t.excl) return false;
  if (state.uf && r[s.uf] !== state.uf) return false;
  if (s.fon !== undefined) {
    const f = r[s.fon];
    if (!(f === 1 ? state.ogu : f === 0 ? state.fin : state.ogu && state.fin)) return false;
  }
  if (t.status && !(r[s.kind] <= 1 ? state.sel : state.enq)) return false;
  if (t.origem && !(r[s.kind] === 0 ? state.mig : state.nov)) return false;
  if (anoFiltrado() && !state.anos[r[s.ano]]) return false;
  return true;
}

// ---- 4.3 · da seleção à obra: seleções → assinados → obras iniciadas → concluídas (origem gmig / gnov)
const SETA = '<svg viewBox="0 0 90 18" aria-hidden="true"><path d="M2 9h84"></path><path d="M78 2l8 7-8 7"></path></svg>';
function renderFunil() {
  const el = document.getElementById('g-funil');
  if (!el) return;
  const t = {};  // sem status / origem: só UF, fonte e ano
  const b = { sel: [0, 0], ass: [0, 0], ini: [0, 0], con: [0, 0] };  // [quantidade, valor]
  const obra = [0, 0, 0, 0, 0];
  let c95 = 0;  // obras somadas às concluídas pelo critério de ≥ 95% físico
  const origem = (r) => (r[3] === 0 ? state.gmig : state.gnov);
  for (const r of SEL) {
    if (!origem(r) || !passa(SRC.sel, r, t)) continue;
    b.sel[0]++; b.sel[1] += r[4] + r[5];
  }
  FUN.bx = 0;
  const conta = (r, v) => {
    b.ass[0]++; b.ass[1] += v;
    const o = sitObra(r), f = fisico(r);
    if (o >= 1 && o <= 4) { b.ini[0]++; b.ini[1] += v; obra[o]++; }
    const quase = state.c95 === '1' && o >= 1 && o <= 4 && o !== 3 && f !== null && f >= 95;
    if (o === 3 || quase) { b.con[0]++; b.con[1] += v; if (quase) c95++; }
  };
  for (const r of CT) {
    if (!origem(r) || r[5] === 3 || r[5] === 4 || !passa(SRC.ct, r, t)) continue;
    conta(r, vMig(r, 8));
  }
  if (comBal()) for (const r of BX) {
    if (!origem(r) || !passa(SRC.bx, r, t)) continue;
    conta(r, r[8]); FUN.bx++;
  }
  const anosSel = state.gmig && state.gnov ? 'migradas + portarias de 2023, 2025 e 2026'
    : state.gmig ? 'migradas (legado)' : 'portarias de 2023, 2025 e 2026';
  const BLOCOS = [
    ['sel', 'Seleções', anosSel],
    ['ass', 'Contratos assinados', comBal() ? 'SACI + ' + I(FUN.bx) + ' itens só no balanço' : 'normal, suspensiva, concluído e outros'],
    ['ini', 'Obras iniciadas', 'em execução ' + I(obra[1]) + ' · paralisadas ' + I(obra[2]) + ' · inacabadas ' + I(obra[4])],
    ['con', 'Obras concluídas', (comBal() ? 'SACI + balanço jun/26' : 'situação da obra no SACI') + (state.c95 === '1' ? ' + ' + I(c95) + ' com ≥ 95%' : '')],
  ];
  const k = state.med === 'valor' ? 1 : 0;
  const base = b.sel[k];
  // altura pela maior barra: nas migradas o repasse contratado pode passar do valor da portaria na base GM
  const teto = Math.max(...BLOCOS.map(([id]) => b[id][k]));
  const pct = state.modo === 'pct';
  // formato do número principal: % das seleções, R$ ou quantidade (usado também pelo contador)
  const fmtNum = pct ? (x) => fmtPct.format(x) + '%' : (k ? BM : (x) => I(Math.round(x)));
  if (!FUN.blocos) montarFunil(el);
  FUN.fmt = fmtNum;
  FUN.alvo = BLOCOS.map(([id, nome, det], i) => {
    const v = b[id][k];
    return {
      h: teto ? Math.max(v ? 3 : 0, Math.round(340 * v / teto)) : 0,
      n: pct ? (base ? 100 * v / base : 0) : v,
      sec: pct ? (k ? BM(v) : I(v)) : (k ? I(b[id][0]) + (id === 'sel' ? ' seleções' : ' contratos') : BM(b[id][1])),
      conv: i ? P(v, b[BLOCOS[i - 1][0]][k]) : '',
      nome, det, title: nome + ': ' + I(b[id][0]) + ' · ' + BM(b[id][1]),
    };
  });
  pararFunil();
  aplicarFunil();
}

// ---- animação do 4.3: o todo (as seleções) aparece inteiro e se quebra nos blocos seguintes.
// Sem biblioteca: transição CSS de altura + contador em requestAnimationFrame.
const FUN = { blocos: null, setas: null, timers: [], rafs: [], alvo: [], fmt: null, bx: 0 };
function montarFunil(el) {
  el.innerHTML = '';
  FUN.blocos = []; FUN.setas = [];
  for (let i = 0; i < 4; i++) {
    if (i) {
      const s = document.createElement('div');
      s.className = 'fseta';
      s.innerHTML = '<div class="pc"></div>' + SETA + '<div class="lb">do anterior</div>';
      el.append(s); FUN.setas.push(s);
    }
    const bl = document.createElement('div');
    bl.className = 'fbloco';
    bl.innerHTML = '<div class="fcol">' + (i ? '<div class="fghost"></div>' : '')
      + '<div class="fbar"></div><div class="flab"><div class="fval"></div><div class="fsec"></div></div></div>'
      + '<div class="fbase"><div class="fnome"></div><div class="fdet"></div></div>';
    el.append(bl);
    FUN.blocos.push({
      el: bl, bar: bl.querySelector('.fbar'), ghost: bl.querySelector('.fghost'), lab: bl.querySelector('.flab'),
      val: bl.querySelector('.fval'), sec: bl.querySelector('.fsec'),
      nome: bl.querySelector('.fnome'), det: bl.querySelector('.fdet'),
    });
  }
  const bt = document.createElement('button');
  bt.type = 'button'; bt.className = 'freplay'; bt.textContent = '↻ Animar';
  bt.title = 'Repetir a animação: o todo das seleções se quebrando nas etapas';
  bt.addEventListener('click', animarFunil);
  el.append(bt);
}
function posFunil(i, h) {  // barra e rótulo na altura h
  const B = FUN.blocos[i];
  B.bar.style.height = h + 'px';
  B.lab.style.bottom = (h + 10) + 'px';
}
function aplicarFunil() {  // estado final (sem animação pendente)
  const a = FUN.alvo;
  a.forEach((x, i) => {
    const B = FUN.blocos[i];
    posFunil(i, x.h);
    if (B.ghost) { B.ghost.style.height = a[0].h + 'px'; B.ghost.style.opacity = ''; }
    B.val.textContent = FUN.fmt(x.n);
    B.sec.textContent = x.sec;
    B.nome.textContent = x.nome; B.det.textContent = x.det; B.el.title = x.title;
    if (i) { FUN.setas[i - 1].querySelector('.pc').textContent = x.conv; FUN.setas[i - 1].classList.remove('oculta'); }
  });
}
function pararFunil() {
  FUN.timers.forEach(clearTimeout); FUN.rafs.forEach(cancelAnimationFrame);
  FUN.timers = []; FUN.rafs = [];
  const el = document.getElementById('g-funil');
  if (el) el.classList.remove('sem-trans');
}
function contar(B, de, ate, ms) {  // contador do número principal, com a mesma curva da barra
  const t0 = performance.now();
  const passo = (t) => {
    const p = Math.max(0, Math.min(1, (t - t0) / ms));  // o 1º quadro pode vir com horário anterior a t0
    const e = p < .5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2;
    B.val.textContent = FUN.fmt(de + (ate - de) * e);
    if (p < 1) FUN.rafs.push(requestAnimationFrame(passo));
  };
  FUN.rafs.push(requestAnimationFrame(passo));
}
function animarFunil() {
  const el = document.getElementById('g-funil');
  if (!el || !FUN.blocos || !FUN.alvo.length) return;
  if (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  pararFunil();
  const a = FUN.alvo, hSel = a[0].h;
  // 1) zera tudo sem transição: barras na base, setas ocultas, todos com o número das seleções
  el.classList.add('sem-trans');
  a.forEach((x, i) => {
    posFunil(i, 0);
    const B = FUN.blocos[i];
    if (B.ghost) { B.ghost.style.height = '0px'; B.ghost.style.opacity = '0'; }
    B.val.textContent = FUN.fmt(a[0].n); B.sec.textContent = a[0].sec;
    if (i) FUN.setas[i - 1].classList.add('oculta');
  });
  void el.offsetHeight;
  el.classList.remove('sem-trans');
  // 2) o todo: as quatro barras sobem juntas até a altura das seleções
  a.forEach((x, i) => posFunil(i, hSel));
  // 3) a quebra, em cascata: cada etapa encolhe até o seu valor, a sombra fica, a seta aparece
  const T = (ms, f) => FUN.timers.push(setTimeout(f, ms));
  for (let i = 1; i < 4; i++) {
    const t = 1000 + (i - 1) * 420;
    T(t, () => {
      const B = FUN.blocos[i];
      B.ghost.style.height = hSel + 'px'; B.ghost.style.opacity = '';
      posFunil(i, a[i].h);
      B.sec.textContent = a[i].sec;
      contar(B, a[0].n, a[i].n, 700);
    });
    T(t + 520, () => FUN.setas[i - 1].classList.remove('oculta'));
  }
  T(1000 + 2 * 420 + 900, () => { FUN.timers = []; aplicarFunil(); });
}

// ---- 1.2 · painel de quadrados (waffle): carteira → OGU/FIN → modalidades. 1 quadrado = 10 propostas,
// o último parcial; 10 × 7 posições por modalidade, mesma escala em todas; primeiro OGU, depois FIN.
const COR_OGU = '#2563EB', COR_FIN = '#16A34A', COR_VAZIO = '#E5E9F0';
function waffleSvg(qo, qf, un, id) {
  // qo / qf na unidade da medida (propostas ou R$); `un` = quanto vale um quadrado completo
  const S = 13, G = 3, COLS = 10, ROWS = 7, CAP = COLS * ROWS * un, tot = qo + qf;
  const W = COLS * S + (COLS - 1) * G, H = ROWS * S + (ROWS - 1) * G;
  const pos = (i) => [(i % COLS) * (S + G), Math.floor(i / COLS) * (S + G)];
  const clip = [], cor = [];
  for (let i = 0; i < COLS * ROWS; i++) {
    const [x, y] = pos(i), ini = i * un;
    clip.push('<rect x="' + x + '" y="' + y + '" width="' + S + '" height="' + S + '" rx="2.5"></rect>');
    const b = Math.max(0, Math.min(un, qo - ini)) / un;          // fração OGU deste quadrado
    const g = Math.max(0, Math.min(un, tot - ini) / un - b);     // fração FIN
    cor.push('<rect x="' + x + '" y="' + y + '" width="' + S + '" height="' + S + '" fill="' + COR_VAZIO + '"></rect>');
    const d = ' class="wq" style="animation-delay:' + (i * 35) + 'ms"';  // preenchimento em sequência (animação)
    if (b > 0) cor.push('<rect' + d + ' x="' + x + '" y="' + y + '" width="' + (S * b) + '" height="' + S + '" fill="' + COR_OGU + '"></rect>');
    if (g > 0) cor.push('<rect' + d + ' x="' + (x + S * b) + '" y="' + y + '" width="' + (S * g) + '" height="' + S + '" fill="' + COR_FIN + '"></rect>');
  }
  return '<svg class="waf-svg" viewBox="0 0 ' + W + ' ' + H + '" width="' + W + '" height="' + H + '" role="img"><defs><clipPath id="'
    + id + '">' + clip.join('') + '</clipPath></defs><g clip-path="url(#' + id + ')">' + cor.join('') + '</g></svg>'
    + (tot > CAP + 1e-6 ? '<div class="waf-cap">acima da capacidade da matriz</div>' : '');
}
// escala "redonda" para que a maior modalidade caiba nas 70 posições (valor); quantidade fica em 10
const ESCALA_RS = [50, 100, 200, 250, 500, 600, 750, 1000, 1500, 2000, 2500, 5000, 10000].map((x) => x * 1e6);
function renderWaffle() {
  const el = document.getElementById('g-waf');
  if (!el) return;
  const t = { status: true, origem: true };  // mesmos filtros da tabela do 1.1
  const m = MODS.slice(0, -1).map((nome, i) => ({ i, nome, qo: 0, qf: 0, vo: 0, vf: 0 }));
  let qo = 0, qf = 0, vo = 0, vf = 0;
  for (const r of SEL) {
    if (!passa(SRC.sel, r, t)) continue;
    const a = m[r[0]];
    if (r[1] === 1) { qo++; if (a) a.qo++; } else if (r[1] === 0) { qf++; if (a) a.qf++; }
    vo += r[4]; vf += r[5];
    if (a) { a.vo += r[4]; a.vf += r[5]; }
  }
  const val = state.wmed === 'valor', pct = state.wmodo === 'pct';
  // medida: nº de propostas ou valor da portaria, por fonte (OGU = vlr_portaria_ogu, FIN = vlr_portaria_fin)
  const ogu = (a) => (val ? a.vo : a.qo), fin = (a) => (val ? a.vf : a.qf);
  const TOT = { qo, qf, vo, vf };
  const tot = ogu(TOT) + fin(TOT);
  const maxMod = Math.max(0, ...m.map((a) => ogu(a) + fin(a)));
  const un = val ? (ESCALA_RS.find((u) => u * 70 >= maxMod) || ESCALA_RS[ESCALA_RS.length - 1]) : 10;
  WAF.un = un;
  const fmt = (x) => (val ? BM(x) : I(x));
  const curto = (x) => (val ? (x >= 1e9 ? fmtBi.format(x / 1e9) + ' bi' : I(Math.round(x / 1e6)) + ' mi') : I(x));  // linhas OGU/FIN
  const pc = (a, b) => (b ? fmtPct.format(100 * a / b) + '%' : '—');
  const unid = val ? '' : (pct ? '' : ' propostas');
  m.sort((a, b) => (ogu(b) + fin(b)) - (ogu(a) + fin(a)) || a.i - b.i);
  const po = tot ? 100 * ogu(TOT) / tot : 0;
  const seg = (cls, rot, q, w) => '<div class="waf-seg ' + cls + '" style="width:' + w + '%">'
    + (w >= 14 ? '<b>' + rot + '</b> ' + (pct ? '' : fmt(q) + ' · ') + pc(q, tot) : '') + '</div>';
  const escala = val ? 'R$ ' + I(un / 1e6) + ' mi' : '10 propostas';
  const o = [];
  o.push('<div class="waf-top"><div class="waf-tot' + (val ? ' rs' : '') + '"><div class="n">' + (val ? BM(tot) : I(tot)) + '</div><div class="l">'
    + (val ? 'valor da carteira' : 'propostas na carteira') + '</div></div>'
    + '<div class="waf-faixa"><div class="waf-bar">' + seg('ogu', 'OGU', ogu(TOT), po) + seg('fin', 'FIN', fin(TOT), 100 - po) + '</div>'
    + '<div class="waf-bar-leg"' + (po >= 14 && po <= 86 ? ' hidden' : '') + '><span><i style="background:' + COR_OGU + '"></i>OGU <b>'
    + fmt(ogu(TOT)) + '</b> · ' + pc(ogu(TOT), tot) + '</span><span><i style="background:' + COR_FIN + '"></i>FIN <b>' + fmt(fin(TOT))
    + '</b> · ' + pc(fin(TOT), tot) + '</span></div></div>'
    + '<div class="waf-leg"><span><i style="background:' + COR_OGU + '"></i>OGU</span><span><i style="background:' + COR_FIN + '"></i>FIN</span>'
    + '<span><i style="background:' + COR_VAZIO + '"></i>posição não utilizada</span><div class="esc">Cada quadrado completo = ' + escala + '.</div></div></div>');
  o.push('<div class="waf-grid">');
  for (const a of m) {
    const n = ogu(a) + fin(a);
    const grande = pct ? pc(n, tot) : fmt(n);
    const rotulo = pct ? 'da carteira' : (val ? 'valor' : 'propostas');
    const linha = (rot, cor, x) => '<div class="f"><i style="background:' + cor + '"></i>' + rot
      + (pct ? '' : ' <b>' + curto(x) + '</b>') + '<span>' + pc(x, n) + '</span></div>';
    o.push('<div class="waf-card"><div class="waf-nome"><span>' + a.nome + '</span>'
      + (ICONES[a.i] ? '<span class="waf-ico"><img src="' + ICONES[a.i] + '" alt=""></span>' : '') + '</div><div class="waf-corpo">' + waffleSvg(ogu(a), fin(a), un, 'wc' + a.i)
      + '<div class="waf-num' + (val && !pct ? ' rs' : '') + '"><div class="q">' + grande + '</div><div class="ql">' + rotulo + '</div>'
      + linha('OGU', COR_OGU, ogu(a)) + linha('FIN', COR_FIN, fin(a)) + '</div></div></div>');
  }
  o.push('</div>');
  o.push('<div class="waf-fin"><div><span>Valor OGU</span><b>R$ ' + M(vo) + ' mi</b></div><div><span>Valor FIN</span><b>R$ ' + M(vf)
    + ' mi</b></div><div class="t"><span>Valor total</span><b>R$ ' + M(vo + vf) + ' mi</b></div></div>');
  el.innerHTML = o.join('');
  el.classList.toggle('so-ogu', state.ogu && !state.fin);
  el.classList.toggle('so-fin', state.fin && !state.ogu);
  if (el.closest('[data-deck-active]')) animarWaffle();  // no slide visível, cada render anima
}
const WAF = { un: 10, timer: 0 };
// animação do 1.2: os quadrados se preenchem em sequência e a faixa OGU/FIN cresce (só CSS)
function animarWaffle() {
  const el = document.getElementById('g-waf');
  if (!el || (window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches)) return;
  el.classList.remove('anim'); void el.offsetWidth; el.classList.add('anim');
  clearTimeout(WAF.timer);
  WAF.timer = setTimeout(() => el.classList.remove('anim'), 70 * 35 + 900);  // último quadrado + duração
}

// ---- 3.2 · régua do prazo da licitação (porte do regua-licitacao.js do painelpac). Antes = prazo legal
// (LAE + 60 / publicação + 120); agora = prazo efetivo (o maior entre o legal e a data-limite de 30/10/2026),
// os dois classificados na data da extração. Medida: 1 ponto = 1 contrato ou ponto com área ∝ repasse.
const RG_LIM = '2026-10-30', RG_PC72 = '2025-10-21';
const RG_COR = { vencido: '#B42318', janela: '#B45309', depois: '#356C8C' };
const RGN = { pub: 0, pc72: 0, semLae: 0, resg: 0, hom: 0, excl: 0, semmod: 0 };
function renderRegua() {
  const el = document.getElementById('g-regua');
  if (!el) return;
  const ref = dUTC(HOJE_ISO), lim = dUTC(RG_LIM), corte = dUTC(RG_PC72);
  const faixa = (iso) => { const t = dUTC(iso); return t < ref ? 'vencido' : (t <= lim ? 'janela' : 'depois'); };
  const efet = (legal, calc) => (calc || (dUTC(legal) < lim ? RG_LIM : legal));
  const pub = [], hom = [];
  Object.assign(RGN, { pub: 0, pc72: 0, semLae: 0, resg: 0, hom: 0, excl: 0, semmod: 0 });
  for (const r of RG) {
    if (!passa(SRC.rg, r, { excl: true })) continue;
    if (r[5]) { if (!r[8]) { if (r[5] === 1) RGN.excl++; else RGN.semmod++; } continue; }  // fora das contas
    const pc72 = r[12] && dUTC(r[12]) < corte;
    if (!r[8]) {
      if (pc72) { RGN.pc72++; continue; }
      if (!r[6]) { RGN.semLae++; continue; }
      const ef = efet(r[6], r[7]);
      pub.push({ r, legal: r[6], ef, antes: faixa(r[6]), agora: faixa(ef) });
    } else if (!r[11]) {
      if (pc72 || !r[9]) continue;
      const ef = efet(r[9], r[10]);
      hom.push({ r, legal: r[9], ef, antes: faixa(r[9]), agora: faixa(ef) });
    }
  }
  RGN.pub = pub.length; RGN.hom = hom.length;
  const val = state.rmed === 'valor';
  const vmax = Math.max(1, ...pub.map((it) => it.r[4] || 0));
  const tam = (it) => (val ? Math.round(8 + 24 * Math.sqrt((it.r[4] || 0) / vmax)) : 17);
  const soma = (l) => (val ? BM(l.reduce((s, it) => s + (it.r[4] || 0), 0)) : I(l.length));
  const br = (iso) => iso.slice(8, 10) + '/' + iso.slice(5, 7) + '/' + iso.slice(0, 4);
  const ponto = (it, cor, anel) => {
    const r = it.r, t = [r[13], [r[14], r[1]].filter(Boolean).join('/'), 'prazo legal ' + br(it.legal)]
      .concat(it.ef !== it.legal ? ['efetivo ' + br(it.ef)] : []).concat(val ? [BM(r[4] || 0)] : []).filter(Boolean).join(' · ');
    return '<a class="rg-dot' + (anel ? ' anel' : '') + '" style="background:' + cor + ';width:' + tam(it) + 'px;height:' + tam(it)
      + 'px" title="' + t + ' · abrir no SACI" href="https://saci.cidades.gov.br/contratos/' + encodeURIComponent(r[15]) + '" target="_blank" rel="noopener"></a>';
  };
  const coluna = (rot, lista, html, larg, dest) => '<div class="rg-col' + (dest ? ' dest' : '') + '"><span class="rg-n">' + soma(lista)
    + '</span><div class="rg-pilha" style="width:' + larg + 'px">' + html + '</div><div class="rg-base"></div><span class="rg-lab">' + rot + '</span></div>';
  const ordem = { vencido: 0, janela: 1, depois: 2 };
  const L = (n) => (val ? n * 32 : n * 21);  // largura da pilha para n pontos por linha
  const o = [];
  const lim2 = RG_LIM.slice(8, 10) + '/' + RG_LIM.slice(5, 7), ref2 = HOJE_ISO.slice(8, 10) + '/' + HOJE_ISO.slice(5, 7);
  o.push('<div class="rg-cab"><h3>' + (val ? soma(pub) + ' em ' + I(pub.length) + ' contratos sem edital publicado · área do ponto ∝ repasse'
    : I(pub.length) + ' contratos sem edital publicado · 1 ponto = 1 contrato') + '</h3><div class="rg-leg">'
    + '<span><i style="background:' + RG_COR.vencido + '"></i>prazo vencido em ' + ref2 + '</span>'
    + '<span><i style="background:' + RG_COR.janela + '"></i>vence até ' + lim2 + '</span>'
    + '<span><i style="background:' + RG_COR.depois + '"></i>vence depois de ' + lim2 + '</span></div></div>');
  if (!pub.length) o.push('<p class="nota">Nenhum contrato aguardando publicação com prazo calculado neste recorte.</p>');
  else {
    const meses = pub.map((it) => +it.legal.slice(0, 4) * 12 + (+it.legal.slice(5, 7) - 1));
    const m0 = Math.min(...meses), m1 = Math.max(...meses);
    const cols = [];
    for (let m = m0; m <= m1; m++) {
      const ano = Math.floor(m / 12), mes = m % 12;
      const doMes = pub.filter((it) => +it.legal.slice(0, 4) === ano && +it.legal.slice(5, 7) - 1 === mes)
        .sort((a, b) => ordem[a.antes] - ordem[b.antes] || (a.legal < b.legal ? -1 : 1));
      cols.push(coluna(MESES[mes] + (mes === 0 || m === m0 ? '/' + String(ano).slice(2) : ''), doMes,
        doMes.map((it) => ponto(it, RG_COR[it.antes])).join(''), L(4)));
    }
    const g = (k) => pub.filter((it) => it.agora === k);
    const venc = g('vencido'), noLim = g('janela').sort((a, b) => ordem[a.antes] - ordem[b.antes]), dep = g('depois');
    RGN.resg = noLim.filter((it) => it.antes === 'vencido').length;
    const ag = [];
    if (venc.length) ag.push(coluna('vencidas', venc, venc.map((it) => ponto(it, RG_COR.vencido)).join(''), L(4)));
    if (noLim.length) ag.push(coluna(lim2, noLim, noLim.map((it) => ponto(it, RG_COR.janela, it.antes === 'vencido')).join(''), L(noLim.length > 40 ? 10 : 6), true));
    if (dep.length) ag.push(coluna('depois', dep, dep.map((it) => ponto(it, RG_COR.depois)).join(''), L(3)));
    o.push('<div class="rg-corpo"><div class="rg-lado"><div class="rg-tit">Antes · mês do prazo legal (LAE + 60 dias)</div><div class="rg-colunas">'
      + cols.join('') + '</div></div><div class="rg-seta">' + SETA + '</div><div class="rg-lado"><div class="rg-tit">Agora · prazo efetivo</div><div class="rg-colunas">'
      + ag.join('') + '</div>' + (RGN.resg ? '<div class="rg-obs"><i class="rg-dot anel" style="background:' + RG_COR.janela + '"></i>anel vermelho: estava vencido e ganhou até 30/10/2026 (<b>'
      + I(RGN.resg) + '</b>)</div>' : '') + '</div></div>');
  }
  // antes × agora, nas duas etapas
  const barra = (rot, lista, k) => {
    const tot = lista.reduce((s, it) => s + (val ? it.r[4] || 0 : 1), 0);
    const segs = ['vencido', 'janela', 'depois'].map((f) => {
      const sub = lista.filter((it) => it[k] === f), v = sub.reduce((s, it) => s + (val ? it.r[4] || 0 : 1), 0);
      return v ? '<div class="rg-seg" style="flex:' + v + ' 1 0;background:' + RG_COR[f] + '" title="' + soma(sub) + '">' + soma(sub) + '</div>' : '';
    }).join('');
    return '<div class="rg-barra"><span>' + rot + '</span><div class="rg-trilho">' + (tot ? segs : '') + '</div></div>';
  };
  const comp = (tit, lista) => '<div class="rg-comp"><div class="rg-comp-t">' + tit + ' · ' + (val ? soma(lista) + ' em ' : '') + I(lista.length)
    + ' contratos com prazo</div>' + (lista.length ? barra('Antes', lista, 'antes') + barra('Agora', lista, 'agora') : '<p class="nota">Nenhum contrato nesta etapa.</p>') + '</div>';
  o.push('<div class="rg-comps">' + comp('Publicação', pub) + comp('Homologação', hom) + '</div>');
  el.innerHTML = o.join('');
}

// ---- 2.2 · alinhamento das suspensivas (DMP, 08/2026) — porte do alinhamento-timeline.js do painelpac:
// uma linha por modalidade, um círculo por data alinhada (área ∝ repasse ou nº de contratos) e o anel
// verde com a fatia já retirada. A data é fixa: o gráfico parte de todos os contratos com data.
const HOJE_ISO = __HOJE__;
const ALN = { n: 0, ret: 0, pc: 0, canc: 0, ps: 0, grupos: null, aberto: null };
const MESES = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez'];
const dUTC = (iso) => Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10));
function renderAlinhamento() {
  const el = document.getElementById('g-alin');
  if (!el) return;
  const t = {};
  Object.assign(ALN, { n: 0, ret: 0, pc: 0, canc: 0, ps: 0 });
  const grupos = new Map();
  for (const r of OG) {
    if (!passa(SRC.og, r, t)) continue;
    if (!r[13]) { if (r[6] === 1 && !r[5]) ALN.ps++; continue; }
    ALN.n++;
    const ret = r[6] === 0;
    if (ret) ALN.ret++; else if (r[5]) ALN.canc++; else ALN.pc++;
    const k = r[0] + '|' + r[13];
    let g = grupos.get(k);
    if (!g) grupos.set(k, g = { key: k, mod: r[0], iso: r[13], n: 0, vlr: 0, ret: 0, vret: 0, canc: 0, vcanc: 0, rows: [] });
    g.n++; g.vlr += r[4]; g.rows.push(r);
    if (ret) { g.ret++; g.vret += r[4]; } else if (r[5]) { g.canc++; g.vcanc += r[4]; }
  }
  // "Só pendentes": tira a fatia já retirada (o anel verde) e os cancelados — só o que falta retirar
  const pend = state.alnp === 'pend';
  const lista = [...grupos.values()]
    .map((g) => (pend ? { ...g, n: g.n - g.ret - g.canc, vlr: g.vlr - g.vret - g.vcanc, ret: 0, vret: 0 } : g))
    .filter((g) => g.n > 0);
  ALN.grupos = new Map(lista.map((g) => [g.key, g]));
  const totMod = new Map();
  for (const g of lista) {
    const tm = totMod.get(g.mod) || { n: 0, v: 0 };
    tm.n += g.n; tm.v += g.vlr; totMod.set(g.mod, tm);
  }
  if (!lista.length) { el.innerHTML = '<p class="nota">Sem contratos com data alinhada neste recorte.</p>'; return; }

  const W = 1712, LEFT = 260, RIGHT = 16, HEAD = 34, HMAX = 572, FOLGA = 12;  // FOLGA: respiro entre as linhas
  const T0 = Date.UTC(2026, 3, 1), T1 = Date.UTC(2027, 3, 1), PLOT = W - LEFT - RIGHT;
  const x = (ms) => LEFT + (ms - T0) / (T1 - T0) * PLOT;
  const pelo = state.aln === 'n' ? 'n' : 'vlr';
  // rótulo da bolha: nº de contratos ou o repasse somado (curto); fora da bolha quando não cabe
  const VC = (v) => (v >= 1e9 ? fmtBi.format(v / 1e9) + ' bi' : I(Math.round(v / 1e6)) + ' mi');
  const rot = (g) => (pelo === 'vlr' ? VC(g.vlr) : I(g.n));
  const largura = (txt, r) => txt.length * (r < 15 ? 7 : 8);
  const max = Math.max(1, ...lista.map((g) => g[pelo]));
  const mods = MODS.map((_, i) => i).filter((i) => totMod.has(i));
  // empacota círculos em faixas na linha; se não couber na altura, reduz o raio máximo
  let RMAX = 30, linhas, altura;
  for (;;) {
    const RMIN = Math.min(11, RMAX);
    altura = HEAD;
    linhas = mods.map((m) => {
      const itens = lista.filter((g) => g.mod === m)
        .map((g) => {
          const r = Math.max(RMIN, Math.sqrt(g[pelo] / max) * RMAX), txt = rot(g), w = largura(txt, r);
          const fora = w > 2 * r - 6, anel = g.ret ? 6 : 0;
          return { g, cx: x(dUTC(g.iso)), r, txt, fora, ini: x(dUTC(g.iso)) - r - anel,
                   fim: x(dUTC(g.iso)) + r + anel + (fora ? w + 8 : 0) };
        })
        .sort((a, b) => a.ini - b.ini);
      const faixas = [];
      for (const it of itens) {
        let f = faixas.find((l) => l.fim + 8 <= it.ini);
        if (!f) faixas.push(f = { itens: [], fim: -1e9, rmax: 0 });
        f.itens.push(it); f.fim = it.fim; f.rmax = Math.max(f.rmax, it.r);
      }
      const h = Math.max(42 + FOLGA, faixas.reduce((s, l) => s + l.rmax * 2 + 8, 0) + 6 + FOLGA);
      const linha = { m, y: altura, h, faixas };
      altura += h;
      return linha;
    });
    if (altura + 14 <= HMAX || RMAX <= 14) break;
    RMAX -= 2;
  }
  const H = altura + 14;
  const FONT = "font-family=\"rawline, Raleway, sans-serif\"";
  const o = ['<svg viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="Linha do tempo do alinhamento das suspensivas">'];
  for (let i = 0, m = new Date(T0); m.getTime() < T1; i++) {
    const a = m.getTime(), b = Date.UTC(m.getUTCFullYear(), m.getUTCMonth() + 1, 1);
    const x0 = x(a), x1 = x(Math.min(b, T1));
    if (i % 2 === 0) o.push('<rect x="' + x0 + '" y="' + (HEAD - 24) + '" width="' + (x1 - x0) + '" height="' + (H - HEAD + 24) + '" fill="#F3F5F8"></rect>');
    const lbl = MESES[m.getUTCMonth()] + (m.getUTCMonth() === 0 || i === 0 ? '/' + String(m.getUTCFullYear()).slice(2) : '');
    o.push('<text x="' + (x0 + x1) / 2 + '" y="' + (HEAD - 8) + '" text-anchor="middle" font-size="17" font-weight="700" fill="#636363" ' + FONT + '>' + lbl + '</text>');
    m = new Date(b);
  }
  for (const l of linhas) {
    o.push('<line x1="0" x2="' + W + '" y1="' + (l.y + l.h) + '" y2="' + (l.y + l.h) + '" stroke="#DCDCDC" stroke-width="1"></line>');
    const ly = l.y + Math.min(l.h / 2, 26);
    o.push('<text x="0" y="' + (ly + 2) + '" font-size="19" font-weight="700" fill="#071D41" ' + FONT + '>' + MODS[l.m].replace('Mobilidade: Médias e Grandes Cidades', 'Mobilidade').replace('Abastecimento de Água', 'Água') + '</text>');
    o.push('<text x="0" y="' + (ly + 22) + '" font-size="15" fill="#636363" ' + FONT + '>' + (pelo === 'vlr' ? BM(totMod.get(l.m).v) + ' · ' : '') + I(totMod.get(l.m).n)
      + (totMod.get(l.m).n === 1 ? ' contrato' + (pend ? ' pendente' : '') : ' contratos' + (pend ? ' pendentes' : '')) + '</text>');
    let cy = l.y + 6 + FOLGA / 2;
    for (const f of l.faixas) {
      cy += f.rmax + 4;
      for (const { g, cx, r, txt, fora } of f.itens) {
        const dt = g.iso.slice(8, 10) + '/' + g.iso.slice(5, 7) + '/' + g.iso.slice(0, 4);
        o.push('<g class="aln-b" data-k="' + g.key + '" tabindex="0" role="button"><title>' + MODS[g.mod] + ' · ' + dt + '\n' + I(g.n) + (pend ? ' pendentes · ' : ' contratos · ') + BM(g.vlr)
          + (pend ? '' : '\nJá retiradas: ' + I(g.ret) + ' (' + BM(g.vret) + ') · pendentes: ' + I(g.n - g.ret)) + '\nClique para ver os contratos</title>');
        o.push('<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="#1351B4" fill-opacity="0.85"></circle>');
        if (g.ret) {
          const rr = r + 5, c = 2 * Math.PI * rr;
          o.push('<circle cx="' + cx + '" cy="' + cy + '" r="' + rr + '" fill="none" stroke="#DCE3EC" stroke-width="3.5"></circle>');
          o.push('<circle cx="' + cx + '" cy="' + cy + '" r="' + rr + '" fill="none" stroke="#168821" stroke-width="3.5" stroke-dasharray="'
            + (c * g.ret / g.n).toFixed(1) + ' ' + c.toFixed(1) + '" transform="rotate(-90 ' + cx + ' ' + cy + ')"></circle>');
        }
        const fs = r < 15 ? 12 : 14;
        o.push(fora
          ? '<text x="' + (cx + r + (g.ret ? 9 : 5)) + '" y="' + (cy + 5) + '" font-size="' + fs + '" font-weight="800" fill="#071D41" ' + FONT + '>' + txt + '</text></g>'
          : '<text x="' + cx + '" y="' + (cy + 5) + '" text-anchor="middle" font-size="' + fs + '" font-weight="800" fill="#FFFFFF" ' + FONT + '>' + txt + '</text></g>');
      }
      cy += f.rmax + 4;
    }
  }
  const hx = x(dUTC(HOJE_ISO));
  o.push('<line x1="' + hx + '" x2="' + hx + '" y1="' + (HEAD - 24) + '" y2="' + H + '" stroke="#BC4749" stroke-width="2" stroke-dasharray="6 5"></line>');
  o.push('<text x="' + (hx + 6) + '" y="' + (H - 4) + '" font-size="14" font-weight="700" fill="#9A383A" ' + FONT + '>extração ' + HOJE_ISO.slice(8, 10) + '/' + HOJE_ISO.slice(5, 7) + '</text>');
  o.push('</svg>');
  o.push('<div class="alin-leg"><span><i class="lg-dot"></i>círculo = data alinhada · área ∝ ' + (pelo === 'n' ? 'nº de contratos' : 'repasse')
    + ' · número = ' + (pelo === 'n' ? 'contratos' : 'repasse somado (R$)') + '</span>'
    + (pend ? '<span>só pendentes: sem a fatia já retirada</span>' : '<span><i class="lg-ring"></i>anel verde = fatia já retirada</span>')
    + '<span><i class="lg-hoje"></i>data da extração</span><span class="aln-dica">clique numa bolinha para ver os contratos</span></div>');
  o.push('<div class="aln-lista" hidden></div>');
  el.innerHTML = o.join('');
  if (!el.dataset.clique) {  // clique numa bolinha abre a lista; fora dela (ou Esc) fecha
    el.dataset.clique = '1';
    const abrir = (b) => {  // o quadro abre do lado oposto ao da bolinha, para não cobri-la
      const rb = b.getBoundingClientRect(), re = el.getBoundingClientRect();
      ALN.lado = rb.left + rb.width / 2 > re.left + re.width / 2 ? 'esq' : 'dir';
      ALN.aberto = b.dataset.k; listaAlinhamento();
    };
    el.addEventListener('click', (e) => {
      // no toque, o deck avança o slide em área não interativa: o clique no gráfico fica com o gráfico
      if (!e.target.closest('a[href]') && (e.target.closest('.aln-b') || e.target.closest('.aln-lista'))) e.preventDefault();
      const b = e.target.closest('.aln-b');
      if (b) { abrir(b); return; }
      if (e.target.closest('.aln-fechar') || !e.target.closest('.aln-lista')) { ALN.aberto = null; listaAlinhamento(); }
    });
    el.addEventListener('keydown', (e) => {
      const b = e.target.closest && e.target.closest('.aln-b');
      if (b && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); abrir(b); }
      if (e.key === 'Escape') { ALN.aberto = null; listaAlinhamento(); }
    });
  }
  listaAlinhamento();  // reabre a lista após troca de filtro, se o grupo ainda existir
}

// quadro com os contratos do grupo clicado (modalidade × data alinhada)
function listaAlinhamento() {
  const box = document.querySelector('#g-alin .aln-lista');
  if (!box) return;
  const g = ALN.aberto && ALN.grupos && ALN.grupos.get(ALN.aberto);
  document.querySelectorAll('#g-alin .aln-b').forEach((b) => b.classList.toggle('sel', !!g && b.dataset.k === ALN.aberto));
  if (!g) { box.hidden = true; box.innerHTML = ''; return; }
  const pend = state.alnp === 'pend';
  const sit = (r) => (r[6] === 0 ? ['retirada', 'ret'] : r[5] ? ['cancelado', 'canc'] : ['pendente', 'pend']);
  const rows = g.rows.filter((r) => !pend || (r[6] !== 0 && !r[5]))
    .sort((a, b) => (sit(a)[1] === 'pend' ? 0 : 1) - (sit(b)[1] === 'pend' ? 0 : 1) || b[4] - a[4]);
  const dt = g.iso.slice(8, 10) + '/' + g.iso.slice(5, 7) + '/' + g.iso.slice(0, 4);
  box.innerHTML = '<div class="aln-l-cab"><div><b>' + MODS[g.mod] + '</b><span>data alinhada ' + dt + ' · ' + I(rows.length)
    + (pend ? ' pendentes' : ' contratos') + ' · ' + BM(rows.reduce((s, r) => s + r[4], 0)) + '</span></div>'
    + '<button type="button" class="aln-fechar" aria-label="Fechar">×</button></div><div class="aln-l-corpo"><table>'
    + '<thead><tr><th>Situação</th><th>Convênio</th><th>Município/UF</th><th>Repasse</th><th></th></tr></thead><tbody>'
    + rows.map((r) => { const [t, c] = sit(r); return '<tr><td><i class="aln-st ' + c + '"></i>' + t + '</td><td>' + (r[17] || '—')
      + '</td><td>' + [r[18], r[1]].filter(Boolean).join('/') + '</td><td>' + BM(r[4]) + '</td><td><a href="https://saci.cidades.gov.br/contratos/'
      + encodeURIComponent(r[19]) + '" target="_blank" rel="noopener">SACI ↗</a></td></tr>'; }).join('')
    + '</tbody></table></div>';
  box.classList.toggle('esq', ALN.lado === 'esq');
  box.hidden = false;
}

function td(c) {
  return Array.isArray(c) ? '<td class="' + c[1] + '">' + c[0] + '</td>' : '<td>' + c + '</td>';
}

function render() {
  const T = {};
  for (const t of TABLES) {
    const acc = MODS.map(() => t.init());
    const tot = t.init();
    for (const p of t.parts) {
      const s = SRC[p.src];
      for (const r of s.rows) {
        if (p.keep && !p.keep(r)) continue;
        if (!passa(s, r, t)) continue;
        p.add(acc[r[0]], r);
        p.add(tot, r);
      }
    }
    T[t.id] = tot;
    const body = [];
    acc.forEach((a, i) => { if (a.n) body.push('<tr><td>' + MODS[i] + '</td>' + t.cols(a, tot).map(td).join('') + '</tr>'); });
    const tb = document.querySelector('#' + t.id + ' tbody');
    const ncols = document.querySelectorAll('#' + t.id + ' thead tr:last-child th').length;
    if (!body.length) {
      tb.innerHTML = '<tr><td class="empty" colspan="' + ncols + '">Sem registros neste recorte.</td></tr>';
    } else {
      body.push('<tr class="tot"><td>TOTAL</td>' + t.cols(tot, tot).map((c) => td(Array.isArray(c) ? c[0] : c)).join('') + '</tr>');
      tb.innerHTML = body.join('');
    }
    if (t.pctHead) {  // cabeçalhos em % quando a tabela está em "% do total"
      document.querySelectorAll('#' + t.id + ' thead th').forEach((th, i) => {
        if (th.dataset.orig === undefined) th.dataset.orig = th.innerHTML;
        const o = th.dataset.orig;
        th.innerHTML = state.pct1 !== '1' || !i ? o : (o.includes('R$ mi') ? o.replace('R$ mi', '%') : o + ' (%)');
      });
    }
    if (t.kpis) t.kpis(tot).forEach((v, i) => {
      const el = document.querySelector('[data-kpi="' + t.id + ':' + i + '"]');
      if (el) el.textContent = tot.n ? v : '—';
    });
  }
  renderFunil();
  renderAlinhamento();
  renderWaffle();
  renderRegua();
  ORIGENS.forEach((sf) => {
    const m = state[sf + 'mig'], n = state[sf + 'nov'];
    const txt = m && n ? 'migradas + novas' : (m ? 'somente migradas' : 'somente novas');
    document.querySelectorAll('.oriname' + sf).forEach((el) => { el.textContent = txt; });
  });
  document.querySelectorAll('.oribtn').forEach((el) => {
    el.setAttribute('aria-pressed', String(state[el.dataset.ori]));
  });
  document.querySelectorAll('.rdbtn').forEach((el) => {
    el.setAttribute('aria-pressed', String(state[el.dataset.k] === el.dataset.v));
  });
  document.querySelectorAll('[data-ref]').forEach((el) => { el.innerHTML = REFS[el.dataset.ref](T); });
  const fonname = state.ogu && state.fin ? 'OGU + FIN' : (state.ogu ? 'somente OGU' : 'somente FIN');
  document.querySelectorAll('.fonname').forEach((el) => { el.textContent = fonname; });
  document.querySelectorAll('.fonbtn').forEach((el) => {
    el.setAttribute('aria-pressed', String(state[el.dataset.fon]));
  });
  const stname = state.sel && state.enq ? 'selecionadas + enquadradas'
    : (state.sel ? 'somente selecionadas' : 'somente enquadradas');
  const anosOn = ANOS.filter((a) => state.anos[a]);
  const anoname = anosOn.length === ANOS.length ? 'todos' : anosOn.join(' + ') + ' (sem migradas)';
  document.querySelectorAll('.ufname').forEach((el) => { el.textContent = state.uf || 'Brasil'; });
  document.querySelectorAll('.stname').forEach((el) => { el.textContent = stname; });
  document.querySelectorAll('.anoname').forEach((el) => { el.textContent = anoname; });
  document.querySelectorAll('select.ufsel').forEach((el) => { el.value = state.uf; });
  document.querySelectorAll('.stbtn[data-st]').forEach((el) => {
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
  const ori = (params.get('origem') || '').toLowerCase().trim();
  if (ori === 'mig') state.nov = false; else if (ori === 'nov') state.mig = false;
  const ori43 = (params.get('origem43') || '').toLowerCase().trim();
  if (ori43 === 'mig') { state.gmig = true; state.gnov = false; } else if (ori43 === 'ambas') state.gmig = true;
  if (params.get('c95') === '1') state.c95 = '1';
  if (params.get('aln') === 'n') state.aln = 'n';
  if (params.get('alnp') === 'pend') state.alnp = 'pend';
  if (params.get('wmed') === 'valor') state.wmed = 'valor';
  if (params.get('wmodo') === 'pct') state.wmodo = 'pct';
  if (params.get('rmed') === 'valor') state.rmed = 'valor';
  if (params.get('obra') === 'saci') state.sitobra = 'saci';
  if (params.get('pct') === '1') state.pct1 = '1';
  if (params.get('med') === 'valor') state.med = 'valor';
  if (params.get('modo') === 'pct') state.modo = 'pct';
  const fon = (params.get('fonte') || '').toLowerCase().trim();
  if (fon === 'ogu') state.fin = false; else if (fon === 'fin') state.ogu = false;
  const anoParam = (params.get('ano') || '').trim();
  if (anoParam) {
    // aceita o ano completo (2025) ou curto (25)
    const pedidos = anoParam.split(',').map((a) => a.trim()).map((a) => a.length === 2 ? '20' + a : a)
      .filter((a) => ANOS.includes(a));
    if (pedidos.length) ANOS.forEach((a) => { state.anos[a] = pedidos.includes(a); });
  }
  render();
  document.querySelectorAll('select.ufsel').forEach((el) => {
    el.addEventListener('change', function () { state.uf = this.value; render(); });
  });
  document.querySelectorAll('.stbtn[data-st], .fonbtn, .oribtn').forEach((el) => {
    el.addEventListener('click', function () {
      const k = this.dataset.st || this.dataset.fon || this.dataset.ori;
      const other = PAR[k];
      if (state[k] && !state[other]) return; // pelo menos um ativo em cada grupo
      state[k] = !state[k];
      render();
    });
  });
  document.querySelectorAll('.rdbtn').forEach((el) => {
    el.addEventListener('click', function () { state[this.dataset.k] = this.dataset.v; render(); });
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

  // ---- animação do 4.3 ao entrar no slide ----
  const deck = document.querySelector('deck-stage');
  if (deck) deck.addEventListener('slidechange', (e) => {
    if (e.detail && e.detail.slide && e.detail.slide.querySelector('#g-funil')) animarFunil();
    if (e.detail && e.detail.slide && e.detail.slide.querySelector('#g-waf')) animarWaffle();
  });
  setTimeout(() => {
    if (document.querySelector('[data-deck-active] #g-funil')) animarFunil();
    if (document.querySelector('[data-deck-active] #g-waf')) animarWaffle();
  }, 120);

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
    pararFunil(); if (FUN.blocos) aplicarFunil();  // gráfico 4.3 no estado final
    const waf = document.getElementById('g-waf'); if (waf) waf.classList.remove('anim');  // 1.2 completo
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
      if (!(state.ogu && state.fin)) partes.push(state.ogu ? 'ogu' : 'fin');
      if (!(state.mig && state.nov)) partes.push(state.mig ? 'migradas' : 'novas');
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
      const filtrado = state.uf !== '' || !state.sel || !state.enq || !state.ogu || !state.fin
        || !state.mig || !state.nov || state.pct1 !== '0' || state.med !== 'qtd' || state.modo !== 'tot'
        || state.gmig || !state.gnov || state.c95 !== '0' || state.aln !== 'vlr' || state.alnp !== 'todos' || state.sitobra !== 'bal'
        || state.wmed !== 'qtd' || state.wmodo !== 'tot' || state.rmed !== 'qtd'
        || ANOS.some((a) => !state.anos[a]);
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


app_js = (APP_JS.replace('__MODS__', js(MODS)).replace('__ANOS__', js(ANOS)).replace('__HOJE__', js(f'{HOJE:%Y-%m-%d}'))
          .replace('__SEL__', js(SEL)).replace('__CT__', js(CT)).replace('__OG__', js(OG)).replace('__BX__', js(BX)).replace('__RG__', js(RG)).replace('__ICONES__', js(ICONES)))

SLIDES = SLIDES.replace('__NSLIDES__', f"{SLIDES.count('<section '):02d}")
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
