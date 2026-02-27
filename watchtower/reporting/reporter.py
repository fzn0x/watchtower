import json
import logging
from fpdf import FPDF
from watchtower.core.memory import MemoryStore

class PentestReport(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.set_text_color(44, 62, 80)
        self.cell(0, 10, 'Watchtower AI Pentest Report', border=False, align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def chapter_title(self, title):
        self.set_font('helvetica', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 10, f' {title}', border=False, fill=True)
        self.ln(12)

    def chapter_body(self, text):
        self.set_font('helvetica', '', 11)
        self.multi_cell(0, 6, text)
        self.ln(6)
        
    def add_finding(self, finding_num, target, title, severity, description, evidence):
        # Determine color for severity
        if severity.lower() == "critical":
            color = (255, 0, 0)
        elif severity.lower() == "high":
            color = (255, 128, 0)
        elif severity.lower() == "medium":
            color = (255, 204, 0)
        else:
            color = (0, 153, 204)

        self.set_font('helvetica', 'B', 14)
        self.set_text_color(0, 0, 0)
        self.cell(0, 10, f"Finding {finding_num}: {title}", ln=True)

        self.set_font('helvetica', 'B', 12)
        self.set_text_color(*color)
        self.cell(0, 8, f"Severity: {severity}", ln=True)

        self.set_font('helvetica', 'B', 11)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, f"Target: {target}", ln=True)
        
        self.ln(2)
        
        self.set_font('helvetica', 'B', 11)
        self.cell(0, 6, "Description:", ln=True)
        self.set_font('helvetica', '', 10)
        self.multi_cell(0, 6, description)
        
        self.ln(2)
        
        if evidence:
            self.set_font('helvetica', 'B', 11)
            self.cell(0, 6, "Evidence/Proof of Concept:", ln=True)
            self.set_font('courier', '', 9)
            self.set_fill_color(245, 245, 245)
            # Remove any special markdown code block characters if they exist
            evidence_clean = str(evidence).replace("```", "")
            self.multi_cell(0, 5, evidence_clean, fill=True)
        
        self.ln(10)

def generate_pdf_report(db_path: str, output_path: str):
    logging.info(f"Generating PDF report from database: {db_path}")
    memory = MemoryStore(db_path)
    findings = memory.get_all_findings()
    
    if not findings:
        logging.warning("No findings present in the local database to generate a report.")
        print(f"ERROR: No pentest findings were found in {db_path}.")
        return

    pdf = PentestReport()
    pdf.add_page()
    
    # Executive Summary section
    pdf.chapter_title("Executive Summary")
    pdf.chapter_body(f"This automated security penetration test utilized the Watchtower AI framework. The assessment discovered {len(findings)} total security findings.")
    
    # Iterate through SQLite DB
    finding_num = 1
    for target, vulnerability, details_json in findings:
        try:
            details = json.loads(details_json)
        except json.JSONDecodeError:
            details = {}
        
        severity = details.get("severity", "Unknown")
        description = details.get("description", "No description provided.")
        evidence = details.get("evidence", "")
        
        pdf.add_finding(
            finding_num=finding_num,
            target=target,
            title=vulnerability,
            severity=severity,
            description=description,
            evidence=evidence
        )
        finding_num += 1

    pdf.output(output_path)
    logging.info(f"PDF successfully exported to: {output_path}")
