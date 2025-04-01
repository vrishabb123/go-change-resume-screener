> C..aa⚕️:
import streamlit as st
import pdfplumber
import spacy
import re
from typing import Dict, List
import json

# Load SpaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    st.error("SpaCy model not found. Please run: `python -m spacy download en_core_web_sm`")
    st.stop()

# Define company requirements
required_skills: List[str] = ["python", "machine learning", "data analysis"]
min_experience: int = 2
required_education: List[str] = ["bachelor", "master", "phd"]
optional_skills: List[str] = ["sql", "tensorflow"]

def read_resume(pdf_file) -> str:
    """Extract text from a PDF resume."""
    try:
        with pdfplumber.open(pdf_file) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            return text if text else "No text extracted from resume."
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")

def screen_resume(text: str) -> Dict[str, str]:
    """Screen a resume based on company requirements."""
    doc = nlp(text.lower())

    # Skills check
    skills_matched = []
    skills_missing = []
    resume_text = " ".join([token.text for token in doc if token.is_alpha])
    for skill in required_skills:
        skill_doc = nlp(skill)
        similarity = nlp(resume_text).similarity(skill_doc)
        if similarity > 0.85:
            skills_matched.append(skill)
        else:
            skills_missing.append(skill)
    
    optional_matched = [
        skill for skill in optional_skills 
        if nlp(resume_text).similarity(nlp(skill)) > 0.85
    ]

    # Experience check
    total_experience = 0
    experience_pattern = r'(\d+)\s*(years?|yrs?)\s*(of)?\s*(experience|exp)?'
    matches = re.findall(experience_pattern, text.lower())
    if matches:
        total_experience = max([int(match[0]) for match in matches], default=0)
    experience_met = total_experience >= min_experience

    # Education check
    education_met = False
    education_found = None
    text_lower = text.lower()
    for edu in required_education:
        if edu in text_lower:
            education_met = True
            education_found = edu.capitalize()
            break

    # Decision and feedback
    if not skills_missing and experience_met and education_met:
        status = "Accepted"
        feedback = (
            f"Skills: All met ({', '.join(skills_matched)}). "
            f"Optional: {', '.join(optional_matched) or 'None'}. "
            f"Experience: {total_experience} years. Education: {education_found}."
        )
    else:
        status = "Rejected"
        feedback = (
            f"Skills: Missing {', '.join(skills_missing) if skills_missing else 'None'}. "
            f"Optional: {', '.join(optional_matched) or 'None'}. "
            f"Experience: {total_experience} years ({'Met' if experience_met else 'Not met'}). "
            f"Education: {education_found if education_met else 'Not found'}."
        )

    return {"status": status, "feedback": feedback}

# Streamlit Interface
st.set_page_config(page_title="GoChange Resume Screener", page_icon="📄", layout="wide")

# Header
st.title("📄 GoChange Resume Screener")
st.markdown("An AI-powered tool to screen resumes based on GoChange's requirements.")

# Sidebar for instructions and settings
with st.sidebar:
    st.header("About")
    st.markdown("""
    This tool evaluates resumes against predefined criteria:
    - Required Skills: Python, Machine Learning, Data Analysis
    - Minimum Experience: 2 years
    - Required Education: Bachelor, Master, or PhD
    - Optional Skills: SQL, TensorFlow
    """)
    st.header("Settings")
    similarity_threshold = st.slider("Similarity Threshold for Skills", 0.0, 1.0, 0.85, 0.05)
    st.markdown("Adjust the threshold for skill matching sensitivity.")

# Main content
st.write("Upload a resume to evaluate it against GoChange's requirements.")

uploaded_file = st.file_uploader("Upload Resume (PDF)", type="pdf")

if uploaded_file:
    try:
        with st.spinner("Screening resume..."):
            text = read_resume(uploaded_file)
            result = screen_resume(text)
            
            # Display results
            st.subheader("Screening Result")
            if result["status"] == "Accepted":
                st.success(f"**Status**: {result['status']}")
            else:
                st.warning(f"**Status**: {result['status']}")
            st.write(f"**Feedback**: {result['feedback']}")

            # Download result as JSON
            result_json = json.dumps(result, indent=4)
            st.download_button(
                label="Download Result as JSON",
                data=result_json,
                file_name="resume_screening_result.json",
                mime="application/json"
            )

    except Exception as e:
        st.error(f"Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("© 2025 GoChange | Built with Streamlit")
