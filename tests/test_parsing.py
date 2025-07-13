import generate_page as gp
import requests
import types

class DummyResponse:
    def __init__(self, text):
        self.text = text
    def raise_for_status(self):
        pass

def test_fetch_details_parses_unique_versions(monkeypatch):
    xml = """<?xml version='1.0' encoding='utf-8'?><items><item id='1' type='boardgameexpansion'>\n<statistics><ratings><averageweight value='2.5'/></ratings></statistics>\n<link type='boardgameimplementation' id='100' inbound='true'/>\n<versions><item id='1'/><item id='2'/><item id='2'/></versions>\n<link type='boardgameversion' id='2' inbound='true'/><link type='boardgameversion' id='3' inbound='true'/></item></items>"""
    def fake_get(url, timeout=30):
        return DummyResponse(xml)
    monkeypatch.setattr(requests, 'get', fake_get)
    gp.fetch_details.cache_clear()
    details = gp.fetch_details(1)
    assert details['weight'] == 2.5
    assert details['version_count'] == 3
    assert details['has_versions']
    assert details['is_expansion']
    assert details['reimplements']

def test_fetch_details_different_outputs(monkeypatch):
    xml1 = """<items><item id='1' type='boardgame'><statistics><ratings><averageweight value='1.0'/></ratings></statistics><versions><item id='1'/></versions></item></items>"""
    xml2 = """<items><item id='2' type='boardgameexpansion'><statistics><ratings><averageweight value='4.0'/></ratings></statistics><link type='boardgameimplementation' id='200' inbound='true'/><versions><item id='2'/><item id='3'/></versions><link type='boardgameversion' id='4' inbound='true'/></item></items>"""
    def fake_get(url, timeout=30):
        if 'id=1' in url:
            return DummyResponse(xml1)
        return DummyResponse(xml2)
    monkeypatch.setattr(requests, 'get', fake_get)
    gp.fetch_details.cache_clear()
    d1 = gp.fetch_details(1)
    d2 = gp.fetch_details(2)
    for key in ['weight','version_count','is_expansion','reimplements','has_versions']:
        assert d1[key] != d2[key]

def test_complexity_status():
    assert gp.complexity_status(1.5) == ("🟢", "Light")
    assert gp.complexity_status(2.5) == ("🟡", "Medium")
    assert gp.complexity_status(3.5) == ("🟠", "Complicated")
    assert gp.complexity_status(4.5) == ("🔴", "Hardcore")
