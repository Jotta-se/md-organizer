#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║              MD ORGANIZER  —  qwen3:14b via Ollama           ║
║  Classifica e organiza arquivos .md por análise semântica    ║
╚══════════════════════════════════════════════════════════════╝

Uso:
    python md_organizer.py
    python md_organizer.py --dry-run          # Simula sem copiar
    python md_organizer.py --limit 50         # Processa primeiros N arquivos
    python md_organizer.py --source Y:\\       # Sobrescreve origem

Dependências:
    pip install ollama
"""

import os
import sys
import json
import shutil
import argparse
import re
import unicodedata
from pathlib import Path
from datetime import datetime
from typing import Optional

# ── Tentativa de importar ollama ──────────────────────────────────────────────
try:
    import ollama
except ImportError:
    print("[ERRO] Biblioteca 'ollama' não encontrada.")
    print("       Instale com: pip install ollama")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════════════════════
SOURCE_DRIVE   = Path(r"X:\\")
DEST_BASE      = Path(r"C:\Users\Jotta\Documents\Acervos\Acervo Markdown")
REPORT_FILE    = DEST_BASE / "_relatorio.md"
MODEL          = "qwen3:14b"
TARGET_EXTENSIONS = [".md"]

MIN_FILE_BYTES         = 10
MIN_WORDS_CLASSIFY     = 100
MAX_WORDS_ANALYSIS     = 5_000
PENDING_CATEGORY       = "_Classificação Pendente"

# Categorias conhecidas para normalização de sinônimos comuns
CATEGORY_SYNONYMS: dict[str, str] = {
    "ia":                           "Inteligência Artificial",
    "inteligencia artificial":      "Inteligência Artificial",
    "ai":                           "Inteligência Artificial",
    "ml":                           "Machine Learning",
    "aprendizado de maquina":       "Machine Learning",
    "aprendizado de máquina":       "Machine Learning",
    "dl":                           "Deep Learning",
    "aprendizado profundo":         "Deep Learning",
    "data engineering":             "Engenharia de Dados",
    "engenharia de dados":          "Engenharia de Dados",
    "software architecture":        "Arquitetura de Software",
    "arquitetura de software":      "Arquitetura de Software",
    "agile":                        "Metodologia Ágil",
    "scrum":                        "Metodologia Ágil",
    "statistics":                   "Estatística",
    "estatistica":                  "Estatística",
    "product management":           "Product Management",
    "gestao de produto":            "Product Management",
    "gestão de produto":            "Product Management",
    "security":                     "Segurança",
    "seguranca":                    "Segurança",
    "databases":                    "Banco de Dados",
    "banco de dados":               "Banco de Dados",
    "networking":                   "Redes",
    "programming":                  "Programação",
    "programacao":                  "Programação",
    "knowledge management":         "Gestão do Conhecimento",
    "gestao do conhecimento":       "Gestão do Conhecimento",
    "devops":                       "DevOps",
    "data science":                 "Ciência de Dados",
    "ciencia de dados":             "Ciência de Dados",
}

BLOCKED_CATEGORIES = {"outros", "misc", "geral", "other", "miscellaneous", "general", "various"}

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITÁRIOS
# ═══════════════════════════════════════════════════════════════════════════════

def strip_accents_lower(text: str) -> str:
    """Remove acentos e retorna em minúsculas (para comparação)."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text.lower())
        if unicodedata.category(c) != 'Mn'
    )

def sanitize_dirname(name: str) -> str:
    """Remove caracteres inválidos para nomes de diretório no Windows."""
    invalid = r'<>:"/\\|?*'
    for ch in invalid:
        name = name.replace(ch, '')
    return name.strip('. ')

def normalize_category(raw: str) -> str:
    """
    Normaliza uma categoria:
    1. Checa se é bloqueada (genérica)
    2. Resolve sinônimos conhecidos
    3. Sanitiza para uso como nome de diretório
    """
    raw = raw.strip()
    key = strip_accents_lower(raw)

    if key in BLOCKED_CATEGORIES:
        return PENDING_CATEGORY

    if key in CATEGORY_SYNONYMS:
        return CATEGORY_SYNONYMS[key]

    return sanitize_dirname(raw)

def resolve_existing_categories(dest_base: Path) -> dict[str, str]:
    """
    Mapeia categoria_normalizada → nome_real nos diretórios já existentes.
    Evita criar 'Machine Learning' e 'machine learning' como pastas distintas.
    """
    mapping: dict[str, str] = {}
    if dest_base.exists():
        for item in dest_base.iterdir():
            if item.is_dir():
                mapping[strip_accents_lower(item.name)] = item.name
    return mapping

def resolve_dest_path(
    dest_base: Path,
    categoria: str,
    subcategoria: Optional[str],
    filename: str,
    cat_map: dict[str, str],
) -> Path:
    """
    Calcula o caminho de destino, reutilizando categorias existentes
    e adicionando sufixo incremental em caso de conflito de nome.
    """
    cat_key = strip_accents_lower(categoria)
    if cat_key in cat_map:
        categoria = cat_map[cat_key]
    else:
        cat_map[cat_key] = categoria

    dest_dir = dest_base / categoria
    if subcategoria:
        sub_key = strip_accents_lower(subcategoria)
        # Verifica subcategorias existentes dentro da categoria
        existing_subs = {}
        if dest_dir.exists():
            for item in dest_dir.iterdir():
                if item.is_dir():
                    existing_subs[strip_accents_lower(item.name)] = item.name
        if sub_key in existing_subs:
            subcategoria = existing_subs[sub_key]
        dest_dir = dest_dir / subcategoria

    dest_file = dest_dir / filename
    if dest_file.exists():
        stem   = Path(filename).stem
        suffix = Path(filename).suffix
        counter = 2
        while dest_file.exists():
            dest_file = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1

    return dest_file

def print_section(title: str):
    print(f"\n{'═'*62}")
    print(f"  {title}")
    print(f"{'═'*62}")

def print_summary(label: str, data: dict):
    print(f"\n  ┌─ Resumo ──────────────────────────────────────")
    for k, v in data.items():
        print(f"  │  {k:<30} {v}")
    print(f"  └──────────────────────────────────────────────\n")

# ═══════════════════════════════════════════════════════════════════════════════
# ETAPA 1 — INVENTÁRIO
# ═══════════════════════════════════════════════════════════════════════════════

def etapa1_inventario(source: Path, extensions: list[str]) -> list[dict]:
    print_section("ETAPA 1 — INVENTÁRIO")
    print(f"  Percorrendo recursivamente: {source}")
    print(f"  Aguarde...\n")

    all_files: list[dict] = []
    inaccessible = 0

    for root, dirs, filenames in os.walk(source, onerror=lambda e: None):
        for fn in filenames:
            ext = Path(fn).suffix.lower()
            if "todos" not in extensions and ext not in extensions:
                continue
            fp = Path(root) / fn
            try:
                size = fp.stat().st_size
                all_files.append({"path": fp, "name": fn, "size": size})
            except (PermissionError, OSError):
                inaccessible += 1

    valid   = [f for f in all_files if f["size"] >= MIN_FILE_BYTES]
    ignored = len(all_files) - len(valid)

    print_summary("Etapa 1 concluída", {
        "Arquivos válidos encontrados:": len(all_files),
        f"Ignorados (< {MIN_FILE_BYTES} bytes):": ignored,
        "Inacessíveis (sem permissão):": inaccessible,
        "Válidos para processamento:":   len(valid),
    })

    return valid

# ═══════════════════════════════════════════════════════════════════════════════
# ETAPA 2 — ANÁLISE SEMÂNTICA
# ═══════════════════════════════════════════════════════════════════════════════

CLASSIFICATION_PROMPT = """\
Você é um classificador semântico de documentos técnicos. Analise o conteúdo textual abaixo e retorne APENAS um objeto JSON — sem texto extra, sem blocos de código, sem explicações.

Arquivo: {filename}

Conteúdo:
---
{content}
---

Regras:
- "categoria": string em português, singular, nomenclatura técnica precisa
- "subcategoria": string ou null (use apenas quando agrega clareza real)
- "justificativa": uma frase curta explicando a escolha
- Categorias válidas (não se limite a esta lista): "Inteligência Artificial", "Machine Learning", "Deep Learning", "Engenharia de Dados", "Arquitetura de Software", "Metodologia Ágil", "Estatística", "Product Management", "Segurança", "DevOps", "Banco de Dados", "Redes", "Programação", "Gestão do Conhecimento", "Ciência de Dados"
- Crie novas categorias se necessário — não force encaixe inadequado
- NUNCA use: "Outros", "Misc", "Geral", "Other", "General"

Responda SOMENTE com JSON válido:
{{"categoria": "...", "subcategoria": "..." ou null, "justificativa": "..."}}\
"""

def call_ollama(client: ollama.Client, content: str, filename: str) -> dict:
    """Chama o modelo qwen3:14b e retorna a classificação como dicionário."""
    prompt = CLASSIFICATION_PROMPT.format(filename=filename, content=content)

    try:
        # think=False desativa o modo de raciocínio do qwen3 (mais rápido)
        response = client.chat(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            options={"temperature": 0.05, "num_predict": 256},
            think=False,
        )
        raw = response.message.content.strip()

    except TypeError:
        # Versão antiga do ollama sem suporte a think=
        response = client.chat(
            model=MODEL,
            messages=[{"role": "user", "content": "/no_think\n" + prompt}],
            options={"temperature": 0.05, "num_predict": 256},
        )
        raw = response.message.content.strip()

    # Remove blocos de código se o modelo os inserir mesmo assim
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    # Extrai o primeiro objeto JSON encontrado
    match = re.search(r'\{.*?\}', raw, re.DOTALL)
    if match:
        raw = match.group(0)

    result = json.loads(raw)
    return {
        "categoria":    normalize_category(result.get("categoria", PENDING_CATEGORY)),
        "subcategoria": sanitize_dirname(result["subcategoria"]) if result.get("subcategoria") else None,
        "justificativa": result.get("justificativa", ""),
    }

def etapa2_analise(files: list[dict]) -> list[dict]:
    print_section("ETAPA 2 — ANÁLISE SEMÂNTICA")
    print(f"  Modelo  : {MODEL}")
    print(f"  Arquivos: {len(files)}\n")

    client  = ollama.Client()
    total   = len(files)
    results = []
    errors  = 0

    for idx, fi in enumerate(files, 1):
        fp   = fi["path"]
        name = fi["name"]

        # ── Leitura ──────────────────────────────────────────────
        try:
            ext = fp.suffix.lower()
            if ext in [".txt", ".md", ".csv", ".json"]:
                content = fp.read_text(encoding="utf-8", errors="ignore")
            else:
                from markitdown import MarkItDown
                md_converter = MarkItDown()
                result = md_converter.convert(str(fp))
                content = result.text_content
        except Exception as exc:
            fi.update({"categoria": PENDING_CATEGORY, "subcategoria": None,
                        "justificativa": f"Erro na extração de texto: {exc}"})
            print(f"  [{idx:>5}/{total}] ERRO extraindo texto de: {name}")
            results.append(fi)
            errors += 1
            continue

        words = content.split()
        wc    = len(words)

        # ── Conteúdo insuficiente ─────────────────────────────────
        if wc < MIN_WORDS_CLASSIFY:
            fi.update({"categoria": PENDING_CATEGORY, "subcategoria": None,
                        "justificativa": f"Conteúdo insuficiente ({wc} palavras)"})
            print(f"  [{idx:>5}/{total}] {name:<45} → {PENDING_CATEGORY}  ({wc} palavras)")
            results.append(fi)
            continue

        # ── Truncagem ─────────────────────────────────────────────
        if wc > MAX_WORDS_ANALYSIS:
            content = " ".join(words[:MAX_WORDS_ANALYSIS])

        # ── Classificação via LLM ─────────────────────────────────
        try:
            clf = call_ollama(client, content, name)
        except json.JSONDecodeError as exc:
            clf = {"categoria": PENDING_CATEGORY, "subcategoria": None,
                   "justificativa": f"JSON inválido retornado pelo modelo: {exc}"}
            errors += 1
        except Exception as exc:
            clf = {"categoria": PENDING_CATEGORY, "subcategoria": None,
                   "justificativa": f"Erro na chamada ao modelo: {exc}"}
            errors += 1

        fi.update(clf)

        cat_display = fi["categoria"]
        if fi["subcategoria"]:
            cat_display += f" / {fi['subcategoria']}"

        print(f"  [{idx:>5}/{total}] {name:<45} → {cat_display}")
        results.append(fi)

    cats     = {f["categoria"] for f in results}
    pending  = sum(1 for f in results if f["categoria"] == PENDING_CATEGORY)

    print_summary("Etapa 2 concluída", {
        "Arquivos analisados:":           total,
        "Categorias distintas:":          len(cats),
        "Em _Classificação Pendente:":    pending,
        "Erros de processamento:":        errors,
    })

    return results

# ═══════════════════════════════════════════════════════════════════════════════
# ETAPA 3 — ORGANIZAÇÃO
# ═══════════════════════════════════════════════════════════════════════════════

def etapa3_organizacao(results: list[dict], dry_run: bool = False) -> list[dict]:
    print_section("ETAPA 3 — ORGANIZAÇÃO")
    print(f"  Destino : {DEST_BASE}")
    print(f"  Modo    : {'DRY-RUN (simulação)' if dry_run else 'CÓPIA REAL'}\n")

    cat_map = resolve_existing_categories(DEST_BASE)
    total   = len(results)
    copied  = 0
    errors  = 0

    for idx, fi in enumerate(results, 1):
        fp         = fi["path"]
        categoria  = fi.get("categoria", PENDING_CATEGORY)
        subcateg   = fi.get("subcategoria")
        filename   = fi["name"]

        dest_file = resolve_dest_path(DEST_BASE, categoria, subcateg, filename, cat_map)
        fi["destino"] = str(dest_file)

        if dry_run:
            print(f"  [DRY] {filename} → {dest_file.relative_to(DEST_BASE)}")
            copied += 1
            continue

        try:
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fp, dest_file)
            copied += 1
        except Exception as exc:
            fi["destino"] = f"ERRO: {exc}"
            print(f"  [ERRO] {filename}: {exc}")
            errors += 1

        if idx % 25 == 0 or idx == total:
            pct = idx / total * 100
            bar = "█" * int(pct // 5) + "░" * (20 - int(pct // 5))
            print(f"  [{bar}] {pct:5.1f}%  ({idx}/{total})", end="\r")

    print()  # quebra de linha após a barra de progresso
    print_summary("Etapa 3 concluída", {
        "Arquivos copiados:":           copied,
        "Erros de cópia:":              errors,
        "Categorias no destino:":       len(cat_map),
    })

    return results

# ═══════════════════════════════════════════════════════════════════════════════
# ETAPA 4 — RELATÓRIO FINAL
# ═══════════════════════════════════════════════════════════════════════════════

def etapa4_relatorio(results: list[dict], cat_map: dict, dry_run: bool):
    print_section("ETAPA 4 — RELATÓRIO FINAL")

    now      = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    total    = len(results)
    pending  = [f for f in results if f.get("categoria") == PENDING_CATEGORY]
    mode_tag = " *(dry-run — nenhum arquivo foi copiado)*" if dry_run else ""

    lines = [
        "# Relatório de Organização — Acervo Markdown",
        "",
        f"| Campo              | Valor |",
        f"|--------------------|-------|",
        f"| **Data e hora**    | {now} |",
        f"| **Modo execução**  | {'Simulação (dry-run)' if dry_run else 'Produção'} |",
        f"| **Origem**         | `{SOURCE_DRIVE}` |",
        f"| **Destino**        | `{DEST_BASE}` |",
        f"| **Modelo LLM**     | `{MODEL}` |",
        f"| **Total arquivos** | {total} |",
        f"| **Categorias**     | {len(cat_map)} |",
        f"| **Pendentes**      | {len(pending)} |",
        "",
        "---",
        "",
        "## Mapeamento Completo",
        "",
        "| # | Arquivo Original | Categoria | Subcategoria | Destino |",
        "|---|-----------------|-----------|--------------|---------|",
    ]

    for i, f in enumerate(results, 1):
        orig_name = f["name"]
        cat       = f.get("categoria", "-")
        sub       = f.get("subcategoria") or "—"
        dest_raw  = f.get("destino", "—")
        dest_disp = (
            dest_raw.replace(str(DEST_BASE) + os.sep, "")
            if not dest_raw.startswith("ERRO") else f"⚠ {dest_raw}"
        )
        lines.append(f"| {i} | `{orig_name}` | {cat} | {sub} | `{dest_disp}` |")

    if pending:
        lines += [
            "",
            "---",
            "",
            "## Arquivos em _Classificação Pendente",
            "",
            "| Arquivo | Justificativa |",
            "|---------|---------------|",
        ]
        for f in pending:
            lines.append(f"| `{f['name']}` | {f.get('justificativa', '—')} |")

    report_content = "\n".join(lines)

    if not dry_run:
        DEST_BASE.mkdir(parents=True, exist_ok=True)
        REPORT_FILE.write_text(report_content, encoding="utf-8")
        print(f"  Relatório salvo em: {REPORT_FILE}")
    else:
        print("  [DRY-RUN] Relatório não foi gravado em disco.")
        print("\n" + "─"*62)
        print(report_content[:800] + "\n  [...]\n")

    print_summary("Execução finalizada", {
        "Arquivos processados:":     total,
        "Categorias criadas:":       len(cat_map),
        "Pendentes:":                len(pending),
        "Relatório:":                str(REPORT_FILE) if not dry_run else "não gravado",
    })

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args():
    parser = argparse.ArgumentParser(
        description="Organiza arquivos .md usando qwen3:14b via Ollama"
    )
    parser.add_argument(
        "--source", type=Path, default=SOURCE_DRIVE,
        help=f"Diretório de origem (padrão: {SOURCE_DRIVE})"
    )
    parser.add_argument(
        "--dest", type=Path, default=DEST_BASE,
        help=f"Diretório de destino (padrão: {DEST_BASE})"
    )
    parser.add_argument(
        "--limit", type=int, default=0,
        help="Limita o número de arquivos processados (0 = sem limite)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simula o processo sem copiar ou criar arquivos"
    )
    return parser.parse_args()



def main():
    args = parse_args()

    print("\n" + "╔" + "═"*60 + "╗")
    print("║{:^60}║".format("MD ORGANIZER  —  Configuração"))
    print("╚" + "═"*60 + "╝\n")

    global SOURCE_DRIVE, DEST_BASE, REPORT_FILE, MODEL, TARGET_EXTENSIONS

    # 1. Extensões
    while True:
        ext_input = input("  [?] Quais formatos de arquivo? (ex: pdf, docx, txt, ou 'todos'): ").strip().lower()
        if not ext_input:
            print("      ⚠ Informe ao menos uma extensão ou digite 'todos'.")
            continue
        
        if ext_input == "todos":
            TARGET_EXTENSIONS = ["todos"]
        else:
            parts = [p.strip() for p in ext_input.replace('.', '').split(",")]
            TARGET_EXTENSIONS = [f".{p}" for p in parts if p]
            if not TARGET_EXTENSIONS:
                print("      ⚠ Formato de entrada inválido.")
                continue
        break

    # 2. Origem
    while True:
        src_input = input("  [?] Diretório de Origem: ").strip()
        if not src_input:
            print("      ⚠ A origem não pode ser vazia.")
            continue
        p_src = Path(src_input)
        if not p_src.exists() or not p_src.is_dir():
            print("      ⚠ Diretório não encontrado ou não é uma pasta válida. Tente novamente.")
            continue
        SOURCE_DRIVE = p_src
        break

    # 2. Destino
    while True:
        dst_input = input("  [?] Diretório de Destino: ").strip()
        if not dst_input:
            print("      ⚠ O destino não pode ser vazio.")
            continue
        p_dst = Path(dst_input)
        if not p_dst.exists():
            print("      ⚠ O diretório de destino não existe.")
            ans = input(f"      Deseja criar '{p_dst}' agora? (s/n): ").strip().lower()
            if ans == 's':
                try:
                    p_dst.mkdir(parents=True, exist_ok=True)
                    print("      ✅ Diretório criado com sucesso.")
                except Exception as e:
                    print(f"      ❌ Erro ao criar diretório: {e}")
                    continue
            else:
                print("      ⚠ Por favor, informe um destino diferente.")
                continue
        elif not p_dst.is_dir():
            print("      ⚠ O caminho existe mas não é uma pasta válida. Tente novamente.")
            continue
        DEST_BASE = p_dst
        break

    # 3. Modelo
    while True:
        mod_input = input("  [?] Modelo Ollama (ex: qwen3:14b): ").strip()
        if not mod_input:
            print("      ⚠ O modelo não pode ser vazio.")
            continue
        
        print(f"      ⏳ Verificando disponibilidade de '{mod_input}' localmente...")
        try:
            import subprocess
            client = ollama.Client()
            models_response = client.list()
            available = [m.model for m in models_response.models]
            
            if not any(m.startswith(mod_input.split(":")[0]) for m in available):
                ans = input(f"      ⚠ Modelo '{mod_input}' não está baixado. Deseja baixar agora? (s/n): ").strip().lower()
                if ans == 's':
                    print(f"      📥 Realizando o download de '{mod_input}'... (Aguarde)")
                    try:
                        subprocess.run(["ollama", "pull", mod_input], check=True)
                        print(f"      ✅ Modelo '{mod_input}' baixado com sucesso.")
                    except subprocess.CalledProcessError as e:
                        print(f"      ❌ Erro ao tentar baixar o modelo. Verifique a conexão. ({e})")
                        continue
                    except FileNotFoundError:
                        print(f"      ❌ Executável 'ollama' não encontrado no PATH.")
                        continue
                else:
                    print("      ⚠ Por favor, informe outro modelo que você já tenha.")
                    continue
            else:
                print(f"      ✅ Modelo '{mod_input}' verificado com sucesso.")
                
        except Exception as exc:
            print(f"      ❌ Erro de comunicação com o Ollama: {exc}")
            ans = input("      O serviço local está em execução? Tentar novamente? (s/n): ").strip().lower()
            if ans != 's':
                print("      ❌ Cancelando operação.")
                sys.exit(1)
            continue

        MODEL = mod_input
        break

    REPORT_FILE = DEST_BASE / "_relatorio.md"

    print("\n" + "─"*62)
    print("  Iniciando com as seguintes configurações:")
    print(f"  Extensões : {', '.join(TARGET_EXTENSIONS)}")
    print(f"  Origem    : {SOURCE_DRIVE}")
    print(f"  Destino   : {DEST_BASE}")
    print(f"  Modelo    : {MODEL}")
    if args.dry_run:
        print("  Modo    : DRY-RUN (nenhum arquivo será copiado)")
    if args.limit:
        print(f"  Limite  : {args.limit} arquivos")

    # ── Pipeline ──────────────────────────────────────────────────────────────
    files = etapa1_inventario(SOURCE_DRIVE, TARGET_EXTENSIONS)

    if not files:
        print("\n  Nenhum arquivo válido encontrado na origem informada. Encerrando.")
        sys.exit(0)

    if args.limit and args.limit < len(files):
        print(f"  Limitando para os primeiros {args.limit} arquivos (de {len(files)} encontrados).")
        files = files[:args.limit]

    results  = etapa2_analise(files)
    results  = etapa3_organizacao(results, dry_run=args.dry_run)
    cat_map  = resolve_existing_categories(DEST_BASE)
    etapa4_relatorio(results, cat_map, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
