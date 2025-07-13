from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import generate_page as gp

def test_single_version_has_no_translation():
    xml = Path('sample.xml').read_text()
    details = gp.parse_details(xml, 219650)
    assert details['has_versions'] is False
    assert details['n_versions'] == 1


def test_zero_versions():
    xml = Path('tests/zero_versions.xml').read_text()
    details = gp.parse_details(xml, 329697)
    assert details['has_versions'] is False
    assert details['n_versions'] == 0


def test_multiple_versions():
    xml = Path('tests/multi_versions.xml').read_text()
    details = gp.parse_details(xml, 1)
    assert details['has_versions'] is True
    assert details['n_versions'] == 2
