
# GenSight-Issue-Insight-Automator

GenSight-Issue-Insight-Automator is a Python-based analytics and AI automation tool designed exclusively for **monthly IT issue tracker sheets**. It processes Excel files where **each sheet represents one month** (e.g., `DEC2025`, `JAN2026`) and automatically generates:

- Monthly issue insights
- Engineer workload summaries
- Issue-type categorization
- Trend visualizations (PNG charts)
- Month-over-month comparisons
- AI-generated natural language summaries
- Auto-generated **PDF Reports**
- Auto-generated **PowerPoint (PPTX) presentations**

This tool is fully **project-agnostic**, meaning it works for any IT support environment.

---

## Supported Input Format (Monthly Only)

### ✔ Monthly Sheets
Each Excel sheet must represent an entire month and follow names like:
- `DEC2025`
- `JAN2026`
- `FEB2026`

---


## Required Columns

| Column                  | Description                     |
|-------------------------|---------------------------------|
| Project Name            | Name of the project             |
| Engineer Name           | Support engineer handling the issue |
| Associate/Employee ID   | Unique ID of the user           |
| Associate/Employee Name | Name of the user                |
| Issue Description       | Brief summary of the issue      |
| Start Date & Time       | Issue start (DD/MM/YYYY HH:MM)  |
| End Date & Time         | Issue end (DD/MM/YYYY HH:MM)    |
| Status                  | Current status (Open / Closed)  |
| Request/Ticket ID       | Reference ticket number         |
| Remarks                 | Additional notes / resolution    |
``

---

## System Overview

### 1️⃣ Data Loader (`data_loader.py`)
- Reads monthly sheets
- Extracts month & year
- Parses and normalizes data

### 2️⃣ Aggregation Engine (`aggregator.py`)
- Computes totals, distributions, patterns
- Engineer workload
- Month-over-month comparison

### 3️⃣ Visualization Engine (`visualizer.py`)
- Issue trend charts
- Issue-type distribution
- Engineer workload charts
- MoM comparison visuals

### 4️⃣ AI Insights (`genai_insights.py`)
- Generates natural language monthly insights

---

# Reporting (PDF & PPTX)

## PDF Report
**Example Output File:**
```
Monthly_Report_JAN2026.pdf
```

## PowerPoint Presentation
**Example Output File:**
```
Monthly_Issue_Insights_JAN2026.pptx
```

---

## Example Usage
```python
from data_loader import load_monthly_tracker
from aggregator import generate_monthly_summary
from visualizer import plot_issue_distribution
from genai_insights import generate_summary_text
from report_generator import generate_pdf_report, generate_ppt_report

df = load_monthly_tracker("Monthly_Tracker.xlsx")
summary = generate_monthly_summary(df)

plot_issue_distribution(summary)

generate_pdf_report(summary, "Monthly_Report_JAN2026.pdf")
generate_ppt_report(summary, "Monthly_Issue_Insights_JAN2026.pptx")

print(generate_summary_text(summary))
```

---

## Project Structure
```
gensightenv/
│
├── src/
│   ├── data_loader.py
│   ├── aggregator.py
│   ├── visualizer.py
│   ├── genai_insights.py
│   ├── report_generator.py
│
├── reports/
│   └── <MONTH>/
│       ├── Monthly_Report_<MONTH>.pdf
│       ├── Monthly_Issue_Insights_<MONTH>.pptx
│       └── charts/
│           ├── daily_trend.png
│           ├── issue_distribution.png
│           ├── engineer_workload.png
│
├── notebooks/
│   └── monthly_analysis.ipynb
│
├── README.md
└── requirements.txt
```

---

## License
MIT License
