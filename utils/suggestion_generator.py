from langchain_community.llms import Ollama as OllamaLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable
from typing import List, Dict


def build_concise_prompt():
    return PromptTemplate(
        input_variables=[
            "opp_title", "opp_org", "opp_role", "opp_skills", "opp_certs",
            "stu_objective", "stu_skills", "stu_projects", "stu_certs",
            "stu_experience", "stu_education", "score"
        ],
        template="""
You are an AI Career Advisor. Your goal is to help students improve their job prospects with encouraging and actionable advice.
Task: Analyze student's resume, a job/project opportunity, a match score (%) and why the given match score was assigned.

 OPPORTUNITY REQUIREMENTS:
- Title: {opp_title}
- Organization: {opp_org}
- Role: {opp_role}
- Required Skills: {opp_skills}
- Required Certifications: {opp_certs}

 STUDENT PROFILE:
- Objective: {stu_objective}
- Skills: {stu_skills}
- Projects: {stu_projects}
- Certifications: {stu_certs}
- Experience: {stu_experience}
- Education: {stu_education}

MATCH SCORE: {score}%

Instructions:
1. ONLY return a bulleted list of recommendations to bridge these gaps and improve the score. Respond ONLY in following format:
    *The specific skills the student should learn to improve their match score.
    *A link to a relevant GitHub repository (public and working) showcasing a similar project that the student can use for inspiration.
    *A working link to a relevant online course or certification that teaches the missing skill (from Coursera, edX, Udemy, or similar).

Key Rules:
- Use positive and user-friendly tone.
- ONLY return direct and concise **main bullets** with clear actions and real URLs (courses, repos, docs)
- Avoid long descriptions or paragraphs
- Prioritize free, high-quality resources when possible
"""
    )


def generate_suggestions(student_dict: Dict, top_opportunities: List[Dict]):
    try:
        if not top_opportunities:
            return (
                "⚠️ No strong matches found to generate suggestions. "
                "Try enhancing your resume or updating your skills and certifications."
            )

        llm = OllamaLLM(model="llama3.2")
        prompt = build_concise_prompt()
        chain: Runnable = prompt | llm

        all_low_scores = all(opp.get("match_score", 0) < 0.7 for opp in top_opportunities)

        if all_low_scores:
            combined_opp = {
                "title": "Top 3 Opportunities (Generalized)",
                "organization": "Multiple",
                "role": "Various",
                "required_skills": list({
                    skill for opp in top_opportunities for skill in opp.get("required_skills", [])
                }),
                "mandatory_certifications": list({
                    cert for opp in top_opportunities for cert in opp.get("mandatory_certifications", [])
                })
            }
            score = max((opp.get("match_score", 0) for opp in top_opportunities), default=0.0)
            return run_chain(chain, student_dict, combined_opp, score)

        else:
            best = max(top_opportunities, key=lambda o: o.get("match_score", 0))
            return run_chain(chain, student_dict, best, best.get("match_score", 0))

    except Exception as e:
        return f"⚠️ Error generating suggestions: {e}"


def run_chain(chain: Runnable, student_dict: Dict, opportunity_dict: Dict, match_score: float):
    inputs = {
        "opp_title": opportunity_dict.get("title", "N/A"),
        "opp_org": opportunity_dict.get("organization", "N/A"),
        "opp_role": opportunity_dict.get("role", "N/A"),
        "opp_skills": ", ".join(opportunity_dict.get("required_skills", [])),
        "opp_certs": ", ".join(opportunity_dict.get("mandatory_certifications", [])),
        "stu_objective": student_dict.get("objective", "N/A"),
        "stu_skills": ", ".join(student_dict.get("skills", [])),
        "stu_projects": ", ".join(student_dict.get("projects", [])),
        "stu_certs": ", ".join(student_dict.get("certifications", [])),
        "stu_experience": ", ".join(student_dict.get("experience", [])),
        "stu_education": ", ".join(student_dict.get("education", [])),
        "score": round(match_score * 100)
    }

    return chain.invoke(inputs)
