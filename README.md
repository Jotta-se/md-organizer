# Semantic File Organizer (ex-MD Organizer)

O **Semantic File Organizer** é uma ferramenta de linha de comando (CLI) baseada em Python que utiliza Modelos de Linguagem Grande (LLMs) executando localmente via [Ollama](https://ollama.com/) para analisar semanticamente, classificar e organizar coleções multimídia de **qualquer tipo de arquivo** (PDF, DOCX, XLSX, PPTX, TXT, CSV, MD, etc.).

Apoiando-se na nova biblioteca **[MarkItDown](https://github.com/microsoft/markitdown)** da Microsoft, o script converte em tempo-real diversos formatos binários complexos para `markdown`. Em vez de organizar seus arquivos por extensões fixas, ele utiliza a "compreensão" de contexto do modelo `qwen3:14b` para agrupar logicamente os seus arquivos originais (sem corrompê-los) em subpastas estruturadas baseadas puramente no assunto (Inteligência Artificial, Engenharia de Dados, Finanças, etc).

## ✨ Funcionalidades

- **Suporte Universal:** Digite "pdf, docx" ou "todos" no terminal. A API lida com slides, planilhas e relatórios pdf magicamente enquanto preserva o seu arquivo real.
- **Inferência Semântica Local:** OLLAMA executa 100% offline. Zero vazamentos para APIs de nuvem! Seus documentos privados e planilhas confidenciais nunca saem da sua máquina.
- **Menu Interativo Blindado:** O script guia você passo a passo na escolha de Tipos de Arquivo, Origem, Destino e Modelo da IA, com tratamento nativo contra erros humanos de digitação.
- **Gerenciamento Automático de LLM:** Detecta se o seu modelo existe. Traz e configura os downloads pesados de IA via terminal automaticamente.
- **Modo de Simulação:** Avalie as decisões da inteligência artificial numa bateria inteira de PDFs rodando de forma inofensiva via flag `--dry-run`.
- **Relatório de Organização:** Produz o `_relatorio.md` perfeito detalhando os de-paras.

## 📦 Requisitos

1. **[Ollama](https://ollama.com/download)**: Baixe e deixe em execução local.
2. **[uv](https://docs.astral.sh/uv/)**: Usado para o gerenciamento nativo do projeto (substituindo o antigo pip).
3. **Python >= 3.12**.

## 🚀 Instalação e Execução

### 1. Preparar o Repositório
```bash
git clone https://github.com/Jotta-se/md-organizer.git
cd md-organizer
```

### 2. Rodar a Mágica
Graças ao _uv_, as instalações pesadas de IA, Ollama, e o motor da Microsoft (markitdown) virão silenciosa e automaticamente ao seu ambiente virtual sem encher seu PC base de lixo. No terminal, apenas execute:

```bash
uv run md_organizer.py
```

### Parâmetros Extras (CLI Defaults)
Você pode pular as perguntas da interface preenchendo as caixas direto no comando:
- `--source "X:\Acervo"`
- `--dest "C:\Final"`
- `--limit 10` analisa apenas os primeiros `N` arquivos.
- `--dry-run` apenas simula as previsões.

## 🤝 Contribuindo
Abra um pull request ou issue a qualquer momento detalhando no [CONTRIBUTING.md](CONTRIBUTING.md).

## 📜 Licença
As ferramentas deste diretório adotam a [Licença MIT](LICENSE). Mude, adapte e fature em cima sem impeditivos.
