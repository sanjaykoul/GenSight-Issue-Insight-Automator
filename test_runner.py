
# test_runner.py
from src.data_loader import load_monthly_tracker
from src.aggregator import generate_monthly_summary
from src.visualizer import plot_issue_distribution, plot_engineer_workload, plot_daily_trend
from src.report_generator import generate_pdf_report, generate_ppt_report
from src.genai_insights import generate_summary_text

EXCEL_PATH = "EmblemHealth_Monthly_Productivity_Tracker.xlsx"  # adjust if needed

print("Loading Excel ...")
df = load_monthly_tracker(EXCEL_PATH)
print(df.head())
print("Shape:", df.shape)

print("Generating summaries ...")
summary = generate_monthly_summary(df)

months = sorted(df["month_label"].unique())
print("Months found:", months)

for m in months:
    print(f"\nProcessing {m} ...")
    chart1 = plot_issue_distribution(summary, m)
    chart2 = plot_engineer_workload(summary, m)
    chart3 = plot_daily_trend(summary["raw"], m)
    charts = [c for c in [chart1, chart2, chart3] if c]

    pdf_path = generate_pdf_report(summary, m, charts=charts)
    ppt_path = generate_ppt_report(summary, m, charts=charts)

    print("PDF:", pdf_path)
    print("PPT:", ppt_path)
    print("\nAI Summary:\n", generate_summary_text(summary, m))
