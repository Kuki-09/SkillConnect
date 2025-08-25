import os
import json
import numpy as np
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import difflib

from utils.entity_extractor import (
    normalize_keywords,
    extract_skills_from_resume,
    extract_skills_from_opportunity
)

model = SentenceTransformer("all-MiniLM-L6-v2", device="cpu")

def embed_list(items: List[str]) -> List[np.ndarray]:
    return [model.encode([item], convert_to_numpy=True)[0] for item in items]

def cosine_similarity(vec1, vec2) -> float:
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

def aggregate_similarity(list1: List[np.ndarray], list2: List[np.ndarray]) -> float:
    if not list1 or not list2:
        return 0.0
    sims = [cosine_similarity(a, b) for a in list1 for b in list2]
    return max(sims) if sims else 0.0

def fuzzy_match_skills(stu_skills: List[str], opp_skills: List[str], threshold: float = 0.8) -> List[str]:
    matches = []
    for skill in stu_skills:
        match = difflib.get_close_matches(skill, opp_skills, n=1, cutoff=threshold)
        if match:
            matches.append(match[0])
    return matches

def certification_similarity(student_certs: List[str], opp_certs: List[str], opp_skills: List[str]) -> float:
    if not opp_certs:
        matched = [c for c in student_certs if any(k.lower() in c.lower() for k in opp_skills)]
        return 1.0 if matched else 0.5
    return aggregate_similarity(embed_list(student_certs), embed_list(opp_certs))

def compute_match_score(student_json: dict, opp_json: dict) -> Dict[str, float]:
    stu_skills = student_json.get("extracted_skills", [])
    opp_skills = opp_json.get("extracted_skills", [])

    stu_set = set(map(str.lower, stu_skills))
    opp_set = set(map(str.lower, opp_skills))

    exact_matches = stu_set & opp_set
    fuzzy_matches = set(fuzzy_match_skills(stu_skills, opp_skills))

    overlap_score = len(exact_matches) / max(len(opp_skills), 1)
    fuzzy_score = len(fuzzy_matches) / max(len(opp_skills), 1)

    stu_certs = student_json.get("certifications", [])
    opp_certs = opp_json.get("mandatory_certifications", [])
    cert_score = certification_similarity(stu_certs, opp_certs, opp_skills)

    final_score = (
        0.6 * overlap_score +
        0.3 * fuzzy_score +
        0.1 * cert_score
    )

    return {
        "overlap_score": round(overlap_score, 3),
        "fuzzy_score": round(fuzzy_score, 3),
        "cert_score": round(cert_score, 3),
        "final_score": round(min(final_score, 1.0), 3)
    }

def find_best_matches(student_json_path: str, opportunity_dir: str, threshold: float = 0.60) -> List[Dict[str, any]]:
    with open(student_json_path, "r") as f:
        student_json = json.load(f)

    matches = []
    for filename in os.listdir(opportunity_dir):
        if filename.endswith(".json"):
            with open(os.path.join(opportunity_dir, filename), "r") as f:
                opp_json = json.load(f)
             
            resume_skills = normalize_keywords(extract_skills_from_resume(student_json))
            opp_skills = normalize_keywords(extract_skills_from_opportunity(opp_json))

            student_json["extracted_skills"] = resume_skills
            opp_json["extracted_skills"] = opp_skills
            
            match_result = compute_match_score(student_json, opp_json)
            final_score = match_result["final_score"]

            if final_score >= threshold:
                matches.append({
                    "file": filename,
                    "score": final_score,
                    "reason": f"Your profile matches {int(final_score * 100)}% with this opportunity.",
                    "details": match_result
                })
                
    return sorted(matches, key=lambda x: x["score"], reverse=True)
