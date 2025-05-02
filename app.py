import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
import json
import tempfile
import uuid
from markupsafe import Markup

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import after db is defined to avoid circular imports
from models import User, Resume, JobDescription
from nlp_processor import process_resume, extract_keywords, get_optimization_suggestions
from resume_generator import generate_resume_pdf, generate_resume_docx
from ats_simulator import simulate_ats_score
from openai_integration import generate_resume_improvement_suggestions, enhance_ats_simulation, extract_key_skills

# Add custom template filter for JSON parsing
@app.template_filter('fromjson')
def parse_json(value):
    if value is None:
        return None
    try:
        return json.loads(value)
    except (ValueError, TypeError):
        return value

with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/resume/new', methods=['GET'])
def new_resume():
    return render_template('resume_form.html')

@app.route('/resume/save', methods=['POST'])
def save_resume():
    try:
        data = request.json
        app.logger.debug(f"Saving resume data: {data}")
        
        # Always create a new UUID for every resume saved
        # This ensures we never have null UUIDs
        new_uuid = str(uuid.uuid4())
        
        # Log the UUID for debugging
        app.logger.info(f"Generated new UUID: {new_uuid}")
        
        # Create a new resume in the database
        resume = Resume(
            uuid=new_uuid,  # Always use the new UUID
            title=f"Resume - {datetime.now().strftime('%Y-%m-%d')}",
            template_id=data.get('template', 'modern'),
            personal_info=data.get('personal_info', {}), 
            education=data.get('education', []),
            experience=data.get('experience', []),
            skills=data.get('skills', [])
        )
        
        db.session.add(resume)
        db.session.commit()
        
        # Store minimal info in session for navigation purposes
        if 'resume_ids' not in session:
            session['resume_ids'] = []
        
        if new_uuid not in session['resume_ids']:
            session['resume_ids'].append(new_uuid)
            session.modified = True
        
        # Extract keywords (simple version to avoid NLTK issues)
        keywords = []
        skills = data.get('skills', [])
        if isinstance(skills, list):
            keywords.extend(skills)
        
        return jsonify({
            'success': True,
            'resume_id': new_uuid,  # Return the new UUID
            'keywords': keywords
        })
    except Exception as e:
        app.logger.error(f"Error saving resume: {str(e)}")
        return jsonify({
            'success': False,
            'error': "Error saving resume. Please try again."
        }), 500

@app.route('/templates')
def templates():
    # Get recently created resumes
    recent_resumes = Resume.query.order_by(Resume.created_at.desc()).limit(5).all()
    return render_template('templates.html', recent_resumes=recent_resumes)

@app.route('/preview/<resume_id>')
def preview(resume_id):
    # Try to get resume from database
    resume = Resume.query.filter_by(uuid=resume_id).first()
    
    if not resume:
        flash('Resume not found')
        return redirect(url_for('index'))
    
    # Parse the JSON strings back to Python objects
    resume_data = {
        'personal_info': json.loads(resume.personal_info),
        'education': json.loads(resume.education),
        'experience': json.loads(resume.experience),
        'skills': json.loads(resume.skills),
        'template': resume.template_id
    }
    
    return render_template('preview.html', resume=resume_data, resume_id=resume_id)

@app.route('/optimize/<resume_id>', methods=['GET', 'POST'])
def optimize(resume_id):
    # Try to get resume from database
    resume = Resume.query.filter_by(uuid=resume_id).first()
    
    if not resume:
        flash('Resume not found')
        return redirect(url_for('index'))
    
    # Parse the JSON strings back to Python objects
    resume_data = {
        'personal_info': json.loads(resume.personal_info),
        'education': json.loads(resume.education),
        'experience': json.loads(resume.experience),
        'skills': json.loads(resume.skills),
        'template': resume.template_id
    }
    
    if request.method == 'POST':
        job_description = request.form.get('job_description', '')
        
        # Convert resume data to text
        resume_text = json.dumps(resume_data)
        
        # Check if OpenAI API key is available
        if os.environ.get("OPENAI_API_KEY"):
            try:
                # Use AI-powered analysis if API key is available
                ai_suggestions = generate_resume_improvement_suggestions(resume_text, job_description)
                ats_analysis = enhance_ats_simulation(resume_text, job_description)
                
                # Extract suggestions from OpenAI response
                suggestions = ai_suggestions.get('suggestions', [])
                
                # Format ATS score data to match template expectations
                ats_score = {
                    'total_score': ats_analysis.get('ats_score', 50),
                    'keyword_match_score': ats_analysis.get('keyword_match_score', 50),
                    'semantic_similarity': ats_analysis.get('content_relevance_score', 50),
                    'formatting_score': ats_analysis.get('format_score', 50),
                    'feedback': ats_analysis.get('feedback', []),
                    'matched_keywords': ai_suggestions.get('keyword_analysis', {}).get('matching_keywords', []),
                    'missing_keywords': ai_suggestions.get('keyword_analysis', {}).get('missing_keywords', [])
                }
                
                # Get overall match score
                score = ai_suggestions.get('match_score', 50) / 100  # Convert 0-100 to 0-1
                
            except Exception as e:
                logging.error(f"Error using OpenAI API: {e}")
                # Fall back to basic NLP processing if OpenAI call fails
                score, suggestions = get_optimization_suggestions(resume_text, job_description)
                ats_score = simulate_ats_score(resume_text, job_description)
        else:
            # Use basic NLP processing if no API key is available
            score, suggestions = get_optimization_suggestions(resume_text, job_description)
            ats_score = simulate_ats_score(resume_text, job_description)
        
        return render_template(
            'optimize.html',
            resume=resume_data,
            resume_id=resume_id,
            job_description=job_description,
            score=score,
            suggestions=suggestions,
            ats_score=ats_score
        )
    
    return render_template('optimize.html', resume=resume_data, resume_id=resume_id)

@app.route('/export/<resume_id>/<format>', methods=['GET'])
def export_resume(resume_id, format):
    # Try to get resume from database
    resume = Resume.query.filter_by(uuid=resume_id).first()
    
    if not resume:
        flash('Resume not found')
        return redirect(url_for('index'))
    
    # Parse the JSON strings back to Python objects
    resume_data = {
        'personal_info': json.loads(resume.personal_info),
        'education': json.loads(resume.education),
        'experience': json.loads(resume.experience),
        'skills': json.loads(resume.skills),
        'template': resume.template_id
    }
    
    if format == 'pdf':
        # Generate PDF
        pdf_file = generate_resume_pdf(resume_data)
        return send_file(
            pdf_file,
            as_attachment=True,
            download_name=f"resume_{resume_id}.pdf",
            mimetype='application/pdf'
        )
    elif format == 'docx':
        # Generate DOCX
        docx_file = generate_resume_docx(resume_data)
        return send_file(
            docx_file,
            as_attachment=True,
            download_name=f"resume_{resume_id}.docx",
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    else:
        flash('Unsupported format')
        return redirect(url_for('preview', resume_id=resume_id))

@app.route('/my-resumes')
def my_resumes():
    # Get all resumes or filter by session if user authentication is not implemented
    if 'resume_ids' in session:
        # Get resumes from the session IDs 
        resume_ids = session.get('resume_ids', [])
        resumes = Resume.query.filter(Resume.uuid.in_(resume_ids)).order_by(Resume.created_at.desc()).all()
    else:
        # If no session, get all recent resumes (normally would filter by user)
        resumes = Resume.query.order_by(Resume.created_at.desc()).all()
    
    return render_template('my_resumes.html', resumes=resumes)

@app.route('/delete-resume/<resume_id>', methods=['GET'])
def delete_resume(resume_id):
    # Get the resume from database
    resume = Resume.query.filter_by(uuid=resume_id).first()
    
    if not resume:
        flash('Resume not found', 'danger')
        return redirect(url_for('my_resumes'))
    
    try:
        # Delete the resume
        db.session.delete(resume)
        db.session.commit()
        
        # Remove from session if present
        if 'resume_ids' in session and resume_id in session['resume_ids']:
            session['resume_ids'].remove(resume_id)
            session.modified = True
        
        flash('Resume deleted successfully', 'success')
    except Exception as e:
        app.logger.error(f"Error deleting resume: {str(e)}")
        flash('Error deleting resume', 'danger')
    
    return redirect(url_for('my_resumes'))

@app.route('/api/analyze-keywords', methods=['POST'])
def analyze_keywords():
    data = request.json
    resume_text = data.get('resume', '')
    job_description = data.get('job_description', '')
    
    # Extract keywords from both
    resume_keywords = extract_keywords(resume_text)
    job_keywords = extract_keywords(job_description)
    
    # Find matches and missing keywords
    matches = list(set(resume_keywords) & set(job_keywords))
    missing = list(set(job_keywords) - set(resume_keywords))
    
    return jsonify({
        'resume_keywords': resume_keywords,
        'job_keywords': job_keywords,
        'matches': matches,
        'missing': missing
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
