import os
import re
import spacy
from typing import List
from dotenv import load_dotenv
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

AZURE_TEXT_ANALYTICS_ENDPOINT = os.getenv("AZURE_TEXT_ANALYTICS_ENDPOINT")
AZURE_TEXT_ANALYTICS_KEY = os.getenv("AZURE_TEXT_ANALYTICS_KEY")

if not AZURE_TEXT_ANALYTICS_ENDPOINT or not AZURE_TEXT_ANALYTICS_KEY:
    raise ValueError("Azure Text Analytics credentials not found. Check .env file.")

client = TextAnalyticsClient(
    endpoint=AZURE_TEXT_ANALYTICS_ENDPOINT,
    credential=AzureKeyCredential(AZURE_TEXT_ANALYTICS_KEY)
)

nlp = spacy.load("en_core_web_sm")

KNOWN_SKILLS = {
    "python", "c++", "sql", "flask", "tensorflow", "postgresql", "sqlite", "langchain", "mongodb", "node.js",
    "machine learning", "firebase", "scikit-learn", "rest apis", "aws", "cloud", "react", "javascript", "nlp",
    "openai", "faiss", "hugging face", "dynamodb", "full stack", "web development", "express", "semantic search",
    "streamlit", "microcontrollers", "iot", "embedded systems", "rtos", "rag", "trading", "portfolio", "risk",
    "derivatives", "compliance", "audit", "financial modeling", "litigation", "contracts", "regulatory",
    "due diligence", "legal research", "clinical", "medical", "patient care", "hipaa", "ehr", "telemedicine",
    "seo", "sem", "social media", "content marketing", "analytics", "campaign management", "recruitment",
    "onboarding", "performance management", "compensation", "benefits", "employee relations","bamboohr", "workday",
    "empathy", "communication", "conflict resolution", "survey design", "spss analysis", "excel", "tableau", "onboarding",
    "resume screening", "scheduling interviews", "organizational psychology","Google Analytics", "HubSpot", "Instagram Ads",
    "Facebook Business Manager", "Email Marketing", "Analytics Reports", "Keyword Research", "SEO Optimization",
    "Adobe Illustrator", "Canva", "Graphic Design", "Branding", "Digital Campaigns","Google Ads", "PPC Campaigns",
    "Marketing Strategy", "Organic Traffic", "Social Media Marketing", "Rebranding","Content Marketing", 
    "Market Research", "Customer Segmentation", "A/B Testing", "Copywriting", "LinkedIn Ads", "YouTube Ads",
    "Sales Funnel Optimization", "CRM Management", "Lead Generation", "Conversion Rate Optimization",
    "Email Automation", "Influencer Marketing", "Performance Marketing",
    "Web Analytics", "Marketing Automation", "Figma", "Trello", "Asana", "Slack"


}

NORMALIZATION_MAP = {
    "js": "javascript",
    "nodejs": "node.js",
    "node js": "node.js",
    "node": "node.js",
    "mongo": "mongodb",
    "postgres": "postgresql",
    "restful apis": "rest apis",
    "tensorflow developer": "tensorflow",
    "huggingface": "hugging face",
    "ml": "machine learning",
    "reactjs": "react.js",
    "react js": "react.js",
    "react": "react.js",
    "amazon web services": "aws",
    "natural language processing": "nlp"
}

def normalize_keywords(keywords: List[str]) -> List[str]:
    normalized = set()
    for kw in keywords:
        kw = kw.lower().strip().replace("\n", " ").replace("\t", " ")
        kw = re.sub(r"\s+", " ", kw)
        kw = NORMALIZATION_MAP.get(kw, kw)
        normalized.add(kw)
    return list(normalized)

def process_raw_skills(raw_skills: List[str]) -> List[str]:
    all_skills = []
    for line in raw_skills:
        line = re.sub(r"^[•\-–●]", "", line).strip().lower()
        line = line.replace("\n", " ")
        if ":" in line:
            _, skills_part = line.split(":", 1)
        else:
            skills_part = line
        skills = [s.strip() for s in skills_part.split(",") if s.strip()]
        all_skills.extend(skills)
    return list(set(normalize_keywords(all_skills)))

def extract_entities(text: str) -> List[str]:
    if not text.strip():
        return []
    try:
        result = client.recognize_entities(documents=[text])[0]
        if result.is_error:
            return []
        allowed_categories = {"Skill", "Product", "Organization", "Event", "Other"}
        return list({ent.text.strip() for ent in result.entities if ent.category in allowed_categories})
    except Exception as e:
        return []

def manual_match_known_skills_from_text(text: str) -> List[str]:
    text = text.lower()
    matches = []
    for skill in KNOWN_SKILLS:
        if skill.lower() in text:
            matches.append(skill)
    return list(set(normalize_keywords(matches)))

def extract_valid_skill_entities(text: str) -> List[str]:
    text = text.replace("\n", " ")
    ner_entities = extract_entities(text)
    ner_normalized = [
        normalize_keywords([ent])[0]
        for ent in ner_entities
        if not any(tok.pos_ in {"VERB", "ADJ", "ADV", "NUM", "PRON"} for tok in nlp(ent))
    ]
    ner_filtered = {kw for kw in ner_normalized if kw in KNOWN_SKILLS}
    manual_matches = set(manual_match_known_skills_from_text(text))
    return list(ner_filtered.union(manual_matches))

def extract_skills_from_resume(resume: dict) -> List[str]:
    raw_skill_lines = resume.get("skills", [])
    raw_skills = process_raw_skills(raw_skill_lines)
    projects_text = " ".join(resume.get("projects", []))
    experience_text = " ".join(resume.get("experience", []))
    certs_text = " ".join(resume.get("certifications", []))
    skills_from_projects = extract_valid_skill_entities(projects_text)
    skills_from_experience = extract_valid_skill_entities(experience_text)
    skills_from_certs = extract_valid_skill_entities(certs_text)
    all_skills = set(raw_skills + skills_from_projects + skills_from_experience + skills_from_certs)
    return list(all_skills)

def extract_skills_from_opportunity(opp: dict) -> List[str]:
    raw_skills = process_raw_skills(opp.get("required_skills", []))
    desc_text = opp.get("description", "")
    role_text = opp.get("role", "")
    certs_text = " ".join(opp.get("mandatory_certifications", []))
    skills_from_desc = extract_valid_skill_entities(desc_text)
    skills_from_role = extract_valid_skill_entities(role_text)
    skills_from_certs = extract_valid_skill_entities(certs_text)
    all_skills = set(raw_skills + skills_from_desc + skills_from_role + skills_from_certs)
    return list(all_skills)

