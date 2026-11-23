"""Splice sections_results.md and sections_discussion.md into manuscript.md, filling the
tables from results/ (code/summarize.py). Run after every change to results or sections."""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "code"))
import summarize as S  # noqa: E402

T = S.md_tables(HERE.parent / "results")
res = (HERE / "sections_results.md").read_text()
dis = (HERE / "sections_discussion.md").read_text()
for k in ["TABLE2", "TABLE3", "TABLE4", "TABLES1"]:
    if k in T:
        res = res.replace(f"{k}_PLACEHOLDER", T[k])
ms = (HERE / "manuscript.md").read_text()
a, b = ms.index("## 3. Results\n"), ms.index("## 6. Back Matter\n")
ms = ms[:a] + res.rstrip() + "\n\n" + dis.rstrip() + "\n\n" + ms[b:]
left = re.findall(r"[A-Z0-9_]+_PLACEHOLDER|INTERP_EA\d", ms)
(HERE / "manuscript.md").write_text(ms)
print("assembled; unfilled markers:", left)
