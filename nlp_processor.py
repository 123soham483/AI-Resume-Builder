import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter
import re
import string
import logging
import json

# Download necessary NLTK resources
try:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
except Exception as e:
    logging.error(f"Error downloading NLTK resources: {e}")

# Initialize lemmatizer
lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

def preprocess_text(text):
    """Preprocess text for NLP analysis"""
    # Convert to lowercase
    text = text.lower()
    
    # Remove special characters and numbers
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords and lemmatize
    filtered_tokens = [lemmatizer.lemmatize(token) for token in tokens if token not in stop_words 
                      and token not in string.punctuation and len(token) > 2]
    
    return filtered_tokens

def extract_keywords(text, n=20):
    """Extract top n keywords from text using TFIDF"""
    # Handle JSON strings or dictionaries
    if isinstance(text, dict) or text.startswith('{'):
        try:
            if isinstance(text, str):
                data = json.loads(text)
            else:
                data = text
            
            # Concatenate all text fields for analysis
            text_parts = []
            
            # Process personal info
            if 'personal_info' in data:
                personal = data['personal_info']
                if isinstance(personal, str):
                    personal = json.loads(personal)
                for k, v in personal.items():
                    if isinstance(v, str):
                        text_parts.append(v)
            
            # Process education
            if 'education' in data:
                education = data['education']
                if isinstance(education, str):
                    education = json.loads(education)
                for edu in education:
                    for k, v in edu.items():
                        if isinstance(v, str):
                            text_parts.append(v)
            
            # Process experience
            if 'experience' in data:
                experience = data['experience']
                if isinstance(experience, str):
                    experience = json.loads(experience)
                for exp in experience:
                    for k, v in exp.items():
                        if isinstance(v, str):
                            text_parts.append(v)
            
            # Process skills
            if 'skills' in data:
                skills = data['skills']
                if isinstance(skills, str):
                    skills = json.loads(skills)
                if isinstance(skills, list):
                    text_parts.extend(skills)
                elif isinstance(skills, dict):
                    for k, v in skills.items():
                        if isinstance(v, str):
                            text_parts.append(v)
                        elif isinstance(v, list):
                            text_parts.extend(v)
            
            text = ' '.join(text_parts)
        except Exception as e:
            logging.error(f"Error processing JSON: {e}")
    
    # Process the extracted text
    tokens = preprocess_text(text)
    
    # Count term frequency
    word_freq = Counter(tokens)
    
    # Get the most common keywords
    keywords = [word for word, count in word_freq.most_common(n)]
    
    return keywords

def process_resume(resume_text):
    """Process resume text to extract structured information"""
    # Extract keywords
    keywords = extract_keywords(resume_text)
    
    # Additional processing could be added here
    # For example, skill categorization, education level analysis, etc.
    
    return {
        'keywords': keywords,
        'processed_text': ' '.join(preprocess_text(resume_text))
    }

def get_optimization_suggestions(resume_text, job_description, threshold=0.5):
    """Generate optimization suggestions based on resume and job description"""
    resume_keywords = set(extract_keywords(resume_text, n=50))
    job_keywords = set(extract_keywords(job_description, n=50))
    
    # Find matching and missing keywords
    matching_keywords = resume_keywords.intersection(job_keywords)
    missing_keywords = job_keywords - resume_keywords
    
    # Calculate match score
    if len(job_keywords) > 0:
        match_score = len(matching_keywords) / len(job_keywords)
    else:
        match_score = 0
    
    # Generate suggestions
    suggestions = []
    
    # Add missing keywords suggestion
    if missing_keywords:
        suggestions.append({
            'type': 'missing_keywords',
            'title': 'Add Missing Keywords',
            'content': f"Consider adding these keywords to your resume: {', '.join(missing_keywords)}"
        })
    
    # Check if match score is below threshold
    if match_score < threshold:
        suggestions.append({
            'type': 'low_match',
            'title': 'Improve Keyword Match',
            'content': "Your resume's keyword match with the job description is low. Consider tailoring your resume more specifically to this role."
        })
    
    # Add skill section suggestion if many keywords are missing
    if len(missing_keywords) > 5:
        suggestions.append({
            'type': 'skill_section',
            'title': 'Update Skills Section',
            'content': "Consider adding a dedicated skills section highlighting the keywords relevant to this job."
        })
    
    # Return match score and suggestions
    return match_score, suggestions
