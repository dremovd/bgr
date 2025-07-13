import csv
from datetime import datetime
from math import sqrt
from typing import Union, Tuple
from pathlib import Path
import xml.etree.ElementTree as ET
import requests
from functools import lru_cache
import time

DEFAULT_Z = 2.576  # z-score for 99.5% one-sided Wilson interval


def wilson_lower_bound_10pt(n: int, S: Union[int, float], z: float = DEFAULT_Z) -> float:
    if n <= 0:
        return 0.0
    R = S / n
    p = (R - 1) / 9.0
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    adj = z * sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    wlb = (centre - adj) / denom
    return 1 + 9 * wlb


PRIOR_VOTES = 25  # pseudo-ratings to reduce team-voting effects
PRIOR_RATING = 6.5  # use a realistic prior around the global average


def weighted_score(n: int, S: Union[int, float]) -> float:
    """Wilson lower bound with prior votes at rating PRIOR_RATING."""
    return wilson_lower_bound_10pt(n + PRIOR_VOTES, S + PRIOR_VOTES * PRIOR_RATING)


def latest_csv() -> str:
    """Return the path to the newest ratings CSV in the current directory."""
    files = sorted(Path(".").glob("20*.csv"))
    if not files:
        raise FileNotFoundError("No ratings CSV found")
    return str(files[-1])


def timestamp_from_csv(path: str) -> str:
    """Parse an ISO-like timestamp from a CSV filename."""
    stem = Path(path).stem
    try:
        dt = datetime.strptime(stem, "%Y-%m-%dT%H-%M-%S")
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except ValueError:
        return stem


def status_for_rank(rank: int) -> Tuple[str, str]:
    """Return emoji and label for a game's BGG rank."""
    if rank <= 200:
        return "🔥", "Bestseller"
    if rank <= 1000:
        return "🔎", "Rare find"
    return "💎", "Hidden gem"


@lru_cache(maxsize=None)
def fetch_details(game_id: int):
    """Return extra info from BGG: weight and flag booleans."""
    url = (
        f"https://api.geekdo.com/xmlapi2/thing?id={game_id}&stats=1&versions=1"
    )
    time.sleep(1)
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    return parse_details(r.text, game_id)


def parse_details(xml_text: str, game_id: int):
    """Parse BGG XML and return details dict."""
    tree = ET.fromstring(xml_text)
    item = tree.find("item")
    weight_node = item.find("./statistics/ratings/averageweight")
    weight = float(weight_node.attrib.get("value", "0")) if weight_node is not None else 0.0
    is_expansion = item.attrib.get("type") == "boardgameexpansion"
    reimplements = (
        item.find(".//link[@type='boardgameimplementation'][@inbound='true']")
        is not None
    )
    versions_node = item.find(".//versions")
    version_items = versions_node.findall("item") if versions_node is not None else []
    inbound_versions = item.findall(
        ".//link[@type='boardgameversion'][@inbound='true']"
    )
    version_ids = {
        v.attrib.get("id")
        for v in version_items
        if v.attrib.get("id") != str(game_id)
    }
    link_ids = {
        l.attrib.get("id")
        for l in inbound_versions
        if l.attrib.get("id") != str(game_id)
    }
    unique_versions = version_ids | link_ids
    has_versions = len(unique_versions) > 1
    n_versions = len(unique_versions)
    return {
        "weight": weight,
        "is_expansion": is_expansion,
        "reimplements": reimplements,
        "has_versions": has_versions,
        "n_versions": n_versions,
    }


def complexity_status(weight: float) -> Tuple[str, str]:
    """Return emoji and label for a game's complexity weight."""
    if weight < 2:
        return "🟢", "Light"
    if weight < 3:
        return "🟡", "Medium"
    if weight < 4:
        return "🟠", "Complicated"
    return "🔴", "Hardcore"


def read_games(path: str):
    games = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row_id = int(row["ID"])
                n = int(row["Users rated"])
                avg = float(row["Average"])
                bgg_rank = int(row["Rank"])
                thumb = row.get("Thumbnail", "")
            except (ValueError, KeyError):
                continue
            S = avg * n
            row["wilson"] = wilson_lower_bound_10pt(n, S)
            row["weighted"] = weighted_score(n, S)
            row["bgg_rank"] = bgg_rank
            row["id"] = row_id
            row["thumb"] = thumb
            games.append(row)
    return games


def enrich_games(games):
    for g in games:
        details = fetch_details(g["id"])
        g.update(details)


def _table_rows(games):
    rows = []
    for idx, g in enumerate(games, 1):
        link = (
            f"<a href='https://boardgamegeek.com/boardgame/{g['id']}' "
            "target='_blank' rel='noopener noreferrer'>" + g["Name"] + "</a>"
        )
        r_emoji, r_label = status_for_rank(g["bgg_rank"])
        c_emoji, c_label = complexity_status(g.get("weight", 0.0))
        thumb = g.get("thumb", "")
        img = f"<img src='{thumb}' alt='{g['Name']} thumbnail'>" if thumb else ""
        parts = [(r_emoji, r_label)]
        if g.get("is_expansion"):
            parts.append(("🧩", "Expansion"))
        if g.get("reimplements"):
            parts.append(("♻️", "Reimplements"))
        if g.get("has_versions"):
            parts.append(("🌐", "Has versions"))
        parts.append((c_emoji, c_label))
        status_icons = "".join(
            f"<span title='{lbl}'>{emo}</span>" for emo, lbl in parts
        )
        rows.append(
            f"<tr><td>{idx}</td><td class='thumb'>{img}</td><td>{link}</td>"
            f"<td>{g['Year']}</td><td>{g['Users rated']}</td><td>{g['Average']}</td>"
            f"<td>{g['bgg_rank']}</td><td class='status'>{status_icons}</td>"
            f"<td>{g.get('weight', 0):.2f}</td>"
            f"<td>{g['wilson']:.3f}</td><td>{g['weighted']:.3f}</td></tr>"
        )
    return "\n".join(rows)


def generate_html(
    games_recent, games_all, out_path: str, recent_year: int, snapshot: str
):
    html_head = f"""<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Best Board Game</title>
<style>
:root{{
  --bg:#fff;
  --text:#333;
  --accent:#007acc;
}}
body{{
  font-family:system-ui,-apple-system,Helvetica,Arial,sans-serif;
  margin:2rem;
  line-height:1.5;
  background:var(--bg);
  color:var(--text);
}}
table{{border-collapse:collapse;width:100%;margin-top:1rem;}}
th,td{{border:1px solid #ccc;padding:0.5rem;text-align:left;}}
th{{cursor:pointer;background:#f3f3f3;}}
thead th{{position:sticky;top:0;z-index:1;background:#f3f3f3;}}
tr:nth-child(even){{background:#fafafa;}}
td.thumb img{{width:48px;height:auto;display:block;}}
td.status,th.status{{white-space:nowrap;}}
button{{background:var(--accent);color:#fff;border:none;border-radius:4px;padding:0.5em 1em;margin-bottom:1rem;cursor:pointer;font-size:1rem;}}
button:hover{{opacity:0.9;}}
</style>
</head>
<body>
<h1>Best Board Game Rankings (Weighted Wilson 99.5% lower bound)</h1>
<p>Snapshot: {snapshot}</p>
<button id='toggle'>Show all years</button>
<table id='recent' class='sortable'>
<thead>
<tr>
  <th class='num'>Rank</th>
  <th>Thumb</th>
  <th>Name</th>
  <th class='num'>Year</th>
  <th class='num'>Users Rated</th>
  <th class='num'>Average</th>
  <th class='num'>BGG Rank</th>
  <th class='status'>Status</th>
  <th class='num'>Complexity</th>
  <th class='num'>Wilson</th>
  <th class='num'>Weighted</th>
</tr>
</thead>
<tbody>
"""
    html_tail = f"""
</tbody>
</table>
<table id='all' class='sortable' style='display:none'>
<thead>
<tr>
  <th class='num'>Rank</th>
  <th>Thumb</th>
  <th>Name</th>
  <th class='num'>Year</th>
  <th class='num'>Users Rated</th>
  <th class='num'>Average</th>
  <th class='num'>BGG Rank</th>
  <th class='status'>Status</th>
  <th class='num'>Complexity</th>
  <th class='num'>Wilson</th>
  <th class='num'>Weighted</th>
</tr>
</thead>
<tbody>
"""
    script = f"""
</tbody>
</table>
<script>
function makeSortable(table){{
  const ths = table.tHead.rows[0].cells;
  const dirs = Array(ths.length).fill(true);
  for(let i=0;i<ths.length;i++){{
    ths[i].addEventListener('click',()=>{{
      const tbody = table.tBodies[0];
      const rows = Array.from(tbody.querySelectorAll('tr'));
      const numeric = ths[i].classList.contains('num');
      rows.sort((a,b)=>{{
        const A = a.cells[i].textContent.trim();
        const B = b.cells[i].textContent.trim();
        if(numeric){{
          return (dirs[i]?1:-1)*(parseFloat(A)-parseFloat(B));
        }}
        return (dirs[i]?1:-1)*A.localeCompare(B);
      }});
      dirs[i] = !dirs[i];
      rows.forEach(r=>tbody.appendChild(r));
    }});
  }}
}}
function setupToggle(){{
  const btn = document.getElementById('toggle');
  const recent = document.getElementById('recent');
  const all = document.getElementById('all');
  btn.addEventListener('click',()=>{{
    if(all.style.display==='none'){{
      recent.style.display='none';
      all.style.display='';
      btn.textContent='Show {recent_year}+';
    }}else{{
      all.style.display='none';
      recent.style.display='';
      btn.textContent='Show all years';
    }}
  }});
}}
document.addEventListener('DOMContentLoaded',()=>{{
  document.querySelectorAll('table.sortable').forEach(makeSortable);
  setupToggle();
}});
</script>
</body>
</html>
"""
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_head)
        f.write(_table_rows(games_recent))
        f.write(html_tail)
        f.write(_table_rows(games_all))
        f.write(script)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("csv_file", nargs="?", default=None)
    parser.add_argument("-o", "--output", default="index.html")
    parser.add_argument(
        "--min-year",
        type=int,
        default=2025,
        help="Year threshold for the recent list",
    )
    args = parser.parse_args()

    csv_path = args.csv_file or latest_csv()
    snapshot = timestamp_from_csv(csv_path)

    all_games = read_games(csv_path)
    games_recent = [g for g in all_games if int(g.get("Year", 0)) >= args.min_year]
    games_all = list(all_games)
    games_recent.sort(key=lambda g: g["weighted"], reverse=True)
    games_all.sort(key=lambda g: g["weighted"], reverse=True)
    top_ids = {g["id"] for g in games_recent[:200]} | {g["id"] for g in games_all[:200]}
    detail_rows = []
    for g in all_games:
        if g["id"] in top_ids:
            details = fetch_details(g["id"])
            g.update(details)
            row = {"id": g["id"], "name": g["Name"]}
            row.update(details)
            detail_rows.append(row)
    if detail_rows:
        out_details = f"details-{Path(csv_path).stem}.csv"
        with open(out_details, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=detail_rows[0].keys())
            writer.writeheader()
            writer.writerows(detail_rows)
    generate_html(games_recent[:200], games_all[:200], args.output, args.min_year, snapshot)


if __name__ == "__main__":
    main()
