# GenSight‑Issue‑Insight‑Automator

**GenAI‑powered analytics and reporting for Excel‑based IT issue trackers.** Give the tool an Excel workbook where **each sheet represents a month** (e.g., `DEC2025`, `JAN2026`) and it will compute insights, generate charts, and export **PDF** and **PowerPoint (PPTX)** reports—optionally with **AI‑authored narrative summaries**.

> This README reflects the modules, inputs and outputs described on the repository’s public page. For details about the pipeline blocks (Data Loader, Aggregator, Visualizer, AI Insights, Reporting) and the monthly sheet + columns convention, see the repo page summary. 

---

## ✨ Features

- **Monthly issue insights**: totals, distributions, patterns.  
- **Engineer workload**: per‑engineer issue counts and load mix.  
- **Issue‑type categorization** and **trend visualizations (PNG)**: daily trend, issue distribution, workload.  
- **Month‑over‑Month (MoM) comparison** across consecutive months.  
- **AI‑generated narrative summaries** (natural‑language) for executive‑friendly context.  
- **Auto‑generated deliverables**: **PDF** executive report and **PPTX** deck for the month.  

---

## 📥 Supported Input (Monthly‑only)

Supply an **Excel workbook** where **each sheet is one month**, named like `DEC2025`, `JAN2026`, `FEB2026`, etc.

**Required columns** (typical monthly tracker):
- Project Name  
- Engineer Name  
- Associate/Employee ID  
- Associate/Employee Name  
- Issue Description  
- Start Date & Time (`DD/MM/YYYY HH:MM`)  
- End Date & Time (`DD/MM/YYYY HH:MM`)  
- Status (`Open` / `Closed`)  
- Request/Ticket ID  
- Remarks  

> Tip: Keep sheet names strictly monthly (e.g., `JAN2026`) so the loader can parse month/year correctly.

---

## 🧠 System Overview

1. **Data Loader (`data_loader.py`)** – Reads monthly sheets, extracts month & year, parses/normalizes data.  
2. **Aggregation Engine (`aggregator.py`)** – Computes totals, distributions, engineer workload, and MoM comparisons.  
3. **Visualization Engine (`visualizer.py`)** – Generates PNG charts (daily trend, issue distribution, engineer workload).  
4. **AI Insights (`genai_insights.py`)** – Produces natural‑language monthly summaries from computed stats.  
5. **Reporting (`report_generator.py`)** – Creates **PDF** and **PPTX** outputs for the month.  

---

## 📂 Project Structure

```
gensightenv/
│
├── src/
│   ├── data_loader.py        # Load & normalize monthly sheets
│   ├── aggregator.py         # Totals, distributions, workload, MoM comparison
│   ├── visualizer.py         # Trend, distribution & workload charts (PNG)
│   ├── genai_insights.py     # AI-generated narrative insights
│   └── report_generator.py   # PDF & PPTX generation
│
├── reports/
│   └── <MONTH>/
│       ├── Monthly_Report_<MONTH>.pdf
│       ├── Monthly_Issue_Insights_<MONTH>.pptx
│       └── charts/
│           ├── daily_trend.png
│           ├── issue_distribution.png
│           └── engineer_workload.png
│
├── notebooks/
│   └── monthly_analysis.ipynb
│
├── auto_commit.sh
├── README.md
└── requirements.txt
```

---

## ⚙️ Installation

```bash
git clone https://github.com/sanjaykoul/GenSight-Issue-Insight-Automator.git
cd GenSight-Issue-Insight-Automator

python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## ▶️ Example Usage (Programmatic)

```python
from data_loader import load_monthly_tracker
from aggregator import generate_monthly_summary
from visualizer import plot_issue_distribution
from genai_insights import generate_summary_text
from report_generator import generate_pdf_report, generate_ppt_report

# 1) Load Excel workbook with monthly sheets like DEC2025, JAN2026, ...
df = load_monthly_tracker("Monthly_Tracker.xlsx")

# 2) Compute monthly aggregates and derived metrics
summary = generate_monthly_summary(df)

# 3) Create charts (PNG files)
plot_issue_distribution(summary)

# 4) Export deliverables (PDF, PPTX)
generate_pdf_report(summary, "Monthly_Report_JAN2026.pdf")
generate_ppt_report(summary, "Monthly_Issue_Insights_JAN2026.pptx")

# 5) Optional: print AI-generated narrative insights
print(generate_summary_text(summary))
```

> The import/usage pattern above follows the end‑to‑end example described on the repository page.

---

## 📊 Outputs

For each processed month, you’ll find under `reports/<MONTH>/`:

- **PDF** → `Monthly_Report_<MONTH>.pdf`
- **PPTX** → `Monthly_Issue_Insights_<MONTH>.pptx`
- **Charts (PNG)** → `daily_trend.png`, `issue_distribution.png`, `engineer_workload.png`

---

## 🔧 Configuration & Tips

- **Sheet naming**: Use `MMMYYYY` (e.g., `JAN2026`) so month/year can be inferred.  
- **Date & time**: Keep `DD/MM/YYYY HH:MM` format consistent across Start/End columns.  
- **AI summaries**: Configure any provider credentials/env vars as required by `genai_insights.py` (if you enable LLM‑based narration).  

---

## 🧪 Sanity Checklist

Before running reports:
- [ ] Each sheet represents a **full month** (no daily/weekly sheets)
- [ ] All **required columns** exist with consistent naming
- [ ] Date/time columns are in `DD/MM/YYYY HH:MM`
- [ ] Output folder has write permissions

---

## 🤝 Contributing

1. Create a feature branch.  
2. Add/adjust tests or sample notebooks as needed.  
3. Open a PR with a clear description and, ideally, sample generated artifacts (PDF/PPT for a sample month).

---

## 📄 License

This project is released under the **MIT License**. See `LICENSE` in the repository root for details.

---


