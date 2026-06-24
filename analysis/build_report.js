const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, Header, Footer, PageNumber, PageBreak
} = require("docx");
const fs = require("fs");

// ── helpers ────────────────────────────────────────────────────────────────────

const LIGHT_BLUE = "DDEEFF";
const MID_BLUE   = "1F5C99";
const RULE_COLOR = "BBBBBB";

const border = { style: BorderStyle.SINGLE, size: 1, color: RULE_COLOR };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorder = { style: BorderStyle.NIL };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after ?? 100, before: opts.before ?? 0 },
    alignment: opts.align ?? AlignmentType.LEFT,
    heading: opts.heading,
    children: [new TextRun({
      text,
      bold: opts.bold ?? false,
      size: opts.size ?? 20,
      font: "Arial",
      color: opts.color ?? "000000",
      italics: opts.italic ?? false,
    })]
  });
}

function h1(text) {
  return new Paragraph({
    spacing: { before: 280, after: 100 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: MID_BLUE, space: 4 } },
    children: [new TextRun({ text, bold: true, size: 28, font: "Arial", color: MID_BLUE })]
  });
}

function h2(text) {
  return new Paragraph({
    spacing: { before: 200, after: 80 },
    children: [new TextRun({ text, bold: true, size: 22, font: "Arial", color: "333333" })]
  });
}

function body(text) {
  return new Paragraph({
    spacing: { after: 100 },
    children: [new TextRun({ text, size: 20, font: "Arial" })]
  });
}

function small(text) {
  return new Paragraph({
    spacing: { after: 80 },
    children: [new TextRun({ text, size: 17, font: "Arial", color: "666666", italics: true })]
  });
}

function spacer() {
  return new Paragraph({ spacing: { after: 80 }, children: [] });
}

function code(text) {
  return new Paragraph({
    spacing: { after: 80, before: 60 },
    shading: { fill: "F4F4F4", type: ShadingType.CLEAR },
    children: [new TextRun({ text, size: 16, font: "Courier New", color: "333333" })]
  });
}

function codeBlock(lines) {
  return lines.map((line, i) => new Paragraph({
    spacing: { after: i === lines.length - 1 ? 100 : 10, before: i === 0 ? 60 : 0 },
    shading: { fill: "F4F4F4", type: ShadingType.CLEAR },
    indent: { left: 200, right: 200 },
    children: [new TextRun({ text: line || " ", size: 16, font: "Courier New", color: "444444" })]
  }));
}

function headerRow(cells, widths) {
  return new TableRow({
    tableHeader: true,
    children: cells.map((text, i) => new TableCell({
      borders,
      width: { size: widths[i], type: WidthType.DXA },
      shading: { fill: MID_BLUE, type: ShadingType.CLEAR },
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      verticalAlign: VerticalAlign.CENTER,
      children: [new Paragraph({
        alignment: AlignmentType.LEFT,
        children: [new TextRun({ text, bold: true, size: 18, font: "Arial", color: "FFFFFF" })]
      })]
    }))
  });
}

function dataRow(cells, widths, shade = false) {
  return new TableRow({
    children: cells.map((text, i) => new TableCell({
      borders,
      width: { size: widths[i], type: WidthType.DXA },
      shading: { fill: shade ? "F0F5FB" : "FFFFFF", type: ShadingType.CLEAR },
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [new Paragraph({
        children: [new TextRun({ text: String(text), size: 18, font: "Arial" })]
      })]
    }))
  });
}

function table(headers, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      headerRow(headers, widths),
      ...rows.map((row, i) => dataRow(row, widths, i % 2 === 1))
    ]
  });
}

// ── document ───────────────────────────────────────────────────────────────────

const W = 9360; // content width US Letter 1" margins

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Arial", size: 20 } }
    }
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: RULE_COLOR, space: 4 } },
          children: [new TextRun({ text: "NYC Yellow Taxi — Driver Earnings Analysis  |  January 2023", size: 16, font: "Arial", color: "888888" })]
        })]
      })
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          border: { top: { style: BorderStyle.SINGLE, size: 4, color: RULE_COLOR, space: 4 } },
          alignment: AlignmentType.RIGHT,
          children: [
            new TextRun({ text: "github.com/DiegoSVBrito/nyc-taxi-gcp-pipeline  |  p. ", size: 16, font: "Arial", color: "888888" }),
            new TextRun({ children: [PageNumber.CURRENT], size: 16, font: "Arial", color: "888888" })
          ]
        })]
      })
    },
    children: [

      // ── Title ──────────────────────────────────────────────────────────────
      spacer(),
      new Paragraph({
        spacing: { after: 60 },
        children: [new TextRun({ text: "NYC Yellow Taxi", bold: true, size: 52, font: "Arial", color: MID_BLUE })]
      }),
      new Paragraph({
        spacing: { after: 140 },
        children: [new TextRun({ text: "Driver Earnings Analysis", bold: false, size: 36, font: "Arial", color: "444444" })]
      }),
      new Paragraph({
        spacing: { after: 200 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: MID_BLUE, space: 6 } },
        children: [
          new TextRun({ text: "Dataset: NYC TLC Yellow Taxi, January 2023    |    Rows: 3,066,766    |    Pipeline: GCS + BigQuery + dbt", size: 17, font: "Arial", color: "666666" })
        ]
      }),
      body("This document presents five analytical queries run against the gold layer of the NYC taxi pipeline. Each query targets a specific part of the driver earnings question. The data is from January 2023 — patterns are consistent with multi-year TLC records, though the exact numbers will shift across months."),
      spacer(),

      // ── Q1 ─────────────────────────────────────────────────────────────────
      new Paragraph({ children: [new PageBreak()] }),
      h1("Query 1 — Best Zone and Hour Combinations"),
      body("Where should a driver be, and at what time? This query ranks pickup zone and hour of day by earnings per working hour — the metric that actually fills a shift, as opposed to per-trip averages which ignore how long each ride takes."),
      spacer(),
      ...codeBlock([
        "SELECT pu_borough, pu_zone, pickup_hour, trip_count,",
        "       earnings_per_hour, avg_fare_per_trip",
        "FROM `massive-network-500412-u2.nyc_taxi.earnings_by_zone_hour`",
        "ORDER BY earnings_per_hour DESC",
        "LIMIT 15;"
      ]),
      spacer(),
      table(
        ["Borough", "Zone", "Hour", "Trips", "$/hr", "Avg Fare"],
        [
          ["Queens","Flushing Meadows-Corona Park","23","98","$262.75","$75.80"],
          ["Queens","Flushing Meadows-Corona Park","22","106","$248.99","$81.84"],
          ["Queens","Flushing Meadows-Corona Park","20","114","$245.83","$75.70"],
          ["Queens","Flushing Meadows-Corona Park","19","94","$245.67","$88.73"],
          ["Queens","Flushing Meadows-Corona Park","21","125","$245.43","$79.81"],
          ["Queens","Flushing Meadows-Corona Park","9","63","$244.45","$79.56"],
          ["Queens","Flushing Meadows-Corona Park","10","62","$219.14","$78.72"],
          ["Queens","Flushing Meadows-Corona Park","11","62","$214.60","$75.75"],
          ["Queens","Flushing Meadows-Corona Park","8","70","$212.85","$84.69"],
          ["Queens","Jamaica","21","57","$212.77","$85.65"],
          ["Queens","Long Island City/Hunters Pt","16","64","$211.30","$74.81"],
          ["Queens","South Jamaica","22","53","$204.92","$90.64"],
          ["Queens","LaGuardia Airport","3","54","$201.91","$57.19"],
          ["Queens","South Jamaica","20","50","$201.89","$85.29"],
          ["Manhattan","UN/Turtle Bay South","4","166","$201.84","$46.32"],
        ],
        [1100, 2000, 500, 600, 700, 760]
      ),
      spacer(),
      h2("What this says"),
      body("Queens dominates the top 15, with Flushing Meadows-Corona Park holding eight of the top ten slots. The zone sits next to Citi Field and the USTA tennis center — event and restaurant traffic drives consistent demand in the 19-23h window. A driver positioned there on a weeknight evening can earn over $260/hr, more than double the citywide average. Jamaica and LaGuardia also appear, confirming that Queens airport-adjacent zones are genuinely productive beyond the Flushing cluster."),

      // ── Q2 ─────────────────────────────────────────────────────────────────
      new Paragraph({ children: [new PageBreak()] }),
      h1("Query 2 — Tipping by Payment Method"),
      body("Do cash riders really tip less? The short answer is: the data says yes, but the data is wrong about this. The key column here is pct_trips_with_recorded_tip."),
      spacer(),
      ...codeBlock([
        "SELECT payment_method, trip_count, avg_fare, avg_tip,",
        "       avg_tip_pct, pct_trips_with_recorded_tip",
        "FROM `massive-network-500412-u2.nyc_taxi.tipping_by_payment`",
        "ORDER BY trip_count DESC;"
      ]),
      spacer(),
      table(
        ["Payment", "Trips", "Avg Fare", "Avg Tip", "Avg Tip %", "% w/ Recorded Tip"],
        [
          ["card",  "2,385,316", "$18.47", "$4.16", "25.9%", "96.0%"],
          ["cash",  "513,185",   "$18.51", "$0.00", "0.0%",  "0.0%"],
          ["other", "24,813",    "$18.38", "$0.02", "0.1%",  "0.1%"],
        ],
        [800, 1000, 900, 800, 900, 1400]
      ),
      spacer(),
      h2("What this says"),
      body("Cash tips are handed to the driver physically and never entered into the meter, so they do not appear in the TLC data at all. The 0.0% recorded tip rate for cash is a data gap, not rider behavior. Fares are nearly identical across payment types ($18.47 card vs $18.51 cash), which suggests no systematic difference in trip type. A driver who starts avoiding cash riders based on the tip column is optimizing against a recording artifact."),

      // ── Q3 ─────────────────────────────────────────────────────────────────
      new Paragraph({ children: [new PageBreak()] }),
      h1("Query 3 — Airport Runs vs. Everything Else"),
      body("Airport trips carry a higher fare, but does the extra time make them worth it? This query compares airport and non-airport trips on fare per trip and dollars per minute."),
      spacer(),
      ...codeBlock([
        "SELECT is_airport_trip, trip_count, avg_total_per_trip,",
        "       avg_duration_min, avg_dollars_per_minute",
        "FROM `massive-network-500412-u2.nyc_taxi.airport_runs`",
        "ORDER BY is_airport_trip DESC;"
      ]),
      spacer(),
      table(
        ["Airport Trip", "Trips", "Avg Total", "Avg Duration", "Avg $/min"],
        [
          ["true",  "296,129",   "$74.54", "33.3 min", "$2.51"],
          ["false", "2,627,105", "$21.95", "12.5 min", "$2.07"],
        ],
        [1200, 1200, 1200, 1200, 1200]
      ),
      spacer(),
      h2("What this says"),
      body("Airport trips earn $2.51/min vs $2.07 for everything else — a real premium. But this only counts the inbound leg. Most airport drop-offs end in a holding queue or an empty return to the city. Neither earns anything, and the data does not capture that dead time. Once the return trip is factored in, the effective per-minute rate often falls close to the city average. Airport runs are worth it when the queue is short; not worth it when it is not."),

      // ── Q4 ─────────────────────────────────────────────────────────────────
      new Paragraph({ children: [new PageBreak()] }),
      h1("Query 4 — Trip Efficiency by Distance"),
      body("Short or long trips — which earns more per minute? Trips are grouped into distance buckets and compared on dollars per minute worked."),
      spacer(),
      ...codeBlock([
        "SELECT distance_bucket, trip_count, avg_total,",
        "       avg_duration_min, avg_dollars_per_minute",
        "FROM `massive-network-500412-u2.nyc_taxi.trip_efficiency`",
        "ORDER BY avg_dollars_per_minute DESC;"
      ]),
      spacer(),
      table(
        ["Distance", "Trips", "Avg Total", "Avg Duration", "Avg $/min"],
        [
          ["0 to 1 mi",    "599,723",   "$13.53", "5.6 min",  "$2.88"],
          ["12 mi and up", "178,636",   "$43.20", "41.2 min", "$2.36"],
          ["6 to 12 mi",   "238,716",   "$54.45", "26.0 min", "$2.28"],
          ["1 to 3 mi",    "1,487,440", "$19.72", "11.6 min", "$1.88"],
          ["3 to 6 mi",    "418,879",   "$31.10", "19.9 min", "$1.68"],
        ],
        [1400, 1200, 1100, 1260, 1100]
      ),
      spacer(),
      h2("What this says"),
      body("Trips under one mile return $2.88/min — the highest rate in the dataset. The base charge and minimum fare are spread over very little time, so the meter starts at a high effective rate before the per-mile component has any chance to dilute it. The 1-6 mile range, which accounts for the majority of trips, is the worst performing on this metric. A driver who turns down short fares to wait for longer ones is giving up the most efficient part of the rate structure."),

      // ── Q5 ─────────────────────────────────────────────────────────────────
      new Paragraph({ children: [new PageBreak()] }),
      h1("Query 5 — Best Hours of the Day"),
      body("Collapsing zone, which hours of the day return the highest earnings per hour city-wide? A simpler cut for a driver who wants to know when to work rather than where."),
      spacer(),
      ...codeBlock([
        "SELECT pickup_hour,",
        "       SUM(trip_count) AS trips,",
        "       ROUND(SUM(total_earnings) / NULLIF(SUM(hours_worked), 0), 2)",
        "           AS earnings_per_hour",
        "FROM `massive-network-500412-u2.nyc_taxi.earnings_by_zone_hour`",
        "GROUP BY pickup_hour",
        "ORDER BY earnings_per_hour DESC;"
      ]),
      spacer(),
      table(
        ["Hour", "Trips", "$/hr"],
        [
          ["5 am",  "14,848",  "$155.53"],
          ["4 am",  "14,785",  "$142.58"],
          ["3 am",  "24,198",  "$130.17"],
          ["11 pm", "108,025", "$128.89"],
          ["6 am",  "38,020",  "$128.39"],
          ["8 am",  "79,251",  "$127.82"],
          ["1 am",  "50,195",  "$125.58"],
          ["2 am",  "38,926",  "$124.79"],
          ["10 pm", "140,217", "$124.72"],
          ["9 pm",  "163,903", "$124.57"],
          ["8 pm",  "158,992", "$121.97"],
          ["7 pm",  "183,906", "$120.47"],
          ["7 am",  "79,867",  "$113.51"],
          ["6 pm",  "205,387", "$112.39"],
          ["9 am",  "123,212", "$108.18"],
        ],
        [1000, 1400, 1000]
      ),
      spacer(),
      h2("What this says"),
      body("The 3-6am window returns the highest rates by a wide margin — 5am at $155.53/hr is 45% above a typical midday hour. Volume is low but competition is minimal and the trips that do come through (airport runs, late workers, bar close) tend to pay well. The 19-23h block has much higher volume at slightly lower rates, making it the better choice for a full shift. Midday (11am-4pm) is consistently the weakest window and should be avoided when flexibility allows."),

      // ── Summary ────────────────────────────────────────────────────────────
      new Paragraph({ children: [new PageBreak()] }),
      h1("Summary — Advice to a New Driver"),
      spacer(),

      h2("1. Work evenings or early mornings"),
      body("Hours 19-23 and 3-6am return the highest earnings per hour. If only one thing about your schedule can change, shift into one of these windows. Midday is where earnings are lowest, not because of fare rates but because demand is diffuse and competition is high."),

      h2("2. Position in Queens, specifically Flushing Meadows-Corona Park"),
      body("Event-driven demand in this zone produces rates above $240/hr on weeknight evenings. Jamaica and South Jamaica are also consistently strong for airport-adjacent work. Manhattan midtown is high-volume but not top-performing on a per-hour basis — the density brings competition that erodes the rate."),

      h2("3. Take short trips without hesitation"),
      body("Under-one-mile trips return $2.88/min — the best rate in the dataset. Refusing them to wait for a longer fare is a bad trade in a dense zone."),

      h2("4. Airport runs are a round trip decision, not a one-way fare"),
      body("The $74 airport fare looks good until you account for the return. Ask whether the queue is short and whether there is pickup demand near the airport before accepting. If the queue is long, staying in a busy zone is probably worth more per hour."),

      h2("5. Ignore the cash tip column"),
      body("It reads zero for 513,185 trips not because cash riders do not tip, but because physical cash tips are never entered into the meter. This is a recording gap. Do not make rider decisions based on it."),

      spacer(),
      new Paragraph({
        spacing: { before: 200 },
        border: { top: { style: BorderStyle.SINGLE, size: 4, color: RULE_COLOR, space: 6 } },
        children: [new TextRun({ text: "Source: NYC TLC Yellow Taxi, January 2023. Pipeline: Cloud Storage + BigQuery load jobs (bronze) + dbt incremental models (silver) + pre-aggregated marts (gold). Repository: github.com/DiegoSVBrito/nyc-taxi-gcp-pipeline", size: 16, font: "Arial", color: "888888", italics: true })]
      }),
    ]
  }]
});

const OUT = "driver_earnings_report.docx";
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(OUT, buf);
  console.log("Written:", OUT);
});
