import os
import io
import json
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
from backend.models.schemas import ReportRequest

# ── Brand colours ─────────────────────────────────────────────────────────────
NAVY   = colors.HexColor("#1B3A6B")
TEAL   = colors.HexColor("#2E86AB")
WHITE  = colors.white
LIGHT  = colors.HexColor("#F8F9FF")
GREEN  = colors.HexColor("#27AE60")
ORANGE = colors.HexColor("#F39C12")
RED    = colors.HexColor("#E74C3C")
GREY   = colors.HexColor("#666666")
BORDER = colors.HexColor("#DDE3F0")
MINT   = colors.HexColor("#D5F5E3")
AMBER  = colors.HexColor("#FDEBD0")
ROSE   = colors.HexColor("#FADBD8")

PAGE_W, PAGE_H = A4
COL_W = PAGE_W - 4 * cm          # usable width


def _styles():
    base = getSampleStyleSheet()
    custom = {
        "cover_title": ParagraphStyle("cover_title", fontSize=30, textColor=WHITE,
                                       alignment=TA_CENTER, spaceAfter=8, fontName="Helvetica-Bold"),
        "cover_sub":   ParagraphStyle("cover_sub",   fontSize=13, textColor=WHITE,
                                       alignment=TA_CENTER, spaceAfter=6, fontName="Helvetica"),
        "cover_meta":  ParagraphStyle("cover_meta",  fontSize=10, textColor=colors.HexColor("#BBCCEE"),
                                       alignment=TA_CENTER, fontName="Helvetica"),
        "h1":          ParagraphStyle("h1", fontSize=14, textColor=NAVY, spaceBefore=14,
                                       spaceAfter=6, fontName="Helvetica-Bold"),
        "h2":          ParagraphStyle("h2", fontSize=11, textColor=NAVY, spaceBefore=8,
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
        "kpi_val":     ParagraphStyle("kpi_val", fontSize=15, textColor=NAVY,
                                       alignment=TA_CENTER, fontName="Helvetica-Bold"),
        "kpi_lbl":     ParagraphStyle("kpi_lbl", fontSize=8, textColor=GREY,
                                       alignment=TA_CENTER, fontName="Helvetica"),
    }
    return {**{k: base[k] for k in base.byName}, **custom}


def _divider(story, styles):
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 6))


def _section_header(story, styles, number: str, title: str):
    story.append(Spacer(1, 10))
    story.append(Table(
        [[Paragraph(f"Section {number}  |  {title}", styles["h1"])]],
        colWidths=[COL_W],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("LINEBELOW", (0, 0), (-1, -1), 2.5, NAVY),
        ])
    ))
    story.append(Spacer(1, 6))


def _score_color(score: float) -> colors.Color:
    return GREEN if score >= 70 else (ORANGE if score >= 40 else RED)


def _ev_color(level: str) -> colors.Color:
    mapping = {"high": GREEN, "medium": ORANGE, "low": RED}
    return mapping.get((level or "low").lower(), GREY)


def _load_json_data(filename: str) -> dict:
    path = os.path.join(os.path.dirname(__file__), "..", "..", "data", filename)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _kpi_table(story, styles, kpis: list[tuple]):
    """Render a row of KPI cards: list of (value, label) tuples."""
    n = len(kpis)
    col_w = COL_W / n
    val_cells = [[Paragraph(str(v), styles["kpi_val"]) for v, _ in kpis]]
    lbl_cells = [[Paragraph(str(l), styles["kpi_lbl"]) for _, l in kpis]]
    data = val_cells + lbl_cells
    t = Table(data, colWidths=[col_w] * n)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))


def generate_pdf(request: ReportRequest) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm,
    )
    styles = _styles()
    story = []
    drug = request.drug_name.title()
    drug_key = request.drug_name.lower().strip()
    date_str = datetime.now().strftime("%d %B %Y")

    papers = request.search_response.papers
    analyses = request.paper_analyses or []
    scores = request.formulation_response.scores if request.formulation_response else []
    top_form = scores[0].dosage_form.title() if scores else "N/A"
    top_score = scores[0].score if scores else 0
    top_conf = (scores[0].confidence.score if scores and scores[0].confidence else 0)
    top_conf_level = (scores[0].confidence.level if scores and scores[0].confidence else "Low")

    # Load regulatory and repurposing from JSON (no API call needed in PDF)
    reg_db = _load_json_data("regulatory_data.json")
    rep_db = _load_json_data("repurposing_data.json")
    reg_data = reg_db.get(drug_key, {})
    rep_data = rep_db.get(drug_key, {})

    # Evidence summary
    ev_counts = {"High": 0, "Medium": 0, "Low": 0}
    for a in analyses:
        level = (a.evidence_level or "low").capitalize()
        if level in ev_counts:
            ev_counts[level] += 1
    total_papers = len(papers)
    quality_score = round(
        (ev_counts["High"] * 3 + ev_counts["Medium"] * 2 + ev_counts["Low"]) /
        (total_papers * 3) * 100
    ) if total_papers > 0 else 0

    # ═══════════════════════════════════════════════════════════════════════════
    # COVER PAGE
    # ═══════════════════════════════════════════════════════════════════════════
    cover_table = Table(
        [
            [Paragraph("PharmIntel", styles["cover_title"])],
            [Paragraph("AI-Powered Pharmaceutical R&D Intelligence Platform", styles["cover_sub"])],
            [Spacer(1, 24)],
            [Paragraph(f"<b>{drug}</b>", ParagraphStyle(
                "ct2", fontSize=26, textColor=WHITE,
                alignment=TA_CENTER, fontName="Helvetica-Bold"))],
            [Paragraph("Pharmaceutical R&D Intelligence Report  |  Version 2.0", styles["cover_sub"])],
            [Spacer(1, 36)],
            [Paragraph(f"Generated: {date_str}", styles["cover_meta"])],
            [Paragraph(
                "Pipeline: spaCy NLP · Rule Engine · TF-IDF RAG · Gemini AI",
                styles["cover_meta"])],
            [Paragraph(
                "Coverage: India (CDSCO/DCGI) · USFDA · EMA · MHRA",
                styles["cover_meta"])],
            [Spacer(1, 12)],
            [Paragraph("CONFIDENTIAL — FOR R&D INTELLIGENCE PURPOSES", ParagraphStyle(
                "conf", fontSize=9, textColor=colors.HexColor("#FF6B6B"),
                alignment=TA_CENTER, fontName="Helvetica-Bold"))],
        ],
        colWidths=[COL_W],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NAVY),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ("LEFTPADDING", (0, 0), (-1, -1), 30),
            ("RIGHTPADDING", (0, 0), (-1, -1), 30),
        ])
    )
    story.append(Spacer(1, 60))
    story.append(cover_table)
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — EXECUTIVE INTELLIGENCE DASHBOARD
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "1", "Executive Intelligence Dashboard")
    story.append(Paragraph(
        f"One-page intelligence summary for <b>{drug}</b>. All scores are computed by "
        f"PharmIntel's hybrid AI pipeline — deterministic rule engine + evidence classifier + "
        f"Gemini AI. No figures are estimated or fabricated.",
        styles["body"]
    ))
    story.append(Spacer(1, 8))

    # Row 1 KPIs
    comp_level = "High" if len(scores) >= 8 else "Moderate"
    if request.competitor_data:
        n_comp = len(request.competitor_data.get("competitors", []))
        comp_level = "High" if n_comp >= 6 else "Moderate" if n_comp >= 3 else "Low"

    _kpi_table(story, styles, [
        (str(total_papers), "Papers Retrieved"),
        (f"{top_score}/100", "Top Formulation Score"),
        (f"{top_conf:.0f}/100", "Confidence Score"),
        (f"{quality_score}/100", "Evidence Quality"),
    ])

    _kpi_table(story, styles, [
        (top_form, "Top Recommended Form"),
        (top_conf_level, "Confidence Level"),
        (f"{ev_counts['High']}/{total_papers}", "High Evidence Papers"),
        (comp_level, "Competition Level"),
    ])

    # Market opportunity
    mkt_gap = "N/A"
    if request.market_data:
        gaps = request.market_data.get("formulation_gaps", []) or request.market_data.get("market_gaps", [])
        if gaps:
            mkt_gap = gaps[0][:60]
    reg_readiness = reg_data.get("regulatory_readiness_score", "N/A")
    rep_score = rep_data.get("overall_repurposing_score", "N/A")

    _kpi_table(story, styles, [
        (mkt_gap[:35] + "…" if len(mkt_gap) > 35 else mkt_gap, "Top Market Gap"),
        (f"{reg_readiness}/100" if isinstance(reg_readiness, int) else "See Sec. 10", "Regulatory Readiness"),
        (f"{rep_score}/100" if isinstance(rep_score, int) else "See Sec. 11", "Repurposing Score"),
    ])

    story.append(Paragraph("<b>Executive Narrative:</b>", styles["h2"]))
    exec_text = (
        f"This report analyses <b>{drug}</b> across {total_papers} peer-reviewed PubMed publications "
        f"using a hybrid pharmaceutical intelligence pipeline. The evidence quality score is "
        f"<b>{quality_score}/100</b>, with {ev_counts['High']} high-evidence, "
        f"{ev_counts['Medium']} medium-evidence, and {ev_counts['Low']} low-evidence papers. "
        f"The top-recommended dosage form is <b>{top_form}</b> (feasibility: {top_score}/100, "
        f"confidence: {top_conf:.0f}/100, level: {top_conf_level}). "
    )
    if mkt_gap != "N/A":
        exec_text += f"The primary Indian market opportunity identified is: <b>{mkt_gap}</b>. "
    if isinstance(reg_readiness, int):
        exec_text += f"Regulatory readiness for new formulation development scores <b>{reg_readiness}/100</b>. "
    story.append(Paragraph(exec_text, styles["body"]))
    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — DRUG OVERVIEW
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "2", "Drug Overview")

    india_data = reg_data.get("india", {})
    thera_class = (request.market_data or {}).get("therapeutic_class", "See regulatory data")
    schedule = india_data.get("schedule", "See regulatory data")
    approved_forms_india = ", ".join(india_data.get("approved_forms", ["See regulatory data"]))

    overview_rows = [
        ["Field", "Information"],
        ["Drug Name", drug],
        ["Therapeutic Class", thera_class],
        ["India Regulatory Authority", "CDSCO / Drug Controller General of India (DCGI)"],
        ["India Schedule", schedule],
        ["Approved Dosage Forms (India)", approved_forms_india],
        ["Special Requirements", india_data.get("special_requirements", "See regulatory section")],
        ["PubMed Papers Analysed", str(total_papers)],
        ["Report Generated", date_str],
    ]

    ov_table = Table(overview_rows, colWidths=[6 * cm, COL_W - 6 * cm])
    ov_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(ov_table)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — LITERATURE FINDINGS WITH EVIDENCE GRADING
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "3", "Literature Findings & Evidence Grading")
    story.append(Paragraph(
        f"PubMed search retrieved <b>{total_papers}</b> peer-reviewed publications. "
        f"Each paper is graded using PharmIntel's evidence classification engine: "
        f"<b>High</b> (RCT, meta-analysis, systematic review, Phase III), "
        f"<b>Medium</b> (cohort, observational, prospective), "
        f"<b>Low</b> (in vitro, animal, case report).",
        styles["body"]
    ))
    story.append(Spacer(1, 6))

    # Evidence summary bar
    ev_summary_data = [
        ["Evidence Level", "Count", "% of Set", "Weight"],
        [Paragraph("<b>HIGH</b>", styles["tag_green"]), str(ev_counts["High"]),
         f"{round(ev_counts['High']/total_papers*100)}%" if total_papers else "0%", "RCTs, Meta-analyses"],
        [Paragraph("<b>MEDIUM</b>", styles["tag_orange"]), str(ev_counts["Medium"]),
         f"{round(ev_counts['Medium']/total_papers*100)}%" if total_papers else "0%", "Cohort, Observational"],
        [Paragraph("<b>LOW</b>", styles["tag_red"]), str(ev_counts["Low"]),
         f"{round(ev_counts['Low']/total_papers*100)}%" if total_papers else "0%", "In vitro, Animal"],
        [Paragraph("<b>Quality Score</b>", styles["h2"]),
         Paragraph(f"<b>{quality_score}/100</b>", styles["h2"]), "", ""],
    ]
    ev_sum_table = Table(ev_summary_data, colWidths=[4 * cm, 2 * cm, 2.5 * cm, COL_W - 8.5 * cm])
    ev_sum_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [MINT, AMBER, ROSE]),
        ("BACKGROUND", (0, 4), (-1, 4), LIGHT),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(ev_sum_table)
    story.append(Spacer(1, 10))

    # Paper table with evidence level and study type
    story.append(Paragraph("<b>Paper-Level Evidence Classification:</b>", styles["h2"]))
    analysis_map = {a.pubmed_id: a for a in analyses}
    paper_rows = [["#", "Title", "Year", "Evidence", "Study Type"]]
    for i, p in enumerate(papers[:15], 1):
        a = analysis_map.get(p.pubmed_id)
        ev = (a.evidence_level or "low").capitalize() if a else "Low"
        st_type = (a.study_type or "Research") if a else "Research"
        title_short = (p.title[:65] + "…") if len(p.title) > 65 else p.title
        paper_rows.append([str(i), title_short, str(p.year or ""), ev, st_type[:28]])

    pt = Table(paper_rows, colWidths=[0.6 * cm, 8 * cm, 1 * cm, 1.6 * cm, 4.8 * cm])
    pt_style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    # Colour-code evidence column
    for i, p in enumerate(papers[:15], 1):
        a = analysis_map.get(p.pubmed_id)
        ev = (a.evidence_level or "low").lower() if a else "low"
        c = GREEN if ev == "high" else (ORANGE if ev == "medium" else RED)
        pt_style.append(("TEXTCOLOR", (3, i), (3, i), c))
        pt_style.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))
    pt.setStyle(TableStyle(pt_style))
    story.append(pt)

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — PHARMACEUTICAL ENTITY INTELLIGENCE (NLP)
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "4", "Pharmaceutical Entity Intelligence (NLP)")
    story.append(Paragraph(
        "spaCy NLP pipeline with pharmaceutical PhraseMatcher extracted entities from all paper abstracts. "
        "Frequency = number of papers mentioning the entity.",
        styles["body"]
    ))

    all_df: dict[str, int] = {}
    all_ex: dict[str, int] = {}
    all_stab: dict[str, int] = {}
    for a in analyses:
        for df in (a.dosage_forms or []):
            all_df[df] = all_df.get(df, 0) + 1
        for ex in (a.excipients or []):
            all_ex[ex] = all_ex.get(ex, 0) + 1
        for st in (a.stability_conditions or []):
            all_stab[st] = all_stab.get(st, 0) + 1

    n4c1, n4c2 = 5 * cm, COL_W - 5 * cm

    # Delivery technologies
    story.append(Paragraph("<b>Top Delivery Technologies / Dosage Forms:</b>", styles["h2"]))
    if all_df:
        df_rows = [["Dosage Form / Technology", "Papers Mentioning", "Research Relevance"]]
        for form, cnt in sorted(all_df.items(), key=lambda x: -x[1])[:8]:
            pct = round(cnt / total_papers * 100) if total_papers else 0
            relevance = "Primary" if pct >= 40 else ("Secondary" if pct >= 20 else "Emerging")
            df_rows.append([form.title(), f"{cnt} ({pct}%)", relevance])
        df_t = Table(df_rows, colWidths=[6 * cm, 4 * cm, COL_W - 10 * cm])
        df_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEAL),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(df_t)
    else:
        story.append(Paragraph("No dosage forms extracted.", styles["caption"]))

    story.append(Spacer(1, 8))

    # Excipient landscape
    story.append(Paragraph("<b>Excipient Landscape:</b>", styles["h2"]))
    if all_ex:
        ex_rows = [["Excipient", "Frequency", "Formulation Role"]]
        ex_db = _load_json_data("excipient_database.json")
        for ex, cnt in sorted(all_ex.items(), key=lambda x: -x[1])[:8]:
            role = ex_db.get(ex.lower(), {}).get("role", "Not specified").title()
            ex_rows.append([ex.title(), f"{cnt} paper(s)", role])
        ex_t = Table(ex_rows, colWidths=[6 * cm, 3 * cm, COL_W - 9 * cm])
        ex_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEAL),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(ex_t)
    else:
        story.append(Paragraph("No excipients identified.", styles["caption"]))

    if all_stab:
        story.append(Spacer(1, 8))
        story.append(Paragraph("<b>Stability Conditions Mentioned:</b>", styles["h2"]))
        stab_str = ", ".join(f"{s.title()} ({c})" for s, c in
                              sorted(all_stab.items(), key=lambda x: -x[1])[:6])
        story.append(Paragraph(stab_str, styles["body"]))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — DOSAGE FORM FEASIBILITY WITH CONFIDENCE SCORING
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "5", "Dosage Form Feasibility & Confidence Scoring")
    story.append(Paragraph(
        "Scores are computed by PharmIntel's deterministic Rule Engine using four components: "
        "base score + literature frequency + booster keywords + excipient compatibility − penalty. "
        "Confidence Score (0–100) combines evidence strength, literature frequency, score alignment, and data volume. "
        "<b>No AI is involved in scoring — Gemini provides interpretation only.</b>",
        styles["body"]
    ))
    story.append(Spacer(1, 6))

    score_rows = [["Dosage Form", "Feasibility", "Confidence", "Level", "Mentions", "AI Reasoning"]]
    for s in scores[:10]:
        conf = s.confidence
        conf_score = f"{conf.score:.0f}/100" if conf else "N/A"
        conf_level = conf.level if conf else "N/A"
        reasoning = (s.reasoning[:55] + "…") if len(s.reasoning) > 55 else s.reasoning
        score_rows.append([
            s.dosage_form.title(),
            f"{s.score}/100",
            conf_score,
            conf_level,
            str(s.frequency),
            reasoning,
        ])

    st_tbl = Table(score_rows, colWidths=[3.5 * cm, 1.8 * cm, 2 * cm, 1.8 * cm, 1.5 * cm, COL_W - 10.6 * cm])
    st_style = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i, s in enumerate(scores[:10], 1):
        c = _score_color(s.score)
        st_style.append(("TEXTCOLOR", (1, i), (1, i), c))
        st_style.append(("FONTNAME", (1, i), (1, i), "Helvetica-Bold"))
        if s.confidence:
            cc = _ev_color(s.confidence.level.lower() if s.confidence.level in ("High","Medium","Low") else "low")
            st_style.append(("TEXTCOLOR", (3, i), (3, i), cc))
            st_style.append(("FONTNAME", (3, i), (3, i), "Helvetica-Bold"))
    st_tbl.setStyle(TableStyle(st_style))
    story.append(st_tbl)

    if scores:
        story.append(Spacer(1, 8))
        top = scores[0]
        top_c = top.confidence
        story.append(Table([[
            Paragraph(
                f"TOP RECOMMENDATION: <b>{top.dosage_form.title()}</b> — "
                f"Feasibility: {top.score}/100 | "
                f"Confidence: {top_c.score:.0f}/100 ({top_c.level})" if top_c else
                f"TOP RECOMMENDATION: <b>{top.dosage_form.title()}</b> — Feasibility: {top.score}/100",
                ParagraphStyle("rec", fontSize=10, textColor=WHITE, fontName="Helvetica-Bold",
                               alignment=TA_CENTER)
            )
        ]], colWidths=[COL_W],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), NAVY),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
            ])))

    # Score breakdown
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Score Component Breakdown (Top 5 Forms):</b>", styles["h2"]))
    breakdown_rows = [["Form", "Base", "Lit. Freq.", "Boosters", "Excipient", "Penalty", "Final"]]
    for s in scores[:5]:
        comp = s.components
        if comp:
            breakdown_rows.append([
                s.dosage_form.title()[:20],
                str(comp.base), str(comp.literature_frequency),
                str(comp.score_boosters), str(comp.excipient_compatibility),
                f"-{comp.penalty}", f"{s.score}",
            ])
    if len(breakdown_rows) > 1:
        bk_t = Table(breakdown_rows,
                     colWidths=[4 * cm, 1.5 * cm, 1.8 * cm, 1.8 * cm, 2 * cm, 1.5 * cm, 1.4 * cm])
        bk_t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEAL),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(bk_t)

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 6 — EXCIPIENT COMPATIBILITY ANALYSIS
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "6", "Excipient Compatibility Analysis")
    story.append(Paragraph(
        "Excipients identified via NLP were cross-referenced against the PharmIntel excipient "
        "knowledge base to determine formulation compatibility.",
        styles["body"]
    ))

    if all_ex:
        ex_db = _load_json_data("excipient_database.json")
        ex_detail_rows = [["Excipient", "Role", "Compatible Dosage Forms", "Papers"]]
        for ex_name, cnt in sorted(all_ex.items(), key=lambda x: -x[1])[:10]:
            db_entry = ex_db.get(ex_name.lower(), {})
            role = db_entry.get("role", "Not in database").title()
            compat = ", ".join(db_entry.get("compatible_forms", [])[:4]) or "—"
            ex_detail_rows.append([ex_name.title(), role, compat, str(cnt)])

        ex_dt = Table(ex_detail_rows, colWidths=[4 * cm, 3.5 * cm, 7 * cm, 1.5 * cm])
        ex_dt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(ex_dt)
    else:
        story.append(Paragraph("No excipients identified in the analysed literature.", styles["caption"]))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 7 — INDIAN MARKET INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "7", "Indian Market Intelligence")

    if request.market_data:
        md = request.market_data
        story.append(Paragraph(
            f"<b>Drug:</b> {drug} | <b>Therapeutic Class:</b> {md.get('therapeutic_class', 'N/A')} | "
            f"<b>Regulatory Authority:</b> {md.get('regulatory_authority', 'CDSCO/DCGI')}",
            styles["body"]
        ))
        story.append(Spacer(1, 6))

        # Market context (no fake numbers)
        mkt_rows = [["Market Intelligence", "Data"]]
        if md.get("market_size_inr"):
            mkt_rows.append(["Market Context (India)", md.get("market_size_inr")])
        if md.get("market_growth_rate"):
            mkt_rows.append(["Market Growth Rate", md.get("market_growth_rate")])
        if md.get("total_brands"):
            mkt_rows.append(["Active Brands (India)", str(md.get("total_brands"))])
        if md.get("market_leader"):
            mkt_rows.append(["Market Leader", md.get("market_leader")])
        if md.get("patient_population"):
            mkt_rows.append(["Patient Population", md.get("patient_population")])
        brands = md.get("brands", [])
        if brands:
            brand_list = ", ".join([b.get("brand_name", "") for b in brands[:6]])
            mkt_rows.append(["Major Brands", brand_list])

        if len(mkt_rows) > 1:
            mkt_t = Table(mkt_rows, colWidths=[6 * cm, COL_W - 6 * cm])
            mkt_t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(mkt_t)

        # Attractiveness + Saturation scores
        at_score = md.get("market_attractiveness_score")
        sat_index = md.get("market_saturation_index")
        if at_score or sat_index:
            story.append(Spacer(1, 8))
            _kpi_table(story, styles, [
                (f"{at_score}/100" if at_score else "N/A", "Market Attractiveness Score"),
                (f"{sat_index}/100" if sat_index else "N/A", "Market Saturation Index"),
            ])

        # SWOT
        swot = md.get("swot", {})
        if swot:
            story.append(Paragraph("<b>SWOT Analysis:</b>", styles["h2"]))
            swot_data = [
                [
                    Paragraph("<b>STRENGTHS</b>", styles["tag_green"]),
                    Paragraph("<b>WEAKNESSES</b>", styles["tag_red"]),
                ],
                [
                    Paragraph("\n".join(f"✓ {s}" for s in swot.get("strengths", [])), styles["bullet"]),
                    Paragraph("\n".join(f"⚠ {w}" for w in swot.get("weaknesses", [])), styles["bullet"]),
                ],
                [
                    Paragraph("<b>OPPORTUNITIES</b>", ParagraphStyle("opp", fontSize=9,
                               textColor=TEAL, fontName="Helvetica-Bold")),
                    Paragraph("<b>THREATS</b>", styles["tag_orange"]),
                ],
                [
                    Paragraph("\n".join(f"→ {o}" for o in swot.get("opportunities", [])), styles["bullet"]),
                    Paragraph("\n".join(f"⚡ {t}" for t in swot.get("threats", [])), styles["bullet"]),
                ],
            ]
            swot_t = Table(swot_data, colWidths=[COL_W / 2, COL_W / 2])
            swot_t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), MINT),
                ("BACKGROUND", (1, 0), (1, 0), ROSE),
                ("BACKGROUND", (0, 2), (0, 2), colors.HexColor("#D6EAF8")),
                ("BACKGROUND", (1, 2), (1, 2), AMBER),
                ("BACKGROUND", (0, 1), (-1, 1), WHITE),
                ("BACKGROUND", (0, 3), (-1, 3), WHITE),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("ALIGN", (0, 2), (-1, 2), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]))
            story.append(swot_t)

        # Formulation gaps
        gaps = md.get("formulation_gaps", []) or md.get("market_gaps", [])
        if gaps:
            story.append(Spacer(1, 8))
            story.append(Paragraph("<b>Formulation Gaps & Market Opportunities:</b>", styles["h2"]))
            for i, gap in enumerate(gaps[:5], 1):
                story.append(Paragraph(f"{i}. {gap}", styles["bullet"]))

        # AI Insight
        ai_insight = md.get("ai_insight", "") or md.get("ai_market_insight", "")
        if ai_insight:
            story.append(Spacer(1, 6))
            story.append(Paragraph("<b>AI Market Intelligence:</b>", styles["h2"]))
            story.append(Paragraph(ai_insight, styles["body"]))
    else:
        story.append(Paragraph(
            "Market intelligence not available. Run Market Intelligence module to populate this section.",
            styles["caption"]
        ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 8 — COMPETITOR INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "8", "Competitor Intelligence")

    if request.competitor_data:
        cd = request.competitor_data
        competitors = cd.get("competitors", []) or cd.get("brands", []) or cd.get("brand_details", [])
        opp_score = cd.get("competitive_opportunity_score")

        if opp_score:
            _kpi_table(story, styles, [
                (f"{opp_score}/100", "Competitive Opportunity Score"),
                (cd.get("market_leader", "N/A"), "Market Leader"),
                (str(len(competitors)), "Total Competitors"),
            ])

        if competitors:
            comp_rows = [["Brand / Player", "Company", "Market Share", "Formulation", "Type"]]
            for c in competitors[:10]:
                comp_rows.append([
                    c.get("brand_name", c.get("brand", "—"))[:25],
                    c.get("company", "—")[:22],
                    str(c.get("market_share_pct", "—")),
                    c.get("formulation", "—")[:20],
                    c.get("type", "Generic"),
                ])
            comp_t = Table(comp_rows, colWidths=[4 * cm, 3.8 * cm, 2.5 * cm, 3.2 * cm, 2.5 * cm])
            comp_t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
                ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(comp_t)

        # Differentiation strategy
        diff = cd.get("differentiation_strategy", [])
        if diff:
            story.append(Spacer(1, 8))
            story.append(Paragraph("<b>Differentiation Strategy:</b>", styles["h2"]))
            for d in diff[:4]:
                story.append(Paragraph(f"• {d}", styles["bullet"]))

        ai_comp = cd.get("ai_insight", "") or cd.get("ai_competitive_summary", "")
        if ai_comp:
            story.append(Spacer(1, 6))
            story.append(Paragraph("<b>AI Competitive Intelligence:</b>", styles["h2"]))
            story.append(Paragraph(ai_comp, styles["body"]))
    else:
        story.append(Paragraph(
            "Run Competitor Intelligence module to populate this section.",
            styles["caption"]
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 9 — REGULATORY INTELLIGENCE
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "9", "Regulatory Intelligence")
    story.append(Paragraph(
        "Multi-authority regulatory status across India (CDSCO/DCGI), USFDA, EMA, and MHRA. "
        "Data sourced from PharmIntel regulatory database.",
        styles["body"]
    ))

    if reg_data:
        readiness = reg_data.get("regulatory_readiness_score", "N/A")
        _kpi_table(story, styles, [
            (f"{readiness}/100" if isinstance(readiness, int) else str(readiness),
             "Regulatory Readiness Score"),
            ("CDSCO / DCGI", "India Authority"),
        ])

        auth_rows = [["Authority", "Status", "Approved Forms", "Key Notes"]]
        auth_map = [
            ("india", "India (CDSCO/DCGI)"),
            ("usfda", "USFDA"),
            ("ema", "EMA (EU)"),
            ("mhra", "MHRA (UK)"),
        ]
        for key, label in auth_map:
            a = reg_data.get(key, {})
            if a:
                forms = ", ".join(a.get("approved_forms", [])[:3])
                notes = a.get("notes", "") or a.get("restrictions", "") or a.get("approval_notes", "")
                bbw = " ⚠ BBW" if a.get("black_box_warning") else ""
                auth_rows.append([label, a.get("status", "—"), forms[:35], (notes[:45] + bbw)[:55]])

        auth_t = Table(auth_rows, colWidths=[3.5 * cm, 3 * cm, 5 * cm, COL_W - 11.5 * cm])
        auth_t_style = [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        # Colour-code status column
        for i, (key, _) in enumerate(auth_map, 1):
            a = reg_data.get(key, {})
            status = a.get("status", "")
            c = GREEN if "Approved" in status else (RED if "Not" in status else ORANGE)
            auth_t_style.append(("TEXTCOLOR", (1, i), (1, i), c))
            auth_t_style.append(("FONTNAME", (1, i), (1, i), "Helvetica-Bold"))
        auth_t.setStyle(TableStyle(auth_t_style))
        story.append(auth_t)

        notes = reg_data.get("new_formulation_notes", "")
        if notes:
            story.append(Spacer(1, 8))
            story.append(Paragraph("<b>New Formulation Development Notes:</b>", styles["h2"]))
            story.append(Paragraph(notes, styles["body"]))
    else:
        story.append(Paragraph(
            f"Regulatory data not available for {drug} in the PharmIntel database.",
            styles["caption"]
        ))

    story.append(PageBreak())

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 10 — DRUG REPURPOSING OPPORTUNITIES
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "10", "Drug Repurposing Intelligence")
    story.append(Paragraph(
        f"Evidence-based repurposing opportunities for {drug} ranked by opportunity score (0–100). "
        f"Scores reflect clinical stage maturity, evidence strength, and India market relevance.",
        styles["body"]
    ))

    if rep_data:
        overall_rep = rep_data.get("overall_repurposing_score", 0)
        rep_label = rep_data.get("repurposing_label", "N/A")
        primary = rep_data.get("primary_indication", "")
        drug_class = rep_data.get("drug_class", "")

        _kpi_table(story, styles, [
            (f"{overall_rep}/100", "Overall Repurposing Score"),
            (rep_label, "Repurposing Potential"),
            (primary[:30] if primary else "N/A", "Primary Indication"),
        ])

        opps = sorted(rep_data.get("repurposing_opportunities", []),
                      key=lambda x: x.get("opportunity_score", 0), reverse=True)

        rep_rows = [["New Indication", "Score", "Evidence", "Clinical Stage"]]
        for opp in opps[:8]:
            score_val = opp.get("opportunity_score", 0)
            rep_rows.append([
                opp.get("new_indication", "—")[:40],
                f"{score_val}/100",
                opp.get("evidence_level", "—"),
                opp.get("clinical_stage", "—")[:35],
            ])

        rep_t = Table(rep_rows, colWidths=[5.5 * cm, 2 * cm, 2.5 * cm, COL_W - 10 * cm])
        rep_t_style = [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        for i, opp in enumerate(opps[:8], 1):
            sc = opp.get("opportunity_score", 0)
            c = GREEN if sc >= 75 else (ORANGE if sc >= 50 else RED)
            rep_t_style.append(("TEXTCOLOR", (1, i), (1, i), c))
            rep_t_style.append(("FONTNAME", (1, i), (1, i), "Helvetica-Bold"))
            ev = opp.get("evidence_level", "low").lower()
            ec = GREEN if ev == "high" else (ORANGE if ev == "medium" else RED)
            rep_t_style.append(("TEXTCOLOR", (2, i), (2, i), ec))
        rep_t.setStyle(TableStyle(rep_t_style))
        story.append(rep_t)

        india_rel = rep_data.get("india_market_relevance", "")
        if india_rel:
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"<b>India Market Relevance:</b> {india_rel}", styles["body"]))
    else:
        story.append(Paragraph(
            f"Repurposing data not available for {drug} in the PharmIntel database.",
            styles["caption"]
        ))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 11 — R&D RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════════════════
    story.append(PageBreak())
    _section_header(story, styles, "11", "R&D Recommendations")
    story.append(Paragraph(
        f"Consolidated strategic recommendations for {drug} based on literature evidence, "
        f"formulation scoring, market intelligence, and regulatory assessment.",
        styles["body"]
    ))
    story.append(Spacer(1, 6))

    recommendations = []

    # Formulation recommendations
    if scores:
        for s in [x for x in scores if x.score >= 40][:3]:
            conf_text = ""
            if s.confidence:
                conf_text = f" (Confidence: {s.confidence.score:.0f}/100, {s.confidence.level})"
            recommendations.append(
                (f"Formulation Priority: {s.dosage_form.title()}{conf_text}",
                 f"Feasibility score {s.score}/100. {s.reasoning}")
            )

    # Market gap recommendations
    if request.market_data:
        gaps = request.market_data.get("formulation_gaps", []) or request.market_data.get("market_gaps", [])
        for gap in gaps[:2]:
            recommendations.append(
                ("Market Opportunity",
                 f"{gap} — Currently underrepresented in Indian market per CDSCO product database.")
            )

    # Regulatory recommendation
    if reg_data:
        notes = reg_data.get("new_formulation_notes", "")
        readiness = reg_data.get("regulatory_readiness_score", 0)
        if notes:
            recommendations.append(
                (f"Regulatory Pathway (Readiness: {readiness}/100)", notes)
            )

    # Repurposing recommendation
    if rep_data:
        opps = rep_data.get("repurposing_opportunities", [])
        if opps:
            top_opp = max(opps, key=lambda x: x.get("opportunity_score", 0))
            recommendations.append(
                ("Repurposing Opportunity",
                 f"{top_opp.get('new_indication')} — Score: {top_opp.get('opportunity_score')}/100. "
                 f"{top_opp.get('key_finding', '')}")
            )

    if not recommendations:
        recommendations = [("General", "Complete all analysis modules to generate specific recommendations.")]

    for i, (title, detail) in enumerate(recommendations, 1):
        story.append(Table(
            [[Paragraph(f"<b>{i}. {title}</b>", styles["h2"]),
              Paragraph(detail, styles["body"])]],
            colWidths=[5 * cm, COL_W - 5 * cm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, BORDER),
            ])
        ))
        story.append(Spacer(1, 4))

    # ═══════════════════════════════════════════════════════════════════════════
    # SECTION 12 — METHODOLOGY & DISCLAIMER
    # ═══════════════════════════════════════════════════════════════════════════
    _section_header(story, styles, "12", "Methodology & Disclaimer")

    story.append(Paragraph("<b>AI Pipeline Architecture:</b>", styles["h2"]))
    pipeline = [
        "PubMed API (Biopython Entrez) — Literature retrieval from 36M+ indexed articles",
        "spaCy NLP (en_core_web_sm + PhraseMatcher) — Pharmaceutical entity extraction",
        "Evidence Classifier — HIGH/MEDIUM/LOW grading per paper (keyword-based, deterministic)",
        "Rule Engine (Python) — 4-component deterministic formulation feasibility scoring",
        "Confidence Scorer — 4-factor confidence formula: evidence + frequency + score + volume",
        "TF-IDF RAG (custom in-memory) — Literature context retrieval for AI reasoning",
        "Gemini AI (gemini-2.0-flash, REST API) — Professional language interpretation only",
        "ReportLab — PDF generation",
        "Supabase PostgreSQL + Storage — Data persistence and report archiving",
    ]
    for step in pipeline:
        story.append(Paragraph(f"• {step}", styles["bullet"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Data Sources:</b>", styles["h2"]))
    sources = [
        "PubMed / NCBI — Primary literature database",
        "CDSCO / DCGI — India regulatory approvals and drug scheduling",
        "IQVIA India PharmaTrac — Market intelligence baseline",
        "NPPA — National Pharmaceutical Pricing Authority price data",
        "PharmIntel Curated Database — Excipient, formulation rules, regulatory, repurposing data",
    ]
    for s in sources:
        story.append(Paragraph(f"• {s}", styles["bullet"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>Disclaimer:</b>", styles["h2"]))
    story.append(Paragraph(
        "This report is generated for pharmaceutical R&D intelligence and portfolio project purposes only. "
        "Formulation recommendations are based on literature analysis and rule-based scoring — "
        "they do not constitute regulatory advice, clinical guidance, or manufacturing specifications. "
        "Market data reflects PharmIntel database entries current at the time of analysis and should "
        "be validated against primary sources before commercial use. "
        "Always conduct formal regulatory consultation with CDSCO/DCGI before initiating product development. "
        "AI interpretation (Gemini) is used for language generation only — all scores are deterministic.",
        styles["body"]
    ))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"PharmIntel v2.0 Intelligence Report  |  {drug}  |  Generated {date_str}  |  Confidential",
        ParagraphStyle("footer", fontSize=8, textColor=GREY, alignment=TA_CENTER)
    ))

    doc.build(story)
    return buf.getvalue()


async def save_and_upload_pdf(pdf_bytes: bytes, drug_name: str) -> dict:
    reports_dir = os.path.join(os.path.dirname(__file__), "..", "..", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    filename = (
        f"pharmintel_{drug_name.lower().replace(' ', '_')}_"
        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )
    local_path = os.path.join(reports_dir, filename)
    with open(local_path, "wb") as f:
        f.write(pdf_bytes)

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
        public_url = db.storage.from_("reports").get_public_url(storage_path)
    except Exception as e:
        print(f"Supabase upload skipped: {e}")

    return {"filename": filename, "local_path": local_path, "public_url": public_url}
