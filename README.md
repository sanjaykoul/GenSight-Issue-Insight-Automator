
# GenSight-Issue-Insight-Automator

GenSight-Issue-Insight-Automator is a Python-based analytics and automation tool designed to process IT issue tracker files (daily sheets, weekly logs, or monthly consolidated sheets). It automatically generates insights, summaries, visualizations, and AI-driven analysis for faster decision-making.

This tool can be used for **any internal IT project**, **client support project**, or **technology operations team**.

---

## 🔧 What the Tool Does

- Reads Excel issue tracker files (daily or monthly formats)
- Normalizes and structures issue records
- Categorizes issues (Compliance, MFA, Citrix, Network, Access, etc.)
- Generates:
  - Daily issue breakdown
  - Monthly summaries
  - Engineer workload insights
  - Issue frequency & patterns
- Creates visual charts (PNG output)
- Produces AI-generated natural‑language summaries
- Works across multiple teams or multiple projects

---

## 📂 Supported Input Formats

### **1. Daily Sheets**
Example:
- `01-01-2026`
- `10-12-2025`
- `5-1-2026`

Each sheet represents one day's tickets.

### **2. Monthly Sheets**
Example:
- `DEC2025`
- `JAN2026`
- `FEB2026`

Each sheet contains all issues for the month.

### **Required Columns**
Your Excel file must include the following fields (in any IT project context):

| Column | Description |
|--------|-------------|
| Project Name | Any internal or client project |
| Engineer Name | Engineer who handled the issue |
| Associate/Employee ID | Internal or client employee ID |
| Associate/Employee Name | User reporting the issue |
| Issue Description | Problem summary |
| Start Date & Time | DD/MM/YYYY |
| End Date & Time | DD/MM/YYYY |
| Status | Open / Closed |
| Request / Ticket ID | Ticket reference (INC, RITM, REQ, etc.) |
| Remarks | Resolution details |

---

## 🧠 Architecture Overview

### **1. Data Loader (`data_loader.py`)**
- Detects sheet type (daily or monthly)
- Parses Excel sheets into a unified DataFrame
- Converts dates and normalizes strings
- Adds:
  - `month`
  - `year`
  - `date`

Works flexibly across multiple projects.

---

### **2. Aggregation Engine (`aggregator.py`)**
Generates:

- Daily and monthly issue counts  
- Issue type distribution  
- Project-wise breakdown  
- Engineer workload  
- Recurring issue patterns  
- Cross-month comparisons  
- Open vs Closed analysis  

---

### **3. Visualization Engine (`visualizer.py`)**

Outputs charts such as:

- Daily trend line / bar chart  
- Monthly comparison bar chart  
- Issue type pie chart  
- Engineer workload distribution  
- Heatmaps (optional extension)  

Charts are saved as PNG for easy reporting.

---

### **4. AI Insight Generator (`genai_insights.py`)**

Generates natural language summaries using LLMs:

- Issue trends  
- Root-cause patterns  
- Highlighted problem areas  
- Comparison insights across months or projects  
- Recommended actions  

---

## 🧪 Example Code Usage

```python
from data_loader import load_tracker_file
from aggregator import generate_monthly_summary
from visualizer import plot_issue_distribution
from genai_insights import generate_summary_text

df = load_tracker_file("IT_Project_Tracker.xlsx")
summary = generate_monthly_summary(df)
plot_issue_distribution(summary)
print(generate_summary_text(summary))