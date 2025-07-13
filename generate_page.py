import csv
from math import sqrt
from typing import Union, Tuple

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


def status_for_rank(rank: int) -> Tuple[str, str]:
    """Return emoji and label for a game's BGG rank."""
    if rank <= 200:
        return "🔥", "Bestseller"
    if rank <= 1000:
        return "🔎", "Rare find"
    return "💎", "Hidden gem"


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


def _table_rows(games):
    rows = []
    for idx, g in enumerate(games, 1):
        link = (
            f"<a href='https://boardgamegeek.com/boardgame/{g['id']}' "
            "target='_blank' rel='noopener noreferrer'>" + g["Name"] + "</a>"
        )
        emoji, label = status_for_rank(g["bgg_rank"])
        thumb = g.get("thumb", "")
        img = f"<img src='{thumb}' alt='{g['Name']} thumbnail'>" if thumb else ""
        rows.append(
            f"<tr><td>{idx}</td><td class='thumb'>{img}</td><td>{link}</td>"
            f"<td>{g['Year']}</td><td>{g['Users rated']}</td><td>{g['Average']}</td>"
            f"<td>{g['bgg_rank']}</td><td><span title='{label}'>{emoji}</span></td>"
            f"<td>{g['wilson']:.3f}</td><td>{g['weighted']:.3f}</td></tr>"
        )
    return "\n".join(rows)


def generate_html(games_recent, games_all, out_path: str, recent_year: int):
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
tr:nth-child(even){{background:#fafafa;}}
td.thumb img{{width:48px;height:auto;display:block;}}
button{{background:var(--accent);color:#fff;border:none;border-radius:4px;padding:0.5em 1em;margin-bottom:1rem;cursor:pointer;font-size:1rem;}}
button:hover{{opacity:0.9;}}
</style>
</head>
<body>
<h1>Best Board Game Rankings (Weighted Wilson 99.5% lower bound)</h1>
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
  <th>Status</th>
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
  <th>Status</th>
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
    parser.add_argument("csv_file")
    parser.add_argument("-o", "--output", default="index.html")
    parser.add_argument(
        "--min-year",
        type=int,
        default=2025,
        help="Year threshold for the recent list",
    )
    args = parser.parse_args()

    all_games = read_games(args.csv_file)
    games_recent = [g for g in all_games if int(g.get("Year", 0)) >= args.min_year]
    games_all = list(all_games)
    games_recent.sort(key=lambda g: g["weighted"], reverse=True)
    games_all.sort(key=lambda g: g["weighted"], reverse=True)
    generate_html(games_recent[:200], games_all[:200], args.output, args.min_year)


if __name__ == "__main__":
    main()
