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

#b_i_s creates starting in memory data-base

#b_g_t simulates buy order, checks cash, checks clearing capacity, waits, creates order, ledger entry, position update, and clearing obligation
#t_block nested function so it can run with or without lock

#finish ends transaction, records its time and reports

#c_i_v checks final state of simulated database for errors, negative cash, capacity, ledger total, excessive orders

#run_trial runs simulation for thread count and isolation settings
#worker nested in run trail and is ran per thread

#print_tables prints results from simulation 

#write_csv saves results to view



#------------------------ Trnasaction function ----------------------------------------------------------


#------------------------------ No isolation vs. Strict Isolation --------------------------------------------

#----------------------------------------------- Integrity Checks ----------------------------------------------

#------------------------------------------------- Running a Trial ------------------------------------------------

#---------------------------------------------- Printing and Saving Results ----------------------------------


