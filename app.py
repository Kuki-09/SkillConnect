import streamlit as st
import os
import json
from utils.form_recognizer import extract_student_profile_from_pdf
from utils.smart_matcher import find_best_matches
from utils.suggestion_generator import generate_suggestions

if "show_opportunities" not in st.session_state:
    st.session_state.show_opportunities = False
if "last_uploaded_resume" not in st.session_state:
    st.session_state.last_uploaded_resume = ""
if "parsed_profile" not in st.session_state:
    st.session_state.parsed_profile = None
if "matches" not in st.session_state:
    st.session_state.matches = []
if "suggestions" not in st.session_state:
    st.session_state.suggestions = ""

st.set_page_config(page_title="SkillConnect", page_icon="🤖", layout="wide")
st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-size: 16px;
        color: #212121 !important;
        background-color: #fafafa;
    }
    .block-container {
        padding: 2rem 3rem;
        background-color: #ffffff;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-top: 1rem;
    }
    h1 {
        color: #1976d2 !important;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    [data-testid="stExpander"] > details > summary {
        background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
        color: #0d47a1;
        font-size: 17px;
        font-weight: 600;
        border: 1px solid #64b5f6;
        padding: 12px 18px;
        border-radius: 10px;
        list-style: none;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    [data-testid="stExpander"] > details > summary:hover {
        background: linear-gradient(135deg, #bbdefb 0%, #e1bee7 100%);
        color: #0b3c91;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    [data-testid="stExpander"] > details > div {
        background-color: #f8fffe;
        color: #212121;
        padding: 16px 22px;
        border-radius: 0 0 10px 10px;
        border: 1px solid #e0e0e0;
        border-top: none;
    }
    h2, h3 {
        color: #1976d2 !important;
        margin-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎯 SkillConnect")
st.markdown("Empowering students and faculty with intelligent matching.")

st.sidebar.markdown("""
    <style>
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%);
        color: white !important;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        border: none;
        transition: all 0.2s ease;
    }
    section[data-testid="stSidebar"] .stButton > button:focus,
    section[data-testid="stSidebar"] .stButton > button:active {
        color: white !important;
        background: linear-gradient(135deg, #1976d2 0%, #42a5f5 100%) !important;
        outline: none;
        box-shadow: 0 4px 12px rgba(25, 118, 210, 0.4);
    }
    </style>
""", unsafe_allow_html=True)

resume_storage_dir = "data/resumes"
os.makedirs(resume_storage_dir, exist_ok=True)
resumes_json_dir = "data/json/resumes"
os.makedirs(resumes_json_dir, exist_ok=True)
opportunity_dir = "data/json/opportunities"
os.makedirs(opportunity_dir, exist_ok=True)

if st.sidebar.button("🔍 Explore Internships/Projects"):
    st.session_state.show_opportunities = not st.session_state.show_opportunities

if st.session_state.show_opportunities:
    if os.listdir(opportunity_dir):
        for opp_file in os.listdir(opportunity_dir):
            with open(os.path.join(opportunity_dir, opp_file)) as f:
                opp = json.load(f)
            with st.sidebar.expander(opp.get("title", "Untitled Opportunity")):
                st.write(f"**Organization:** {opp.get('organization')}")
                st.write(f"**Duration:** {opp.get('duration')}")
                st.write(f"**Type:** {opp.get('type')}")
                st.write(f"**Role:** {opp.get('role', 'Not specified')}")
                st.write(f"**Skills:** {', '.join(opp.get('required_skills', []))}")
                st.write(f"**Description:** {opp.get('description')}")
                if opp.get("faculty"):
                    st.write(f"**Faculty / Contact Person:** {opp.get('faculty')}")
                if opp.get("mandatory_certifications"):
                    certs = ', '.join(opp["mandatory_certifications"])
                    st.write(f"**Mandatory Courses / Certifications:** {certs}")
                if opp.get("stipend"):
                    st.write(f"**Stipend / Compensation:** {opp.get('stipend')}")
    else:
        st.sidebar.info("📭 Oops! No opportunities posted yet. Check back later.")

user_type = st.radio("I am a:", ["🎓 Student", "🏢 Faculty / Recruiter"])

if user_type == "🎓 Student":
    st.sidebar.header("📄 Upload Resume")
    uploaded_file = st.sidebar.file_uploader("Upload your resume (PDF only)", type=["pdf"])

    if uploaded_file:
        resume_filename = uploaded_file.name.lower().replace(" ", "_")
        if resume_filename != st.session_state.last_uploaded_resume:
            resume_path = os.path.join(resume_storage_dir, resume_filename)
            with open(resume_path, "wb") as f:
                f.write(uploaded_file.read())

            try:
                with st.spinner("🔍 Analyzing your resume with AI..."):
                    profile = extract_student_profile_from_pdf(resume_path)

                if not any(profile.values()):
                    st.error("😕 We couldn’t understand your resume. Try uploading a clearer version.")
                    st.session_state.parsed_profile = None
                else:
                    st.success("📄 Your resume has been successfully analyzed! Let’s find your best matches.")
                    st.session_state.last_uploaded_resume = resume_filename
                    st.session_state.parsed_profile = profile

                    profile_json_path = os.path.join(resumes_json_dir, f"{resume_filename}.json")
                    with open(profile_json_path, "w") as f:
                        json.dump(profile, f, indent=2)

                    matches = find_best_matches(profile_json_path, opportunity_dir, threshold=0.60)
                    st.session_state.matches = matches


                    top_opp_data = []
                    for match in st.session_state.matches:
                        opp_file_path = os.path.join(opportunity_dir, match['file'])
                        with open(opp_file_path, 'r') as f:
                            opp = json.load(f)
                        opp["match_score"] = match['score']
                        top_opp_data.append(opp)

                    st.session_state.suggestions = generate_suggestions(profile, top_opp_data)

            except Exception as e:
                st.error(f"❌ Error processing resume: {e}")
                st.session_state.parsed_profile = None

    if st.session_state.parsed_profile:
        st.subheader("🎯 Matching Opportunities")
        if st.session_state.matches:
            for match in st.session_state.matches:
                opp_file_path = os.path.join(opportunity_dir, match['file'])
                with open(opp_file_path, 'r') as f:
                    opp_data = json.load(f)
                match_score_percent = round(match['score'] * 100)
                contact_label = "Faculty" if opp_data.get('type', '').lower() == 'project' else "Contact Person"
                with st.expander(f"{opp_data.get('title')} — Match Score: {match_score_percent}%"):
                    st.write(f"**Organization:** {opp_data.get('organization')}")
                    st.write(f"**Duration:** {opp_data.get('duration')}")
                    st.write(f"**Type:** {opp_data.get('type')}")
                    st.write(f"**Stipend:** {opp_data.get('stipend', 'Not disclosed')}")
                    if opp_data.get('faculty'):
                        st.write(f"**{contact_label}:** {opp_data.get('faculty')}")
                    st.write("**Role:**")
                    for line in opp_data.get('role', '').splitlines():
                        if line.strip():
                            st.markdown(f"- {line.strip()}")
                    st.write(f"**Required Skills:** {', '.join(opp_data.get('required_skills', []))}")
                    st.write(f"**Mandatory Certifications:** {', '.join(opp_data.get('mandatory_certifications', [])) or 'None'}")
                    st.write("**Description:**")
                    st.write(opp_data.get('description'))
        else:
            st.info("🤔 No strong matches found. Try updating skills or certifications.")

        st.markdown("---")
        st.subheader("📈 Suggestions to Improve Your Profile")
        st.markdown(st.session_state.suggestions, unsafe_allow_html=True)

else:
    st.header("📤 Post an Internship or Project")
    with st.form("post_opportunity_form"):
        title = st.text_input("Title of the Opportunity")
        organization = st.text_input("Organization / Institute")
        opp_type = st.selectbox("Type", ["Internship", "Project"])
        required_skills = st.text_area("Required Skills (comma separated)")
        duration = st.text_input("Duration & Mode (e.g., 3 months, Remote)")
        role = st.text_area("Enter role")
        description = st.text_area("Opportunity Description (at least 5 lines)")
        faculty_name = st.text_input("Faculty / Contact Person (Optional)")
        stipend = st.text_input("Stipend / Compensation (Optional)")
        mandatory_certs = st.text_area("Mandatory Courses / Certifications (Optional)")

        submitted = st.form_submit_button("📌 Submit Opportunity")

        if submitted:
            if not title or not organization or not required_skills or not duration or not description:
                st.error("⚠️ Please complete all required fields to post your opportunity.")
            else:
                try:
                    safe_filename = title.lower().replace(" ", "_").replace("/", "_") + ".json"
                    opportunity_data = {
                        "title": title,
                        "organization": organization,
                        "type": opp_type,
                        "required_skills": [s.strip() for s in required_skills.split(",") if s.strip()],
                        "duration": duration,
                        "description": description,
                        "role": role,
                        "faculty": faculty_name,
                        "stipend": stipend,
                        "mandatory_certifications": [c.strip() for c in mandatory_certs.split(",") if c.strip()]
                    }
                    with open(os.path.join(opportunity_dir, safe_filename), "w") as f:
                        json.dump(opportunity_data, f, indent=2)
                    st.success("✅ Opportunity posted successfully!")
                except Exception as e:
                    st.error(f"🚨 Something went wrong while saving. Please try again: {e}")

st.markdown("""
---
<center>
    Made with ❤️ for students and educators
</center>
""", unsafe_allow_html=True)
