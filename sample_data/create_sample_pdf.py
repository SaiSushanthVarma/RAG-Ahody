from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch


def create_sample_pdf():
    doc = SimpleDocTemplate(
        "sample_data/board_report_q2_2024.pdf",
        pagesize=A4,
        title="NordMedia Group Board Report Q2 2024",
        author="Sarah Mitchell",
        subject="Board Report",
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("NordMedia Group", styles["Title"]))
    story.append(Paragraph("Board Report — Q2 2024", styles["Title"]))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("Prepared by: Sarah Mitchell, CEO", styles["Normal"]))
    story.append(Paragraph("Date: May 1, 2024", styles["Normal"]))
    story.append(Paragraph("Classification: Confidential", styles["Normal"]))
    story.append(Spacer(1, 0.3 * inch))

    story.append(Paragraph("1. Executive Summary", styles["Heading1"]))
    story.append(Paragraph(
        "NordMedia Group has delivered exceptional results in Q2 2024. CEO Sarah Mitchell "
        "presented the board with a comprehensive overview of strategic initiatives that have "
        "positioned NordMedia Group as the leading digital media company in Scandinavia. "
        "The AI platform launched in collaboration with DataBridge Solutions has exceeded "
        "all performance benchmarks set at the beginning of the year.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("2. Financial Performance", styles["Heading1"]))
    story.append(Paragraph(
        "CFO Marcus Johansson reported a 28% revenue increase compared to Q2 2023. "
        "Total revenue for the quarter reached 42 million SEK, driven by digital advertising "
        "growth and new partnership agreements. The Norway expansion through Oslo Media House "
        "contributed 8 million SEK in new revenue. Copenhagen Digital partnership added "
        "an additional 5 million SEK. Marcus Johansson confirmed that NordMedia Group is "
        "on track to exceed annual targets by Q3 2024.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("3. AI Platform Performance", styles["Heading1"]))
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
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("4. Organizational Updates", styles["Heading1"]))
    story.append(Paragraph(
        "Anna Bergström has formally taken over as Chief Technology Officer and has begun "
        "restructuring the technology team to support the AI platform expansion. Erik Lindqvist "
        "has successfully led the Gothenburg temporary office operations during the Stockholm "
        "headquarters renovation managed by Nordic Construction AB. The board expressed "
        "confidence in both appointments made by Sarah Mitchell in Q1 2024.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("5. Expansion Plans", styles["Heading1"]))
    story.append(Paragraph(
        "Sarah Mitchell presented the Scandinavia expansion roadmap to the board. "
        "Partnerships with Oslo Media House and Copenhagen Digital will be extended through "
        "2026. Peter Hansen from Oslo Media House and Maria Andersen from Copenhagen Digital "
        "have both signed letters of intent. Scandinavia Press, an early partner of NordMedia "
        "Group, will integrate with the AI platform in Q3 2024. The board unanimously approved "
        "the additional 5 million SEK investment proposed by Marcus Johansson for the expansion.",
        styles["Normal"]
    ))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("6. Outlook", styles["Heading1"]))
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