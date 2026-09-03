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
# BrokerageStore = in memory data base

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


#----------------    Initial Data Setup -----------------------------------------------------------------
# create starting states for user, brokerage account, GME security, GME position, limited amount of cash, and capacity


#------------------------ Trnasaction function ----------------------------------------------------------


#------------------------------ No isolation vs. Strict Isolation --------------------------------------------

#----------------------------------------------- Integrity Checks ----------------------------------------------

#------------------------------------------------- Running a Trial ------------------------------------------------

#---------------------------------------------- Printing and Saving Results ----------------------------------


