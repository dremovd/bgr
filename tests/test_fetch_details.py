from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import generate_page as gp

def test_single_version_has_no_translation():
    xml = Path('sample.xml').read_text()
    details = gp.parse_details(xml, 219650)
    assert details['has_versions'] is False
    assert details['n_versions'] == 1
