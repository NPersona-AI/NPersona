"""Coverage analyzer – maps personas to testing taxonomy and identifies gaps."""
import logging
from app.taxonomy.master_taxonomy import MASTER_TAXONOMY, TAXONOMY_BY_ID

logger = logging.getLogger(__name__)


def analyze_coverage(personas: list[dict]) -> list[dict]:
    """Analyze testing coverage based on generated personas.
    
    Returns a list of coverage entries, one per taxonomy type.
    """
    # Build lookup: taxonomy_id → list of persona names covering it
    coverage_map: dict[str, list[str]] = {t.id: [] for t in MASTER_TAXONOMY}

    for persona in personas:
        team = persona.get("team", "")
        name = persona.get("name", "Unknown")

        if team == "adversarial":
            # Check attack_taxonomy_ids
            for tid in persona.get("attack_taxonomy_ids", []):
                if tid in coverage_map:
                    coverage_map[tid].append(name)
        elif team == "user_centric":
            # Check edge_case_taxonomy_id
            tid = persona.get("edge_case_taxonomy_id", "")
            if tid in coverage_map:
                coverage_map[tid].append(name)

    # Build results
    results = []
    for taxonomy in MASTER_TAXONOMY:
        covering_personas = coverage_map.get(taxonomy.id, [])
        if len(covering_personas) == 0:
            status = "missing"
        elif len(covering_personas) == 1:
            status = "partial"
        else:
            status = "covered"

        results.append({
            "taxonomy_id": taxonomy.id,
            "name": taxonomy.name,
            "category": taxonomy.category,
            "description": taxonomy.description,
            "team": taxonomy.team,
            "owasp_mapping": taxonomy.owasp_mapping,
            "status": status,
            "covered_by": covering_personas,
            "coverage_count": len(covering_personas),
        })

    covered = sum(1 for r in results if r["status"] == "covered")
    partial = sum(1 for r in results if r["status"] == "partial")
    missing = sum(1 for r in results if r["status"] == "missing")
    logger.info(f"Coverage: {covered} covered, {partial} partial, {missing} missing / {len(results)} total")

    return results
