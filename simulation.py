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


#--------------      Dataclasses Represent ERD Entities    ----------------------------------------------
# Entities: User, BrokerageAccount, Security, Order, Position, CashLedgerEntry, ClearingObligation, TradingRestriction
# BrokerageStore = in memory data base


#----------------    Initial Data Setup -----------------------------------------------------------------
# create starting states for user, brokerage account, GME security, GME position, limited amount of cash, and capacity


#------------------------ Trnasaction function ----------------------------------------------------------


#------------------------------ No isolation vs. Strict Isolation --------------------------------------------

#----------------------------------------------- Integrity Checks ----------------------------------------------

#------------------------------------------------- Running a Trial ------------------------------------------------

#---------------------------------------------- Printing and Saving Results ----------------------------------


