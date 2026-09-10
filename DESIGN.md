---
name: Pastel da TATI
description: PDV de balcão no idioma do cupom térmico
colors:
  paper: "#e4e8df"
  paper-deep: "#d5d9ce"
  ink: "#111411"
  ink-soft: "#3a4038"
  housing: "#1c211c"
  housing-2: "#262c25"
  rule: "#9aa194"
  alarm: "#c23b22"
  stamp: "#2f4a32"
  paper-on-housing: "#e4e8df"
typography:
  ui:
    fontFamily: "Source Sans 3, Segoe UI, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.4
    letterSpacing: "normal"
  mono:
    fontFamily: "Fragment Mono, ui-monospace, monospace"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.3
    letterSpacing: "0.02em"
  total:
    fontFamily: "Fragment Mono, ui-monospace, monospace"
    fontSize: "2.25rem"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "normal"
rounded:
  none: "0px"
spacing:
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
    rounded: "{rounded.none}"
    padding: "12px 20px"
  button-quiet:
    backgroundColor: "transparent"
    textColor: "{colors.paper}"
    rounded: "{rounded.none}"
    padding: "8px 16px"
  ticket:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "20px 24px"
---

# Design

## Overview

Sistema operacional de pastelaria. A venda é um cupom térmico saindo no balcão. Fundo é a carcaça da impressora. Superfície de trabalho é o papel térmico. Alarme vermelhão só para erro, estoque baixo e cancelamento.

## Colors

- `housing` carrega sidebar, header e fundo da app.
- `paper` carrega formulários, tabelas e o cupom do PDV.
- `ink` é texto e ação primária sobre o papel.
- `alarm` é a única cor de alerta. Não decora.

## Typography

Uma sans de trabalho (Source Sans 3) para labels e navegação. Fragment Mono para SKU, número da venda, data/hora e dinheiro. Totais usam o mono em escala grande, números tabulares.

## Layout

Desktop: sidebar 17rem + área de trabalho. PDV em duas colunas — campo de produtos e cupom de 24rem. Mobile: menu em details, cupom empilha abaixo da grade. Sem tipografia fluida.

## Elevation & Depth

Ticket tem sombra deslocada (`0 18px 40px`). Sem halo colorido. Picote é furo radial contra o housing, não borda decorativa.

## Shapes

Cantos retos. Sem pill. Controles de quantidade grandes, quadrados. O mundo é plástico de impressora e corte de papel, não card arredondado.

## Components

- Ticket: papel + picote superior/inferior + regra tracejada.
- Linha invertida: filtro ou forma de pagamento ativa vira ink sobre paper.
- Tabela operacional: cabeçalho mono pequeno, linhas com divisor 10% ink.
- PDV: busca em foco, grade com vão, total pregado, finalizar no pé do cupom.

## Do's and Don'ts

- Do: tratar o total como o valor do cupom, sempre visível.
- Do: prefixar dado fictício com DEMO.
- Don't: cards de métrica iguais como estrutura da página (o dashboard usa três instrumentos, não um template de hero-metric).
- Don't: segunda cor de destaque. O alarme não vira marca.
