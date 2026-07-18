#!/usr/bin/env python3
"""
Backup Automático
=================
Compacta uma pasta em um .zip com carimbo de data/hora, verifica a
integridade do arquivo gerado e aplica rotação (mantém apenas os N backups
mais recentes). Pensado para rodar via agendador (cron / Task Scheduler).

Uso:
    python backup_automatico.py --origem ./projetos --destino ./backups --manter 5

Exemplo de agendamento (cron, todo dia às 02h):
    0 2 * * * /usr/bin/python3 /caminho/backup_automatico.py --origem ~/projetos --destino ~/backups --manter 7
"""

import argparse
import logging
import sys
import zipfile
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("backup.log", encoding="utf-8")],
)
log = logging.getLogger(__name__)


def criar_backup(origem: Path, destino: Path, prefixo: str) -> Path:
    """Compacta a pasta de origem em um zip com timestamp no nome."""
    destino.mkdir(parents=True, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    caminho_zip = destino / f"{prefixo}_{carimbo}.zip"

    arquivos = [p for p in origem.rglob("*") if p.is_file()]
    with zipfile.ZipFile(caminho_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arquivo in arquivos:
            zf.write(arquivo, arquivo.relative_to(origem))

    tamanho_mb = caminho_zip.stat().st_size / 1024**2
    log.info("Backup criado: %s (%d arquivo(s), %.2f MB)", caminho_zip.name, len(arquivos), tamanho_mb)
    return caminho_zip


def verificar_integridade(caminho_zip: Path) -> bool:
    """Testa o CRC de todos os membros do zip; retorna True se íntegro."""
    with zipfile.ZipFile(caminho_zip) as zf:
        corrompido = zf.testzip()
    if corrompido is None:
        log.info("Integridade verificada: OK")
        return True
    log.error("Arquivo corrompido dentro do backup: %s", corrompido)
    return False


def aplicar_rotacao(destino: Path, prefixo: str, manter: int) -> None:
    """Remove os backups mais antigos, mantendo apenas os `manter` mais recentes."""
    backups = sorted(destino.glob(f"{prefixo}_*.zip"))  # timestamp no nome garante ordem cronológica
    excedentes = backups[:-manter] if manter > 0 else []
    for antigo in excedentes:
        antigo.unlink()
        log.info("Rotação: removido backup antigo %s", antigo.name)
    log.info("Rotação concluída: %d backup(s) mantido(s)", min(len(backups), manter))


def main() -> None:
    parser = argparse.ArgumentParser(description="Backup .zip com verificação de integridade e rotação.")
    parser.add_argument("--origem", required=True, type=Path, help="Pasta a ser copiada")
    parser.add_argument("--destino", required=True, type=Path, help="Pasta onde os .zip serão gravados")
    parser.add_argument("--manter", type=int, default=5, help="Quantidade de backups a manter (padrão: 5)")
    parser.add_argument("--prefixo", default="backup", help="Prefixo do nome do arquivo (padrão: backup)")
    args = parser.parse_args()

    origem = args.origem.expanduser().resolve()
    destino = args.destino.expanduser().resolve()

    if not origem.is_dir():
        log.error("Pasta de origem não encontrada: %s", origem)
        sys.exit(1)
    if destino == origem or destino.is_relative_to(origem):
        log.error("A pasta de destino não pode estar dentro da origem (backup recursivo).")
        sys.exit(1)

    try:
        caminho_zip = criar_backup(origem, destino, args.prefixo)
        if not verificar_integridade(caminho_zip):
            sys.exit(1)
        aplicar_rotacao(destino, args.prefixo, args.manter)
    except Exception as exc:  # noqa: BLE001 - borda do CLI: loga e sai com erro
        log.exception("Falha no backup: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
