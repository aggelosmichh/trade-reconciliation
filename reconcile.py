"""Reconcile client-side vs. company-side trade blotters.

Reads client_trades.csv and company_trades.csv, matches trades by ticket,
classifies each ticket (MATCHED, MISSING_CLIENT, MISSING_COMPANY, or one or
more break types), writes reconciliation_report.csv, and prints a summary.
"""
import csv
import sys
from collections import OrderedDict

CLIENT_FILE = "client_trades.csv"
COMPANY_FILE = "company_trades.csv"
REPORT_FILE = "reconciliation_report.csv"

# Tolerances beyond which a field difference is considered a break.
VOLUME_TOLERANCE = 0.001
PRICE_TOLERANCE = 0.0010
PROFIT_TOLERANCE = 10.00

REPORT_FIELDNAMES = [
    "ticket", "symbol", "status",
    "client_volume", "company_volume",
    "client_open_price", "company_open_price",
    "client_profit", "company_profit",
    "notes",
]


def load_trades(path):
    """Load a trades CSV into a dict keyed by integer ticket number."""
    trades = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ticket = int(row["ticket"])
            trades[ticket] = {
                "ticket": ticket,
                "symbol": row["symbol"],
                "volume": float(row["volume"]),
                "open_time": row["open_time"],
                "close_time": row["close_time"],
                "open_price": float(row["open_price"]),
                "close_price": float(row["close_price"]),
                "profit": float(row["profit"]),
            }
    return trades


def classify_matched_trade(client, company):
    """Compare a trade present on both sides and return (status, notes)."""
    breaks = []
    notes = []

    volume_diff = abs(client["volume"] - company["volume"])
    if volume_diff > VOLUME_TOLERANCE:
        breaks.append("VOLUME_BREAK")
        notes.append(f"volume diff {volume_diff:.2f}")

    price_diff = abs(client["open_price"] - company["open_price"])
    if price_diff > PRICE_TOLERANCE:
        breaks.append("PRICE_BREAK")
        notes.append(f"open_price diff {price_diff:.4f}")

    profit_diff = abs(client["profit"] - company["profit"])
    if profit_diff > PROFIT_TOLERANCE:
        breaks.append("PROFIT_BREAK")
        notes.append(f"profit diff {profit_diff:.2f}")

    if not breaks:
        return "MATCHED", ""
    return "|".join(breaks), "; ".join(notes)


def reconcile(client_trades, company_trades):
    """Compare both blotters ticket-by-ticket and return report rows."""
    all_tickets = sorted(set(client_trades) | set(company_trades))
    rows = []

    for ticket in all_tickets:
        client = client_trades.get(ticket)
        company = company_trades.get(ticket)

        if client and not company:
            rows.append({
                "ticket": ticket,
                "symbol": client["symbol"],
                "status": "MISSING_COMPANY",
                "client_volume": client["volume"],
                "company_volume": "",
                "client_open_price": client["open_price"],
                "company_open_price": "",
                "client_profit": client["profit"],
                "company_profit": "",
                "notes": "Trade exists on client side only",
            })
        elif company and not client:
            rows.append({
                "ticket": ticket,
                "symbol": company["symbol"],
                "status": "MISSING_CLIENT",
                "client_volume": "",
                "company_volume": company["volume"],
                "client_open_price": "",
                "company_open_price": company["open_price"],
                "client_profit": "",
                "company_profit": company["profit"],
                "notes": "Trade exists on company side only",
            })
        else:
            status, notes = classify_matched_trade(client, company)
            rows.append({
                "ticket": ticket,
                "symbol": client["symbol"],
                "status": status,
                "client_volume": client["volume"],
                "company_volume": company["volume"],
                "client_open_price": client["open_price"],
                "company_open_price": company["open_price"],
                "client_profit": client["profit"],
                "company_profit": company["profit"],
                "notes": notes,
            })

    return rows


def write_report(rows, path):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows):
    total = len(rows)
    matched = sum(1 for r in rows if r["status"] == "MATCHED")
    missing_client = sum(1 for r in rows if r["status"] == "MISSING_CLIENT")
    missing_company = sum(1 for r in rows if r["status"] == "MISSING_COMPANY")

    break_counts = OrderedDict([
        ("VOLUME_BREAK", 0), ("PRICE_BREAK", 0), ("PROFIT_BREAK", 0),
    ])
    breaking_trades = 0
    for r in rows:
        status = r["status"]
        if status in ("MATCHED", "MISSING_CLIENT", "MISSING_COMPANY"):
            continue
        breaking_trades += 1
        for break_type in status.split("|"):
            break_counts[break_type] += 1

    pnl_discrepancy = sum(
        abs(r["client_profit"] - r["company_profit"])
        for r in rows
        if r["client_profit"] != "" and r["company_profit"] != ""
    )

    print("=" * 52)
    print("TRADE RECONCILIATION SUMMARY")
    print("=" * 52)
    print(f"Total trades reviewed:     {total}")
    print(f"Matched:                   {matched}")
    print(f"Breaks:                    {breaking_trades}")
    for break_type, count in break_counts.items():
        print(f"  - {break_type:<20} {count}")
    print(f"Missing client-side:       {missing_client}")
    print(f"Missing company-side:      {missing_company}")
    print(f"Total P&L discrepancy:     €{pnl_discrepancy:,.2f}")
    print("=" * 52)


def main():
    # Ensure the € sign prints correctly even on Windows terminals whose
    # default console codepage isn't UTF-8.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    client_trades = load_trades(CLIENT_FILE)
    company_trades = load_trades(COMPANY_FILE)

    report_rows = reconcile(client_trades, company_trades)
    write_report(report_rows, REPORT_FILE)
    print_summary(report_rows)
    print(f"\nDetailed report written to {REPORT_FILE}")


if __name__ == "__main__":
    main()
