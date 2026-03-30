# MD Organizer

**MD Organizer** é uma ferramenta de linha de comando (CLI) baseada em Python que utiliza Modelos de Linguagem Grande (LLMs) executando localmente via [Ollama](https://ollama.com/) para analisar semanticamente, classificar e organizar coleções de arquivos Markdown (`.md`).

Em vez de organizar seus arquivos por expressões regulares ou palavras-chave fixas, ele utiliza a "compreensão" de contexto do modelo `qwen3:14b` (ou qualquer outro modelo local que você preferir) para agrupar logicamente os arquivos dentro de subpastas estruturadas (Inteligência Artificial, Engenharia de Dados, etc).

## ✨ Funcionalidades

- **Inferência Semântica Local:** OLLAMA executa 100% offline. Zero dados evadidos para APIs externas, mantendo seus documentos privados seguros.
- **Menu Interativo e Amigável:** O script guia você passo a passo na escolha de Origem, Destino e Modelo de IA, com validação anti-erros.
- **Gerenciamento Automático:** Ele checa se o seu modelo (`qwen3:14b`) existe e se propõe a baixar e exibir a barra de progresso caso não o tenha instalado. Cria pastas automaticamente caso não existam.
- **Modo de Ensaio (Dry-Run):** Teste toda a categorização antes de mover os arquivos fisicamente usando a flag `--dry-run`.
- **Geração de Relatório Final:** Ao final de tudo, gera um `_relatorio.md` na pasta destino mapeando o caminho de cada arquivo perfeitamente organizado.

## 📦 Requisitos

Você precisará apenas de:
1. **[Ollama](https://ollama.com/download)**: Baixe e instale a versão para o seu sistema operacional. Certifique-se de que o aplicativo Ollama está em execução (como serviço).
2. **[uv](https://docs.astral.sh/uv/)**: Usado para gerenciamento ultrarrápido do projeto em Python.
3. **Python >= 3.12**.

## 🚀 Instalação e Execução

### 1. Clonar o Repositório
```bash
git clone https://github.com/Jotta-se/md-organizer.git
cd md-organizer
```

### 2. Executar o Organizador
A maravilha de usar o `uv` é que você nem sequer precisa criar os ambientes virtuais (venv) manualmente ou usar `pip install`. Para instalar todas as dependências isoladamente e rodar o script no seu terminal, basta usar:

```bash
uv run md_organizer.py
```
*O `uv` vai ler o `pyproject.toml`, instalar a biblioteca oficial do Ollama e carregar a linda interface no seu terminal!*

### Parâmetros Extras
Você pode pular as perguntas do prompt ou configurar opções extras via linha de comando:
- `--source "X:\Meus Textos"` força a origem.
- `--dest "C:\Docs"` força o destino final.
- `--limit 10` analisa e copia apenas 10 arquivos (útil para testes de velocidade).
- `--dry-run` faz a análise semântica mas não gera as novas pastas nem move os documentos físicos.

## 🤝 Contribuindo
Sinta-se livre para reportar issues, solicitar novas categorias genéricas para a engine no código ou abrir Pull Requests de melhorias. Veja o [CONTRIBUTING.md](CONTRIBUTING.md) para detalhes.

## 📜 Licença
Este projeto encontra-se sobre a [Licença MIT](LICENSE). Faça o que desejar.
