#!/usr/bin/env python3
"""評估器：用 template/TRUTH.md（prod-eks、web1–web3 是 prod）跑 guard.py，印出處理方式。

    python3 thinking/09-data/check.py '<指令>' ['<指令>' ...]
    KIT_PROD_CONFIRM=0 python3 thinking/09-data/check.py '<指令>'

輸出：allow（不攔）／fix（擋下請 agent 自己修正）／ask（要求使用者確認）／deny（直接拒絕）
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "evals"))
from guard_test import decide  # noqa: E402

extra = {"KIT_PROD_CONFIRM": os.environ["KIT_PROD_CONFIRM"]} if "KIT_PROD_CONFIRM" in os.environ else {}
for cmd in sys.argv[1:]:
    print(f"{decide(cmd, **extra)}\t{cmd!r}")
