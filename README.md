# Automações em Python

Coleção de automações em Python voltadas a rotinas de dados e produtividade: ETL, qualidade de dados, geração de relatórios, organização de arquivos, backups e coleta via API. Cada script é autocontido, com CLI (`argparse`), logging e tratamento de erros — prontos para uso direto ou agendamento via cron / Task Scheduler.

## Scripts

| Script | O que faz | Exemplo de uso |
|---|---|---|
| `etl_csv_para_sqlite.py` | Pipeline ETL: lê CSV, normaliza colunas para snake_case, limpa espaços, remove duplicatas, adiciona coluna de auditoria e carrega em SQLite com validação de volume | `python etl_csv_para_sqlite.py --input train.csv --db titanic.db --tabela passageiros` |
| `validador_qualidade_dados.py` | Relatório de qualidade (profiling) em Markdown: nulos, duplicatas, colunas constantes, alta cardinalidade e outliers (IQR) | `python validador_qualidade_dados.py --input train.csv --output relatorio.md` |
| `gerador_relatorio_excel.py` | Converte CSV de vendas em relatório .xlsx formatado: KPIs por fórmula, tabelas de apoio e gráficos de barras/linha | `python gerador_relatorio_excel.py --input vendas.csv --output relatorio.xlsx` |
| `organizador_arquivos.py` | Organiza uma pasta em subpastas por categoria de extensão ou por data (AAAA-MM), com modo `--dry-run` e tratamento de colisões | `python organizador_arquivos.py --pasta ~/Downloads --dry-run` |
| `backup_automatico.py` | Backup .zip com timestamp, verificação de integridade (CRC) e rotação dos N mais recentes | `python backup_automatico.py --origem ./projetos --destino ./backups --manter 5` |
| `coletor_github_api.py` | Registra snapshots de métricas de repositórios do GitHub (estrelas, forks, issues...) em CSV histórico para acompanhamento temporal | `python coletor_github_api.py --repos pandas-dev/pandas --saida historico.csv` |

## Instalação

```bash
git clone https://github.com/kagenash/automacoes-python.git
cd automacoes-python
pip install -r requirements.txt
```

Requer Python 3.10+.

## Testes

As funções centrais de ETL e de qualidade de dados possuem testes unitários:

```bash
pytest -v
```

## Exemplos de saída

A pasta [`exemplos/`](exemplos/) contém saídas reais geradas pelos scripts: relatório de qualidade do dataset Titanic (`relatorio_qualidade_titanic.md`), CSV de vendas fictícias (`exemplo_vendas.csv`) e o relatório Excel formatado gerado a partir dele (`relatorio_vendas.xlsx`).

## Estrutura

```
automacoes-python/
├── etl_csv_para_sqlite.py
├── validador_qualidade_dados.py
├── gerador_relatorio_excel.py
├── organizador_arquivos.py
├── backup_automatico.py
├── coletor_github_api.py
├── tests/
│   └── test_automacoes.py
├── exemplos/
├── requirements.txt
└── README.md
```

## Licença

MIT — use, adapte e compartilhe à vontade.
