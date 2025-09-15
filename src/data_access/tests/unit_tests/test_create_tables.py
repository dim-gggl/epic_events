import pytest

import src.data_access.create_tables as ct


def test_database_has_any_data_false(monkeypatch):
    class Insp:
        def get_table_names(self):
            return []
    monkeypatch.setattr(ct, "inspect", lambda *a, **k: Insp())
    assert ct._database_has_any_data() is False


