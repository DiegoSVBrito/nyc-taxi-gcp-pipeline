"""Generate the analytical findings PDF report for the NYC Taxi project."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)

OUTPUT = "query_results_report.pdf"

# ── Colors ────────────────────────────────────────────────────────────────────
DARK   = colors.HexColor("#1a1a1a")
MID    = colors.HexColor("#4a4a4a")
LIGHT  = colors.HexColor("#f5f5f5")
RULE   = colors.HexColor("#cccccc")
ACCENT = colors.HexColor("#185FA5")

# ── Styles ────────────────────────────────────────────────────────────────────
base = getSampleStyleSheet()

def style(name, parent="Normal", **kw):
    s = ParagraphStyle(name, parent=base[parent], **kw)
    return s

H1 = style("H1", "Title",   fontSize=22, textColor=DARK,   leading=28, spaceAfter=6)
H2 = style("H2", "Heading2",fontSize=13, textColor=ACCENT,  leading=18, spaceBefore=18, spaceAfter=6)
H3 = style("H3", "Heading3",fontSize=10, textColor=MID,     leading=14, spaceBefore=10, spaceAfter=4)
BODY = style("BODY",         fontSize=9,  textColor=DARK,   leading=14, spaceAfter=6)
CODE = style("CODE", "Code", fontSize=7.5,textColor=MID,    leading=11, spaceAfter=6,
             backColor=LIGHT, borderPadding=(4, 6, 4, 6))
META = style("META",         fontSize=8,  textColor=MID,    leading=12, spaceAfter=12)

def table_style(header_color=ACCENT):
    return TableStyle([
        ("BACKGROUND",   (0,0), (-1,0), header_color),
        ("TEXTCOLOR",    (0,0), (-1,0), colors.white),
        ("FONTNAME",     (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0), (-1,0), 8),
        ("FONTNAME",     (0,1), (-1,-1),"Helvetica"),
        ("FONTSIZE",     (0,1), (-1,-1), 8),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, LIGHT]),
        ("GRID",         (0,0), (-1,-1), 0.3, RULE),
        ("TOPPADDING",   (0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0), (-1,-1), 4),
        ("LEFTPADDING",  (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("ALIGN",        (0,0), (-1,-1), "LEFT"),
        ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
    ])

def rule():
    return HRFlowable(width="100%", thickness=0.5, color=RULE, spaceAfter=4, spaceBefore=4)

def code(sql):
    return Paragraph(sql.replace("\n","<br/>").replace(" ","&nbsp;"), CODE)


# ── Content ───────────────────────────────────────────────────────────────────
story = []

# Cover
story.append(Spacer(1, 0.6*inch))
story.append(Paragraph("NYC Yellow Taxi", H1))
story.append(Paragraph("Driver Earnings Analysis", H1))
story.append(rule())
story.append(Paragraph(
    "Dataset: January 2023 &nbsp;|&nbsp; Source: NYC TLC &nbsp;|&nbsp; "
    "Pipeline: GCS + BigQuery + dbt &nbsp;|&nbsp; Rows: 3,066,766",
    META
))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph(
    "This report presents five analytical queries run against the gold layer of the "
    "NYC Taxi pipeline. Each query targets a different dimension of the driver earnings "
    "question: where to be, when to work, whether airport runs pay, how trip length "
    "affects the rate, and what the cash tip data actually means. "
    "The findings are drawn directly from the BigQuery output for January 2023.",
    BODY
))

# ── Q1 ────────────────────────────────────────────────────────────────────────
story.append(PageBreak())
story.append(Paragraph("Query 1 — Top Zones and Hours by Earnings per Hour", H2))
story.append(Paragraph(
    "Ranks pickup zone and hour combinations by dollars earned per working hour. "
    "This is the primary lens for maximizing a shift: it captures both fare size and "
    "trip frequency, unlike per-trip averages which ignore how long each ride takes.",
    BODY
))
story.append(code(
    "SELECT pu_borough, pu_zone, pickup_hour, trip_count,\n"
    "       earnings_per_hour, avg_fare_per_trip\n"
    "FROM `massive-network-500412-u2.nyc_taxi.earnings_by_zone_hour`\n"
    "ORDER BY earnings_per_hour DESC\n"
    "LIMIT 15;"
))

q1_data = [
    ["Borough", "Zone", "Hour", "Trips", "$/hr", "Avg Fare"],
    ["Queens", "Flushing Meadows-Corona Park", "23", "98",  "$262.75", "$75.80"],
    ["Queens", "Flushing Meadows-Corona Park", "22", "106", "$248.99", "$81.84"],
    ["Queens", "Flushing Meadows-Corona Park", "20", "114", "$245.83", "$75.70"],
    ["Queens", "Flushing Meadows-Corona Park", "19", "94",  "$245.67", "$88.73"],
    ["Queens", "Flushing Meadows-Corona Park", "21", "125", "$245.43", "$79.81"],
    ["Queens", "Flushing Meadows-Corona Park", "9",  "63",  "$244.45", "$79.56"],
    ["Queens", "Flushing Meadows-Corona Park", "10", "62",  "$219.14", "$78.72"],
    ["Queens", "Flushing Meadows-Corona Park", "11", "62",  "$214.60", "$75.75"],
    ["Queens", "Flushing Meadows-Corona Park", "8",  "70",  "$212.85", "$84.69"],
    ["Queens", "Jamaica",                       "21", "57",  "$212.77", "$85.65"],
    ["Queens", "Long Island City/Hunters Pt",  "16", "64",  "$211.30", "$74.81"],
    ["Queens", "South Jamaica",                 "22", "53",  "$204.92", "$90.64"],
    ["Queens", "LaGuardia Airport",             "3",  "54",  "$201.91", "$57.19"],
    ["Queens", "South Jamaica",                 "20", "50",  "$201.89", "$85.29"],
    ["Manhattan","UN/Turtle Bay South",         "4",  "166", "$201.84", "$46.32"],
]
t = Table(q1_data, colWidths=[70, 150, 38, 45, 55, 58])
t.setStyle(table_style())
story.append(t)
story.append(Spacer(1, 8))
story.append(Paragraph(
    "<b>What this means for a driver.</b> Queens dominates the top 15, with "
    "Flushing Meadows-Corona Park occupying eight of the top ten slots. The pattern "
    "is not random: the zone sits near Citi Field and the USTA tennis center, and "
    "the high evening hours (19-23) align with event and restaurant traffic. "
    "A driver who positions there in the late evening can earn over $260 per hour — "
    "more than twice the citywide average. Jamaica and LaGuardia also appear, "
    "confirming that Queens airport-adjacent zones are genuinely productive, "
    "not just high-fare outliers.",
    BODY
))

# ── Q2 ────────────────────────────────────────────────────────────────────────
story.append(PageBreak())
story.append(Paragraph("Query 2 — Tipping by Payment Method", H2))
story.append(Paragraph(
    "Compares tip behavior across payment types. The key field is "
    "pct_trips_with_recorded_tip, which distinguishes a genuine absence of tips "
    "from a recording gap.",
    BODY
))
story.append(code(
    "SELECT payment_method, trip_count, avg_fare, avg_tip,\n"
    "       avg_tip_pct, pct_trips_with_recorded_tip\n"
    "FROM `massive-network-500412-u2.nyc_taxi.tipping_by_payment`\n"
    "ORDER BY trip_count DESC;"
))

q2_data = [
    ["Payment", "Trips", "Avg Fare", "Avg Tip", "Avg Tip %", "% w/ Recorded Tip"],
    ["card",    "2,385,316", "$18.47", "$4.16", "25.9%", "96.0%"],
    ["cash",    "513,185",   "$18.51", "$0.00", "0.0%",  "0.0%"],
    ["other",   "24,813",    "$18.38", "$0.02", "0.1%",  "0.1%"],
]
t = Table(q2_data, colWidths=[55, 80, 68, 60, 65, 110])
t.setStyle(table_style())
story.append(t)
story.append(Spacer(1, 8))
story.append(Paragraph(
    "<b>What this means for a driver.</b> Cash trips record zero tips — not because "
    "cash riders do not tip, but because cash tips are handed over physically and "
    "never entered into the meter. The TLC data is technically correct; it simply "
    "does not capture physical cash. A driver who reads the raw average and starts "
    "avoiding cash riders is making a decision based on a recording artifact, not "
    "rider behavior. Card trips show a 25.9% average tip rate across 96% of rides — "
    "the card system captures every tip automatically. The practical takeaway is to "
    "accept all payment types and judge tipping only through the card data.",
    BODY
))

# ── Q3 ────────────────────────────────────────────────────────────────────────
story.append(PageBreak())
story.append(Paragraph("Query 3 — Airport Runs versus All Other Trips", H2))
story.append(Paragraph(
    "Compares airport trips to the rest on total fare, duration, and dollars per "
    "minute. Airport trips are flagged where either the pickup or dropoff location "
    "is JFK, LaGuardia, or Newark.",
    BODY
))
story.append(code(
    "SELECT is_airport_trip, trip_count, avg_total_per_trip,\n"
    "       avg_duration_min, avg_dollars_per_minute\n"
    "FROM `massive-network-500412-u2.nyc_taxi.airport_runs`\n"
    "ORDER BY is_airport_trip DESC;"
))

q3_data = [
    ["Airport Trip", "Trips", "Avg Total", "Avg Duration", "Avg $/min"],
    ["true",  "296,129",   "$74.54", "33.3 min", "$2.51"],
    ["false", "2,627,105", "$21.95", "12.5 min", "$2.07"],
]
t = Table(q3_data, colWidths=[80, 90, 80, 95, 90])
t.setStyle(table_style())
story.append(t)
story.append(Spacer(1, 8))
story.append(Paragraph(
    "<b>What this means for a driver.</b> Airport fares average $74.54 — more than "
    "three times a regular trip. The per-minute rate is also higher ($2.51 vs $2.07). "
    "However, this comparison only counts the inbound leg. Airport drop-offs almost "
    "always force an empty return to the city or a long queue at the airport holding "
    "lot before the next pickup. Once that dead time is included, the effective rate "
    "drops materially. Airport runs are not a bad choice, but a driver should treat "
    "them as a round trip when deciding whether to accept: if the queue is short and "
    "demand in the destination zone is high, they are worth it; if the queue is long "
    "and the zone is quiet, staying in a high-rate city zone likely pays more.",
    BODY
))

# ── Q4 ────────────────────────────────────────────────────────────────────────
story.append(PageBreak())
story.append(Paragraph("Query 4 — Trip Efficiency by Distance Bucket", H2))
story.append(Paragraph(
    "Groups trips into distance buckets and compares dollars per minute. "
    "Ranked by the per-minute rate, not total fare, so longer and shorter trips "
    "are compared on the metric that determines how much a full shift earns.",
    BODY
))
story.append(code(
    "SELECT distance_bucket, trip_count, avg_total,\n"
    "       avg_duration_min, avg_dollars_per_minute\n"
    "FROM `massive-network-500412-u2.nyc_taxi.trip_efficiency`\n"
    "ORDER BY avg_dollars_per_minute DESC;"
))

q4_data = [
    ["Distance",     "Trips",     "Avg Total", "Avg Duration", "Avg $/min"],
    ["0 to 1 mi",    "599,723",   "$13.53",    "5.6 min",      "$2.88"],
    ["12 mi and up", "178,636",   "$43.20",    "41.2 min",     "$2.36"],
    ["6 to 12 mi",   "238,716",   "$54.45",    "26.0 min",     "$2.28"],
    ["1 to 3 mi",    "1,487,440", "$19.72",    "11.6 min",     "$1.88"],
    ["3 to 6 mi",    "418,879",   "$31.10",    "19.9 min",     "$1.68"],
]
t = Table(q4_data, colWidths=[90, 90, 80, 95, 80])
t.setStyle(table_style())
story.append(t)
story.append(Spacer(1, 8))
story.append(Paragraph(
    "<b>What this means for a driver.</b> Short trips under one mile return the "
    "highest rate per minute at $2.88. The base charge and minimum fare are spread "
    "over very little time, so the meter starts high and the trip ends before the "
    "per-mile rate has much chance to dilute it. Trips in the 1-6 mile range — "
    "the most common in the dataset — are actually the least efficient per minute. "
    "A driver who dismisses short fares as not worth the trouble is leaving the most "
    "efficient part of the rate structure on the table. The practical advice: accept "
    "short trips freely when positioned in a dense zone, because the per-minute return "
    "is stronger than longer rides and the next pickup comes quickly.",
    BODY
))

# ── Q5 ────────────────────────────────────────────────────────────────────────
story.append(PageBreak())
story.append(Paragraph("Query 5 — Best Hours of the Day (City-Wide)", H2))
story.append(Paragraph(
    "Collapses zone and ranks all 24 hours by aggregate earnings per working hour. "
    "A simpler view for a driver who wants to know when to drive rather than where.",
    BODY
))
story.append(code(
    "SELECT pickup_hour,\n"
    "       SUM(trip_count) AS trips,\n"
    "       ROUND(SUM(total_earnings) / NULLIF(SUM(hours_worked), 0), 2)\n"
    "           AS earnings_per_hour\n"
    "FROM `massive-network-500412-u2.nyc_taxi.earnings_by_zone_hour`\n"
    "GROUP BY pickup_hour\n"
    "ORDER BY earnings_per_hour DESC;"
))

q5_data = [
    ["Hour", "Trips",   "$/hr"],
    ["5",    "14,848",  "$155.53"],
    ["4",    "14,785",  "$142.58"],
    ["3",    "24,198",  "$130.17"],
    ["23",   "108,025", "$128.89"],
    ["6",    "38,020",  "$128.39"],
    ["8",    "79,251",  "$127.82"],
    ["1",    "50,195",  "$125.58"],
    ["2",    "38,926",  "$124.79"],
    ["22",   "140,217", "$124.72"],
    ["21",   "163,903", "$124.57"],
    ["20",   "158,992", "$121.97"],
    ["19",   "183,906", "$120.47"],
    ["7",    "79,867",  "$113.51"],
    ["18",   "205,387", "$112.39"],
    ["9",    "123,212", "$108.18"],
    ["10",   "136,945", "$107.81"],
    ["17",   "199,250", "$107.23"],
]
t = Table(q5_data, colWidths=[60, 100, 80])
t.setStyle(table_style())
story.append(t)
story.append(Spacer(1, 8))
story.append(Paragraph(
    "<b>What this means for a driver.</b> The highest earning hours are in the early "
    "morning window of 3-6am, with 5am returning $155.53 per hour — 45% more than a "
    "typical midday hour. Demand at these hours comes from airport runs, late-night "
    "workers, and bar close traffic, with very little competition from other drivers. "
    "Late evening (19-23) also performs well and carries far more total volume. "
    "Midday hours (11-16) are consistently the weakest. A driver optimizing for "
    "earnings should build shifts around either the 3-6am window or the 19-23 block, "
    "and avoid the 11am-4pm range if flexibility allows.",
    BODY
))

# ── Summary ───────────────────────────────────────────────────────────────────
story.append(PageBreak())
story.append(Paragraph("Summary: Advice to a New Driver", H2))
story.append(rule())
story.append(Spacer(1, 6))

advice = [
    ("<b>1. Work the late evening or early morning.</b>",
     "Hours 19-23 and 3-6am return the highest earnings per hour. "
     "If you can only change one thing about your schedule, shift into one of these windows."),
    ("<b>2. Position in Queens, specifically Flushing Meadows-Corona Park.</b>",
     "Event-driven demand in this zone produces rates above $240/hr in the evening. "
     "Jamaica and South Jamaica are also consistently productive for airport-adjacent work."),
    ("<b>3. Take short trips without hesitation.</b>",
     "Under-one-mile trips earn $2.88 per minute — the best rate in the dataset. "
     "Refusing them to wait for longer fares is a losing strategy in a dense zone."),
    ("<b>4. Treat airport runs as round trips before accepting.</b>",
     "The inbound fare is high, but the empty return or holding queue often erases the "
     "rate advantage. Airport runs are worth it when queues are short; otherwise, "
     "staying in a busy zone pays more per hour."),
    ("<b>5. Ignore the cash tip column.</b>",
     "It reads zero because the system does not record physical cash tips, not because "
     "cash riders do not tip. Do not avoid cash riders based on this number."),
]

for heading, body in advice:
    story.append(Paragraph(heading, H3))
    story.append(Paragraph(body, BODY))
    story.append(Spacer(1, 4))

story.append(rule())
story.append(Spacer(1, 6))
story.append(Paragraph(
    "Data source: NYC TLC Yellow Taxi trip records, January 2023. "
    "Pipeline: Cloud Storage landing bucket + BigQuery load jobs (bronze) + "
    "dbt incremental models (silver) + pre-aggregated marts (gold). "
    "All figures are from the January 2023 month; patterns are consistent with "
    "multi-year TLC data reported in public studies.",
    META
))

# ── Build ─────────────────────────────────────────────────────────────────────
doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=letter,
    leftMargin=0.85*inch,
    rightMargin=0.85*inch,
    topMargin=0.85*inch,
    bottomMargin=0.85*inch,
    title="NYC Yellow Taxi — Driver Earnings Analysis",
    author="Diego Brito",
    subject="BigQuery analytical findings, January 2023",
)
doc.build(story)
print(f"Report written to {OUTPUT}")
