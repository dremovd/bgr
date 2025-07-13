import csv
from pathlib import Path
import pytest
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate_page as gp


def test_parse_details_sample():
    xml_path = Path(__file__).with_name("174430.xml")
    xml = xml_path.read_text(encoding="utf-8")
    details = gp.parse_details(xml)
    assert details["version_count"] >= 28
    assert details["weight"] == pytest.approx(3.9149, rel=1e-4)
    assert not details["is_expansion"]
    assert not details["reimplements"]


def test_games_columns_unique():
    csv_files = sorted(Path(".").glob("20*.csv"))
    assert csv_files
    games = gp.read_games(str(csv_files[-1]))
    assert len({g["wilson"] for g in games[:10]}) > 1
    assert len({g["weighted"] for g in games[:10]}) > 1
    assert len({g["bgg_rank"] for g in games[:10]}) > 1


def test_complexity_status_boundaries():
    assert gp.complexity_status(1.5)[1] == "Light"
    assert gp.complexity_status(2.5)[1] == "Medium"
    assert gp.complexity_status(3.5)[1] == "Complicated"
    assert gp.complexity_status(4.5)[1] == "Hardcore"


def test_version_icon_threshold():
    games = [
        {
            "id": 1,
            "Name": "A",
            "Year": "2025",
            "Users rated": "10",
            "Average": "8",
            "bgg_rank": 1,
            "wilson": 0.0,
            "weighted": 0.0,
            "version_count": 1,
        },
        {
            "id": 2,
            "Name": "B",
            "Year": "2025",
            "Users rated": "10",
            "Average": "8",
            "bgg_rank": 1,
            "wilson": 0.0,
            "weighted": 0.0,
            "version_count": 2,
        },
    ]
    html = gp._table_rows(games)
    assert html.count("🌐") == 1
