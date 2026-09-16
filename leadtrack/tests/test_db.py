import os
import tempfile
import importlib
from pathlib import Path

import pytest


@pytest.fixture
def db_module(monkeypatch):
    """Use a fresh temp DB per test instead of ~/.leadtrack."""
    tmpdir = tempfile.mkdtemp()
    from leadtrack import db as db_mod
    importlib.reload(db_mod)
    monkeypatch.setattr(db_mod, "DB_DIR", Path(tmpdir))
    monkeypatch.setattr(db_mod, "DB_PATH", Path(tmpdir) / "leads.db")
    db_mod.init_db()
    return db_mod


def test_add_and_get_lead(db_module):
    lead_id = db_module.add_lead("Jane Doe", company="Acme Corp", email="jane@acme.com")
    lead = db_module.get_lead(lead_id)
    assert lead["name"] == "Jane Doe"
    assert lead["company"] == "Acme Corp"
    assert lead["stage"] == "new"


def test_invalid_stage_raises(db_module):
    with pytest.raises(ValueError):
        db_module.add_lead("Bad Stage", stage="not_a_stage")


def test_list_leads_filter_by_stage(db_module):
    db_module.add_lead("Lead A", stage="new")
    db_module.add_lead("Lead B", stage="won")
    won = db_module.list_leads(stage="won")
    assert len(won) == 1
    assert won[0]["name"] == "Lead B"


def test_list_leads_search(db_module):
    db_module.add_lead("Rahul Sharma", company="Gemius")
    db_module.add_lead("Priya Nair", company="Cinematize")
    results = db_module.list_leads(search="Gemius")
    assert len(results) == 1
    assert results[0]["name"] == "Rahul Sharma"


def test_update_lead_stage(db_module):
    lead_id = db_module.add_lead("Test Lead")
    db_module.update_lead(lead_id, stage="meeting")
    lead = db_module.get_lead(lead_id)
    assert lead["stage"] == "meeting"


def test_delete_lead(db_module):
    lead_id = db_module.add_lead("To Delete")
    db_module.delete_lead(lead_id)
    assert db_module.get_lead(lead_id) is None


def test_notes(db_module):
    lead_id = db_module.add_lead("Noted Lead")
    db_module.add_note(lead_id, "Had a great call, interested in Q3.")
    notes = db_module.get_notes(lead_id)
    assert len(notes) == 1
    assert "great call" in notes[0]["note"]


def test_followups_due(db_module):
    lead_id = db_module.add_lead("Followup Lead")
    db_module.update_lead(lead_id, followup_date="2020-01-01")
    due = db_module.get_followups_due("2099-01-01")
    assert len(due) == 1
    assert due[0]["id"] == lead_id


def test_stats(db_module):
    db_module.add_lead("A", stage="new")
    db_module.add_lead("B", stage="won")
    db_module.add_lead("C", stage="won")
    s = db_module.stats()
    assert s["total"] == 3
    assert s["by_stage"]["won"] == 2
