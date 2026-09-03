"""
Robinhood/GameStop ACID concurrency simulation.

This script models a simplified brokerage buy-order transaction using in-memory
objects that correspond to an ERD for a retail trading platform. It compares two
phases:

1. Unenforced isolation: no lock around the transaction block.
2. Strict isolation: one mutex protects the full read-delay-write transaction.

The goal is not to reproduce Robinhood's production system. The goal is to create
a small experiment that demonstrates the ACID trade-off discussed in Jim Gray's
"The Transaction Concept: Virtues and Limitations": strict isolation protects
entity integrity, while high contention can reduce throughput and increase
latency.
"""
#---------------------------- Imports ------------------------------------------------------------------
from __future__ import annotations

import argparse
import csv
import statistics
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

#--------------      Dataclasses Represent ERD Entities    ----------------------------------------------
# Entities: User, BrokerageAccount, Security, Order, Position, CashLedgerEntry, ClearingObligation, TradingRestriction

@dataclass
class User:
    user_id: str
    full_name: str
    kyc_status: str 

@dataclass
class BrokerageAccount:
    account_id: str
    user_id: str
    account_status: str
    margin_enabled: bool
    available_cash: float


@dataclass
class Security:
    security_id: str
    ticker_symbol: str
    security_name: str
    exchange: str
    trading_status: str = "OPEN"


@dataclass
class Order:
    order_id: str
    account_id: str
    security_id: str
    side: str
    quantity: int
    estimated_price: float
    order_status: str
    created_at: float


@dataclass
class Position:
    position_id: str
    account_id: str
    security_id: str
    share_quantity: int = 0


@dataclass
class CashLedgerEntry:
    ledger_entry_id: str
    account_id: str
    order_id: str
    amount: float
    entry_type: str
    created_at: float


@dataclass
class ClearingObligation:
    obligation_id: str
    order_id: str
    required_deposit: float
    settlement_date: str
    obligation_status: str


@dataclass
class TradingRestriction:
    restriction_id: str
    security_id: str
    restriction_type: str
    active: bool

# ----------------------  BrokerageStore = in memory data base ------------------------------------------------------

@dataclass
class BrokerageStore:
    users: Dict[str, User] = field(default_factory=dict)
    accounts: Dict[str, BrokerageAccount] = field(default_factory=dict)
    securities: Dict[str, Security] = field(default_factory=dict)
    orders: Dict[str, Order] = field(default_factory=dict)
    positions: Dict[str, Position] = field(default_factory=dict)
    cash_ledger: List[CashLedgerEntry] = field(default_factory=list)
    clearing_obligations: List[ClearingObligation] = field(default_factory=list)
    restrictions: List[TradingRestriction] = field(default_factory=list)
    clearing_capacity_remaining: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock)

#----------------    Initial Data Setup -----------------------------------------------------------------
# create starting states for user, brokerage account, GME security, GME position, limited amount of cash, and capacity

#new_id create unique id for every order
def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"

#b_i_s creates starting in memory data-base
def build_initial_store(
    initial_cash: float,
    clearing_capacity: float,
) -> BrokerageStore:
    store = BrokerageStore(clearing_capacity_remaining=clearing_capacity)

    user = User(
        user_id="usr_001",
        full_name="Retail Trader",
        kyc_status="VERIFIED",
    )
    account = BrokerageAccount(
        account_id="acct_001",
        user_id=user.user_id,
        account_status="ACTIVE",
        margin_enabled=False,
        available_cash=initial_cash,
    )
    security = Security(
        security_id="sec_gme",
        ticker_symbol="GME",
        security_name="GameStop Corp.",
        exchange="NYSE",
    )
    position = Position(
        position_id="pos_acct001_gme",
        account_id=account.account_id,
        security_id=security.security_id,
    )

    store.users[user.user_id] = user
    store.accounts[account.account_id] = account
    store.securities[security.security_id] = security
    store.positions[position.position_id] = position
    return store

#b_g_t simulates buy order, checks cash, checks clearing capacity, waits, creates order, ledger entry, position update, and clearing obligation
#t_block nested function so it can run with or without lock
def buy_gme_transaction(
    store: BrokerageStore,
    account_id: str,
    security_id: str,
    quantity: int,
    estimated_price: float,
    synthetic_delay: float,
    strict_isolation: bool,
) -> Dict[str, object]:
    start = time.perf_counter()

    def transaction_block() -> Dict[str, object]:
        account = store.accounts[account_id]
        security = store.securities[security_id]
        position = store.positions["pos_acct001_gme"]
        total_cost = quantity * estimated_price
        required_deposit = total_cost * 0.50

        # READ: check the business constraints before accepting the order.
        read_cash = account.available_cash
        read_capacity = store.clearing_capacity_remaining
        read_trading_status = security.trading_status

        if read_trading_status != "OPEN":
            return finish(start, False, "SECURITY_RESTRICTED")

        if read_cash < total_cost:
            return finish(start, False, "INSUFFICIENT_CASH")

        if read_capacity < required_deposit:
            return finish(start, False, "CLEARING_CAPACITY_EXCEEDED")

        # PROCESS: simulate server processing and network/database latency.
        time.sleep(synthetic_delay)

        # WRITE: update multiple entity objects as one logical transaction.
        order_id = new_id("ord")
        order = Order(
            order_id=order_id,
            account_id=account.account_id,
            security_id=security.security_id,
            side="BUY",
            quantity=quantity,
            estimated_price=estimated_price,
            order_status="ACCEPTED",
            created_at=time.time(),
        )
        ledger_entry = CashLedgerEntry(
            ledger_entry_id=new_id("led"),
            account_id=account.account_id,
            order_id=order_id,
            amount=-total_cost,
            entry_type="BUY_HOLD",
            created_at=time.time(),
        )
        obligation = ClearingObligation(
            obligation_id=new_id("clr"),
            order_id=order_id,
            required_deposit=required_deposit,
            settlement_date="T+2",
            obligation_status="OPEN",
        )

        store.orders[order_id] = order
        account.available_cash -= total_cost
        position.share_quantity += quantity
        store.cash_ledger.append(ledger_entry)
        store.clearing_obligations.append(obligation)
        store.clearing_capacity_remaining -= required_deposit

        return finish(start, True, "ACCEPTED")

    if strict_isolation:
        with store.lock:
            return transaction_block()

    return transaction_block()

#finish ends transaction, records its time and reports
def finish(start: float, success: bool, reason: str) -> Dict[str, object]:
    latency_ms = (time.perf_counter() - start) * 1000
    return {
        "success": success,
        "reason": reason,
        "latency_ms": latency_ms,
    }

#c_i_v checks final state of simulated database for errors, negative cash, capacity, ledger total, excessive orders
def count_integrity_violations(
    store: BrokerageStore,
    initial_cash: float,
    clearing_capacity: float,
    share_price: float,
) -> Dict[str, int]:
    account = store.accounts["acct_001"]
    position = store.positions["pos_acct001_gme"]
    accepted_orders = [o for o in store.orders.values() if o.order_status == "ACCEPTED"]

    total_order_cost = sum(o.quantity * o.estimated_price for o in accepted_orders)
    total_ledger_debits = -sum(entry.amount for entry in store.cash_ledger)
    total_required_deposit = sum(o.required_deposit for o in store.clearing_obligations)
    expected_position = sum(o.quantity for o in accepted_orders)

    violations = {
        "negative_cash": int(account.available_cash < -0.000001),
        "negative_clearing_capacity": int(store.clearing_capacity_remaining < -0.000001),
        "cash_ledger_mismatch": int(abs(total_order_cost - total_ledger_debits) > 0.000001),
        "position_mismatch": int(position.share_quantity != expected_position),
        "clearing_obligation_mismatch": int(
            abs(total_required_deposit - (clearing_capacity - store.clearing_capacity_remaining))
            > 0.000001
        ),
        "accepted_over_cash_limit": int(total_order_cost > initial_cash + 0.000001),
        "accepted_over_clearing_limit": int(total_required_deposit > clearing_capacity + 0.000001),
        "ledger_count_mismatch": int(len(store.cash_ledger) != len(accepted_orders)),
        "clearing_count_mismatch": int(len(store.clearing_obligations) != len(accepted_orders)),
    }
    violations["total"] = sum(violations.values())

    # Extra derived check useful for paper discussion.
    affordable_shares = int(initial_cash // share_price)
    violations["shares_over_affordable_limit"] = int(position.share_quantity > affordable_shares)
    violations["total"] += violations["shares_over_affordable_limit"]
    return violations


#run_trial runs simulation for thread count and isolation settings
#worker nested in run trail and is ran per thread
def run_trial(
    thread_count: int,
    strict_isolation: bool,
    initial_cash: float,
    clearing_capacity: float,
    quantity: int,
    share_price: float,
    synthetic_delay: float,
) -> Dict[str, object]:
    store = build_initial_store(initial_cash, clearing_capacity)
    results: List[Dict[str, object]] = []
    results_lock = threading.Lock()

    def worker() -> None:
        result = buy_gme_transaction(
            store=store,
            account_id="acct_001",
            security_id="sec_gme",
            quantity=quantity,
            estimated_price=share_price,
            synthetic_delay=synthetic_delay,
            strict_isolation=strict_isolation,
        )
        with results_lock:
            results.append(result)

    started = time.perf_counter()
    threads = [threading.Thread(target=worker) for _ in range(thread_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    elapsed_seconds = time.perf_counter() - started

    accepted = sum(1 for result in results if result["success"])
    rejected = thread_count - accepted
    latencies = [float(result["latency_ms"]) for result in results]
    violations = count_integrity_violations(
        store=store,
        initial_cash=initial_cash,
        clearing_capacity=clearing_capacity,
        share_price=share_price,
    )

    return {
        "threads": thread_count,
        "phase": "strict_isolation" if strict_isolation else "no_isolation",
        "accepted_orders": accepted,
        "rejected_orders": rejected,
        "final_cash": round(store.accounts["acct_001"].available_cash, 2),
        "final_gme_shares": store.positions["pos_acct001_gme"].share_quantity,
        "clearing_capacity_remaining": round(store.clearing_capacity_remaining, 2),
        "integrity_violations": violations["total"],
        "throughput_tx_per_sec": round(accepted / elapsed_seconds, 2),
        "avg_latency_ms": round(statistics.mean(latencies), 2),
        "max_latency_ms": round(max(latencies), 2),
        "elapsed_seconds": round(elapsed_seconds, 4),
    }


#print_tables prints results from simulation 
def print_table(rows: List[Dict[str, object]]) -> None:
    headers = [
        "threads",
        "phase",
        "accepted_orders",
        "rejected_orders",
        "integrity_violations",
        "throughput_tx_per_sec",
        "avg_latency_ms",
        "max_latency_ms",
        "final_cash",
        "final_gme_shares",
        "clearing_capacity_remaining",
    ]
    widths = {
        header: max(len(header), *(len(str(row[header])) for row in rows))
        for header in headers
    }
    print(" | ".join(header.ljust(widths[header]) for header in headers))
    print("-+-".join("-" * widths[header] for header in headers))
    for row in rows:
        print(" | ".join(str(row[header]).ljust(widths[header]) for header in headers))

#write_csv saves results to view
def write_csv(rows: List[Dict[str, object]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Robinhood/GameStop ACID concurrency simulation."
    )
    parser.add_argument(
        "--threads",
        nargs="+",
        type=int,
        default=[10, 100, 1000],
        help="Concurrent thread counts to test.",
    )
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=10_000.0,
        help="Starting buying power for the simulated brokerage account.",
    )
    parser.add_argument(
        "--clearing-capacity",
        type=float,
        default=5_000.0,
        help="Starting clearing/collateral capacity available to the broker.",
    )
    parser.add_argument(
        "--quantity",
        type=int,
        default=1,
        help="Shares requested per buy order.",
    )
    parser.add_argument(
        "--share-price",
        type=float,
        default=250.0,
        help="Estimated GME share price used by each order.",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.01,
        help="Synthetic processing/network delay inside each transaction.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/simulation_results.csv"),
        help="CSV output path.",
    )
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    rows: List[Dict[str, object]] = []
    for thread_count in args.threads:
        rows.append(
            run_trial(
                thread_count=thread_count,
                strict_isolation=False,
                initial_cash=args.initial_cash,
                clearing_capacity=args.clearing_capacity,
                quantity=args.quantity,
                share_price=args.share_price,
                synthetic_delay=args.delay,
            )
        )
        rows.append(
            run_trial(
                thread_count=thread_count,
                strict_isolation=True,
                initial_cash=args.initial_cash,
                clearing_capacity=args.clearing_capacity,
                quantity=args.quantity,
                share_price=args.share_price,
                synthetic_delay=args.delay,
            )
        )

    print_table(rows)
    write_csv(rows, args.output)
    print(f"\nWrote CSV results to: {args.output}")


if __name__ == "__main__":
    main()

