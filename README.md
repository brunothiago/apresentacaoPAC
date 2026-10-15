# Novo PAC — MCid · Balanço da carteira

Apresentação em HTML (deck 16:9, mesmo layout gov.br da `novopac-apresentacao`) para a
Secretaria-Executiva, com o caminho da carteira em cinco etapas (slides numerados 1.1 … 5.2):

| Etapa | Slides | Fonte |
|---|---|---|
| 01 Seleção | Carteira de seleções (migradas + novas) · Novas seleções por ano | `se_cgpac.tab_base_unica_gm` (painelgm) |
| 02 Suspensivas | Cláusulas suspensivas OGU · Prazo das pendentes (PC 48/2026) | consulta OGU do painelpac |
| 03 Licitação | Etapa atual dos contratos OGU · Prazos do art. 36-A | consulta OGU do painelpac |
| 04 Contratação | Selecionado × contratado · Situação dos contratos assinados · Da seleção à obra (gráfico de blocos) | base GM × `se_saci.view_mat_carteira_investimento` |
| 05 Execução | Situação das obras · Execução média e paralisações | `se_saci.view_mat_carteira_investimento` |

## Como usar

Abra **`index.html`** em qualquer navegador. Não precisa de servidor.

- **← / →** (ou ↑ / ↓ e a rolagem do mouse) navegam · **M** abre o menu · **F** tela cheia.
- **Recorte (UF)**, **Fonte** (OGU / FIN) e **Ano** (23 / 25 / 26) valem para todos os slides;
  **Status** (Selecionadas / Enquadradas) só para os slides de seleção. Nos slides do painelpac
  (suspensivas e licitação) a fonte é sempre OGU. Também pela URL:
  `index.html?uf=SP&fonte=ogu&status=sel&ano=25,26` (ano curto ou completo).
- Slide 1.1: filtro **Origem** (Migradas / Novas, `?origem=mig|nov`) e, no rodapé, **Exibir
  Valores / % do total** (participação da modalidade em cada coluna, `?pct=1`).
- Slide 4.3 (da seleção à obra): **Medida** Quantidade / Valor e **Exibir** Total / %
  (`?med=valor&modo=pct`). Seleções → contratos assinados → obras iniciadas → concluídas;
  valor das seleções pela portaria e dos contratos pelo repasse/financiamento do SACI.
  **Origem** própria, que começa só com as novas (`?origem43=ambas|mig`), e **Concluídas**
  Situação no SACI / + obras iniciadas com ≥ 95% de execução física (`?c95=1`).
- As notas de rodapé conciliam os totais entre slides (ex.: novas seleções + migradas = carteira)
  e se recalculam com os filtros.
- **Exportar PDF** (encerramento): sem filtro baixa o PDF pré-gerado; com filtro, gera no navegador.
- Os botões **Seleção / SACI / Painelpac** do encerramento baixam as fotos do banco (com senha).

## Como atualizar os dados

Requer VPN, `uv` e `python/config.env` (credenciais do banco + `SENHA_BASE_XLSX` — o mesmo
arquivo da `novopac-apresentacao`, fora do git).

```bash
./atualizar.sh
```

1. `python/extrair.py` tira as três fotos do banco e registra a extração em `data/extracoes.json`;
2. `build.py` regera o `index.html` (dados embutidos) e o PDF (com o Google Chrome instalado).

Depois, se os números mudaram: suba a `VERSAO`, acrescente a linha em `HISTORICO` no `build.py`,
rode o build de novo e faça o commit.

> **Não edite o `index.html` à mão**: todo ajuste vai no `build.py`.

## Conferência: contratos sem modalidade

```bash
uv run --with pandas --with openpyxl --with python-dotenv --with msoffcrypto-tool \
       python python/conferir_sem_modalidade.py
```

Grava `conferencia/sem_modalidade.txt` com os contratos em "Outras / sem modalidade" (SACI e
painelpac). A pasta `conferencia/` fica fora do git (dados por contrato).

## Versionamento das bases

- Cada extração grava `data/<base>_<DDMMYYYY>_<HHMM>.xlsx` (carimbo = hora da extração), sempre
  **protegido por senha** (`SENHA_BASE_XLSX`), porque o repositório é público.
- Se uma base não mudou desde a extração anterior (mesmo conteúdo), a foto anterior é reaproveitada;
  se nada mudou, a extração nem é registrada.
- `data/extracoes.json` guarda o histórico: carimbo, arquivos, linhas, hash do conteúdo e a data de
  atualização de cada fonte (base GM, SACI, Transferegov, BDGestores, Power BI Caixa). O build usa
  sempre a última entrada.
- A apresentação mostra a versão (`VERSAO`, com histórico no rodapé do encerramento), a data de
  atualização de cada fonte na linha da tabela/rodapé e a data/hora da extração.

## Regras de recorte (`dados.py`)

- **Seleção**: as mesmas da `novopac-apresentacao` — migradas = `retomada`; seleções = `selecionada`
  e `enquadrada`; `substituída` e as 2 propostas MCMV FNHIS ficam de fora; uma linha por fonte.
- **Carteira SACI**: fases `NOVO PAC - Seleção` e `NOVO PAC - Migrado`, **sem a SNH** (o
  `NOVO PAC - MCMV` fica de fora). Contratação usa só a Seleção; Execução usa Seleção + Migrado,
  sem contratos cancelados/distratados nem obras canceladas.
- **painelpac**: a consulta é importada do próprio painelpac (`../painelpac/python/ogu/2_gerar_base_pc32.py`,
  ou `PAINELPAC_DIR` no config.env) — OGU do `NOVO PAC - Seleção`, sem SNH. Os status de prazo usam
  a data da extração (`CURRENT_DATE`); cancelados ficam fora das tabelas.
- **Ano e status dos contratos**: vêm da base GM pelo número da proposta + fonte
  (`num_proposta_selecao_pac`). Quem não casa usa o ano do instrumento/assinatura e conta como
  selecionada. Migradas não têm ano: com algum ano desligado, saem da conta.
- **Modalidade**: a da base GM quando casa; senão a do SACI. O que não é uma das 10 modalidades
  (Assessoria Técnica HIS, sem modalidade) aparece em "Outras / sem modalidade".
- **% físico / financeiro médio**: média simples por contrato, só das obras em execução ou paralisadas.

## Estrutura

```
index.html                     apresentação (autocontida, com filtros)
novopac-balanco-carteira.pdf   PDF pré-gerado no build
build.py                       gerador do index.html e do PDF
dados.py                       carga das fotos e regras de recorte
atualizar.sh                   extração + build
python/extrair.py              extrator do banco (somente leitura)
data/                          fotos protegidas por senha + extracoes.json
assets/                        design system do deck (da novopac-apresentacao)
```
