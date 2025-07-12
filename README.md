# bgr

Board Game Rank

This repository contains a small tool to rank board games using the Wilson 99% lower-bound and output a static HTML table.

## Usage

1. Prepare a CSV file with columns `name`, `votes`, and `sum_scores` where `votes` is the number of ratings and `sum_scores` is the sum of all 1–10 scores for the game. See `sample_ratings.csv` for an example.
2. Run `python rank_games.py ratings.csv output.html` to generate the page. A more complete dataset is provided in `2025-06-18T11-00-01.csv`.
3. Open the resulting `output.html` (or any name you choose) in any browser to view and sort the Top 1000 board games.

The ranking uses the provided helper function `wilson_lower_bound_10pt` to compute a hype-proof score. The output page contains a sortable table implemented with a small JavaScript function, so no dependencies are required.
