"""Rebuild data model and Power BI project from sales_data.csv."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

for script in ("build_powerbi_model.py", "build_pbip_project.py"):
    subprocess.run([sys.executable, str(ROOT / script)], check=True)
