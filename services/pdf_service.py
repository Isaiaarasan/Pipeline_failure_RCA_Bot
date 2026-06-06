import os
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class PDFService:
    @staticmethod
    def generate_rca_pdf(report):
        """
        Generates a beautiful, professionally formatted PDF of the RCA report.
        Returns a BytesIO stream containing the binary PDF content.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=54,  # 0.75 in
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )
        
        styles = getSampleStyleSheet()
        
        # Define Custom Color Palette
        primary_color = colors.HexColor("#1e293b")   # Slate 800
        secondary_color = colors.HexColor("#0f172a") # Slate 900
        accent_color = colors.HexColor("#3b82f6")    # Blue 500
        text_color = colors.HexColor("#334155")      # Slate 700
        light_bg = colors.HexColor("#f8fafc")        # Slate 50
        
        # Color coding for severity
        sev_lower = report.severity.lower()
        if "critical" in sev_lower:
            sev_color = colors.HexColor("#ef4444") # Red 500
        elif "high" in sev_lower:
            sev_color = colors.HexColor("#f97316") # Orange 500
        elif "medium" in sev_lower:
            sev_color = colors.HexColor("#eab308") # Yellow 500
        else:
            sev_color = colors.HexColor("#22c55e") # Green 500
            
        # Define Custom Styles
        title_style = ParagraphStyle(
            name='RcaTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=primary_color,
            alignment=TA_CENTER,
            spaceAfter=8
        )
        
        subtitle_style = ParagraphStyle(
            name='RcaSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#64748b"),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        h1_style = ParagraphStyle(
            name='RcaH1',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            leading=18,
            textColor=secondary_color,
            spaceBefore=14,
            spaceAfter=8,
            keepWithNext=True
        )
        
        body_style = ParagraphStyle(
            name='RcaBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=15,
            textColor=text_color,
            spaceAfter=8
        )
        
        code_style = ParagraphStyle(
            name='RcaCode',
            parent=styles['Normal'],
            fontName='Courier',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#0f172a"),
            spaceAfter=8
        )

        metadata_label_style = ParagraphStyle(
            name='MetaLabel',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#475569")
        )
        
        metadata_val_style = ParagraphStyle(
            name='MetaVal',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#0f172a")
        )

        story = []
        
        # Document Header
        story.append(Paragraph("PIPELINE FAILURE ROOT CAUSE ANALYSIS", title_style))
        story.append(Paragraph("Automated AI Incident Analysis & Resolution Report", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=accent_color, spaceAfter=15))
        
        # Summary Box / Metadata Table
        created_str = report.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") if report.created_at else "N/A"
        metadata_data = [
            [
                Paragraph("Report ID:", metadata_label_style),
                Paragraph(f"RCA-{report.id:04d}", metadata_val_style),
                Paragraph("Created At:", metadata_label_style),
                Paragraph(created_str, metadata_val_style)
            ],
            [
                Paragraph("Severity:", metadata_label_style),
                Paragraph(f"<font color='{sev_color.hexval()}'><b>{report.severity.upper()}</b></font>", metadata_val_style),
                Paragraph("Confidence Score:", metadata_label_style),
                Paragraph(f"<b>{report.confidence_score}</b>", metadata_val_style)
            ]
        ]
        
        meta_table = Table(metadata_data, colWidths=[1.2*inch, 2.3*inch, 1.2*inch, 2.3*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), light_bg),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#e2e8f0")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#f1f5f9")),
        ]))
        
        story.append(meta_table)
        story.append(Spacer(1, 20))
        
        # Section 1: Failure Summary
        story.append(Paragraph("1. Incident Summary", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
        story.append(Paragraph(report.failure_summary, body_style))
        story.append(Spacer(1, 12))
        
        # Section 2: Root Cause Analysis
        story.append(Paragraph("2. Root Cause Identification", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
        # Formatted Root Cause paragraph
        rc_text = report.root_cause.replace('\n', '<br/>')
        story.append(Paragraph(rc_text, body_style))
        story.append(Spacer(1, 12))
        
        # Section 3: Suspicious Code Changes (if exists in reports relationship)
        if report.github_analysis:
            story.append(Paragraph("3. Correlated GitHub Code Changes", h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
            
            commit_info = f"<b>Commit ID:</b> {report.github_analysis.commit_id}<br/>"
            changed_files = ", ".join(report.github_analysis.changed_files) if report.github_analysis.changed_files else "None"
            commit_info += f"<b>Changed Files:</b> {changed_files}"
            
            story.append(Paragraph(commit_info, body_style))
            story.append(Spacer(1, 6))
            
            diff_text = report.github_analysis.diff_summary
            if diff_text:
                # Format diff summary for PDF display safely
                safe_diff = diff_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
                # Wrap in Courier style table to simulate a code block
                diff_table_data = [[Paragraph(f"<font face='Courier' size='8'>{safe_diff}</font>", body_style)]]
                diff_table = Table(diff_table_data, colWidths=[7.0*inch])
                diff_table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#1e293b")),
                    ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
                    ('LEFTPADDING', (0,0), (-1,-1), 10),
                    ('RIGHTPADDING', (0,0), (-1,-1), 10),
                    ('TOPPADDING', (0,0), (-1,-1), 10),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 10),
                    ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#0f172a")),
                ]))
                story.append(diff_table)
            story.append(Spacer(1, 12))
            
        # Section 4: Fix Recommendation
        story.append(Paragraph("4. Recommended Resolution Path", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
        rec_text = report.recommendation.replace('\n', '<br/>')
        story.append(Paragraph(rec_text, body_style))
        story.append(Spacer(1, 12))
        
        # Section 5: Retry Steps
        story.append(Paragraph("5. Recommended Rerun/Retry Steps", h1_style))
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
        
        retry_text = report.retry_steps.replace('\n', '<br/>')
        # Display in a light border warning box style
        retry_table_data = [[Paragraph(retry_text, body_style)]]
        retry_table = Table(retry_table_data, colWidths=[7.0*inch])
        retry_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#fef3c7")), # Light Amber
            ('LEFTPADDING', (0,0), (-1,-1), 12),
            ('RIGHTPADDING', (0,0), (-1,-1), 12),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('BOX', (0,0), (-1,-1), 1.5, colors.HexColor("#f59e0b")), # Amber 500
        ]))
        story.append(retry_table)
        
        # Build document
        doc.build(story)
        buffer.seek(0)
        return buffer
