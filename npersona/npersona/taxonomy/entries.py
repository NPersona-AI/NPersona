"""Master taxonomy of AI security and usability test categories.

Adversarial: A01–A20 (LLM-specific attack patterns)
User-centric: U01–U08 (edge-case usability failures)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


Team = Literal["adversarial", "user_centric", "both"]
Category = Literal["security", "privacy", "robustness", "usability", "compliance", "functional"]
Risk = Literal["critical", "high", "medium", "low"]


@dataclass(frozen=True)
class TaxonomyEntry:
    id: str
    name: str
    team: Team
    category: Category
    default_risk: Risk
    description: str
    owasp_mapping: str
    mitre_atlas_id: str


TAXONOMY: list[TaxonomyEntry] = [
    # ── Adversarial ──────────────────────────────────────────────────────────
    TaxonomyEntry(
        id="A01",
        name="Direct Prompt Injection",
        team="adversarial",
        category="security",
        default_risk="critical",
        description="Override or hijack system instructions via crafted user input.",
        owasp_mapping="LLM01",
        mitre_atlas_id="AML.T0051",
    ),
    TaxonomyEntry(
        id="A02",
        name="Indirect Prompt Injection",
        team="adversarial",
        category="security",
        default_risk="critical",
        description="Malicious instructions embedded in retrieved documents, tool outputs, or external data sources.",
        owasp_mapping="LLM02",
        mitre_atlas_id="AML.T0052",
    ),
    TaxonomyEntry(
        id="A03",
        name="System Prompt Leakage",
        team="adversarial",
        category="privacy",
        default_risk="high",
        description="Extract hidden system prompt, internal instructions, or configuration parameters.",
        owasp_mapping="LLM07",
        mitre_atlas_id="AML.T0054",
    ),
    TaxonomyEntry(
        id="A04",
        name="PII and Data Exfiltration",
        team="adversarial",
        category="privacy",
        default_risk="critical",
        description="Extract user PII, API keys, conversation history, or training data from the system.",
        owasp_mapping="LLM06",
        mitre_atlas_id="AML.T0048",
    ),
    TaxonomyEntry(
        id="A05",
        name="Jailbreak and Role Hijacking",
        team="adversarial",
        category="security",
        default_risk="high",
        description="Bypass safety guardrails via roleplay, fictional framing, DAN variants, or hypothetical scenarios.",
        owasp_mapping="LLM01",
        mitre_atlas_id="AML.T0054",
    ),
    TaxonomyEntry(
        id="A06",
        name="Output Weaponization",
        team="adversarial",
        category="security",
        default_risk="high",
        description="Generate XSS payloads, SQL injections, malicious scripts, or harmful content through the LLM.",
        owasp_mapping="LLM02",
        mitre_atlas_id="AML.T0043",
    ),
    TaxonomyEntry(
        id="A07",
        name="Excessive Agency Exploit",
        team="adversarial",
        category="security",
        default_risk="critical",
        description="Trick agents into unauthorized tool calls, file writes, API actions, or resource access.",
        owasp_mapping="LLM08",
        mitre_atlas_id="AML.T0047",
    ),
    TaxonomyEntry(
        id="A08",
        name="Multi-Turn Manipulation",
        team="adversarial",
        category="security",
        default_risk="high",
        description="Build false trust or manipulate context across multiple turns before delivering the exploit payload.",
        owasp_mapping="LLM01",
        mitre_atlas_id="AML.T0051",
    ),
    TaxonomyEntry(
        id="A09",
        name="Payload Splitting",
        team="adversarial",
        category="security",
        default_risk="medium",
        description="Split attack payload across multiple turns or hide it in continuation context to evade filters.",
        owasp_mapping="LLM01",
        mitre_atlas_id="AML.T0051",
    ),
    TaxonomyEntry(
        id="A10",
        name="Context Window Overflow",
        team="adversarial",
        category="robustness",
        default_risk="medium",
        description="Flood context to push safety instructions out of the attention window.",
        owasp_mapping="LLM04",
        mitre_atlas_id="AML.T0046",
    ),
    TaxonomyEntry(
        id="A11",
        name="Few-Shot Poisoning",
        team="adversarial",
        category="security",
        default_risk="medium",
        description="Provide manipulative in-context examples to shift model behavior within the session.",
        owasp_mapping="LLM03",
        mitre_atlas_id="AML.T0044",
    ),
    TaxonomyEntry(
        id="A12",
        name="Encoding Evasion",
        team="adversarial",
        category="security",
        default_risk="medium",
        description="Use Base64, ROT13, Unicode homoglyphs, or leetspeak to bypass keyword-based filters.",
        owasp_mapping="LLM01",
        mitre_atlas_id="AML.T0051",
    ),
    TaxonomyEntry(
        id="A13",
        name="Authority Impersonation",
        team="adversarial",
        category="security",
        default_risk="high",
        description="Claim admin, developer, or vendor identity to unlock restricted behaviors.",
        owasp_mapping="LLM01",
        mitre_atlas_id="AML.T0054",
    ),
    TaxonomyEntry(
        id="A14",
        name="Cross-Agent Chaining",
        team="adversarial",
        category="security",
        default_risk="critical",
        description="Exploit one agent to attack another in a multi-agent pipeline via trust propagation.",
        owasp_mapping="LLM08",
        mitre_atlas_id="AML.T0047",
    ),
    TaxonomyEntry(
        id="A15",
        name="Supply Chain Manipulation",
        team="adversarial",
        category="security",
        default_risk="critical",
        description="Poison tool responses, plugin outputs, or RAG retrieval results with adversarial instructions.",
        owasp_mapping="LLM03",
        mitre_atlas_id="AML.T0018",
    ),
    TaxonomyEntry(
        id="A16",
        name="Hallucination Exploitation",
        team="adversarial",
        category="functional",
        default_risk="medium",
        description="Prompt the model to confabulate false but plausible harmful facts, credentials, or instructions.",
        owasp_mapping="LLM09",
        mitre_atlas_id="AML.T0048",
    ),
    TaxonomyEntry(
        id="A17",
        name="Embedding and Vector Manipulation",
        team="adversarial",
        category="security",
        default_risk="high",
        description="Craft inputs that manipulate RAG retrieval results to inject adversarial content.",
        owasp_mapping="LLM02",
        mitre_atlas_id="AML.T0052",
    ),
    TaxonomyEntry(
        id="A18",
        name="Resource Exhaustion",
        team="adversarial",
        category="robustness",
        default_risk="medium",
        description="Trigger recursive loops, infinite generation, or token flooding to degrade availability.",
        owasp_mapping="LLM04",
        mitre_atlas_id="AML.T0046",
    ),
    TaxonomyEntry(
        id="A19",
        name="Social Engineering",
        team="adversarial",
        category="security",
        default_risk="high",
        description="Use emotional manipulation, urgency, sympathy, or authority pressure to bypass guardrails.",
        owasp_mapping="LLM01",
        mitre_atlas_id="AML.T0051",
    ),
    TaxonomyEntry(
        id="A20",
        name="Compliance Violation Trigger",
        team="adversarial",
        category="compliance",
        default_risk="high",
        description="Force GDPR, HIPAA, SOC2, or other compliance violations through output manipulation.",
        owasp_mapping="LLM10",
        mitre_atlas_id="AML.T0048",
    ),
    # ── User-Centric ─────────────────────────────────────────────────────────
    TaxonomyEntry(
        id="U01",
        name="Ambiguous Query",
        team="user_centric",
        category="usability",
        default_risk="low",
        description="Vague intent, missing context, pronoun ambiguity — the system must handle gracefully.",
        owasp_mapping="LLM09",
        mitre_atlas_id="N/A",
    ),
    TaxonomyEntry(
        id="U02",
        name="Typo and Malformed Input",
        team="user_centric",
        category="robustness",
        default_risk="low",
        description="Misspellings, autocorrect corruption, swapped characters, missing spaces.",
        owasp_mapping="LLM09",
        mitre_atlas_id="N/A",
    ),
    TaxonomyEntry(
        id="U03",
        name="Long and Complex Input",
        team="user_centric",
        category="robustness",
        default_risk="medium",
        description="Multi-paragraph pastes, nested conditions, 500+ word requests that stress context handling.",
        owasp_mapping="LLM04",
        mitre_atlas_id="N/A",
    ),
    TaxonomyEntry(
        id="U04",
        name="Contradictory Instructions",
        team="user_centric",
        category="usability",
        default_risk="low",
        description="Conflicting constraints in one message — 'make it short but include everything'.",
        owasp_mapping="LLM09",
        mitre_atlas_id="N/A",
    ),
    TaxonomyEntry(
        id="U05",
        name="Accessibility Edge Case",
        team="user_centric",
        category="usability",
        default_risk="low",
        description="Screen reader navigation artifacts, high-contrast mode, cognitive load patterns, motor impairment.",
        owasp_mapping="N/A",
        mitre_atlas_id="N/A",
    ),
    TaxonomyEntry(
        id="U06",
        name="Domain Confusion",
        team="user_centric",
        category="functional",
        default_risk="medium",
        description="Asking the system to do something adjacent to but outside its actual capabilities.",
        owasp_mapping="LLM09",
        mitre_atlas_id="N/A",
    ),
    TaxonomyEntry(
        id="U07",
        name="Copy-Paste Artifacts",
        team="user_centric",
        category="robustness",
        default_risk="low",
        description="Excel tab-delimited data, HTML tags from Outlook, formula strings, zero-width characters.",
        owasp_mapping="LLM09",
        mitre_atlas_id="N/A",
    ),
    TaxonomyEntry(
        id="U08",
        name="Multi-Language Input",
        team="user_centric",
        category="usability",
        default_risk="low",
        description="Mid-sentence language switching, transliteration, non-Latin scripts, mixed encodings.",
        owasp_mapping="LLM09",
        mitre_atlas_id="N/A",
    ),
]

TAXONOMY_BY_ID: dict[str, TaxonomyEntry] = {entry.id: entry for entry in TAXONOMY}
ADVERSARIAL_TAXONOMY: list[TaxonomyEntry] = [e for e in TAXONOMY if e.team in ("adversarial", "both")]
USER_TAXONOMY: list[TaxonomyEntry] = [e for e in TAXONOMY if e.team in ("user_centric", "both")]
