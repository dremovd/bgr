# bgr

Board Game Rank

This project ranks board games using a weighted Wilson lower bound and generates a static HTML table.

## Generate the page

Run the helper script to produce `docs/index.html`:

```bash
python3 generate_page.py 2025-06-18T11-00-01.csv -o docs/index.html
```

The CSV file contains the raw ratings exported from BoardGameGeek.

## GitHub Pages

Publish the contents of the `docs/` directory as a GitHub Pages site.
In the repository settings, set **Pages** → **Source** to the `docs/` folder.
After pushing to GitHub, the table will be available at
`https://<username>.github.io/<repository>/`.
