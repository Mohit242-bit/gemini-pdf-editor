import os
import tempfile
import streamlit as st
import pdfkit
import markdown
import platform
from PyPDF2 import PdfReader
from dotenv import load_dotenv
from google.generativeai import configure, GenerativeModel

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
configure(api_key=GOOGLE_API_KEY)
model = GenerativeModel("gemini-1.5-flash-latest")

# OS-aware wkhtmltopdf config
if platform.system() == "Windows":
    config = pdfkit.configuration(wkhtmltopdf=r"C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
else:
    config = pdfkit.configuration()  # Let it auto-detect on Linux/Streamlit Cloud

st.set_page_config(page_title="Gemini PDF Editor", layout="wide")
st.title("📄 AI PDF Editor using Gemini ✨")
st.markdown("Upload a PDF, write your prompt, and generate a beautifully formatted edited PDF using Gemini.")

# Function to extract text from PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() or ""
    return text

# Function to edit text using Gemini
def edit_with_gemini(text, prompt):
    response = model.generate_content([prompt, text])
    return response.text

# Function to convert markdown to PDF with style
def markdown_to_pdf(markdown_text, output_path):
    try:
        html = markdown.markdown(markdown_text, extensions=['extra', 'smarty'])
        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', sans-serif;
                    margin: 40px;
                    line-height: 1.8;
                    color: #333;
                }}
                h1, h2, h3, h4 {{
                    color: #4F8BF9;
                }}
                p {{
                    margin-bottom: 16px;
                }}
                ul, ol {{
                    margin-left: 25px;
                    margin-bottom: 16px;
                }}
                li {{
                    margin-bottom: 10px;
                }}
                strong {{
                    font-weight: bold;
                }}
                em {{
                    font-style: italic;
                }}
                code {{
                    font-family: 'Courier New', monospace;
                    background-color: #f4f4f4;
                    padding: 2px 4px;
                    border-radius: 4px;
                }}
                pre {{
                    background-color: #f4f4f4;
                    padding: 10px;
                    border-radius: 4px;
                    overflow-x: auto;
                }}
                blockquote {{
                    border-left: 4px solid #4F8BF9;
                    margin: 16px 0;
                    padding-left: 16px;
                    color: #555;
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
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        pdfkit.from_string(styled_html, output_path, configuration=config)
        return True, None
    except Exception as e:
        return False, f"Error converting to PDF: {str(e)}"

# File uploader
pdf_file = st.file_uploader("📤 Upload a PDF file", type=["pdf"])

if pdf_file:
    extracted_text = extract_text_from_pdf(pdf_file)
    st.subheader("📃 Extracted Text")
    st.text_area("Text from PDF", extracted_text, height=200)

    prompt = st.text_input("✍️ Enter your edit instructions (e.g., Summarize, Fix grammar, Translate to Hindi)")

    if st.button("✨ Edit with Gemini") and prompt:
        edited_text = edit_with_gemini(extracted_text, prompt)
        st.session_state.edited_text = edited_text
        st.success("✅ Gemini edited your content!")

# Show edited text and download button if available
if "edited_text" in st.session_state:
    st.subheader("📝 Edited Text")
    st.text_area("Output from Gemini", st.session_state.edited_text, height=300)

    if st.button("📥 Download Edited PDF"):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            output_path = tmp.name
            success, error = markdown_to_pdf(st.session_state.edited_text, output_path)
            if success:
                with open(output_path, "rb") as f:
                    st.download_button("⬇️ Download PDF", f, file_name="edited_output.pdf")
                st.success("🎉 PDF generated and ready!")
            else:
                st.error(error)
