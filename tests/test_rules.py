"""Tests for Lantern git-backed RuleStore."""

import os
import shutil
import subprocess
import tempfile
import pytest

from lantern.config import Settings
from lantern.rules import RuleStore


@pytest.fixture
def temp_repo():
    """Create a temporary git repo for rule testing."""
    tmpdir = tempfile.mkdtemp()
    subprocess.run(["git", "init"], cwd=tmpdir, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "TestUser"], cwd=tmpdir, check=True)
    subprocess.run(["git", "config", "user.email", "test@lantern.local"], cwd=tmpdir, check=True)

    lessons_dir = os.path.join(tmpdir, "lessons")
    settings = Settings(
        lessons_dir=lessons_dir,
        approver_ids=["approver_alice"],
        rule_token_cap=1000,
    )
    store = RuleStore(settings)
    yield store, tmpdir
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_rule_propose_approve_and_forget(temp_repo):
    store, tmpdir = temp_repo

    # Propose
    p = store.propose("Always prefix commits with phase number")
    assert p.id == "R-001"
    assert p.status == "proposed"

    # Unauthorized approve should fail
    with pytest.raises(PermissionError):
        store.approve("R-001", approver_id="unauthorized_bob")

    # Authorized approve
    approved = store.approve("R-001", approver_id="approver_alice")
    assert approved.status == "approved"
    assert approved.commit_hash != ""

    # Check active rules
    active = store.active()
    assert len(active) == 1
    assert active[0].id == "R-001"

    # Rules in prompt format
    prompt_text = store.rules_for_prompt()
    assert "<LEARNED_RULES>" in prompt_text
    assert "R-001" in prompt_text

    # Forget (git revert)
    store.forget("R-001", approver_id="approver_alice")
    active_after = store.active()
    assert len(active_after) == 0


def test_rule_sanitization(temp_repo):
    store, _ = temp_repo
    with pytest.raises(ValueError, match="forbidden pattern"):
        store.propose("Visit https://malicious-site.com/exploit")
