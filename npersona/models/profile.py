"""System profile — structured representation of an AI system extracted from documentation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Integration(BaseModel):
    """External system or service the AI integrates with."""

    name: str
    integration_type: str  # database, api, file_system, message_queue, etc.
    data_exchanged: list[str] = Field(default_factory=list)
    bidirectional: bool = False


class Guardrail(BaseModel):
    """A declared safety or access control mechanism."""

    name: str
    description: str
    guardrail_type: str  # input_filter, output_filter, rate_limit, auth, etc.
    protects_agents: list[str] = Field(default_factory=list)
    protects_data: list[str] = Field(default_factory=list)
    known_limitations: str = ""


class Agent(BaseModel):
    """An AI agent, assistant, bot, or autonomous component."""

    id: str
    name: str
    description: str
    capabilities: list[str] = Field(default_factory=list)
    data_accessed: list[str] = Field(default_factory=list)
    connected_agents: list[str] = Field(default_factory=list)  # downstream agents
    tools_available: list[str] = Field(default_factory=list)
    user_facing: bool = True
    guardrails_applied: list[str] = Field(default_factory=list)


class SystemProfile(BaseModel):
    """Structured profile of an AI system, extracted from its documentation."""

    system_name: str = "Unknown System"
    system_description: str = ""
    agents: list[Agent] = Field(default_factory=list)
    sensitive_data: list[str] = Field(default_factory=list)
    guardrails: list[Guardrail] = Field(default_factory=list)
    integrations: list[Integration] = Field(default_factory=list)
    user_roles: list[str] = Field(default_factory=list)

    # Topology flags — used by attack surface mapper
    is_multi_agent: bool = False
    has_rag: bool = False
    has_tool_use: bool = False
    has_code_execution: bool = False
    has_external_api_calls: bool = False

    def to_context_string(self) -> str:
        """Serialize profile to a compact string for inclusion in LLM prompts."""
        lines: list[str] = [f"System: {self.system_name}", f"{self.system_description}", ""]

        if self.agents:
            lines.append("AGENTS:")
            for agent in self.agents:
                caps = ", ".join(agent.capabilities) or "none listed"
                data = ", ".join(agent.data_accessed) or "none listed"
                tools = ", ".join(agent.tools_available) or "none"
                connected = ", ".join(agent.connected_agents) or "none"
                guardrails = ", ".join(agent.guardrails_applied) or "none"
                lines.append(f"  [{agent.id}] {agent.name}: {agent.description}")
                lines.append(f"    Capabilities: {caps}")
                lines.append(f"    Data accessed: {data}")
                lines.append(f"    Tools: {tools}")
                lines.append(f"    Connected to: {connected}")
                lines.append(f"    Guardrails: {guardrails}")

        if self.sensitive_data:
            lines.append(f"\nSENSITIVE DATA: {', '.join(self.sensitive_data)}")

        if self.guardrails:
            lines.append("\nGUARDRAILS:")
            for g in self.guardrails:
                lines.append(f"  {g.name} ({g.guardrail_type}): {g.description}")
                if g.known_limitations:
                    lines.append(f"    Known limitations: {g.known_limitations}")

        if self.integrations:
            lines.append("\nINTEGRATIONS:")
            for i in self.integrations:
                lines.append(f"  {i.name} ({i.integration_type})")

        flags: list[str] = []
        if self.is_multi_agent:
            flags.append("multi-agent")
        if self.has_rag:
            flags.append("RAG")
        if self.has_tool_use:
            flags.append("tool-use")
        if self.has_code_execution:
            flags.append("code-execution")
        if self.has_external_api_calls:
            flags.append("external-api-calls")
        if flags:
            lines.append(f"\nARCHITECTURE FLAGS: {', '.join(flags)}")

        return "\n".join(lines)
