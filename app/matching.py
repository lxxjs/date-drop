"""Matching algorithm module.

This is a placeholder -- the actual algorithm will be implemented later.
The schema and endpoints are ready to receive results from this module.
"""

from app.supabase_client import get_supabase


def compute_compatibility(profile_a: dict, profile_b: dict) -> tuple[float, list[str]]:
    """Compute compatibility score (0-100) and reasons between two profiles.

    TODO: Implement the actual algorithm. Options include:
    - Weighted Euclidean distance across 16 scale dimensions
    - Trait Jaccard similarity (partner_traits vs self_traits)
    - Preference boolean matching (religion, race, relationship goal)
    - Claude API for nuanced analysis
    """
    return 0.0, []


def generate_weekly_matches(match_round: str) -> list[dict]:
    """Generate matches for all opted-in users for the given round.

    TODO: Implement the full pipeline:
    1. Fetch all opted-in profiles
    2. Filter candidates by hard constraints (gender, height, age, grad year)
    3. Score all valid pairs with compute_compatibility()
    4. Apply cupid boost (+5) for nominated pairs
    5. Run 1:1 assignment (Hungarian algorithm or greedy)
    6. Insert matches into the database
    7. Reset is_opted_in for all processed users

    Returns list of created match records.
    """
    sb = get_supabase()

    # Fetch opted-in profiles
    result = sb.table("profiles").select("*").eq("is_opted_in", True).execute()
    opted_in = result.data

    if len(opted_in) < 2:
        return []

    # Placeholder: no matches generated yet
    # When implemented, this will insert into the matches table and return results
    return []
