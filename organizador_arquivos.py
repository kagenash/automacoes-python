#!/usr/bin/env python3
"""
Organizador de Arquivos
=======================
Organiza os arquivos de uma pasta movendo-os para subpastas por categoria
(com base na extensão) ou por data de modificação (AAAA-MM). Possui modo
``--dry-run`` para visualizar o plano sem mover nada e tratamento de
colisão de nomes.

Uso:
    python organizador_arquivos.py --pasta ~/Downloads --dry-run
    python organizador_arquivos.py --pasta ~/Downloads --modo extensao
    python organizador_arquivos.py --pasta ~/Downloads --modo data
"""

import argparse
import shutil
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

CATEGORIAS = {
    "Imagens": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"},
    "Documentos": {".pdf", ".doc", ".docx", ".txt", ".md", ".odt", ".rtf"},
    "Planilhas": {".xls", ".xlsx", ".csv", ".ods"},
    "Apresentações": {".ppt", ".pptx", ".odp"},
    "Vídeos": {".mp4", ".mkv", ".avi", ".mov", ".webm"},
    "Áudio": {".mp3", ".wav", ".flac", ".ogg", ".m4a"},
    "Compactados": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Código": {".py", ".sql", ".js", ".sh", ".ps1", ".ipynb", ".json", ".yml", ".yaml"},
    "Executáveis": {".exe", ".msi", ".deb", ".appimage"},
}


def categoria_de(arquivo: Path) -> str:
    """Retorna a categoria do arquivo com base na extensão."""
    ext = arquivo.suffix.lower()
    for categoria, extensoes in CATEGORIAS.items():
        if ext in extensoes:
            return categoria
    return "Outros"


def destino_para(arquivo: Path, base: Path, modo: str) -> Path:
    """Calcula a subpasta de destino conforme o modo escolhido."""
    if modo == "extensao":
        subpasta = categoria_de(arquivo)
    else:  # data
        modificado = datetime.fromtimestamp(arquivo.stat().st_mtime)
        subpasta = modificado.strftime("%Y-%m")
    return base / subpasta / arquivo.name


def resolver_colisao(destino: Path) -> Path:
    """Se o destino já existir, acrescenta sufixo incremental: arquivo_1.ext, arquivo_2.ext..."""
    if not destino.exists():
        return destino
    contador = 1
    while True:
        candidato = destino.with_name(f"{destino.stem}_{contador}{destino.suffix}")
        if not candidato.exists():
            return candidato
        contador += 1


def organizar(pasta: Path, modo: str, dry_run: bool) -> Counter:
    """Move os arquivos da pasta (não recursivo) e retorna o resumo por subpasta."""
    resumo: Counter = Counter()
    proprio = Path(__file__).resolve()

    for arquivo in sorted(pasta.iterdir()):
        if not arquivo.is_file() or arquivo.resolve() == proprio:
            continue
        destino = resolver_colisao(destino_para(arquivo, pasta, modo))
        resumo[destino.parent.name] += 1

        if dry_run:
            print(f"[PLANO] {arquivo.name}  ->  {destino.parent.name}/{destino.name}")
        else:
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(arquivo), str(destino))
            print(f"[MOVIDO] {arquivo.name}  ->  {destino.parent.name}/")

    return resumo


def main() -> None:
    parser = argparse.ArgumentParser(description="Organiza arquivos em subpastas por categoria ou data.")
    parser.add_argument("--pasta", required=True, type=Path, help="Pasta a organizar")
    parser.add_argument("--modo", choices=["extensao", "data"], default="extensao",
                        help="Critério de organização (padrão: extensao)")
    parser.add_argument("--dry-run", action="store_true", help="Só exibe o plano, sem mover arquivos")
    args = parser.parse_args()

    pasta = args.pasta.expanduser()
    if not pasta.is_dir():
        print(f"[ERRO] Pasta não encontrada: {pasta}", file=sys.stderr)
        sys.exit(1)

    resumo = organizar(pasta, args.modo, args.dry_run)
    total = sum(resumo.values())
    verbo = "seriam movidos" if args.dry_run else "movidos"
    print(f"\n{total} arquivo(s) {verbo}:")
    for subpasta, qtd in resumo.most_common():
        print(f"  {subpasta}: {qtd}")


if __name__ == "__main__":
    main()
