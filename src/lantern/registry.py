"""Lantern – Central registry for extensions and add-ons."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lantern.interfaces import CommandHandler, Postprocessor

# Registry lists for add-ons
COMMAND_HANDLERS: list[type[CommandHandler]] = []
POSTPROCESSORS: list[type[Postprocessor]] = []


def register_command(handler_cls: type[CommandHandler]) -> type[CommandHandler]:
    """Decorator or function to register a CommandHandler."""
    if handler_cls not in COMMAND_HANDLERS:
        COMMAND_HANDLERS.append(handler_cls)
    return handler_cls


def register_postprocessor(postproc_cls: type[Postprocessor]) -> type[Postprocessor]:
    """Decorator or function to register a Postprocessor."""
    if postproc_cls not in POSTPROCESSORS:
        POSTPROCESSORS.append(postproc_cls)
    return postproc_cls


# ---------------------------------------------------------------------------
# Default built-in add-ons registered here
# ---------------------------------------------------------------------------
from lantern.addons.ping_cmd import PingCommandHandler
from lantern.addons.status_cmd import StatusCommandHandler
from lantern.addons.rule_cmds import RulesCommandHandler
from lantern.postprocessors import (
    ProvenancePostprocessor,
    RiskCautionPostprocessor,
    VerifyQueuePostprocessor,
)

register_command(PingCommandHandler)
register_command(StatusCommandHandler)
register_command(RulesCommandHandler)

register_postprocessor(RiskCautionPostprocessor)
register_postprocessor(ProvenancePostprocessor)
register_postprocessor(VerifyQueuePostprocessor)
