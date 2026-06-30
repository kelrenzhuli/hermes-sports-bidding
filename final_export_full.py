"""
final_export_full.py — 薄封装

从 projects_v3 表读取结构化数据，输出 15 字段商业情报 Excel。
底层实现由 llm_pipeline/export_v3.py 提供。
"""

import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from llm_pipeline.export_v3 import export_to_excel

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm_bidding_v2.db")
OUTPUT = os.path.join(os.path.expanduser("~"), "Desktop", "体育招投标_商业情报单.xlsx")


def main():
    print("=" * 50)
    print("final_export_full.py -> projects_v3 -> Excel")
    print("=" * 50)
    out = export_to_excel(db_path=DB_PATH, output_path=OUTPUT)
    print(f"\nDone: {out}")


if __name__ == "__main__":
    main()
