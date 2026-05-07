from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors


def create_sample_pdf():
    doc = SimpleDocTemplate(
        "sample_data/board_report_q2_2024.pdf",
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72,
        title="NordMedia Group Board Report Q2 2024",
        author="Sarah Mitchell",
        subject="Board Report",
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.grey,
        spaceAfter=4
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#1a1a2e'),
        spaceBefore=16,
        spaceAfter=6
    )

    story = []

    # Header
    story.append(Paragraph("NordMedia Group", title_style))
    story.append(Paragraph("Board Report — Q2 2024", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * inch))

    # Document info table
    data = [
        ["Prepared by:", "Sarah Mitchell, CEO"],
        ["Date:", "May 1, 2024"],
        ["Classification:", "Confidential — Board Members Only"],
        ["Period:", "April 1 – June 30, 2024"],
    ]
    
    table = Table(data, colWidths=[2*inch, 4*inch])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.3 * inch))

    # Financial summary table
    story.append(Paragraph("Financial Highlights Q2 2024", heading_style))
    
    fin_data = [
        ["Metric", "Q2 2024", "Q2 2023", "Change"],
        ["Total Revenue", "42M SEK", "32.8M SEK", "+28%"],
        ["Digital Advertising", "18M SEK", "12M SEK", "+50%"],
        ["Oslo Media House", "8M SEK", "0M SEK", "New"],
        ["Copenhagen Digital", "5M SEK", "0M SEK", "New"],
        ["Operating Margin", "22%", "18%", "+4pp"],
    ]
    
    fin_table = Table(fin_data, colWidths=[2.2*inch, 1.3*inch, 1.3*inch, 1.2*inch])
    fin_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(fin_table)
    story.append(Spacer(1, 0.2 * inch))

    # Section 1
    story.append(Paragraph("1. Executive Summary", heading_style))
    story.append(Paragraph(
        "NordMedia Group has delivered exceptional results in Q2 2024. CEO Sarah Mitchell "
        "presented the board with a comprehensive overview of strategic initiatives that have "
        "positioned NordMedia Group as the leading digital media company in Scandinavia. "
        "The AI platform launched in collaboration with DataBridge Solutions has exceeded "
        "all performance benchmarks set at the beginning of the year. Total revenue reached "
        "42 million SEK, representing a 28% increase compared to Q2 2023.",
        styles["Normal"]
    ))

    # Section 2
    story.append(Paragraph("2. Financial Performance", heading_style))
    story.append(Paragraph(
        "CFO Marcus Johansson reported a 28% revenue increase compared to Q2 2023. "
        "Total revenue for the quarter reached 42 million SEK, driven by digital advertising "
        "growth and new partnership agreements. The Norway expansion through Oslo Media House "
        "contributed 8 million SEK in new revenue. Copenhagen Digital partnership added "
        "an additional 5 million SEK. Marcus Johansson confirmed that NordMedia Group is "
        "on track to exceed annual targets by Q3 2024. The board unanimously approved the "
        "additional 5 million SEK investment proposed by Marcus Johansson for the Norway "
        "and Denmark expansion.",
        styles["Normal"]
    ))

    # Section 3
    story.append(Paragraph("3. AI Platform Performance", heading_style))
    story.append(Paragraph(
        "The AI content platform, built with DataBridge Solutions, went live in April 2024 "
        "under the leadership of CTO Anna Bergström and Head of Digital Operations Erik Lindqvist. "
        "Since launch, the platform has processed over 50,000 articles and reduced manual "
        "content operations by 58%, slightly ahead of the 60% target. DataBridge Solutions CEO "
        "James Carter attended the board meeting and presented a roadmap for Phase 2 features "
        "planned for Q3 2024. TechVentures AB representative Lisa Holm also attended and "
        "confirmed the extended technical support contract through 2025.",
        styles["Normal"]
    ))

    # Section 4
    story.append(Paragraph("4. Organizational Updates", heading_style))
    story.append(Paragraph(
        "Anna Bergström has formally taken over as Chief Technology Officer and has begun "
        "restructuring the technology team to support the AI platform expansion. Erik Lindqvist "
        "has successfully led the Gothenburg temporary office operations during the Stockholm "
        "headquarters renovation managed by Nordic Construction AB. The board expressed "
        "confidence in both appointments made by Sarah Mitchell in Q1 2024.",
        styles["Normal"]
    ))

    # Section 5
    story.append(Paragraph("5. Expansion Plans", heading_style))
    story.append(Paragraph(
        "Sarah Mitchell presented the Scandinavia expansion roadmap to the board. "
        "Partnerships with Oslo Media House and Copenhagen Digital will be extended through "
        "2026. Peter Hansen from Oslo Media House and Maria Andersen from Copenhagen Digital "
        "have both signed letters of intent. Scandinavia Press, an early partner of NordMedia "
        "Group, will integrate with the AI platform in Q3 2024.",
        styles["Normal"]
    ))

    # Section 6
    story.append(Paragraph("6. Outlook", heading_style))
    story.append(Paragraph(
        "NordMedia Group enters Q3 2024 in a strong position. Sarah Mitchell and Marcus "
        "Johansson will present the annual forecast update at the next board meeting in August. "
        "Erik Lindqvist and Anna Bergström will lead the Phase 2 AI platform development. "
        "The Stockholm headquarters renovation by Nordic Construction AB is expected to complete "
        "by September 2024, allowing all teams to reunite at the main office. NordMedia Group "
        "remains committed to its mission of leading digital media innovation across Scandinavia.",
        styles["Normal"]
    ))

    doc.build(story)
    print("PDF created: sample_data/board_report_q2_2024.pdf")


if __name__ == "__main__":
    create_sample_pdf()