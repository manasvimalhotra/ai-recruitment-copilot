from typing import Optional
 
LEVELS = ["none", "basic", "intermediate", "advanced"]
LEVEL_INDEX = {lvl: i for i, lvl in enumerate(LEVELS)}
 
 
def _approximate_candidate_level(total_experience_years: Optional[float]) -> str:
    """Rough proxy for proficiency, used only when a candidate has the skill at all."""
    years = total_experience_years or 0
    if years >= 3:
        return "advanced"
    if years >= 1:
        return "intermediate"
    return "basic"
 
 
def _skill_status(candidate_skills: list, skill: str, candidate_level: str) -> dict:
    """
    Compares a single required skill against the candidate's skill list.
    Returns the candidate's approximate level for that skill ("none" if
    they don't have it) plus a 0-100 bar percentage for the UI.
    """
    has_skill = skill.lower() in [s.lower() for s in candidate_skills]
    level = candidate_level if has_skill else "none"
    percent = round((LEVEL_INDEX[level] / (len(LEVELS) - 1)) * 100)
    return {"level": level, "percent": percent}
 
 
def calculate_match(candidate, job) -> dict:
    """
    Computes an overall match score (0-100) between a candidate and a job.
 
    Score = 70% skill coverage (how many required skills the candidate has,
    weighted slightly by whether they meet the required level) + 30%
    experience fit (candidate years vs. the job's minimum, capped at 100%
    once the minimum is met -- more experience than required doesn't
    inflate the score further).
    """
    required = job.get("required_skills", [])
    candidate_skills = candidate.get("skills", [])
    candidate_years = candidate.get("total_experience_years") or 0
    candidate_level = _approximate_candidate_level(candidate_years)
 
    if required:
        skill_scores = []
        for req in required:
            status = _skill_status(candidate_skills, req["skill"], candidate_level)
            required_idx = LEVEL_INDEX.get(req.get("level", "intermediate"), 2)
            candidate_idx = LEVEL_INDEX[status["level"]]
            # Full credit if candidate meets/exceeds the required level,
            # partial credit scaled by how close they are otherwise.
            if candidate_idx >= required_idx:
                skill_scores.append(1.0)
            else:
                skill_scores.append(candidate_idx / max(required_idx, 1))
        skill_coverage = sum(skill_scores) / len(skill_scores)
    else:
        skill_coverage = 1.0  # no requirements specified -> don't penalize
 
    min_years = job.get("min_experience_years")
    if min_years and min_years > 0:
        experience_fit = min(candidate_years / min_years, 1.0)
    else:
        experience_fit = 1.0
 
    overall = (skill_coverage * 0.7 + experience_fit * 0.3) * 100
    return {
        "match_percent": round(overall, 1),
        "skill_coverage_percent": round(skill_coverage * 100, 1),
        "experience_fit_percent": round(experience_fit * 100, 1),
    }
 
 
def analyze_skill_gap(candidate, job) -> dict:
    """
    Per-skill breakdown for the "Skill Gap Analysis" view: for every skill
    the job requires, shows the candidate's approximate level, the required
    level, and a bar percentage -- plus a short templated recommendation.
    """
    required = job.get("required_skills", [])
    candidate_skills = candidate.get("skills", [])
    candidate_years = candidate.get("total_experience_years") or 0
    candidate_level = _approximate_candidate_level(candidate_years)
 
    breakdown = []
    gaps = []
    for req in required:
        status = _skill_status(candidate_skills, req["skill"], candidate_level)
        required_idx = LEVEL_INDEX.get(req.get("level", "intermediate"), 2)
        candidate_idx = LEVEL_INDEX[status["level"]]
        meets_requirement = candidate_idx >= required_idx
        breakdown.append({
            "skill": req["skill"],
            "required_level": req.get("level", "intermediate"),
            "candidate_level": status["level"],
            "percent": status["percent"],
            "meets_requirement": meets_requirement,
        })
        if not meets_requirement:
            gaps.append(req["skill"])
 
    recommendation = _build_recommendation(candidate.get("name"), gaps, breakdown)
 
    return {"skills": breakdown, "gaps": gaps, "recommendation": recommendation}
 
 
def _build_recommendation(name: Optional[str], gaps: list, breakdown: list) -> str:
    """Simple templated recommendation -- no external AI call, stays offline like the rest of Milestone 1."""
    who = name or "This candidate"
    strong = [s["skill"] for s in breakdown if s["meets_requirement"]]
 
    if not gaps:
        return f"{who} meets or exceeds every required skill for this role."
 
    strong_part = (
        f"{who} shows strong fundamentals in {', '.join(strong[:2])} but"
        if strong else f"{who}"
    )
    gap_list = ", ".join(gaps[:3])
    weeks = max(2, len(gaps) * 2)
    return (
        f"{strong_part} needs development in {gap_list}. "
        f"Consider targeted training or certification in {gaps[0]} first. "
        f"Estimated learning time: {weeks - 1}-{weeks} weeks."
    )
 









