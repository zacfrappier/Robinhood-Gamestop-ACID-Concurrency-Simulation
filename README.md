# Robinhood/GameStop ACID Concurrency Simulation

This repository contains a small Python simulation for an academic post-mortem paper on the 2021 Robinhood/GameStop trading halt. The project models a simplified retail brokerage transaction and compares what happens when concurrent buy orders are processed with and without transaction isolation.

The simulation is intended to support the paper:

**"Post-Mortem Analysis and Simulation: The Virtues and Limitations of ACID in Hyper-Scale Systems"**

## Purpose

The goal is to demonstrate a core trade-off in transaction processing:

- Without isolation, the system can process requests quickly, but concurrent transactions can corrupt financial state.
- With strict isolation, the system protects entity integrity, but throughput decreases and latency increases under high concurrency.

The code does not attempt to reproduce Robinhood's real production systems. Instead, it provides a small-scale experiment that mirrors the kind of multi-entity transaction pressure involved in high-volume retail trading.

## Academic Foundation

This simulation is modeled from three sources:

1. Jim Gray's foundational transaction theory:
   - Gray explains that transactions protect consistency, atomicity, and durability, but also have practical limitations in complex and large-scale systems.

2. Peter Chen's entity-relationship model:
   - Chen's ER model motivates representing real-world business concepts as entities, relationships, and attributes before implementation.

3. Recent research on broker restrictions and scalable transactions:
   - Garvey, He, and Wu study GameStop broker trading restrictions and their market effects.
   - Idziorek et al. describe how modern distributed systems implement ACID transactions at scale.

## Conceptual Entities Represented

The simulation uses in-memory Python classes that correspond to the ERD entities used in the paper:

| ERD Entity | Purpose in Simulation |
|---                    | ---|
| `User`                | Represents a verified retail trader. |
| `BrokerageAccount`    | Holds account status, margin status, and available cash. |
| `Security`            | Represents GameStop stock using ticker symbol `GME`. |
| `Order`               | Represents a buy order submitted by the brokerage account. |
| `Position`            | Tracks the account's number of GME shares. |
| `CashLedgerEntry`     | Records cash holds/debits caused by accepted orders. |
| `ClearingObligation`  | Represents downstream clearing/collateral obligations  created by executed orders. |
| `TradingRestriction`  | Represents possible restrictions such as buy limits or trading halts. |

## Simulated Transaction

Each thread represents one concurrent request to buy one share of GME.

Each transaction follows a three-step process:

1. **Read**
   - Check whether GME trading is open.
   - Check whether the brokerage account has enough available cash.
   - Check whether clearing capacity remains available.

2. **Synthetic Delay**
   - Pause briefly using `time.sleep(0.01)` to simulate server processing time, network latency, or database latency.

3. **Write**
   - Create an accepted order.
   - Debit or hold cash in the brokerage account.
   - Update the GME position.
   - Create a cash ledger entry.
   - Create a clearing obligation.
   - Reduce remaining clearing capacity.

## Test Phases

The experiment runs the same workload under two phases:

| Phase | Description | Expected Behavior |
|---|---|---|
| `no_isolation` | No lock protects the transaction block. | Higher throughput, lower latency, but possible race-condition anomalies. |
| `strict_isolation` | A mutex protects the full read-delay-write transaction. | Correct entity state, but lower throughput and higher latency. |

## Metrics Collected

The script reports:

- Number of concurrent threads
- Accepted orders
- Rejected orders
- Final cash balance
- Final GME share position
- Remaining clearing capacity
- Number of integrity violations
- Throughput in successful transactions per second
- Average latency in milliseconds
- Maximum latency in milliseconds

These metrics can be used in the Results section of the paper.

## How to Run

This project uses only the Python standard library.

Run the default experiment:

```bash
python simulation.py
```

Run with custom thread counts:

```bash
python simulation.py --threads 10 100 1000
```

Run with a larger synthetic delay:

```bash
python simulation.py --delay 0.05
```

Run with different cash and clearing limits:

```bash
python simulation.py --initial-cash 10000 --clearing-capacity 5000
```

## Output

The script prints a comparison table to the terminal and writes a CSV file to:

```text
results/simulation_results.csv
```

You can use the CSV file to create a line graph or comparison table for the Results section of the paper.

## Paper Interpretation

- In the no-isolation phase, multiple threads can read the same valid cash and clearing-capacity state before any one thread writes its update. This can cause the simulation to accept more orders than the account or clearing system can safely support.
- In the strict-isolation phase, the lock forces each transaction to complete before the next begins. This preserves entity integrity but creates queueing delays as concurrency increases.

This supports the paper's argument that ACID properties remain necessary for financial correctness, but strict isolation can become a bottleneck in hyper-scale systems.

## IEEE References

```text
[1] J. Gray, "The transaction concept: virtues and limitations," in Proc. 7th Int. Conf. Very Large Data Bases (VLDB), Cannes, France, 1981, pp. 144-154.

[2] P. P.-S. Chen, "The entity-relationship model: Toward a unified view of data," ACM Transactions on Database Systems, vol. 1, no. 1, pp. 9-36, Mar. 1976, doi: 10.1145/320434.320440.

[3] R. Garvey, J. He, and F. Wu, "Retail broker trading restrictions and market liquidity: An examination of GameStop," Applied Economics, vol. 56, no. 34, pp. 4140-4153, 2024, doi: 10.1080/00036846.2023.2210819.

[4] J. Idziorek, A. Keyes, C. Lazier, S. Perianayagam, P. Ramanathan, J. C. Sorenson III, D. Terry, and A. Vig, "Distributed transactions at scale in Amazon DynamoDB," in Proc. 2023 USENIX Annual Technical Conf. (USENIX ATC 23), Boston, MA, USA, 2023, pp. 705-717.
```

