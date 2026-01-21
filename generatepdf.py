from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime


def create_parse_friendly_pdf(filename="parse_friendly_student.pdf"):
    """Create a PDF that's optimized for the parser to extract data"""
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Simple header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(1*inch, height - 1*inch, "STUDENT INFORMATION RECORD")
    c.setFont("Helvetica", 10)
    c.drawString(1*inch, height - 1.2*inch, "St. Peter's College - Iligan City")
    
    # Add separator
    c.line(1*inch, height - 1.3*inch, 7.5*inch, height - 1.3*inch)
    
    y = height - 1.6*inch
    
    # Format that's easy to parse
    student_data = [
        ("STUDENT IDENTIFICATION", ""),
        ("ID Number: S2024-00123", ""),
        ("First Name: Juan Carlos", ""),
        ("Middle Name: Santos", ""),
        ("Last Name: Dela Cruz", ""),
        ("LRN: 123456789012", ""),
        ("", ""),
        ("PERSONAL DETAILS", ""),
        ("Date of Birth: 2008-05-15", ""),
        ("Gender: Male", ""),
        ("Contact Number: 09171234567", ""),
        ("Religion: Roman Catholic", ""),
        ("", ""),
        ("ADDRESS INFORMATION", ""),
        ("Home Address: 123 Main Street, Iligan City, Lanao del Norte", ""),
        ("", ""),
        ("PARENT INFORMATION", ""),
        ("Father Name: Jose Dela Cruz", ""),
        ("Mother Name: Maria Santos Dela Cruz", ""),
        ("", ""),
        ("ACADEMIC INFORMATION", ""),
        ("Grade Level: 10", ""),
        ("School Year: 2023-2024", ""),
        ("Status: Enrolled", ""),
    ]
    
    c.setFont("Helvetica", 11)
    for line, _ in student_data:
        if ":" in line:
            c.setFillColor(colors.black)
            c.drawString(1*inch, y, line)
        elif line and ":" not in line:
            c.setFillColor(colors.HexColor('#800000'))
            c.setFont("Helvetica-Bold", 12)
            c.drawString(1*inch, y, line)
            c.setFont("Helvetica", 11)
        y -= 0.25*inch
    
    # Footer note
    c.setFillColor(colors.gray)
    c.setFont("Helvetica", 8)
    c.drawString(1*inch, 0.5*inch, "This document is machine-readable. Fields are labeled for automatic processing.")
    
    c.save()
    print(f"Parse-friendly PDF created: {filename}")

# Create all three versions
if __name__ == "__main__":
    print("Creating formal student information PDFs...")
    try:
        create_formal_student_pdf()
        create_simple_formal_pdf()
        create_parse_friendly_pdf()
        print("\n✓ PDFs created successfully!")
        print("1. student_information_form.pdf - Full formal layout")
        print("2. simple_student_form.pdf - Simplified version")
        print("3. parse_friendly_student.pdf - Optimized for parsing")
        print("\nUse these to test the PDF import functionality.")
    except Exception as e:
        print(f"\n✗ Error creating PDFs: {e}")
        print("Make sure you have reportlab installed: pip install reportlab")