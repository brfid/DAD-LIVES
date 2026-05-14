import pytest
from server import _x, make_svg, make_html, response_type


def test_escape():
    assert _x("A&B<C>D") == "A&amp;B&lt;C&gt;D"
    assert _x("plain") == "plain"


def test_make_svg():
    svg = make_svg("DAD RULES")
    assert "DAD RULES" in svg
    assert "viewBox='0 0 600 100'" in svg
    assert "font-weight='900'" in svg
    assert "letter-spacing='4'" in svg


def test_make_svg_escapes():
    svg = make_svg("A&B")
    assert "&amp;" in svg
    assert "A&B" not in svg


def test_make_html():
    html = make_html("DAD RULES")
    assert "DAD RULES" in html
    assert "<!DOCTYPE html>" in html
    assert "Impact" in html


def test_make_html_escapes():
    html = make_html("<script>")
    assert "&lt;script&gt;" in html
    assert "<script>" not in html


@pytest.mark.parametrize("accept,path,expected", [
    ("image/png, */*", "", "svg"),
    ("*/*", "banner.jpg", "svg"),
    ("*/*", "ad.svg", "svg"),
    ("application/javascript, */*", "", "js"),
    ("*/*", "track.js", "js"),
    ("text/html, */*", "", "html"),
    ("*/*", "iframe", "html"),
])
def test_response_type(accept, path, expected):
    assert response_type(accept, path) == expected
