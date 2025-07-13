import os
from dotenv import load_dotenv
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient 

load_dotenv()

AZURE_ENDPOINT = os.getenv("AZURE_FORM_RECOGNIZER_ENDPOINT")
AZURE_KEY = os.getenv("AZURE_FORM_RECOGNIZER_KEY")
AZURE_CUSTOM_MODEL_ID = os.getenv("AZURE_CUSTOM_MODEL_ID")

client = DocumentIntelligenceClient(
    endpoint=AZURE_ENDPOINT,
    credential=AzureKeyCredential(AZURE_KEY)
)

def split_list_field(field_value: str) -> list:
    if not field_value:
        return []
    return [item.strip("\u2022-\u2013 ").strip() for item in field_value.split("\n") if item.strip()]

def parse_education_field(value: str) -> list:
    if not value:
        return []
    return [line.strip() for line in value.split("\n") if line.strip()]

def extract_student_profile_from_pdf(resume_path: str) -> dict:
    try:
        with open(resume_path, "rb") as f:
            document_data = f.read()

        poller = client.begin_analyze_document(
            model_id=AZURE_CUSTOM_MODEL_ID,
            body=document_data,
            content_type="application/pdf"
        )

        result = poller.result()
        fields = result.documents[0].fields if result.documents else {}

        def get_field(name):
            return fields.get(name).content.strip() if fields.get(name) and fields.get(name).content else ""

        profile = {
            "name": get_field("Name"),
            "email": get_field("Email"),
            "phone": get_field("Phone"),
            "social_links": split_list_field(get_field("SocialLinks")),
            "objective": get_field("Objective"),
            "certifications": split_list_field(get_field("Certifications")),
            "skills": split_list_field(get_field("Skills")),
            "experience": split_list_field(get_field("Experience")),
            "projects": split_list_field(get_field("Projects")),
        }

        education_text = get_field("Education")
        profile["education_raw"] = education_text
        profile["education"] = parse_education_field(education_text)

        return profile

    except Exception as e:
        return {"error": str(e)}