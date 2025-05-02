import io
import tempfile
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import json
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import logging

def generate_resume_pdf(resume_data):
    """Generate a PDF version of the resume from the given data"""
    try:
        # Ensure resume_data is a dict
        if isinstance(resume_data, str):
            resume_data = json.loads(resume_data)
            
        # Create a temporary file to store the PDF
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        styles.add(ParagraphStyle(
            name='Heading1',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        
        styles.add(ParagraphStyle(
            name='Heading2',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            textColor=colors.darkblue
        ))
        
        styles.add(ParagraphStyle(
            name='Normal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6
        ))
        
        # Build content elements
        elements = []
        
        # Personal information section
        personal_info = resume_data.get('personal_info', {})
        name = personal_info.get('name', '')
        elements.append(Paragraph(name, styles['Title']))
        
        contact_info = []
        if personal_info.get('email'):
            contact_info.append(personal_info.get('email'))
        if personal_info.get('phone'):
            contact_info.append(personal_info.get('phone'))
        if personal_info.get('location'):
            contact_info.append(personal_info.get('location'))
        
        elements.append(Paragraph(' | '.join(contact_info), styles['Normal']))
        
        if personal_info.get('summary'):
            elements.append(Spacer(1, 12))
            elements.append(Paragraph('Professional Summary', styles['Heading1']))
            elements.append(Paragraph(personal_info.get('summary'), styles['Normal']))
        
        # Experience section
        experience = resume_data.get('experience', [])
        if experience:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph('Professional Experience', styles['Heading1']))
            
            for job in experience:
                job_title = job.get('title', '')
                company = job.get('company', '')
                dates = f"{job.get('start_date', '')} - {job.get('end_date', '')}"
                
                elements.append(Paragraph(f"{job_title} at {company}", styles['Heading2']))
                elements.append(Paragraph(dates, styles['Normal']))
                
                if job.get('description'):
                    elements.append(Paragraph(job.get('description'), styles['Normal']))
                
                elements.append(Spacer(1, 8))
        
        # Education section
        education = resume_data.get('education', [])
        if education:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph('Education', styles['Heading1']))
            
            for edu in education:
                degree = edu.get('degree', '')
                institution = edu.get('institution', '')
                dates = f"{edu.get('start_date', '')} - {edu.get('end_date', '')}"
                
                elements.append(Paragraph(f"{degree} - {institution}", styles['Heading2']))
                elements.append(Paragraph(dates, styles['Normal']))
                
                if edu.get('description'):
                    elements.append(Paragraph(edu.get('description'), styles['Normal']))
                
                elements.append(Spacer(1, 8))
        
        # Skills section
        skills = resume_data.get('skills', [])
        if skills:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph('Skills', styles['Heading1']))
            
            # Format skills as a paragraph
            if isinstance(skills, list):
                skill_text = ', '.join(skills)
                elements.append(Paragraph(skill_text, styles['Normal']))
        
        # Build the PDF
        doc.build(elements)
        output.seek(0)
        return output
    
    except Exception as e:
        logging.error(f"Error generating PDF: {e}")
        # Create a simple error PDF
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = [Paragraph("Error generating resume PDF", styles['Title'])]
        doc.build(elements)
        output.seek(0)
        return output

def generate_resume_docx(resume_data):
    """Generate a DOCX version of the resume from the given data"""
    try:
        # Ensure resume_data is a dict
        if isinstance(resume_data, str):
            resume_data = json.loads(resume_data)
            
        # Create a new document
        doc = Document()
        
        # Set document margins
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.8)
            section.bottom_margin = Inches(0.8)
            section.left_margin = Inches(0.8)
            section.right_margin = Inches(0.8)
        
        # Personal information section
        personal_info = resume_data.get('personal_info', {})
        name = personal_info.get('name', '')
        
        # Add name as title
        title = doc.add_paragraph()
        title_run = title.add_run(name)
        title_run.font.size = Pt(18)
        title_run.font.bold = True
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add contact information
        contact_info = []
        if personal_info.get('email'):
            contact_info.append(personal_info.get('email'))
        if personal_info.get('phone'):
            contact_info.append(personal_info.get('phone'))
        if personal_info.get('location'):
            contact_info.append(personal_info.get('location'))
        
        contact = doc.add_paragraph()
        contact_run = contact.add_run(' | '.join(contact_info))
        contact_run.font.size = Pt(11)
        contact.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Add summary if available
        if personal_info.get('summary'):
            doc.add_heading('Professional Summary', level=1)
            doc.add_paragraph(personal_info.get('summary'))
        
        # Experience section
        experience = resume_data.get('experience', [])
        if experience:
            doc.add_heading('Professional Experience', level=1)
            
            for job in experience:
                job_title = job.get('title', '')
                company = job.get('company', '')
                dates = f"{job.get('start_date', '')} - {job.get('end_date', '')}"
                
                p = doc.add_paragraph()
                p.add_run(f"{job_title} at {company}").bold = True
                p.add_run(f"\n{dates}")
                
                if job.get('description'):
                    doc.add_paragraph(job.get('description'))
        
        # Education section
        education = resume_data.get('education', [])
        if education:
            doc.add_heading('Education', level=1)
            
            for edu in education:
                degree = edu.get('degree', '')
                institution = edu.get('institution', '')
                dates = f"{edu.get('start_date', '')} - {edu.get('end_date', '')}"
                
                p = doc.add_paragraph()
                p.add_run(f"{degree} - {institution}").bold = True
                p.add_run(f"\n{dates}")
                
                if edu.get('description'):
                    doc.add_paragraph(edu.get('description'))
        
        # Skills section
        skills = resume_data.get('skills', [])
        if skills:
            doc.add_heading('Skills', level=1)
            
            # Format skills as a paragraph
            if isinstance(skills, list):
                skill_text = ', '.join(skills)
                doc.add_paragraph(skill_text)
        
        # Save the document to a BytesIO object
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return output
    
    except Exception as e:
        logging.error(f"Error generating DOCX: {e}")
        # Create a simple error document
        doc = Document()
        doc.add_heading("Error generating resume", 0)
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return output
