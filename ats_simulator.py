import re
import nltk
import random
import logging
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import string
import json

try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

# Initialize stop words
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    """Clean and tokenize text"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation and numbers
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    
    # Tokenize and remove stop words
    tokens = word_tokenize(text)
    filtered_tokens = [word for word in tokens if word not in stop_words 
                      and word not in string.punctuation and len(word) > 2]
    
    return ' '.join(filtered_tokens)

def extract_text_from_json(json_data):
    """Extract text from resume JSON data"""
    if isinstance(json_data, str):
        try:
            data = json.loads(json_data)
        except:
            return json_data
    else:
        data = json_data
    
    texts = []
    
    # Extract from personal info
    if 'personal_info' in data:
        personal = data['personal_info']
        if isinstance(personal, str):
            try:
                personal = json.loads(personal)
            except:
                texts.append(personal)
                personal = {}
        
        for key, value in personal.items():
            if isinstance(value, str):
                texts.append(value)
    
    # Extract from education
    if 'education' in data:
        education = data['education']
        if isinstance(education, str):
            try:
                education = json.loads(education)
            except:
                texts.append(education)
                education = []
        
        for edu in education:
            if isinstance(edu, dict):
                for key, value in edu.items():
                    if isinstance(value, str):
                        texts.append(value)
    
    # Extract from experience
    if 'experience' in data:
        experience = data['experience']
        if isinstance(experience, str):
            try:
                experience = json.loads(experience)
            except:
                texts.append(experience)
                experience = []
        
        for exp in experience:
            if isinstance(exp, dict):
                for key, value in exp.items():
                    if isinstance(value, str):
                        texts.append(value)
    
    # Extract from skills
    if 'skills' in data:
        skills = data['skills']
        if isinstance(skills, str):
            try:
                skills = json.loads(skills)
            except:
                texts.append(skills)
                skills = []
        
        if isinstance(skills, list):
            texts.extend(skills)
        elif isinstance(skills, dict):
            for key, value in skills.items():
                if isinstance(value, str):
                    texts.append(value)
    
    return ' '.join(texts)

def simulate_ats_score(resume, job_description):
    """Simulate an ATS scoring system"""
    try:
        # Extract text from resume if it's in JSON format
        resume_text = extract_text_from_json(resume)
        
        # Preprocess texts
        processed_resume = preprocess_text(resume_text)
        processed_job = preprocess_text(job_description)
        
        # Calculate keyword match score
        job_keywords = set(processed_job.split())
        resume_keywords = set(processed_resume.split())
        
        # Calculate the overlap between keywords
        common_keywords = job_keywords.intersection(resume_keywords)
        keyword_match_score = len(common_keywords) / max(len(job_keywords), 1) * 100
        
        # Calculate semantic similarity using TF-IDF and cosine similarity
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([processed_resume, processed_job])
            similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0] * 100
        except:
            similarity_score = 0
        
        # Calculate formatting score (randomized for simulation)
        # In a real system, this would check resume format, length, etc.
        formatting_score = random.uniform(70, 95)
        
        # Combine scores with different weights
        final_score = (
            keyword_match_score * 0.5 + 
            similarity_score * 0.3 + 
            formatting_score * 0.2
        )
        
        # Generate feedback based on the score
        feedback = generate_ats_feedback(
            final_score, 
            keyword_match_score, 
            similarity_score, 
            common_keywords, 
            job_keywords - resume_keywords
        )
        
        return {
            'total_score': round(final_score, 1),
            'keyword_match_score': round(keyword_match_score, 1),
            'semantic_similarity': round(similarity_score, 1),
            'formatting_score': round(formatting_score, 1),
            'feedback': feedback,
            'matched_keywords': list(common_keywords),
            'missing_keywords': list(job_keywords - resume_keywords)
        }
    
    except Exception as e:
        logging.error(f"Error in ATS simulation: {e}")
        # Return a default score with error message
        return {
            'total_score': 50.0,
            'keyword_match_score': 50.0,
            'semantic_similarity': 50.0,
            'formatting_score': 50.0,
            'feedback': ["Error processing resume. Please try again."],
            'matched_keywords': [],
            'missing_keywords': []
        }

def generate_ats_feedback(final_score, keyword_score, similarity_score, matched_keywords, missing_keywords):
    """Generate feedback based on ATS scores"""
    feedback = []
    
    # Overall score feedback
    if final_score >= 80:
        feedback.append("Your resume is well-optimized for this job posting.")
    elif final_score >= 60:
        feedback.append("Your resume is moderately optimized. Some improvements would help.")
    else:
        feedback.append("Your resume needs significant optimization for this job posting.")
    
    # Keyword match feedback
    if keyword_score < 50:
        feedback.append("Low keyword match. Consider adding more relevant keywords from the job description.")
    
    # Missing important keywords feedback
    if missing_keywords:
        important_missing = list(missing_keywords)[:5]  # Limit to 5 keywords
        if important_missing:
            feedback.append(f"Missing important keywords: {', '.join(important_missing)}.")
    
    # Content alignment feedback
    if similarity_score < 50:
        feedback.append("The content of your resume doesn't align well with the job requirements.")
    
    return feedback
