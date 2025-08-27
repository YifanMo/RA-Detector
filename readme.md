# Introduction

RA-Detector is a novel system for the automated detection of malicious smart contracts. It specifically focuses on contracts that exploit asset approval mechanisms. The system operates in two main stages. First, it identifies and categorizes various types of token approvals from transaction traces. This process determines the owner's account type (EOA or CA) and the approval method (on-chain transaction or off-chain signature). Second, RA-Detector employs static analysis on the contracts' bytecode. This static analysis identifies unauthorized transfer logic. It uses a combination of taint analysis, control flow graph (CFG) analysis, and reachability analysis. This three-step process pinpoints malicious transfer calls, understands the conditions required for their execution, and verifies if these conditions are attacker-reachable. Ultimately, RA-Detector systematically identifies contracts that can transfer assets without the legitimate owner's explicit consent.

# Download Data

```bash
python download_approval.py

python download_code.py

python download_tx_trace.py
```

# Detect Transaction

```
python detect_txs.py

```

# Detect Contract

```
python detect_contract.py
```
