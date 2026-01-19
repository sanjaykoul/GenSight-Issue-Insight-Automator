
# GenSight-Issue-Insight-Automator

GenSight-Issue-Insight-Automator is a Python-based analytics tool designed specifically to process **monthly IT issue tracker sheets**. It analyzes Excel files where each sheet represents one month (e.g., `DEC2025`, `JAN2026`) and generates:

- Monthly issue insights
- Engineer workload summaries
- Issue-type categorization
- Trend visualizations
- AI-generated monthly summaries

This tool is ideal for IT support teams who maintain **monthly consolidated logs**.

---

## 📂 Supported Input Format (Monthly Only)

### ✔ Monthly Sheets  
Your Excel file should contain one or more sheets named as:

- `DEC2025`
- `JAN2026`
- `FEB2026`
- etc.

Each monthly sheet contains all issues handled during that month.

### ✔ Required Columns

| Column | Description |
|--------|-------------|
| Project Name | Name of the project (can be any project) |
| Engineer Name | Person handling the issue |
| Associate/Employee ID | Internal or client employee ID |
| Associate/Employee Name | End-user name |
| Issue Description | Summary of issue |
| Start Date & Time | DD/MM/YYYY |
| End Date & Time | DD/MM/YYYY |
| Status | Open / Closed |
| Request / Ticket ID | INC / RITM / REQ / Internal |
| Remarks | Resolution details |

---

## 🧠 How the Tool Works (Monthly‑Only Pipeline)

### **1. Data Loading (`data_loader.py`)**
- Reads monthly sheets only  
- Identifies month + year from sheet names  
- Parses dates  
- Normalizes and cleans data  
- Returns a unified DataFrame with columns like:
  - `month`
  - `year`
  - `date` (derived from Start Date)

---

### **2. Monthly Aggregation (`aggregator.py`)**
Generates monthly insights such as:

- Total issues per month  
- Issue-type distribution  
- Engineer workload  
- Daily patterns inside the month  
- Open vs Closed summary  
- Cross-month comparison (DEC vs JAN, etc.)

---

### **3. Visualization (`visualizer.py`)**
Produces PNG charts:

- Monthly issue comparison  
- Issue category distribution  
- Engineer workload chart  
- Daily issue trend for each month  

---

### **4. AI-Generated Summary (`genai_insights.py`)**
Creates natural language monthly insights:

- What issues occurred most  
- Key recurring problems  
- Engineer performance patterns  
- Comparison with previous months  
- Recommendations or observations  

---

## 🧪 Example Usage

```python
from data_loader import load_monthly_tracker
from aggregator import generate_monthly_summary
from visualizer import plot_issue_distribution
from genai_insights import generate_summary_text

df = load_monthly_tracker("Monthly_Tracker.xlsx")
summary = generate_monthly_summary(df)
plot_issue_distribution(summary)

print(generate_summary_text(summary))