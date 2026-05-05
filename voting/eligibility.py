"""
voting/eligibility.py — email suffix → race eligibility + candidate/race seeder.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger("voting")

BASE_DIR = Path(__file__).resolve().parent.parent
CANDIDATES_DIR = BASE_DIR / "candidates"

SUFFIX_RACE_MAP: list[tuple[str, list[str]]] = [
    ("_ug2023@ashoka.edu.in", ["president", "gensec", "council_4th_year"]),
    ("_ug2024@ashoka.edu.in", ["president", "gensec", "council_3rd_year"]),
    ("_ug2025@ashoka.edu.in", ["president", "gensec", "council_2nd_year"]),
    ("_ug25@ashoka.edu.in", ["president", "gensec", "council_2nd_year", "council_3rd_year", "council_4th_year", "council_masters"]),
    ("_ma2024@ashoka.edu.in", ["president", "gensec", "council_masters"]),
    ("_ma2025@ashoka.edu.in", ["president", "gensec", "council_masters"]),
    ("@ashoka.edu.in",        ["president", "gensec"]),
    
]

CANDIDATE_FILES = [
    "president.json",
    "gensec.json",
    "council_2nd_year.json",
    "council_3rd_year.json",
    "council_4th_year.json",
    "council_masters.json"
]


def get_eligible_race_ids(email: str) -> list[str]:
    email = email.lower().strip()
    for suffix, race_ids in SUFFIX_RACE_MAP:
        if email.endswith(suffix):
            return race_ids
    return []


def load_candidate_file(filename: str) -> dict:
    path = CANDIDATES_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Candidate file not found: {path}")
    with open(path) as f:
        return json.load(f)


def seed_races_and_candidates():
    """Idempotent: create/update Race and Candidate rows from all JSON files."""
    from voting.models import Race, Candidate

    for filename in CANDIDATE_FILES:
        try:
            data = load_candidate_file(filename)
        except FileNotFoundError as e:
            logger.error("seed: %s", e)
            continue

        race, created = Race.objects.update_or_create(
            race_id=data["race_id"],
            defaults={
                "race_name":   data["race_name"],
                "max_votes":   data.get("max_votes", 1),
                "nota_ref_id": data.get("nota_ref_id", 999),
            },
        )
        if created:
            logger.info("Created race: %s (max_votes=%d)", race.race_name, race.max_votes)

        for c in data["candidates"]:
            _, created = Candidate.objects.update_or_create(
                race=race,
                candidate_ref_id=c["id"],
                defaults={
                    "name":           c.get("name", ""),
                    "affiliation":    c.get("affiliation", ""),
                    "year":           c.get("year", ""),
                    "bio":            c.get("bio", ""),
                    "manifesto_url":  c.get("manifesto_url", ""),
                    "photo_initials": c.get("photo_initials", ""),
                    "is_nota":        c.get("is_nota", False),
                },
            )
            if created:
                nota_tag = " [NOTA]" if c.get("is_nota") else ""
                logger.info("  Created candidate: %s%s (%s)", c["name"], nota_tag, data["race_name"])

    logger.info("Seeding complete.")