import os
import tempfile
import streamlit as st
import markdown
import platform
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Load environment variables
load_dotenv()

# Retrieve API key from environment variables
API_KEY = os.getenv("GENAI_API_KEY")

# Check if API key is loaded correctly
if API_KEY is None or API_KEY.strip() == "":
    st.error("⚠️ API key not found in .env file. Please add GENAI_API_KEY to your .env file.")
else:
    # Setup Gemini API
    genai.configure(api_key=API_KEY)

# Streamlit page config
st.set_page_config(page_title="Gemini PDF Editor", layout="wide")

# Sidebar Info
st.sidebar.title("ℹ️ App Info")
st.sidebar.markdown("**Model**: `Gemini 2.0 Flash` via Google Generative AI API")
st.sidebar.markdown("**Powered by**: Streamlit, PyPDF2, ReportLab, Gemini 2.0 Flash")

st.title("📄 AI PDF Editor using Gemini 2.0 Flash ✨")
st.markdown("Upload a PDF ➡️ Provide a prompt ➡️ Generate and download an AI-edited PDF.")

# Function: Extract text from uploaded PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text.strip()

# Function: Edit content using Gemini 2.0 Flash API
def edit_with_gemini(text, prompt):
    try:
        inputs = f"{prompt}: {text}"
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(inputs)

        if not response or not hasattr(response, 'text'):
            return None, "❌ No response or empty content from Gemini API."

        return response.text, None

    except Exception as e:
        st.write("Exception details:", str(e))
        return None, f"⚠️ Exception: {str(e)}"

# Function: Convert Markdown to PDF using ReportLab
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import markdown
import re

def markdown_to_pdf(markdown_text, output_path):
    try:
        # Split markdown manually by line for better formatting control
        lines = markdown_text.split('\n')

        doc = SimpleDocTemplate(output_path, pagesize=letter)
        styles = getSampleStyleSheet()

        # Add custom styles
        styles.add(ParagraphStyle(
            name='CustomBody',
            fontName='Helvetica',
            fontSize=12,
            leading=14,
            spaceBefore=6,
            spaceAfter=6
        ))

        styles.add(ParagraphStyle(
            name='CodeBlock',
            fontName='Courier',
            fontSize=10,
            leading=12,
            backColor=colors.whitesmoke,
            leftIndent=10,
            rightIndent=10,
            spaceBefore=6,
            spaceAfter=6
        ))

        story = []
        code_block = []
        inside_code = False

        for line in lines:
            if line.strip().startswith("```"):
                # Toggle code block mode
                if inside_code:
                    # End code block
                    code = "\n".join(code_block)
                    story.append(Preformatted(code, styles['CodeBlock']))
                    story.append(Spacer(1, 12))
                    code_block = []
                    inside_code = False
                else:
                    inside_code = True
            elif inside_code:
                code_block.append(line)
            elif line.strip():
                story.append(Paragraph(line.strip(), styles['CustomBody']))
                story.append(Spacer(1, 12))

        doc.build(story)
        return True, None

    except Exception as e:
        return False, f"❌ PDF conversion error: {str(e)}"


# Function: Check if API key is configured
def is_api_key_configured():
    return API_KEY is not None and API_KEY.strip() != ""

# Upload PDF
pdf_file = st.file_uploader("📤 Upload a PDF file", type=["pdf"])

if pdf_file:
    extracted_text = extract_text_from_pdf(pdf_file)
    st.subheader("📃 Extracted Text")
    st.text_area("Text from PDF", extracted_text, height=200)

    if not is_api_key_configured():
        st.error("⚠️ API key not configured. Please add GENAI_API_KEY to your .env file.")
    else:
        st.subheader("✍️ Enter Instructions")
        prompt = st.text_input("e.g., Summarize, Fix grammar, Translate to Hindi")

        with st.expander("💡 Prompt Examples"):
            st.markdown("""
            - Summarize this document  
            - Fix grammatical errors  
            - Translate to Hindi  
            - Make it more formal  
            - Rephrase for 5th grade reading level  
            - Replace all instances of 'Akanksha' with 'Mohit'
            """)

        if st.button("✨ Edit with Gemini 2.0 Flash"):
            if not prompt:
                st.error("Please enter processing instructions.")
            else:
                with st.spinner("Generating..."):
                    edited_text, error = edit_with_gemini(extracted_text, prompt)
                if error:
                    st.error(error)
                elif edited_text:
                    st.session_state.edited_text = edited_text
                    st.success("✅ Successfully edited using Gemini 2.0 Flash!")
                else:
                    st.error("❌ No text was returned from the API.")

if "edited_text" in st.session_state and st.session_state.edited_text.strip():
    st.subheader("📝 Edited Output")
    st.text_area("Gemini 2.0 Flash Output", st.session_state.edited_text, height=300)

if st.button("Download PDF"):
    if "edited_text" in st.session_state and st.session_state.edited_text.strip():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
            output_path = tmp_pdf.name
            success, error = markdown_to_pdf(st.session_state.edited_text, output_path)
            if success:
                with open(output_path, "rb") as f:
                    st.download_button("Click to Download PDF", f, file_name="edited_output.pdf")
            else:
                st.error(f"PDF generation failed: {error}")
    else:
        st.warning("⚠️ No AI-edited content available to convert. Please edit the PDF first.")

