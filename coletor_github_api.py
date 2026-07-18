#!/usr/bin/env python3
"""
Coletor de Métricas — API do GitHub
===================================
Consome a API pública do GitHub e registra um snapshot das métricas de cada
repositório (estrelas, forks, issues abertas, watchers, tamanho, último push)
em um CSV histórico — cada execução acrescenta novas linhas com timestamp,
permitindo acompanhar a evolução ao longo do tempo.

Uso:
    python coletor_github_api.py --repos pandas-dev/pandas,microsoft/vscode --saida historico_github.csv
    python coletor_github_api.py --usuario kagenash --saida historico_github.csv

Observações:
- Sem autenticação, a API limita a 60 requisições/hora por IP.
- Para limites maiores, exporte um token: GITHUB_TOKEN=ghp_xxx (opcional).
"""

import argparse
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

API = "https://api.github.com"
CAMPOS = ["coleta_em", "repo", "estrelas", "forks", "issues_abertas", "watchers", "tamanho_kb", "ultimo_push"]


def _sessao() -> requests.Session:
    sessao = requests.Session()
    sessao.headers.update({
        "Accept": "application/vnd.github+json",
        "User-Agent": "coletor-github-metricas",
    })
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        sessao.headers["Authorization"] = f"Bearer {token}"
    return sessao


def listar_repos_do_usuario(sessao: requests.Session, usuario: str) -> list[str]:
    """Lista os repositórios públicos de um usuário (até 100)."""
    resposta = sessao.get(f"{API}/users/{usuario}/repos", params={"per_page": 100}, timeout=15)
    resposta.raise_for_status()
    return [item["full_name"] for item in resposta.json()]


def coletar_repo(sessao: requests.Session, repo: str) -> dict | None:
    """Coleta as métricas de um repositório; retorna None se indisponível."""
    resposta = sessao.get(f"{API}/repos/{repo}", timeout=15)

    if resposta.status_code == 404:
        print(f"[AVISO] Repositório não encontrado: {repo}", file=sys.stderr)
        return None
    if resposta.status_code == 403 and resposta.headers.get("X-RateLimit-Remaining") == "0":
        print("[ERRO] Limite de requisições da API atingido. Tente mais tarde ou use GITHUB_TOKEN.", file=sys.stderr)
        return None
    resposta.raise_for_status()

    dados = resposta.json()
    return {
        "coleta_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "repo": dados["full_name"],
        "estrelas": dados["stargazers_count"],
        "forks": dados["forks_count"],
        "issues_abertas": dados["open_issues_count"],
        "watchers": dados["subscribers_count"],
        "tamanho_kb": dados["size"],
        "ultimo_push": dados["pushed_at"],
    }


def salvar_snapshots(linhas: list[dict], saida: Path) -> None:
    """Acrescenta os snapshots ao CSV, criando o cabeçalho na primeira execução."""
    arquivo_novo = not saida.exists()
    with saida.open("a", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=CAMPOS)
        if arquivo_novo:
            escritor.writeheader()
        escritor.writerows(linhas)


def main() -> None:
    parser = argparse.ArgumentParser(description="Registra snapshots de métricas de repositórios do GitHub em CSV.")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--repos", help="Lista separada por vírgula: dono/repo,dono/repo")
    grupo.add_argument("--usuario", help="Coleta todos os repositórios públicos do usuário")
    parser.add_argument("--saida", type=Path, default=Path("historico_github.csv"), help="CSV histórico de destino")
    args = parser.parse_args()

    sessao = _sessao()
    try:
        if args.repos:
            repos = [r.strip() for r in args.repos.split(",") if r.strip()]
        else:
            repos = listar_repos_do_usuario(sessao, args.usuario)
            print(f"[INFO] {len(repos)} repositório(s) público(s) de {args.usuario}")

        snapshots = [linha for repo in repos if (linha := coletar_repo(sessao, repo))]
    except requests.RequestException as exc:
        print(f"[ERRO] Falha de comunicação com a API: {exc}", file=sys.stderr)
        sys.exit(1)

    if not snapshots:
        print("[AVISO] Nenhuma métrica coletada.", file=sys.stderr)
        sys.exit(1)

    salvar_snapshots(snapshots, args.saida)
    print(f"[OK] {len(snapshots)} snapshot(s) registrado(s) em {args.saida}")
    for s in snapshots:
        print(f"  {s['repo']}: {s['estrelas']} estrelas | {s['forks']} forks | {s['issues_abertas']} issues abertas")


if __name__ == "__main__":
    main()
