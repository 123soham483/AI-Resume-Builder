import json
import os
import logging
from openai import OpenAI

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Initialize OpenAI client only if API key is available
openai = None
if OPENAI_API_KEY:
    try:
        openai = OpenAI(api_key=OPENAI_API_KEY)
    except Exception as e:
        logging.error(f"Failed to initialize OpenAI client: {e}")
        openai = None

def generate_resume_improvement_suggestions(resume_text, job_description):
    """
    Generate improvement suggestions for a resume based on a job description.
    Uses OpenAI API to analyze the match and provide tailored suggestions.
    """
    # Check if OpenAI client is available
    if openai is None:
        logging.warning("OpenAI client not available, returning default suggestions")
        return {
            "match_score": 50,
            "keyword_analysis": {
                "matching_keywords": [],
                "missing_keywords": []
            },
            "suggestions": [
                {
                    "title": "OpenAI API Not Available",
                    "content": "AI-powered resume analysis requires an OpenAI API key. Basic analysis will be used instead."
                }
            ],
            "overall_feedback": "Please provide an OpenAI API key for enhanced analysis."
        }
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert resume optimizer and career advisor. "
                        "Your task is to analyze a resume against a job description "
                        "and provide specific, actionable suggestions to improve the resume. "
                        "Focus on keyword matching, content relevance, skills alignment, and "
                        "professional presentation. Provide your analysis in JSON format."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Here is a resume:\n\n{resume_text}\n\n"
                        f"And here is a job description:\n\n{job_description}\n\n"
                        "Please analyze how well the resume matches the job description. "
                        "Provide suggestions for improvement in the following JSON format:\n"
                        "{\n"
                        "  \"match_score\": <score between 0-100>,\n"
                        "  \"keyword_analysis\": {\n"
                        "    \"matching_keywords\": [<keywords present in both>],\n"
                        "    \"missing_keywords\": [<important keywords in job description but missing in resume>]\n"
                        "  },\n"
                        "  \"suggestions\": [\n"
                        "    {\"title\": <suggestion title>, \"content\": <detailed suggestion>},\n"
                        "    ...\n"
                        "  ],\n"
                        "  \"overall_feedback\": <general feedback string>\n"
                        "}"
                    )
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=1500
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {e}")
        # Return a basic structure if API call fails
        return {
            "match_score": 0,
            "keyword_analysis": {
                "matching_keywords": [],
                "missing_keywords": []
            },
            "suggestions": [
                {
                    "title": "API Error",
                    "content": "Unable to analyze resume with AI at this time. Please try again later."
                }
            ],
            "overall_feedback": "An error occurred during AI analysis."
        }

def enhance_ats_simulation(resume_text, job_description):
    """
    Enhance ATS simulation with AI analysis to provide more accurate scoring.
    """
    # Check if OpenAI client is available
    if openai is None:
        logging.warning("OpenAI client not available, returning default ATS simulation")
        return {
            "ats_score": 50,
            "keyword_match_score": 50,
            "content_relevance_score": 50,
            "format_score": 50,
            "feedback": ["AI-powered ATS simulation requires an OpenAI API key. Basic scoring will be used instead."],
            "red_flags": [],
            "improvement_areas": ["Provide an OpenAI API key for enhanced analysis"]
        }
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert in Applicant Tracking Systems (ATS). "
                        "Your task is to simulate how an ATS would score this resume "
                        "against the provided job description. Provide scores and analysis "
                        "in JSON format."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Resume:\n\n{resume_text}\n\n"
                        f"Job Description:\n\n{job_description}\n\n"
                        "Please simulate an ATS system's evaluation of this resume against the job description. "
                        "Respond with JSON in this format:\n"
                        "{\n"
                        "  \"ats_score\": <overall score 0-100>,\n"
                        "  \"keyword_match_score\": <keyword matching score 0-100>,\n"
                        "  \"content_relevance_score\": <content relevance score 0-100>,\n"
                        "  \"format_score\": <resume format/structure score 0-100>,\n"
                        "  \"feedback\": [<array of feedback strings>],\n"
                        "  \"red_flags\": [<potential issues that might cause ATS rejection>],\n"
                        "  \"improvement_areas\": [<specific areas to improve>]\n"
                        "}"
                    )
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {e}")
        # Return a basic structure if API call fails
        return {
            "ats_score": 50,
            "keyword_match_score": 50,
            "content_relevance_score": 50,
            "format_score": 50,
            "feedback": ["Unable to analyze with AI at this time"],
            "red_flags": [],
            "improvement_areas": ["Try again later"]
        }

def extract_key_skills(job_description):
    """
    Extract key skills and requirements from a job description.
    """
    # Check if OpenAI client is available
    if openai is None:
        logging.warning("OpenAI client not available, returning basic skills extraction")
        return {
            "hard_skills": [],
            "soft_skills": [],
            "qualifications": [],
            "experience": [],
            "key_responsibilities": [],
            "keywords": []
        }
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a skilled job analyzer. Extract the most important skills, "
                        "qualifications, and keywords from the job description."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Job Description:\n\n{job_description}\n\n"
                        "Please extract and categorize the key requirements from this job description "
                        "in the following JSON format:\n"
                        "{\n"
                        "  \"hard_skills\": [<technical skills required>],\n"
                        "  \"soft_skills\": [<interpersonal skills mentioned>],\n"
                        "  \"qualifications\": [<education/certification requirements>],\n"
                        "  \"experience\": [<experience requirements>],\n"
                        "  \"key_responsibilities\": [<main job duties>],\n"
                        "  \"keywords\": [<important terms/phrases for ATS>]\n"
                        "}"
                    )
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=800
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logging.error(f"Error calling OpenAI API: {e}")
        # Return a basic structure if API call fails
        return {
            "hard_skills": [],
            "soft_skills": [],
            "qualifications": [],
            "experience": [],
            "key_responsibilities": [],
            "keywords": []
        }