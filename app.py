import os
import tempfile
import streamlit as st
import pdfkit
import markdown
import platform
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import google.generativeai as genai

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

# OS-aware wkhtmltopdf config
if platform.system() == "Windows":
    config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
else:
    config = pdfkit.configuration(wkhtmltopdf="/usr/bin/wkhtmltopdf")

# Streamlit page config
st.set_page_config(page_title="Gemini PDF Editor", layout="wide")

# Sidebar Info
st.sidebar.title("ℹ️ App Info")
st.sidebar.markdown("**Model**: `Gemini 2.0 Flash` via Google Generative AI API")
st.sidebar.markdown("**Powered by**: Streamlit, PyPDF2, pdfkit, Gemini 2.0 Flash")

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
        
        
        # Initialize Gemini model - Use gemini-1.5-flash for Gemini 2.0 Flash
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Call Gemini API for text generation
        response = model.generate_content(inputs)

        if not response or not hasattr(response, 'text'):
            return None, "❌ No response or empty content from Gemini API."

        return response.text, None

    except Exception as e:
        st.write("Exception details:", str(e))
        return None, f"⚠️ Exception: {str(e)}"

# Function: Convert Markdown to styled PDF
def markdown_to_pdf(markdown_text, output_path):
    try:
        html = markdown.markdown(markdown_text, extensions=['extra', 'smarty'])
        styled_html = f"""
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8">
        <style>
            @page {{
                margin: 1cm;
                background-color: #FFFFFF !important;
            }}
            body {{
                font-family: 'Segoe UI', sans-serif;
                margin: 40px;
                line-height: 1.8;
                color: #000000; /* Pure black text */
                background-color: #FFFFFF !important; /* Force white background */
            }}
            h1, h2, h3 {{ color: #000000; }}
            p {{ margin-bottom: 16px; }}
            ul, ol {{ margin-left: 25px; margin-bottom: 16px; }}
            li {{ margin-bottom: 10px; }}
            strong {{ font-weight: bold; }}
            em {{ font-style: italic; }}
            code {{
                font-family: 'Courier New', monospace;
                background-color: #f4f4f4;
                padding: 2px 4px;
                border-radius: 4px;
                color: #000000;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
                color: #000000;
            }}
            blockquote {{
                border-left: 4px solid #4F8BF9;
                margin: 16px 0;
                padding-left: 16px;
                color: #555;
                background-color: #FFFFFF !important;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 16px;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
                color: #000000;
            }}
            th {{ background-color: #f2f2f2; }}
        </style></head><body>{html}</body></html>
        """
        options = {
            'background': True,
            'no-background': False,
            'enable-local-file-access': True,
            'page-size': 'Letter',
            'encoding': 'UTF-8',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'print-media-type': True
        }
        pdfkit.from_string(styled_html, output_path, configuration=config, options=options)
        return True, None
    except Exception as e:
        return False, f"❌ PDF conversion error: {str(e)}"



# Function: Simple text to PDF without markdown conversion
def text_to_pdf(text, output_path):
    try:
        # Clean up the text - remove explanatory comments after the code block
        cleaned_text = ""
        in_code_block = False
        
        for line in text.split('\n'):
            # If we see a code block marker, we're either entering or exiting a code block
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
                
            # Only keep lines that are inside the code block
            if in_code_block:
                cleaned_text += line + '\n'
            
        # Further cleanup for specific cases
        cleaned_text = cleaned_text.replace('%This PRN seems unlikely', '%')
        
        # Simple HTML wrapping with styling to match MATLAB output
        styled_html = f"""
        <!DOCTYPE html>
        <html><head><meta charset="UTF-8">
        <style>
            @page {{
                margin: 1cm;
                background-color: #FFFFFF !important;
            }}
            body {{
                font-family: Courier, monospace;
                margin: 20px;
                line-height: 1.2;
                color: #000000;
                background-color: #FFFFFF !important;
            }}
            pre {{
                white-space: pre-wrap;
                font-family: Courier, monospace;
                font-size: 12px;
                color: #000000;
                background-color: #FFFFFF !important;
                margin: 0;
                padding: 0;
            }}
        </style></head>
        <body><pre>{cleaned_text}</pre></body></html>
        """
        
        # Options to match the original PDF
        options = {
            'background': True,
            'enable-local-file-access': True,
            'page-size': 'A4',
            'encoding': 'UTF-8',
            'margin-top': '0.5in',
            'margin-right': '0.5in',
            'margin-bottom': '0.5in',
            'margin-left': '0.5in',
            'no-outline': None,
            'disable-smart-shrinking': None
        }
        
        pdfkit.from_string(styled_html, output_path, configuration=config, options=options)
        return True, None
    except Exception as e:
        st.write("PDF Error details:", str(e))
        return False, f"❌ PDF conversion error: {str(e)}"

# Function to check if API key is configured
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

        # Prompt Suggestions
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

# Show Edited Text
if "edited_text" in st.session_state and st.session_state.edited_text.strip():
    st.subheader("📝 Edited Output")
    st.text_area("Gemini 2.0 Flash Output", st.session_state.edited_text, height=300)

if st.button("Download PDF"):
    if "edited_text" in st.session_state and st.session_state.edited_text.strip():
        output_path = "edited_output.pdf"
        
        if st.session_state.edited_text.strip().startswith("```") and st.session_state.edited_text.strip().endswith("```"):
            success, error = text_to_pdf(st.session_state.edited_text, output_path)
        else:
            success, error = markdown_to_pdf(st.session_state.edited_text, output_path)

        if success:
            with open(output_path, "rb") as f:
                st.download_button("Click to Download PDF", f, file_name="edited_output.pdf")
        else:
            st.error(f"PDF generation failed: {error}")
    else:
        st.warning("⚠️ No AI-edited content available to convert. Please edit the PDF first.")




