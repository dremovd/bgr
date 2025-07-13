# best board game

Best Board Game

This project ranks board games using a weighted Wilson lower bound with a strict 99.5% one-sided confidence (z≈2.576). Each game is adjusted with 25 prior votes at rating 6.5 to reduce small-sample effects. The script reads a CSV export from BoardGameGeek and produces a sortable HTML table.

## Generate the page

Run the helper script to produce `docs/index.html`:

```bash
python3 generate_page.py -o docs/index.html
```

Use `--min-year` to pick the cutoff year for the "recent" list. The generated page contains two tables and a toggle button to switch between them: one shows only games from the chosen year onward, the other shows all years. For example:

```bash
python3 generate_page.py -o docs/index.html --min-year 2025
```

The CSV file contains the raw ratings exported from BoardGameGeek. Each game name
links directly to its BoardGameGeek page. A status column now combines several
emojis: 🔥/🔎/💎 for the official rank, 🧩 if the entry is an expansion, ♻️ if it
reimplements another game, 🌐 if different language versions exist, and a colour
dot for the complexity level (🟢 light, 🟡 medium, 🟠 complicated, 🔴 hardcore).
Each row also displays a small thumbnail image and a numeric complexity rating
fetched from the BGG API.
The page header also shows the snapshot time parsed from the CSV filename so visitors can see when the rankings were last updated.


## GitHub Pages

Publish the contents of the `docs/` directory as a GitHub Pages site. In the repository settings, set **Pages** → **Source** to the `docs/` folder. After pushing to GitHub, the table will be available at [https://bestboardga.me](https://bestboardga.me).
