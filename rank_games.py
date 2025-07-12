#!/usr/bin/env python3
"""Generate a static HTML ranking table for board games.

Usage:
    python rank_games.py ratings.csv output.html

The input CSV must have columns: name,votes,sum_scores
where ``votes`` is the total number of ratings for the game and
``sum_scores`` is the sum of the 1-10 ratings.

The script computes a Wilson lower bound score for each game and
outputs the top 1000 games into a sortable HTML table.
"""

import csv
import sys
from pathlib import Path
from typing import List, Tuple

from math import sqrt
from typing import Union


def wilson_lower_bound_10pt(n: int, S: Union[int, float], z: float = 2.326) -> float:
    """Wilson 99% lower-confidence bound for a 1-10 rating scale."""
    if n <= 0:
        return 0.0
    R = S / n
    p = (R - 1) / 9.0
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    wlb = (centre - adj) / denom
    return 1 + 9 * wlb


def load_ratings(path: Path) -> List[Tuple[str, int, float]]:
    games = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            votes = int(row["votes"])
            sum_scores = float(row["sum_scores"])
            games.append((name, votes, sum_scores))
    return games


def build_rows(games: List[Tuple[str, int, float]]) -> str:
    parts = []
    for rank, (name, votes, sum_scores, score) in enumerate(games, start=1):
        parts.append(
            f"<tr><td>{rank}</td><td>{name}</td><td>{votes}</td>"
            f"<td>{score:.2f}</td></tr>"
        )
    return "\n".join(parts)


def generate_html(games: List[Tuple[str, int, float, float]]) -> str:
    rows = build_rows(games)
    return f"""<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'>
<title>Top Board Games</title>
<style>
body {{ font-family: Arial, sans-serif; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
th {{ background: #eee; cursor: pointer; }}
</style>
<script>
// Simple table sort
function sortTable(n) {{
  var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
  table = document.getElementById("games");
  switching = true;
  dir = "asc";
  while (switching) {{
    switching = false;
    rows = table.rows;
    for (i = 1; i < (rows.length - 1); i++) {{
      shouldSwitch = false;
      x = rows[i].getElementsByTagName("TD")[n];
      y = rows[i + 1].getElementsByTagName("TD")[n];
      if (dir == "asc") {{
        if (n === 0 || n === 2) {{
          if (parseFloat(x.innerHTML) > parseFloat(y.innerHTML)) {{
            shouldSwitch= true;
            break;
          }}
        }} else if (x.innerHTML.toLowerCase() > y.innerHTML.toLowerCase()) {{
          shouldSwitch = true;
          break;
        }}
      }} else if (dir == "desc") {{
        if (n === 0 || n === 2) {{
          if (parseFloat(x.innerHTML) < parseFloat(y.innerHTML)) {{
            shouldSwitch = true;
            break;
          }}
        }} else if (x.innerHTML.toLowerCase() < y.innerHTML.toLowerCase()) {{
          shouldSwitch = true;
          break;
        }}
      }}
    }}
    if (shouldSwitch) {{
      rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
      switching = true;
      switchcount ++;
    }} else {{
      if (switchcount == 0 && dir == "asc") {{
        dir = "desc";
        switching = true;
      }}
    }}
  }}
}}
</script>
</head>
<body>
<h1>Top Board Games</h1>
<table id='games'>
<thead>
<tr><th onclick='sortTable(0)'>Rank</th><th onclick='sortTable(1)'>Name</th><th onclick='sortTable(2)'>Votes</th><th onclick='sortTable(3)'>Score</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>"""


def main(args: List[str]) -> int:
    if len(args) != 3:
        print("Usage: python rank_games.py ratings.csv output.html")
        return 1
    in_file = Path(args[1])
    out_file = Path(args[2])
    games = load_ratings(in_file)
    ranked = []
    for name, votes, sum_scores in games:
        score = wilson_lower_bound_10pt(votes, sum_scores)
        ranked.append((name, votes, sum_scores, score))
    ranked.sort(key=lambda g: g[3], reverse=True)
    ranked = ranked[:1000]
    html = generate_html(ranked)
    out_file.write_text(html, encoding="utf-8")
    print(f"Wrote {len(ranked)} games to {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
