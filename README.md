# Trade Reconciliation Tool

A small Python tool that compares a client-side trade blotter against a
company-side trade blotter, matches trades by ticket number, and flags any
discrepancies between the two.

Only the Python standard library is used — no extra dependencies to install.

## What it does

1. **`generate_mock_data.py`** creates two sample CSVs representing 50
   forex trades as seen by two different systems:
   - `client_trades.csv`
   - `company_trades.csv`

   The two files describe the same underlying trades but contain 5
   intentional discrepancies, so the reconciliation script has real breaks
   to detect.

2. **`reconcile.py`** reads both CSVs, matches records by `ticket`, and
   classifies every ticket into one of the statuses below. It writes a
   detailed `reconciliation_report.csv` and prints a summary to the
   terminal.

## Break types

| Status             | Meaning                                                              |
|---------------------|-----------------------------------------------------------------------|
| `MATCHED`           | All compared fields agree within tolerance.                          |
| `MISSING_CLIENT`    | Ticket exists in the company file but not in the client file.        |
| `MISSING_COMPANY`   | Ticket exists in the client file but not in the company file.        |
| `VOLUME_BREAK`      | `volume` differs by more than `0.001`.                                |
| `PRICE_BREAK`       | `open_price` differs by more than `0.0010`.                           |
| `PROFIT_BREAK`      | `profit` differs by more than `10.00`.                                |

A single ticket can trigger more than one break at once — these are
combined with a pipe, e.g. `PRICE_BREAK|PROFIT_BREAK`.

## How to run

```bash
python generate_mock_data.py
python reconcile.py
```

This produces:
- `client_trades.csv` / `company_trades.csv` — the mock input data
- `reconciliation_report.csv` — per-ticket reconciliation results
- A summary table printed to the terminal, e.g.:

```
====================================================
TRADE RECONCILIATION SUMMARY
====================================================
Total trades reviewed:     50
Matched:                   46
Breaks:                    3
  - VOLUME_BREAK           1
  - PRICE_BREAK            1
  - PROFIT_BREAK           1
Missing client-side:       1
Missing company-side:      1
Total P&L discrepancy:     €47.50
====================================================
```

## Report columns

`reconciliation_report.csv` contains one row per ticket (the union of both
files) with these columns:

`ticket, symbol, status, client_volume, company_volume, client_open_price,
company_open_price, client_profit, company_profit, notes`

Fields are left blank where a trade is missing from one side.
