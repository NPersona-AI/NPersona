"""Persona scoring – novelty, coverage impact, and composite scoring."""
import logging
from app.taxonomy.master_taxonomy import TAXONOMY_BY_ID

logger = logging.getLogger(__name__)

# Risk severity → numeric score mapping
RISK_SCORES = {
    "critical": 1.0,
    "high": 0.75,
    "medium": 0.5,
    "low": 0.25,
}

SKILL_SCORES = {
    "nation_state": 1.0,
    "expert": 0.75,
    "intermediate": 0.5,
    "script_kiddie": 0.25,
}


def score_personas(personas: list[dict]) -> list[dict]:
    """Score each persona for novelty, coverage impact, and overall composite score."""

    # Track which taxonomy IDs have been seen (for coverage impact)
    seen_taxonomy_ids: set[str] = set()

    # Track unique characteristics for novelty
    seen_characteristics: list[set[str]] = []

    for persona in personas:
        team = persona.get("team", "")

        # ── Risk Score ──────────────────────────────────────
        if team == "adversarial":
            risk_severity = persona.get("risk_severity", "medium")
            risk_score = RISK_SCORES.get(risk_severity, 0.5)
            skill_bonus = SKILL_SCORES.get(persona.get("skill_level", "intermediate"), 0.5) * 0.2
            risk_score = min(1.0, risk_score + skill_bonus)
        else:
            frustration = persona.get("frustration_level", 5) or 5
            risk_score = min(1.0, frustration / 10.0)

        # ── Coverage Impact ─────────────────────────────────
        persona_taxa = set()
        if team == "adversarial":
            persona_taxa = set(persona.get("attack_taxonomy_ids", []))
        else:
            tid = persona.get("edge_case_taxonomy_id", "")
            if tid:
                persona_taxa = {tid}

        new_taxa = persona_taxa - seen_taxonomy_ids
        coverage_impact = len(new_taxa) / max(len(persona_taxa), 1) if persona_taxa else 0.0
        seen_taxonomy_ids.update(persona_taxa)

        # ── Novelty Score ───────────────────────────────────
        # Compare characteristics with previously seen personas
        char_set = _extract_characteristics(persona)
        max_overlap = 0.0
        for prev_chars in seen_characteristics:
            if prev_chars:
                overlap = len(char_set & prev_chars) / max(len(char_set | prev_chars), 1)
                max_overlap = max(max_overlap, overlap)

        novelty_score = 1.0 - max_overlap
        seen_characteristics.append(char_set)

        # ── Composite Score ─────────────────────────────────
        composite = (
            risk_score * 0.35 +
            coverage_impact * 0.35 +
            novelty_score * 0.30
        )

        persona["risk_score"] = round(risk_score * 100, 1)
        persona["coverage_impact"] = round(coverage_impact * 100, 1)
        persona["novelty_score"] = round(novelty_score * 100, 1)
        persona["composite_score"] = round(composite * 100, 1)

    # Sort by composite score descending
    personas.sort(key=lambda p: p.get("composite_score", 0), reverse=True)

    return personas


def _extract_characteristics(persona: dict) -> set[str]:
    """Extract a set of characteristic tokens from a persona for similarity comparison."""
    chars = set()

    # Add taxonomy IDs
    for tid in persona.get("attack_taxonomy_ids", []):
        chars.add(f"tax:{tid}")
    if persona.get("edge_case_taxonomy_id"):
        chars.add(f"tax:{persona['edge_case_taxonomy_id']}")

    # Add target info
    if persona.get("target_agent"):
        chars.add(f"target:{persona['target_agent']}")
    if persona.get("target_data"):
        chars.add(f"data:{persona['target_data']}")

    # Add skill/literacy
    if persona.get("skill_level"):
        chars.add(f"skill:{persona['skill_level']}")
    if persona.get("tech_literacy"):
        chars.add(f"tech:{persona['tech_literacy']}")

    # Add strategy
    if persona.get("attack_strategy"):
        chars.add(f"strat:{persona['attack_strategy']}")

    # Add evasion techniques
    for tech in persona.get("evasion_techniques", []):
        chars.add(f"evasion:{tech}")

    # Add motivation
    if persona.get("motivation"):
        chars.add(f"motive:{persona['motivation'][:30]}")

    return chars
