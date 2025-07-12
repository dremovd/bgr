import csv
from math import sqrt
from typing import Union


def wilson_lower_bound_10pt(n: int, S: Union[int, float], z: float = 2.326) -> float:
    if n <= 0:
        return 0.0
    R = S / n
    p = (R - 1) / 9.0
    denom = 1 + z*z / n
    centre = p + z*z / (2*n)
    adj = z * sqrt((p*(1 - p) + z*z / (4*n)) / n)
    wlb = (centre - adj) / denom
    return 1 + 9 * wlb


def read_games(path: str):
    games = []
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                n = int(row['Users rated'])
                avg = float(row['Average'])
            except (ValueError, KeyError):
                continue
            S = avg * n
            row['wlb'] = wilson_lower_bound_10pt(n, S)
            games.append(row)
    return games


def generate_html(games, out_path: str):
    html_head = """
<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='UTF-8'>
<title>Top Board Games</title>
<style>
body{font-family:Arial,Helvetica,sans-serif;margin:2em;}
table{border-collapse:collapse;width:100%;}
th,td{border:1px solid #ccc;padding:0.4em;text-align:left;}
th{cursor:pointer;background:#f2f2f2;}
tr:nth-child(even){background:#fafafa;}
</style>
</head>
<body>
<h1>Top Board Games (Wilson 99% lower bound)</h1>
<table class='sortable'>
<thead>
<tr>
  <th class='num'>Rank</th>
  <th>Name</th>
  <th class='num'>Year</th>
  <th class='num'>Users Rated</th>
  <th class='num'>Average</th>
  <th class='num'>Score</th>
</tr>
</thead>
<tbody>
"""
    html_tail = """
</tbody>
</table>
<script>
function makeSortable(table){
  const ths = table.tHead.rows[0].cells;
  const dirs = Array(ths.length).fill(true);
  for(let i=0;i<ths.length;i++){
    ths[i].addEventListener('click',()=>{
      const tbody = table.tBodies[0];
      const rows = Array.from(tbody.querySelectorAll('tr'));
      const numeric = ths[i].classList.contains('num');
      rows.sort((a,b)=>{
        const A = a.cells[i].textContent.trim();
        const B = b.cells[i].textContent.trim();
        if(numeric){
          return (dirs[i]?1:-1)*(parseFloat(A)-parseFloat(B));
        }
        return (dirs[i]?1:-1)*A.localeCompare(B);
      });
      dirs[i] = !dirs[i];
      rows.forEach(r=>tbody.appendChild(r));
    });
  }
}
document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('table.sortable').forEach(makeSortable);
});
</script>
</body>
</html>
"""
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_head)
        for idx, g in enumerate(games, 1):
            f.write(f"<tr><td>{idx}</td><td>{g['Name']}</td><td>{g['Year']}</td>"
                    f"<td>{g['Users rated']}</td><td>{g['Average']}</td>"
                    f"<td>{g['wlb']:.3f}</td></tr>\n")
        f.write(html_tail)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('csv_file')
    parser.add_argument('-o', '--output', default='index.html')
    args = parser.parse_args()

    games = read_games(args.csv_file)
    games.sort(key=lambda g: g['wlb'], reverse=True)
    top_games = games[:200]
    generate_html(top_games, args.output)

if __name__ == '__main__':
    main()
