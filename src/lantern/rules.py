"""Lantern – git-backed teachable rules (Phase 4).

Rules are stored in lessons/RULES.md, one rule per git commit.
Approvers identified by Mattermost user ID (from config allow-list).
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import subprocess
import threading
from pathlib import Path

from lantern.config import Settings
from lantern.log import get_logger
from lantern.models import Rule

log = get_logger("rules")

_RULE_ID_RE = re.compile(r"^R-(\d+)$")


class RuleStore:
    """Git-backed rule storage with approve/reject/forget workflow."""

    def __init__(self, settings: Settings) -> None:
        self._dir = Path(settings.lessons_dir)
        self._file = self._dir / "RULES.md"
        self._approver_ids = set(settings.approver_ids)
        self._token_cap = settings.rule_token_cap
        self._lock = threading.Lock()
        self._proposals: dict[str, Rule] = {}
        self._next_id = 1
        self._ensure_file()
        self._load_existing_ids()

    def _ensure_file(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        if not self._file.exists():
            self._file.write_text(
                "# Lantern learned rules\n\n"
                "| ID | Rule | Scope | Approver | Date |\n"
                "|---|---|---|---|---|\n",
                encoding="utf-8",
            )
            self._git("add", str(self._file))
            self._git("commit", "-m", "Initialize RULES.md", "--allow-empty")

    def _load_existing_ids(self) -> None:
        """Scan RULES.md for existing rule IDs to set _next_id."""
        if not self._file.exists():
            return
        content = self._file.read_text(encoding="utf-8")
        ids = [int(m.group(1)) for m in _RULE_ID_RE.finditer(content) if m]
        if ids:
            self._next_id = max(ids) + 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def propose(self, text: str, source: str = "") -> Rule:
        """Create a new rule proposal. Returns the rule with a fresh ID."""
        text = self._sanitize(text)
        if not text:
            raise ValueError("Rule text is empty after sanitization")

        # Near-duplicate check
        for rule in self._proposals.values():
            if rule.text.lower().strip() == text.lower().strip():
                raise ValueError(f"Duplicate of existing proposal {rule.id}")
        for rule in self.active():
            if rule.text.lower().strip() == text.lower().strip():
                raise ValueError(f"Duplicate of active rule {rule.id}")

        rule_id = f"R-{self._next_id:03d}"
        self._next_id += 1
        rule = Rule(
            id=rule_id,
            text=text,
            source_link=source,
            date=_dt.date.today().isoformat(),
            status="proposed",
        )
        with self._lock:
            self._proposals[rule_id] = rule
        log.info("Rule proposed: %s – %s", rule_id, text[:80])
        return rule

    def approve(self, rule_id: str, approver_id: str) -> Rule:
        """Approve a proposed rule. Only allowed for configured approvers."""
        if not self.is_approver(approver_id):
            raise PermissionError(f"User {approver_id} is not an approver")

        with self._lock:
            rule = self._proposals.pop(rule_id, None)
            if not rule:
                raise KeyError(f"No pending proposal with id {rule_id}")

            rule.approver = approver_id
            rule.status = "approved"

            # Check token cap
            current_rules = self.active()
            total_chars = sum(len(r.text) for r in current_rules) + len(rule.text)
            if total_chars > self._token_cap:
                self._proposals[rule_id] = rule  # put it back
                rule.status = "proposed"
                raise ValueError(
                    f"Adding this rule would exceed the {self._token_cap}-char cap "
                    f"({total_chars} chars). Remove old rules first."
                )

            # Append to RULES.md
            line = f"| {rule.id} | {rule.text} | {rule.scope} | {rule.approver} | {rule.date} |\n"
            with open(self._file, "a", encoding="utf-8") as f:
                f.write(line)

            # Git commit
            commit_msg = f"rule: approve {rule.id} – {rule.text[:60]}"
            self._git("add", str(self._file))
            self._git("commit", "-m", commit_msg)

            # Store the commit hash
            rule.commit_hash = self._git_output("rev-parse", "HEAD").strip()

        log.info("Rule approved: %s by %s", rule_id, approver_id)
        return rule

    def reject(self, rule_id: str, approver_id: str) -> None:
        """Reject a proposed rule."""
        if not self.is_approver(approver_id):
            raise PermissionError(f"User {approver_id} is not an approver")
        with self._lock:
            rule = self._proposals.pop(rule_id, None)
            if not rule:
                raise KeyError(f"No pending proposal with id {rule_id}")
        log.info("Rule rejected: %s by %s", rule_id, approver_id)

    def forget(self, rule_id: str, approver_id: str) -> None:
        """Revert a previously approved rule via git revert."""
        if not self.is_approver(approver_id):
            raise PermissionError(f"User {approver_id} is not an approver")

        # Find the commit hash for this rule
        commit_hash = self._find_rule_commit(rule_id)
        if not commit_hash:
            raise KeyError(f"Cannot find commit for rule {rule_id}")

        with self._lock:
            self._git("revert", "--no-edit", commit_hash)
        log.info("Rule forgotten: %s (reverted %s)", rule_id, commit_hash[:8])

    def active(self, scope: str = "global") -> list[Rule]:
        """Return all active (approved, not forgotten) rules."""
        if not self._file.exists():
            return []
        content = self._file.read_text(encoding="utf-8")
        rules = []
        for line in content.split("\n"):
            line = line.strip()
            if not line.startswith("|") or line.startswith("| ID") or line.startswith("|---"):
                continue
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 5:
                rules.append(Rule(
                    id=parts[0],
                    text=parts[1],
                    scope=parts[2],
                    approver=parts[3],
                    date=parts[4],
                    status="approved",
                ))
        return rules

    def pending(self) -> list[Rule]:
        """Return all pending proposals."""
        return list(self._proposals.values())

    def is_approver(self, user_id: str) -> bool:
        """Check if a user is in the approver allow-list.

        If no approvers are configured, everyone is an approver (dev mode).
        """
        if not self._approver_ids:
            return True
        return user_id in self._approver_ids

    def rules_for_prompt(self) -> str:
        """Format active rules for injection into the system prompt."""
        rules = self.active()
        if not rules:
            return ""
        lines = ["<LEARNED_RULES>"]
        for r in rules:
            lines.append(f"- [{r.id}] {r.text}")
        lines.append("</LEARNED_RULES>")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _sanitize(self, text: str) -> str:
        """Remove dangerous patterns from rule text."""
        text = text.strip()
        if len(text) > 200:
            text = text[:200]
        # Reject rules that look like URLs or tool invocations
        for pattern in ["http://", "https://", "```", "exec(", "os.system", "subprocess"]:
            if pattern.lower() in text.lower():
                raise ValueError(f"Rule text contains forbidden pattern: {pattern}")
        return text

    def _find_rule_commit(self, rule_id: str) -> str | None:
        """Find the git commit that approved a specific rule."""
        try:
            output = self._git_output(
                "log", "--oneline", "--all", "--grep", f"rule: approve {rule_id}"
            )
            for line in output.strip().split("\n"):
                if line.strip():
                    return line.split()[0]
        except Exception:
            pass
        return None

    def _git(self, *args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=str(self._dir.parent),
            capture_output=True,
            text=True,
            check=True,
        )

    def _git_output(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=str(self._dir.parent),
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
