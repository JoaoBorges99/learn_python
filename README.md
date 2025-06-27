# Projeto Python - Overview

Este repositório contém diversos projetos e utilitários em Python. Abaixo está um resumo das principais pastas e seus propósitos, com destaque especial para o projeto **graficos_analytics**.

---

## Estrutura de Pastas

- **graficos_analytics/**
  - Projeto principal para geração dinâmica de gráficos a partir de dados tabulares.
  - Utiliza FastAPI para expor endpoints REST.
  - Gera gráficos interativos com Plotly e serve páginas HTML customizadas.
  - Permite upload de dados, escolha de métricas e dimensões, e exportação dos gráficos.
  - Contém:
    - `api_graficos.py`: API principal.
    - `docs/`: Exemplos de dados e documentação.
    - `static/`: Arquivos estáticos e templates HTML.
    - `error_page/`: Página de erro customizada.

- **outros_projetos/**
  - Espaço reservado para outros projetos Python auxiliares ou experimentais.

- **utils/**
  - Scripts utilitários e funções de apoio reutilizáveis.

---

## Destaque: graficos_analytics

O **graficos_analytics** é um microserviço para análise visual de dados, com as seguintes características:

- **API REST**: Endpoints para upload de dados, escolha de gráficos e geração de relatórios.
- **Plotly**: Geração de gráficos interativos (barras, linhas, áreas, funil, scatter).
- **Templates HTML**: Relatórios customizados com múltiplos gráficos.
- **Conversão Automática de Dados**: Interpretação automática de tipos numéricos e dimensionais.
- **Fácil Integração**: Pode ser utilizado como backend para dashboards ou sistemas de BI.

### Como usar

1. Suba o serviço com FastAPI (ex: `uvicorn graficos_analytics.api_graficos:app`).
2. Envie dados via POST para `/graficos` ou `/escolha_grafico`.
3. Receba a URL do relatório gerado com gráficos interativos.

---

## Requisitos

- Python 3.9+
- FastAPI
- Plotly
- Pandas

---

## Observações

- Consulte a pasta `docs/` para exemplos de dados.
- Personalize templates HTML em `static/pagina_template/`.
- Para erros, uma página customizada é servida de `error_page/`.

---

Para dúvidas ou contribuições, abra uma issue ou envie um pull request.
