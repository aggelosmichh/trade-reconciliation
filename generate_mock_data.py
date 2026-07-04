"""Generate mock client-side and company-side forex trade blotters.

Produces two CSVs (client_trades.csv, company_trades.csv) that represent the
same 50 underlying trades as seen by two different systems, with exactly five
intentional discrepancies ("breaks") injected between them so that
reconcile.py has something realistic to detect.
"""
import csv
import random
from datetime import datetime, timedelta

RANDOM_SEED = 42
NUM_TRADES = 50
FIRST_TICKET = 1_000_001

FIELDNAMES = [
    "ticket", "symbol", "volume", "open_time", "close_time",
    "open_price", "close_price", "profit",
]

SYMBOLS = ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "GBPJPY"]

# Realistic price bands per symbol: (min_price, max_price, decimal_places)
PRICE_RANGES = {
    "EURUSD": (1.0500, 1.1500, 5),
    "GBPUSD": (1.2000, 1.3500, 5),
    "USDJPY": (140.00, 155.00, 3),
    "XAUUSD": (1900.00, 2400.00, 2),
    "GBPJPY": (180.00, 200.00, 3),
}

# Tickets used for the 5 intentional reconciliation breaks.
TICKET_MISSING_ON_COMPANY = 1_000_005
TICKET_VOLUME_BREAK = 1_000_012
TICKET_PRICE_BREAK = 1_000_023
TICKET_PROFIT_BREAK = 1_000_031
TICKET_MISSING_ON_CLIENT = 1_000_044


def random_open_time():
    """Return a random datetime within the last 30 days."""
    now = datetime.now()
    seconds_ago = random.randint(0, 30 * 24 * 3600)
    return now - timedelta(seconds=seconds_ago)


def generate_trade(ticket):
    """Build one synthetic forex trade with realistic-looking values."""
    symbol = random.choice(SYMBOLS)
    min_price, max_price, decimals = PRICE_RANGES[symbol]

    volume = round(random.uniform(0.01, 2.00), 2)

    open_time = random_open_time()
    close_time = open_time + timedelta(minutes=random.randint(1, 2880))  # up to 2 days

    open_price = round(random.uniform(min_price, max_price), decimals)
    # Small realistic price move between open and close (+/- 0.5%).
    close_price = round(open_price * (1 + random.uniform(-0.005, 0.005)), decimals)

    profit = round((close_price - open_price) * volume * 100_000, 2)

    return {
        "ticket": ticket,
        "symbol": symbol,
        "volume": volume,
        "open_time": open_time.strftime("%Y-%m-%d %H:%M:%S"),
        "close_time": close_time.strftime("%Y-%m-%d %H:%M:%S"),
        "open_price": open_price,
        "close_price": close_price,
        "profit": profit,
    }


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main():
    random.seed(RANDOM_SEED)

    # Generate the 50 "source of truth" trades, keyed by ticket.
    client_by_ticket = {
        FIRST_TICKET + i: generate_trade(FIRST_TICKET + i) for i in range(NUM_TRADES)
    }
    # Company side starts as an exact copy (independent dicts) of the client side.
    company_by_ticket = {ticket: dict(trade) for ticket, trade in client_by_ticket.items()}

    # --- Inject the 5 intentional breaks ---

    # 1. Ticket 1000005 missing entirely from the company side.
    del company_by_ticket[TICKET_MISSING_ON_COMPANY]

    # 2. Ticket 1000012: client volume 0.50 vs company volume 1.00.
    client_by_ticket[TICKET_VOLUME_BREAK]["volume"] = 0.50
    company_by_ticket[TICKET_VOLUME_BREAK]["volume"] = 1.00

    # 3. Ticket 1000023: company open_price differs from client by exactly 0.0015.
    client_price = client_by_ticket[TICKET_PRICE_BREAK]["open_price"]
    company_by_ticket[TICKET_PRICE_BREAK]["open_price"] = round(client_price + 0.0015, 4)

    # 4. Ticket 1000031: company profit differs from client by exactly 47.50.
    client_profit = client_by_ticket[TICKET_PROFIT_BREAK]["profit"]
    company_by_ticket[TICKET_PROFIT_BREAK]["profit"] = round(client_profit + 47.50, 2)

    # 5. Ticket 1000044 missing entirely from the client side (company-only trade).
    del client_by_ticket[TICKET_MISSING_ON_CLIENT]

    client_rows = [client_by_ticket[t] for t in sorted(client_by_ticket)]
    company_rows = [company_by_ticket[t] for t in sorted(company_by_ticket)]

    write_csv("client_trades.csv", client_rows)
    write_csv("company_trades.csv", company_rows)

    print(f"Generated {len(client_rows)} rows -> client_trades.csv")
    print(f"Generated {len(company_rows)} rows -> company_trades.csv")
    print("Injected breaks on tickets:", TICKET_MISSING_ON_COMPANY, TICKET_VOLUME_BREAK,
          TICKET_PRICE_BREAK, TICKET_PROFIT_BREAK, TICKET_MISSING_ON_CLIENT)


if __name__ == "__main__":
    main()
