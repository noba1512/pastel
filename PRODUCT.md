# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

delegated: Django monólito server-rendered, Django Templates, Tailwind via CDN, Vanilla JS, SQLite padrão com PostgreSQL via env, Docker Compose. Escolha do brief do usuário, não do agente.

## Users

- **Caixa (primário):** funcionário no balcão, mouse e teclado, turno corrido. Job: localizar produto, montar pedido, receber pagamento, calcular troco, finalizar venda com o mínimo de cliques e erros.
- **Gerente:** controla operação do dia. Job: produtos, categorias, estoque, vendas, dashboard. Sem superuser automático.
- **Administrador:** acesso total, inclusive usuários, permissões e administração operacional.

## Product Purpose

Sistema interno de PDV, caixa, estoque e gestão operacional para a pastelaria Pastel da TATI. Success: venda no balcão fecha rápido, totais e estoque são verdade do servidor, histórico e cancelamento preservam auditoria.

## Positioning

PDV de balcão com preço, total e estoque recalculados no servidor em transação atômica. O navegador só acelera o gesto; nunca é fonte de verdade financeira.

## Operating Context

Uso principal em desktop/notebook no balcão. Login por grupo redireciona: Caixa para PDV, Gerente e Administrador para Dashboard. Fluxo típico: busca → categoria/produto → quantidade → pagamento → finalizar. Depois da venda, pedido limpa e próxima venda começa na mesma tela. Estoque baixa na finalização e volta no cancelamento com motivo obrigatório.

## Capabilities and Constraints

- Idioma da interface: pt-BR. Moeda: R$ 12,50. Data: dd/mm/aaaa. Data/hora: dd/mm/aaaa HH:mm.
- Roles: Administrador, Gerente, Caixa via Django Groups e Permissions. Views protegidas no backend.
- Pagamentos MVP: DINHEIRO, PIX, DEBITO, CREDITO. Sem maquininha/gateway real.
- Um pagamento por venda no MVP; modelo não impede split futuro.
- Dinheiro exige valor recebido ≥ total e mostra troco. Outros métodos não pedem troco.
- Dinheiro no backend: Decimal. Estoque concorrente: transaction.atomic + select_for_update.
- Produtos com histórico não são apagados; desativação.
- Desconto só se autorizado (Administrador/Gerente).
- [Inferido] Sem requisito de acessibilidade específico além de HTML semântico e alvos grandes no PDV.
- [Inferido] Sem marca visual vinculante além do nome Pastel da TATI e interface pt-BR.

## Brand Commitments

- Nome: **Pastel da TATI**.
- Voz operacional, direta, sem hype.
- Dados DEMO devem ser claramente fictícios. Não inventar cardápio real da pastelaria.

## Evidence on Hand

Nenhum logo, foto, depoimento, preço real ou cardápio oficial no repositório. Dados de demonstração, se existirem, são sintéticos e rotulados.

## Product Principles

- Velocidade do caixa sem ceder a verdade financeira ao JavaScript.
- Permissão no servidor, não só no menu.
- Auditoria: snapshot de nome/preço, movimentação de estoque, cancelamento sem apagar.
- Interface some no gesto do balcão: busca em foco, total visível, erro objetivo.
- Demo nunca se passa por produto real da TATI.

## Accessibility & Inclusion

Alvos de clique grandes no PDV, contraste legível, teclado na busca. Sem padrão formal (WCAG nível) confirmado.
