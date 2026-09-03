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

#section for entities --------------------

