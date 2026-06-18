# File: backend/services/pdf_generator.py
# Purpose: Generate consulting-style 10-section PDF report using ReportLab
# Connects to: services/formulation.py (called from generate_pdf_report), database/db.py (Supabase upload)

import os
import io
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether,
)
from reportlab.platypus.flowables import HRFlowable
from backend.models.schemas import ReportRequest

# ── Brand colours ─────────────────────────────────────────────────────────────
NAVY    = colors.HexColor("#1B3A6B")
WHITE   = colors.white
LIGHT   = colors.HexColor("#F8F9FF")
GREEN   = colors.HexColor("#27AE60")
ORANGE  = colors.HexColor("#F39C12")
RED     = colors.HexColor("#E74C3C")
GREY    = colors.HexColor("#666666")
BORDER  = colors.HexColor("#DDE3F0")

PAGE_W, PAGE_H = A4


def _styles():
    base = getSampleStyleSheet()
    custom = {
        "cover_title": ParagraphStyle("cover_title", fontSize=32, textColor=WHITE,
                                       alignment=TA_CENTER, spaceAfter=8, fontName="Helvetica-Bold"),
        "cover_sub":   ParagraphStyle("cover_sub",   fontSize=14, textColor=WHITE,
                                       alignment=TA_CENTER, spaceAfter=6, fontName="Helvetica"),
        "cover_meta":  ParagraphStyle("cover_meta",  fontSize=11, textColor=colors.HexColor("#BBCCEE"),
                                       alignment=TA_CENTER, fontName="Helvetica"),
        "h1":          ParagraphStyle("h1", fontSize=16, textColor=NAVY, spaceBefore=14,
                                       spaceAfter=6, fontName="Helvetica-Bold"),
        "h2":          ParagraphStyle("h2", fontSize=12, textColor=NAVY, spaceBefore=10,
                                       spaceAfter=4, fontName="Helvetica-Bold"),
        "body":        ParagraphStyle("body", fontSize=9.5, textColor=colors.black,
                                       spaceAfter=5, leading=14, alignment=TA_JUSTIFY,
                                       fontName="Helvetica"),
        "caption":     ParagraphStyle("caption", fontSize=8.5, textColor=GREY,
                                       spaceAfter=3, fontName="Helvetica-Oblique"),
        "tag_green":   ParagraphStyle("tag_green", fontSize=9, textColor=GREEN, fontName="Helvetica-Bold"),
        "tag_orange":  ParagraphStyle("tag_orange", fontSize=9, textColor=ORANGE, fontName="Helvetica-Bold"),
        "tag_red":     ParagraphStyle("tag_red", fontSize=9, textColor=RED, fontName="Helvetica-Bold"),
        "bullet":      ParagraphStyle("bullet", fontSize=9.5, textColor=colors.black,
                                       leftIndent=12, spaceAfter=3, leading=14, fontName="Helvetica"),
    }
    return {**{k: base[k] for k in base.byName}, **custom}


def _divider(story, styles):
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 6))


def _section_header(story, styles, number: str, title: str):
    story.append(Spacer(1, 10))
    story.append(Table(
        [[Paragraph(f"{number}. {title}", styles["h1"])]],
        colWidths=[PAGE_W - 4*cm],
        style=TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), LIGHT),
            ("LEFTPADDING", (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("LINEBELOW", (0,0), (-1,-1), 2, NAVY),
        ])
    ))
    story.append(Spacer(1, 6))


def _score_color(score: float) -> colors.Color:
    if score >= 70:
        return GREEN
    elif score >= 40:
        return ORANGE
    return RED


def generate_pdf(request: ReportRequest) -> bytes:
    """
    Generate a 10-section consulting-style PDF report.
    Returns raw PDF bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    styles = _styles()
    story = []
    drug = request.drug_name.title()
    date_str = datetime.now().strftime("%d %B %Y")

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 0 — COVER PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    cover_table = Table(
        [
            [Paragraph("⚗ PharmIntel", styles["cover_title"])],
            [Paragraph("AI-Powered Pharmaceutical R&D Intelligence", styles["cover_sub"])],
            [Spacer(1, 20)],
            [Paragraph(f"<b>{drug}</b>", ParagraphStyle("ct2", fontSize=26, textColor=WHITE,
                        alignment=TA_CENTER, fontName="Helvetica-Bold"))],
            [Paragraph("Pharmaceutical R&D Intelligence Report", styles["cover_sub"])],
            [Spacer(1, 30)],
            [Paragraph(f"Generated: {date_str}", styles["cover_meta"])],
            [Paragraph("Powered by: spaCy NLP · Rule Engine · ChromaDB RAG · Gemini AI", styles["cover_meta"])],
            [Paragraph("Indian Market Focus | CDSCO/DCGI Regulatory Context", styles["cover_meta"])],
        ],
        colWidths=[PAGE_W - 4*cm],
        rowHeights=None,
        style=TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), NAVY),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("TOPPADDING", (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("LEFTPADDING", (0,0), (-1,-1), 30),
            ("RIGHTPADDING", (0,0), (-1,-1), 30),
            ("ROUNDEDCORNERS", [8]),
        ])
    )
    story.append(Spacer(1, 60))
    story.append(cover_table)
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — EXECUTIVE SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "1", "Executive Summary")

    papers = request.search_response.papers
    scores = request.formulation_response.scores if request.formulation_response else []
    top_form = scores[0].dosage_form.title() if scores else "N/A"
    top_score = scores[0].score if scores else 0
    gaps = request.market_data.get("market_gaps", []) if request.market_data else []
    gap_str = gaps[0] if gaps else "novel delivery systems"

    exec_summary = (
        f"This report presents a comprehensive pharmaceutical R&D intelligence analysis for <b>{drug}</b>, "
        f"generated by the PharmIntel AI platform. The analysis is based on {len(papers)} peer-reviewed "
        f"PubMed publications processed through a hybrid AI pipeline comprising spaCy NLP entity extraction, "
        f"a deterministic rule-based formulation scoring engine, ChromaDB vector retrieval, and Gemini AI interpretation. "
        f"The top-recommended dosage form is <b>{top_form}</b> (feasibility score: {top_score}/100), "
        f"supported by literature frequency analysis and excipient compatibility data. "
        f"Key Indian market opportunity identified: <b>{gap_str}</b>. "
        f"All recommendations in this report are grounded in retrieved literature and structured market data."
    )
    story.append(Paragraph(exec_summary, styles["body"]))
    _divider(story, styles)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — DRUG OVERVIEW
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "2", "Drug Overview")

    thera_class = request.market_data.get("therapeutic_class", "Not specified") if request.market_data else "Not specified"
    reg_auth = request.market_data.get("regulatory_authority", "CDSCO") if request.market_data else "CDSCO"

    overview_data = [
        ["Field", "Information"],
        ["Drug Name", drug],
        ["Therapeutic Class", thera_class],
        ["Regulatory Authority (India)", reg_auth],
        ["Registration Body", "Drug Controller General of India (DCGI)"],
        ["Market (India) Size", "$50 Billion (2024 estimate)"],
        ["PubMed Papers Analysed", str(len(papers))],
        ["Analysis Date", date_str],
    ]
    overview_table = Table(overview_data, colWidths=[7*cm, PAGE_W - 4*cm - 7*cm])
    overview_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("BACKGROUND", (0,1), (-1,-1), LIGHT),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT]),
        ("GRID", (0,0), (-1,-1), 0.5, BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(overview_table)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — LITERATURE FINDINGS
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "3", "Literature Findings")
    story.append(Paragraph(
        f"PubMed database search retrieved <b>{len(papers)}</b> peer-reviewed publications "
        f"relevant to {drug} formulation, pharmacokinetics, and drug delivery.",
        styles["body"]
    ))
    story.append(Spacer(1, 6))

    paper_rows = [["#", "Title", "Authors", "Year", "Journal"]]
    for i, p in enumerate(papers[:10], 1):
        title_short = (p.title[:55] + "…") if len(p.title) > 55 else p.title
        authors_short = (p.authors[:30] + "…") if len(p.authors) > 30 else p.authors
        journal_short = (p.journal[:25] + "…") if len(p.journal) > 25 else p.journal
        paper_rows.append([str(i), title_short, authors_short, str(p.year or ""), journal_short])

    paper_table = Table(paper_rows, colWidths=[0.5*cm, 7.5*cm, 4*cm, 1.2*cm, 3.8*cm])
    paper_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT]),
        ("GRID", (0,0), (-1,-1), 0.3, BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    story.append(paper_table)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — NLP EXTRACTION SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "4", "NLP Extraction Summary")
    story.append(Paragraph(
        "The following pharmaceutical entities were extracted from paper abstracts using the "
        "spaCy NLP pipeline with PhraseMatcher targeting our pharmaceutical knowledge base.",
        styles["body"]
    ))

    all_df: dict[str, int] = {}
    all_ex: dict[str, int] = {}
    for analysis in request.paper_analyses:
        for df in analysis.dosage_forms:
            all_df[df] = all_df.get(df, 0) + 1
        for ex in analysis.excipients:
            all_ex[ex] = all_ex.get(ex, 0) + 1

    nlp_data = [["Entity Type", "Entities Found", "Frequency"]]
    for form, cnt in sorted(all_df.items(), key=lambda x: -x[1])[:6]:
        nlp_data.append(["Dosage Form", form.title(), f"{cnt} paper(s)"])
    for ex, cnt in sorted(all_ex.items(), key=lambda x: -x[1])[:6]:
        nlp_data.append(["Excipient", ex.title(), f"{cnt} paper(s)"])

    if len(nlp_data) > 1:
        nlp_table = Table(nlp_data, colWidths=[4*cm, 9*cm, 4*cm])
        nlp_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), NAVY),
            ("TEXTCOLOR", (0,0), (-1,0), WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT]),
            ("GRID", (0,0), (-1,-1), 0.3, BORDER),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(nlp_table)
    else:
        story.append(Paragraph("No entities extracted. Run NLP Analysis first.", styles["caption"]))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — DOSAGE FORM FEASIBILITY ASSESSMENT
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "5", "Dosage Form Feasibility Assessment")
    story.append(Paragraph(
        "Scores are computed by a deterministic rule engine using four components: "
        "base score, literature frequency, score-booster keyword matching, and excipient "
        "compatibility — all from pharmaceutical knowledge bases. No AI was used in scoring.",
        styles["body"]
    ))
    story.append(Spacer(1, 6))

    score_rows = [["Dosage Form", "Score", "Tier", "Literature Mentions", "AI Reasoning"]]
    for s in scores[:10]:
        tier = "HIGH" if s.score >= 70 else ("MED" if s.score >= 40 else "LOW")
        reasoning_short = (s.reasoning[:70] + "…") if len(s.reasoning) > 70 else s.reasoning
        score_rows.append([
            s.dosage_form.title(),
            f"{s.score}/100",
            tier,
            str(s.frequency),
            reasoning_short,
        ])

    score_table = Table(score_rows, colWidths=[4*cm, 1.8*cm, 1.5*cm, 2*cm, 7.7*cm])
    score_table_style = [
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT]),
        ("GRID", (0,0), (-1,-1), 0.3, BORDER),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]
    # Colour-code the tier column
    for i, s in enumerate(scores[:10], 1):
        c = GREEN if s.score >= 70 else (ORANGE if s.score >= 40 else RED)
        score_table_style.append(("TEXTCOLOR", (2,i), (2,i), c))
        score_table_style.append(("FONTNAME", (2,i), (2,i), "Helvetica-Bold"))

    score_table.setStyle(TableStyle(score_table_style))
    story.append(score_table)

    if scores:
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            f"<b>Top Recommendation:</b> {request.formulation_response.top_recommendation} "
            f"(Score: {scores[0].score}/100)",
            styles["h2"]
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 6 — EXCIPIENT ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "6", "Excipient Analysis")
    story.append(Paragraph(
        "Excipients identified in the literature were matched against our pharmaceutical "
        "excipient knowledge base to verify formulation compatibility.",
        styles["body"]
    ))

    if all_ex:
        ex_rows = [["Excipient", "Role", "Compatible Dosage Forms", "Frequency"]]
        try:
            import json, os as _os
            ex_db_path = _os.path.join(_os.path.dirname(__file__), "..", "..", "data", "excipient_database.json")
            with open(ex_db_path) as f:
                ex_db = json.load(f)
        except Exception:
            ex_db = {}

        for ex_name, cnt in sorted(all_ex.items(), key=lambda x: -x[1])[:8]:
            db_entry = ex_db.get(ex_name.lower(), ex_db.get(ex_name, {}))
            role = db_entry.get("role", "Unknown")
            compat = ", ".join(db_entry.get("compatible_forms", [])[:3])
            ex_rows.append([ex_name.title(), role.title(), compat or "—", f"{cnt} paper(s)"])

        ex_table = Table(ex_rows, colWidths=[4*cm, 4*cm, 6*cm, 3*cm])
        ex_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), NAVY),
            ("TEXTCOLOR", (0,0), (-1,0), WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT]),
            ("GRID", (0,0), (-1,-1), 0.3, BORDER),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(ex_table)
    else:
        story.append(Paragraph("No excipients identified in the analysed literature.", styles["caption"]))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 7 — INDIAN MARKET OPPORTUNITY
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "7", "Indian Market Opportunity")

    if request.market_data:
        md = request.market_data
        story.append(Paragraph(
            f"<b>Regulatory Authority:</b> {md.get('regulatory_authority','CDSCO')} | "
            f"<b>Market Size:</b> ${md.get('market_size_usd_billion',50)}B",
            styles["body"]
        ))
        story.append(Spacer(1, 6))

        market_rows = [["Category", "Details"]]
        market_rows.append(["Approved Dosage Forms", ", ".join(md.get("approved_forms", []))])
        market_rows.append(["Major Brands", ", ".join(md.get("major_brands", [])[:5])])
        market_rows.append(["Dominant Manufacturer", md.get("dominant_manufacturer", "—")])
        market_rows.append(["Price Range (India)", md.get("approximate_price_inr", "—")])
        for i, gap in enumerate(md.get("market_gaps", []), 1):
            market_rows.append([f"R&D Gap {i}", gap])

        mkt_table = Table(market_rows, colWidths=[5*cm, PAGE_W - 4*cm - 5*cm])
        mkt_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), NAVY),
            ("TEXTCOLOR", (0,0), (-1,0), WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT]),
            ("GRID", (0,0), (-1,-1), 0.3, BORDER),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(mkt_table)

        ai_insight = md.get("ai_market_insight", "")
        if ai_insight:
            story.append(Spacer(1, 8))
            story.append(Paragraph("<b>AI Market Intelligence:</b>", styles["h2"]))
            story.append(Paragraph(ai_insight, styles["body"]))
    else:
        story.append(Paragraph("Market analysis not available. Run Market Intelligence module first.", styles["caption"]))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 8 — COMPETITOR INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "8", "Competitor Intelligence")

    if request.competitor_data and request.competitor_data.get("found_in_database"):
        cd = request.competitor_data
        comp_rows = [["Brand", "Available in India", "Dosage Forms"]]
        for b in cd.get("brand_details", [])[:8]:
            forms = ", ".join([f.title() for f in b.get("dosage_forms", [])][:3])
            comp_rows.append([b.get("brand",""), "Yes", forms])

        comp_table = Table(comp_rows, colWidths=[5*cm, 4*cm, PAGE_W - 4*cm - 9*cm])
        comp_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), NAVY),
            ("TEXTCOLOR", (0,0), (-1,0), WHITE),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 9),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [WHITE, LIGHT]),
            ("GRID", (0,0), (-1,-1), 0.3, BORDER),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        story.append(comp_table)

        ai_comp = cd.get("ai_competitive_summary","")
        if ai_comp:
            story.append(Spacer(1, 8))
            story.append(Paragraph("<b>AI Competitive Summary:</b>", styles["h2"]))
            story.append(Paragraph(ai_comp, styles["body"]))
    else:
        story.append(Paragraph("Run Competitor Intelligence module to populate this section.", styles["caption"]))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 9 — R&D RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    _section_header(story, styles, "9", "R&D Recommendations")

    recommendations = []
    if scores:
        top3 = [s for s in scores if s.score >= 40][:3]
        for s in top3:
            recommendations.append(
                f"<b>Prioritise {s.dosage_form.title()} development</b> — "
                f"Feasibility score {s.score}/100. {s.reasoning}"
            )
    if request.market_data:
        for gap in request.market_data.get("market_gaps", [])[:3]:
            recommendations.append(
                f"<b>Market gap opportunity:</b> {gap} — "
                f"Currently underrepresented in the Indian market per CDSCO-approved product list."
            )

    if not recommendations:
        recommendations.append("Complete all analysis modules to generate specific recommendations.")

    for rec in recommendations:
        story.append(Paragraph(f"• {rec}", styles["bullet"]))
        story.append(Spacer(1, 4))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 10 — METHODOLOGY & DISCLAIMER
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "10", "Methodology & Disclaimer")

    story.append(Paragraph("<b>AI Pipeline Architecture:</b>", styles["h2"]))
    pipeline = [
        "PubMed API (Biopython Entrez) → Literature retrieval",
        "spaCy NLP (en_core_web_sm + PhraseMatcher) → Entity extraction",
        "Rule Engine (Python) → Deterministic formulation scoring",
        "ChromaDB TF-IDF RAG → Literature context retrieval",
        "Gemini AI (gemini-2.0-flash) → Professional language interpretation",
        "ReportLab → PDF generation",
        "Supabase → Data persistence and report storage",
    ]
    for step in pipeline:
        story.append(Paragraph(f"• {step}", styles["bullet"]))

    story.append(Spacer(1, 8))
    story.append(Paragraph("<b>Disclaimer:</b>", styles["h2"]))
    story.append(Paragraph(
        "This report is generated for research and R&D intelligence purposes only. "
        "All formulation recommendations are based on literature analysis and rule-based scoring. "
        "They do not constitute regulatory advice or clinical guidance. "
        "Market data reflects publicly available information and database entries current at the time of analysis. "
        "Always conduct formal regulatory consultation with CDSCO/DCGI before product development.",
        styles["body"]
    ))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"PharmIntel Report — {drug} — Generated {date_str} | Confidential",
        ParagraphStyle("footer", fontSize=8, textColor=GREY, alignment=TA_CENTER)
    ))

    doc.build(story)
    return buf.getvalue()


async def save_and_upload_pdf(pdf_bytes: bytes, drug_name: str) -> dict:
    """
    Save PDF locally and upload to Supabase Storage.
    Returns local path and Supabase public URL.
    """
    # Save locally first
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    filename = f"pharmintel_{drug_name.lower().replace(' ','_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    local_path = os.path.join(reports_dir, filename)

    with open(local_path, "wb") as f:
        f.write(pdf_bytes)

    # Upload to Supabase Storage
    public_url = None
    try:
        from backend.database.db import get_db
        db = get_db()
        storage_path = f"reports/{filename}"
        db.storage.from_("reports").upload(
            path=storage_path,
            file=pdf_bytes,
            file_options={"content-type": "application/pdf"},
        )
        url_response = db.storage.from_("reports").get_public_url(storage_path)
        public_url = url_response
    except Exception as e:
        print(f"Supabase upload skipped: {e}")

    return {
        "filename": filename,
        "local_path": local_path,
        "public_url": public_url,
    }
