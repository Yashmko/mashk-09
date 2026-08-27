from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SyntheticAction = Literal["catalogue", "probe", "replay", "session", "correlate", "watch", "detect", "contain", "patch"]


@dataclass(frozen=True)
class AgentDecision:
    agent: Literal["red", "blue"]
    action: SyntheticAction
    rationale: str


class ConstrainedPolicy:
    """Safe policy boundary: return labels only, never executable commands.

    This interface is intentionally small so a future local model adapter can be
    validated against an allowlist before the simulator applies any state change.
    """

    allowed_red: tuple[SyntheticAction, ...] = ("catalogue", "probe", "replay", "session", "correlate")
    allowed_blue: tuple[SyntheticAction, ...] = ("watch", "detect", "contain", "patch")

    def validate(self, decision: AgentDecision) -> AgentDecision:
        allowed = self.allowed_red if decision.agent == "red" else self.allowed_blue
        if decision.action not in allowed:
            raise ValueError(f"Action {decision.action!r} is not allowed for {decision.agent} policy")
        return decision
