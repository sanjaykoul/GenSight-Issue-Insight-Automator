
from src.data_loader import load_monthly_tracker
from src.aggregator import generate_monthly_summary
from src.visualizer import plot_issue_distribution, plot_engineer_workload, plot_daily_trend, plot_status_breakdown
from src.report_generator import generate_pdf_report, generate_ppt_report
from src.genai_insights import generate_summary_text

EXCEL_PATH = "EmblemHealth_Monthly_Productivity_Tracker.xlsx"
LOGO_PATH = None  # e.g., "assets/logo.png" if you have one

print("Loading Excel ...")
df = load_monthly_tracker(EXCEL_PATH)
summary = generate_monthly_summary(df)
months = sorted(df["month_label"].unique())

for m in months:
    print(f"\nProcessing {m} ...")

    # Per-month charts
    chart1 = plot_issue_distribution(summary, m)
    chart2 = plot_engineer_workload(summary, m)
    chart3 = plot_daily_trend(summary["raw"], m)
    chart4 = plot_status_breakdown(summary, m)  # NEW
    charts = [c for c in [chart1, chart2, chart3, chart4] if c]

    # AI text
    ai_text = generate_summary_text(summary, m)

    # Reports
    pdf_path = generate_pdf_report(summary, m, charts=charts, ai_text=ai_text, logo_path=LOGO_PATH, include_mom=True)
    ppt_path = generate_ppt_report(summary, m, charts=charts, ai_text=ai_text, logo_path=LOGO_PATH, include_mom=True)

    print("PDF:", pdf_path)
    print("PPT:", ppt_path)
    print("\nAI Summary:\n", ai_text)
