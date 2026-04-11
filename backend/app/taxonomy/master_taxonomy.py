"""Master testing taxonomy – 28 categories aligned with OWASP LLM Top 10 & MITRE ATLAS."""

from dataclasses import dataclass


@dataclass
class TaxonomyEntry:
    id: str
    name: str
    category: str  # security, functional, privacy, robustness, usability, compliance
    description: str
    owasp_mapping: str | None = None
    mitre_atlas_id: str | None = None
    team: str = "both"  # user_centric, adversarial, both


MASTER_TAXONOMY: list[TaxonomyEntry] = [
    # ── Security (Adversarial) ──────────────────────────────────────
    TaxonomyEntry(
        id="A01", name="Direct Prompt Injection",
        category="security",
        description="Attacker directly injects instructions to override system behavior",
        owasp_mapping="LLM01", mitre_atlas_id="AML.T0051",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A02", name="Indirect Prompt Injection",
        category="security",
        description="Malicious instructions hidden in retrieved documents or external data",
        owasp_mapping="LLM01", mitre_atlas_id="AML.T0051.001",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A03", name="System Prompt Leakage",
        category="security",
        description="Extracting the system prompt to understand and bypass guardrails",
        owasp_mapping="LLM07",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A04", name="PII / Data Exfiltration",
        category="privacy",
        description="Extracting personal information, API keys, or training data",
        owasp_mapping="LLM02",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A05", name="Jailbreak / Role Hijacking",
        category="security",
        description="Bypassing safety filters via role-play, DAN, or developer mode exploits",
        owasp_mapping="LLM01",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A06", name="Output Weaponization",
        category="security",
        description="Generating XSS, SQL injection, or malicious code via LLM output",
        owasp_mapping="LLM05",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A07", name="Excessive Agency Exploit",
        category="security",
        description="Tricking agents into unauthorized tool calls, file access, or API actions",
        owasp_mapping="LLM06", mitre_atlas_id="AML.T0040",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A08", name="Multi-Turn Manipulation",
        category="security",
        description="Building trust across conversation turns before launching attack",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A09", name="Payload Splitting",
        category="security",
        description="Distributing attack payload across multiple messages to evade detection",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A10", name="Context Window Overflow",
        category="security",
        description="Flooding context to push safety instructions out of active memory",
        owasp_mapping="LLM10",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A11", name="Few-Shot Poisoning",
        category="security",
        description="Providing manipulative examples to shift model behavior",
        owasp_mapping="LLM04",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A12", name="Encoding Evasion",
        category="security",
        description="Bypassing content filters via Base64, ROT13, Unicode, or homoglyph tricks",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A13", name="Authority Impersonation",
        category="security",
        description="Claiming admin/developer privileges to override restrictions",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A14", name="Cross-Agent Chaining",
        category="security",
        description="Exploiting one agent to attack another in multi-agent systems",
        owasp_mapping="LLM06",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A15", name="Supply Chain Manipulation",
        category="security",
        description="Poisoning tool/plugin responses or model dependencies",
        owasp_mapping="LLM03",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A16", name="Hallucination Exploitation",
        category="robustness",
        description="Triggering confident misinformation or fabricated references",
        owasp_mapping="LLM09",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A17", name="Embedding / Vector Manipulation",
        category="security",
        description="Crafting inputs to manipulate similarity search and retrieval",
        owasp_mapping="LLM08",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A18", name="Resource Exhaustion (DoS)",
        category="security",
        description="Recursive loops, token flooding, or infinite generation attacks",
        owasp_mapping="LLM10",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A19", name="Social Engineering",
        category="security",
        description="Emotional manipulation, urgency, or sympathy to bypass guardrails",
        team="adversarial",
    ),
    TaxonomyEntry(
        id="A20", name="Compliance Violation Trigger",
        category="compliance",
        description="Tricking system into violating GDPR, HIPAA, or other regulations",
        team="adversarial",
    ),
    # ── User-Centric (Edge Cases) ──────────────────────────────────
    TaxonomyEntry(
        id="U01", name="Ambiguous Query",
        category="usability",
        description="User sends vague or under-specified requests",
        team="user_centric",
    ),
    TaxonomyEntry(
        id="U02", name="Typo / Malformed Input",
        category="robustness",
        description="Input with spelling errors, grammar issues, or garbled text",
        team="user_centric",
    ),
    TaxonomyEntry(
        id="U03", name="Long / Complex Input",
        category="robustness",
        description="Extremely long messages, multi-paragraph instructions, or nested requests",
        team="user_centric",
    ),
    TaxonomyEntry(
        id="U04", name="Contradictory Instructions",
        category="robustness",
        description="User gives conflicting requirements in the same or successive messages",
        team="user_centric",
    ),
    TaxonomyEntry(
        id="U05", name="Accessibility Edge Case",
        category="usability",
        description="Users with screen readers, low vision, cognitive load, or language barriers",
        team="user_centric",
    ),
    TaxonomyEntry(
        id="U06", name="Domain Confusion",
        category="usability",
        description="User misunderstands what the system can do, asks off-topic questions",
        team="user_centric",
    ),
    TaxonomyEntry(
        id="U07", name="Copy-Paste Artifacts",
        category="robustness",
        description="Input containing formatting artifacts, hidden characters, or HTML tags",
        team="user_centric",
    ),
    TaxonomyEntry(
        id="U08", name="Multi-Language Input",
        category="robustness",
        description="User mixes languages or uses non-English text the system may not handle",
        team="user_centric",
    ),
]


# Quick lookup helpers
TAXONOMY_BY_ID = {t.id: t for t in MASTER_TAXONOMY}
ADVERSARIAL_TYPES = [t for t in MASTER_TAXONOMY if t.team in ("adversarial", "both")]
USER_TYPES = [t for t in MASTER_TAXONOMY if t.team in ("user_centric", "both")]
ALL_IDS = [t.id for t in MASTER_TAXONOMY]
