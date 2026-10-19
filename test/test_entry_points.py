from types import SimpleNamespace

import marrow.mailer


class FakeEntryPoints:
    def __init__(self, points):
        self.points = points
        self.selection = None

    def select(self, **selection):
        self.selection = selection
        return [
            point
            for point in self.points
            if point.group == selection["group"]
            and point.name == selection["name"]
        ]


def test_load_selects_named_entry_point(monkeypatch):
    expected = object()
    selected = SimpleNamespace(
        group="example.plugins",
        name="selected",
        load=lambda: expected,
    )
    ignored = SimpleNamespace(
        group="example.plugins",
        name="other",
        load=lambda: None,
    )
    points = FakeEntryPoints([selected, ignored])
    monkeypatch.setattr(marrow.mailer, "entry_points", lambda: points)

    assert marrow.mailer.Mailer._load("selected", "example.plugins") is expected
    assert points.selection == {
        "group": "example.plugins",
        "name": "selected",
    }


def test_load_returns_none_when_entry_point_is_missing(monkeypatch):
    points = FakeEntryPoints([])
    monkeypatch.setattr(marrow.mailer, "entry_points", lambda: points)

    assert marrow.mailer.Mailer._load("missing", "example.plugins") is None