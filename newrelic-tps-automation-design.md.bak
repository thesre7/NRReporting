# New Relic TPS/Capacity Monitoring Automation - Design Document

## Executive Summary

This document outlines the design and implementation approach for an automated reporting system that extracts metrics from New Relic dashboards, generates intelligent performance trend narratives, and securely delivers formatted status reports to stakeholders.

**Project Goal:** Automate the collection, analysis, and distribution of Card Core TSYS TPS/Capacity metrics to provide real-time insights into system performance and capacity utilization.

### Key Architectural Decisions

**1. Direct Dashboard Widget Parsing (No Calculations Required)**
- The New Relic dashboard **already displays** all metrics with trend indicators (↗ ↘)
- We simply **extract** the displayed values, percentages, and arrows
- **No need to query historical data** - the dashboard shows week-over-week changes
- **No complex calculations** - just parse and translate what's already there

**2. Simple Translation Engine**
- Convert dashboard indicators to natural language
- Arrow logic: `↗ = "higher than last week"`, `↘ = "lower than last week"`
- Direct mapping of dashboard widgets to report sections
- Minimal processing - maximum reliability

**3. Enterprise-Grade Security**
- All credentials stored in enterprise secrets management (AWS Secrets Manager, HashiCorp Vault, or Azure Key Vault)
- Zero credentials in code, config files, or environment variables
- OAuth 2.0 for email delivery (O365 Microsoft Graph API)
- Slack incoming webhooks for simple, secure messaging
- Comprehensive audit logging

**4. Flexible Deployment**
- Python-based for maintainability and rich ecosystem
- Multiple deployment options (GitHub Actions, AWS Lambda, Kubernetes, standalone)
- Containerized for portability
- Scheduled or on-demand execution

---

## 1. Overview & Objectives

### 1.1 Problem Statement
Currently, performance metrics from New Relic dashboards require manual review and interpretation. Stakeholders need regular updates on system performance, capacity utilization, and trend analysis for both TSYS Mainframe and HPNS services.

### 1.2 Objectives
- Extract metrics directly from New Relic dashboard widgets (values, arrows, percentages)
- Translate dashboard indicators (↗ ↘) into natural language narratives
- Generate formatted reports matching existing template structure
- Deliver reports securely to specified channels (Slack/Email/Webhook)
- Support arbitrary time ranges for dashboard queries
- Maintain enterprise-grade security for credentials and secrets

### 1.3 Success Criteria
- Reports generated within 2 minutes of scheduled time
- 100% accuracy in extracting and translating dashboard indicators
- Zero manual intervention required for standard reporting
- All credentials stored securely using enterprise secrets management
- Natural language narratives match expected format

---

## 2. System Architecture

### 2.1 High-Level Components

```
┌─────────────────────────────────────────┐
│   New Relic Dashboard                   │
│   ┌─────────────────────────────────┐   │
│   │ Total TPS: 2.48k ↗10.2%        │   │
│   │ HPNS TPS: 989 ↘4.7%            │   │
│   │ TSYS Capacity: 26.2% ↗10.2%    │   │
│   │ HPNS Capacity: 28.3% ↘4.7%     │   │
│   │ TPS Ratio: 39.9% ↘13.2%        │   │
│   └─────────────────────────────────┘   │
└────────┬────────────────────────────────┘
         │ Dashboard API
         │ (fetch widget data as-is)
         │
┌────────▼────────────────────────────────┐
│   Widget Parser                         │
│   - Extract current values              │
│   - Extract arrow indicators (↗ ↘)     │
│   - Extract percentage changes          │
└────────┬────────────────────────────────┘
         │
┌────────▼────────────────────────────────┐
│   Translation Engine                    │
│   - ↗ + 10.2% → "10.2% higher"         │
│   - ↘ + 4.7% → "4.7% lower"            │
│   - Generate status indicators          │
└────────┬────────────────────────────────┘
         │
┌────────▼────────────────────────────────┐
│   Report Generator                      │
│   - Plug values into template           │
│   - Format for Slack/Email              │
└────────┬────────────────────────────────┘
         │
┌────────▼────────────────────────────────┐
│   Secure Delivery                       │
│   - Slack incoming webhook              │
│   - O365 OAuth email                    │
└────────┬────────────────────────────────┘
         │
┌────────▼────────────────────────────────┐
│   Secrets Management                    │
│   - AWS Secrets Manager                 │
│   - HashiCorp Vault                     │
│   - Azure Key Vault                     │
└─────────────────────────────────────────┘
```

### 2.2 Technology Stack Options

**Option A: Python-based Solution (Recommended)**
- Language: Python 3.10+
- API Client: `requests` or `httpx`
- Data Processing: `pandas` for time-series analysis
- Template Engine: `jinja2` or f-strings
- Scheduling: GitHub Actions, AWS Lambda, or cron
- Deployment: Docker container or serverless

**Option B: Node.js Solution**
- Language: Node.js 18+
- API Client: `axios`
- Data Processing: Native JS with lodash
- Template Engine: Handlebars or template literals
- Scheduling: Same as Option A

**Recommendation:** Python for better data analysis libraries and your team's expertise

---

## 3. Data Sources & Dashboard Widget Parsing

### 3.1 Understanding the Dashboard

The New Relic dashboard **already contains all the data we need** in a pre-calculated, human-readable format. Each widget displays:
- **Current value** (e.g., 2.48k, 989, 26.2%)
- **Trend indicator** (↗ for increase, ↘ for decrease)
- **Percentage change** from previous period (e.g., 10.2%, 4.7%)

**Example Dashboard Widgets:**
```
┌──────────────────────┐    ┌──────────────────────┐
│  Total TPS           │    │  HPNS TPS            │
│  2.48k  ↗10.2%      │    │  989  ↘4.7%         │
└──────────────────────┘    └──────────────────────┘

┌──────────────────────┐    ┌──────────────────────┐
│  TSYS Capacity       │    │  HPNS Capacity       │
│  26.2%  ↗10.2%      │    │  28.3%  ↘4.7%       │
└──────────────────────┘    └──────────────────────┘

┌──────────────────────┐
│  TPS Ratio           │
│  39.9%  ↘13.2%      │
└──────────────────────┘
```

**Our job:** Extract these values and translate them into the report template.

### 3.2 New Relic Dashboard API

**Required Credentials:**
- New Relic User API Key (stored in secrets manager)
- Dashboard GUID (from dashboard URL)

**API Endpoint:**
```
https://api.newrelic.com/graphql
```

### 3.3 Widget Data Structure

When we query the dashboard API, we get a JSON response with widget data:

```json
{
  "widget": {
    "id": "widget-1",
    "title": "Total TPS",
    "visualization": {
      "id": "viz.billboard"
    },
    "rawConfiguration": {
      "nrqlQueries": [...],
      "thresholds": [...]
    },
    "results": {
      "value": 2480,           // Current value
      "comparison": 10.2,      // Percentage change
      "trend": "up"            // or "down" or "neutral"
    }
  }
}
```

### 3.4 Simple Extraction Logic

**Step 1: Fetch Dashboard Data**
```python
def fetch_dashboard_data(api_key, dashboard_guid):
    """Fetch all widget data from dashboard"""
    
    query = """
    {
      actor {
        entity(guid: "%s") {
          ... on DashboardEntity {
            pages {
              widgets {
                id
                title
                rawConfiguration
                # Widget data includes current values and comparisons
              }
            }
          }
        }
      }
    }
    """ % dashboard_guid
    
    response = requests.post(
        "https://api.newrelic.com/graphql",
        headers={"API-Key": api_key, "Content-Type": "application/json"},
        json={"query": query}
    )
    
    return response.json()
```

**Step 2: Parse Widget Values**
```python
def parse_widget(widget_data):
    """Extract value, arrow, and percentage from widget"""
    
    title = widget_data['title']
    
    # The widget's displayed data contains:
    # - current_value: The number shown (e.g., 2.48k)
    # - comparison_pct: The percentage change (e.g., 10.2)
    # - trend: "up" or "down" based on arrow indicator
    
    return {
        'title': title,
        'current_value': extract_current_value(widget_data),
        'comparison_pct': extract_comparison(widget_data),
        'trend': extract_trend(widget_data)  # "up", "down", or "neutral"
    }
```

### 3.5 Complete Data Extraction Example

```python
class NewRelicDashboardClient:
    """Simple client to extract dashboard widget data"""
    
    def __init__(self, api_key: str, dashboard_guid: str):
        self.api_key = api_key
        self.dashboard_guid = dashboard_guid
        self.base_url = "https://api.newrelic.com/graphql"
    
    def fetch_all_widgets(self) -> dict:
        """Fetch all dashboard widgets and parse values"""
        
        raw_data = self._fetch_dashboard_json()
        
        widgets = {}
        for widget in raw_data['widgets']:
            title = widget['title'].lower()
            parsed = self._parse_widget(widget)
            
            # Map widgets to our data structure
            if 'total tps' in title or 'tsys tps' in title:
                widgets['tsys_tps'] = parsed
            elif 'hpns tps' in title:
                widgets['hpns_tps'] = parsed
            elif 'tsys' in title and 'capacity' in title:
                widgets['tsys_capacity'] = parsed
            elif 'hpns' in title and 'capacity' in title:
                widgets['hpns_capacity'] = parsed
            elif 'ratio' in title:
                widgets['tps_ratio'] = parsed
        
        return widgets
    
    def _parse_widget(self, widget) -> dict:
        """Parse individual widget data"""
        
        # Widget structure varies, but contains the displayed values
        # This is where we extract the actual numbers, arrows, and percentages
        
        return {
            'current_value': self._extract_value(widget),
            'comparison_pct': self._extract_comparison(widget),
            'trend': self._extract_trend(widget),
            'raw_data': widget  # Keep for debugging
        }
    
    def _extract_value(self, widget) -> float:
        """Extract the current displayed value"""
        # Parse from widget's result data
        # Could be in different formats (2.48k, 989, 26.2%)
        pass
    
    def _extract_comparison(self, widget) -> float:
        """Extract the percentage change value"""
        # e.g., 10.2 from "↗10.2%"
        pass
    
    def _extract_trend(self, widget) -> str:
        """Extract trend direction from arrow indicator"""
        # Returns: "up", "down", or "neutral"
        pass
```

### 3.6 Expected Output Structure

After parsing, we have a clean dictionary:

```python
{
    'tsys_tps': {
        'current_value': 2480,
        'comparison_pct': 10.2,
        'trend': 'up'  # from ↗
    },
    'hpns_tps': {
        'current_value': 989,
        'comparison_pct': 4.7,
        'trend': 'down'  # from ↘
    },
    'tsys_capacity': {
        'current_value': 26.2,
        'comparison_pct': 10.2,
        'trend': 'up'
    },
    'hpns_capacity': {
        'current_value': 28.3,
        'comparison_pct': 4.7,
        'trend': 'down'
    },
    'tps_ratio': {
        'current_value': 39.9,
        'comparison_pct': 13.2,
        'trend': 'down'
    }
}
```

**That's it!** No calculations needed. We just extract what's already displayed on the dashboard.

---

## 4. Simple Translation Engine

### 4.1 Core Purpose

The "analysis" is actually just **translation logic** - converting dashboard indicators into natural language. No complex calculations, no statistical analysis - just:

```
Dashboard Data → Natural Language
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
↗10.2%         → "10.2% higher than last week"
↘4.7%          → "4.7% lower than last week"
26.2%          → "26.2%"
```

### 4.2 Translation Rules

**Rule 1: TPS Trends**
```python
def translate_tps_trend(service_name, trend, comparison_pct):
    """Convert dashboard indicator to narrative"""
    
    if trend == "up":
        return f"The TPS is {comparison_pct}% higher than last week for {service_name}"
    elif trend == "down":
        return f"The TPS is {comparison_pct}% lower than last week for {service_name}"
    else:
        return f"The TPS is stable for {service_name}"

# Examples:
# translate_tps_trend("TSYS Mainframe", "up", 0.5)
# → "The TPS is 0.5% higher than last week for TSYS Mainframe"

# translate_tps_trend("HPNS", "down", 28.6)
# → "The TPS is 28.6% lower than last week for HPNS"
```

**Rule 2: Ratio Behavior**
```python
def translate_ratio_behavior(ratio_value, trend, comparison_pct):
    """Convert ratio indicator to narrative"""
    
    stability_text = "in line with what we have been seeing since last week"
    
    if abs(comparison_pct) < 2:  # Less than 2% change is "stable"
        stability = stability_text
    elif trend == "up":
        stability = f"{comparison_pct}% higher than last week"
    else:
        stability = f"{comparison_pct}% lower than last week"
    
    return (
        f"Requests that require data from HPNS have been approx. {ratio_value}% of total, "
        f"which is {stability}."
    )

# Example:
# translate_ratio_behavior(43.0, "down", 13.2)
# → "Requests that require data from HPNS have been approx. 43.0% of total, 
#    which is 13.2% lower than last week."
```

**Rule 3: Capacity Assessment**
```python
def translate_capacity_assessment(tsys_capacity, hpns_capacity):
    """Generate capacity health statement"""
    
    max_capacity = max(tsys_capacity, hpns_capacity)
    
    if max_capacity >= 80:
        concern_service = 'TSYS' if tsys_capacity > hpns_capacity else 'HPNS'
        return (
            f"⚠️ Capacity utilization is elevated at {max_capacity}% for {concern_service}. "
            f"Recommend monitoring closely."
        )
    elif max_capacity >= 60:
        return (
            f"Capacity utilization is manageable (TSYS: {tsys_capacity}%, HPNS: {hpns_capacity}%). "
            f"Monitoring trends."
        )
    else:
        return (
            "Growth is closely matching last week's behavior. "
            "There are no capacity concerns at this time."
        )

# Example:
# translate_capacity_assessment(26.2, 28.3)
# → "Growth is closely matching last week's behavior. 
#    There are no capacity concerns at this time."
```

### 4.3 Status Indicators

**Traffic Status (🟢 🟡 🔴):**
```python
def get_traffic_status(tsys_tps, hpns_tps):
    """Simple traffic health indicator"""
    
    # If both services have TPS above baseline, green
    # This can be customized based on your thresholds
    
    if tsys_tps > 2000 and hpns_tps > 800:
        return '🟢'
    elif tsys_tps > 1000 or hpns_tps > 400:
        return '🟡'
    else:
        return '🔴'
```

**Capacity Status:**
```python
def get_capacity_status(tsys_capacity, hpns_capacity):
    """Simple capacity health indicator"""
    
    max_utilization = max(tsys_capacity, hpns_capacity)
    
    if max_utilization >= 80:
        return '🔴'
    elif max_utilization >= 60:
        return '🟡'
    else:
        return '🟢'
```

### 4.4 Complete Translation Engine

```python
class TrendTranslator:
    """Simple translator: Dashboard indicators → Natural language"""
    
    def __init__(self, threshold_config: dict = None):
        self.thresholds = threshold_config or {
            'capacity_warning': 60,
            'capacity_critical': 80,
            'ratio_stability_threshold': 2
        }
    
    def translate_all(self, dashboard_data: dict) -> dict:
        """Convert all dashboard indicators to narratives"""
        
        # Extract parsed data
        tsys_tps = dashboard_data['tsys_tps']
        hpns_tps = dashboard_data['hpns_tps']
        tsys_cap = dashboard_data['tsys_capacity']
        hpns_cap = dashboard_data['hpns_capacity']
        ratio = dashboard_data['tps_ratio']
        
        # Generate three narrative lines
        narratives = []
        
        # Line 1: TPS Trends
        tsys_desc = self._trend_to_text(
            "TSYS Mainframe",
            tsys_tps['trend'],
            tsys_tps['comparison_pct']
        )
        
        hpns_desc = self._trend_to_text(
            "HPNS",
            hpns_tps['trend'],
            hpns_tps['comparison_pct'],
            include_prefix=False
        )
        
        narratives.append(
            f"The TPS is {tsys_desc} for TSYS Mainframe; HPNS is running about {hpns_desc}."
        )
        
        # Line 2: Ratio Behavior
        narratives.append(self._ratio_to_text(
            ratio['current_value'],
            ratio['trend'],
            ratio['comparison_pct']
        ))
        
        # Line 3: Capacity Assessment
        narratives.append(self._capacity_to_text(
            tsys_cap['current_value'],
            hpns_cap['current_value']
        ))
        
        # Generate status indicators
        return {
            'trends': narratives,
            'traffic_status': self._get_traffic_status(
                tsys_tps['current_value'],
                hpns_tps['current_value']
            ),
            'capacity_status': self._get_capacity_status(
                tsys_cap['current_value'],
                hpns_cap['current_value']
            )
        }
    
    def _trend_to_text(self, service: str, trend: str, pct: float, include_prefix: bool = True) -> str:
        """Convert trend indicator to text"""
        
        prefix = f"{service} is " if include_prefix else ""
        
        if trend == "up":
            return f"{prefix}{abs(pct)}% higher than last week"
        elif trend == "down":
            return f"{prefix}{abs(pct)}% lower than last week"
        else:
            return f"{prefix}stable"
    
    def _ratio_to_text(self, value: float, trend: str, pct: float) -> str:
        """Convert ratio indicator to text"""
        
        if abs(pct) < self.thresholds['ratio_stability_threshold']:
            stability = "in line with what we have been seeing since last week"
        elif trend == "up":
            stability = f"{abs(pct)}% higher than last week"
        else:
            stability = f"{abs(pct)}% lower than last week"
        
        return (
            f"Requests that require data from HPNS have been approx. {value:.1f}% of total, "
            f"which is {stability}."
        )
    
    def _capacity_to_text(self, tsys_cap: float, hpns_cap: float) -> str:
        """Generate capacity assessment text"""
        
        max_cap = max(tsys_cap, hpns_cap)
        
        if max_cap >= self.thresholds['capacity_critical']:
            service = 'TSYS' if tsys_cap > hpns_cap else 'HPNS'
            return (
                f"⚠️ Capacity utilization is elevated at {max_cap:.1f}% for {service}. "
                f"Recommend monitoring closely."
            )
        elif max_cap >= self.thresholds['capacity_warning']:
            return (
                f"Capacity utilization is elevated but manageable "
                f"(TSYS: {tsys_cap:.1f}%, HPNS: {hpns_cap:.1f}%). "
                f"Monitoring trends."
            )
        else:
            return (
                "Growth is closely matching last week's behavior. "
                "There are no capacity concerns at this time."
            )
    
    def _get_traffic_status(self, tsys_tps: float, hpns_tps: float) -> str:
        """Simple traffic status indicator"""
        if tsys_tps > 2000 and hpns_tps > 800:
            return '🟢'
        elif tsys_tps > 1000 or hpns_tps > 400:
            return '🟡'
        else:
            return '🔴'
    
    def _get_capacity_status(self, tsys_cap: float, hpns_cap: float) -> str:
        """Simple capacity status indicator"""
        max_util = max(tsys_cap, hpns_cap)
        
        if max_util >= self.thresholds['capacity_critical']:
            return '🔴'
        elif max_util >= self.thresholds['capacity_warning']:
            return '🟡'
        else:
            return '🟢'
```

### 4.5 Usage Example

```python
# After parsing dashboard widgets
dashboard_data = {
    'tsys_tps': {'current_value': 2480, 'comparison_pct': 10.2, 'trend': 'up'},
    'hpns_tps': {'current_value': 989, 'comparison_pct': 4.7, 'trend': 'down'},
    'tsys_capacity': {'current_value': 26.2, 'comparison_pct': 10.2, 'trend': 'up'},
    'hpns_capacity': {'current_value': 28.3, 'comparison_pct': 4.7, 'trend': 'down'},
    'tps_ratio': {'current_value': 39.9, 'comparison_pct': 13.2, 'trend': 'down'}
}

# Translate to narratives
translator = TrendTranslator()
analysis = translator.translate_all(dashboard_data)

# Result:
# {
#     'trends': [
#         "The TPS is 10.2% higher than last week for TSYS Mainframe; HPNS is running about 4.7% lower than last week.",
#         "Requests that require data from HPNS have been approx. 39.9% of total, which is 13.2% lower than last week.",
#         "Growth is closely matching last week's behavior. There are no capacity concerns at this time."
#     ],
#     'traffic_status': '🟢',
#     'capacity_status': '🟢'
# }
```

**That's the entire "analysis" engine - just straightforward translation!**

---

## 5. Report Template & Formatting

### 5.1 Output Format

**Primary Format:** Slack Markdown (compatible with most platforms)

**Template Structure:**
```
[User Avatar] [Username] [Timestamp]

Peak season reporting for TSYS Real Time Inquiry/Update System [Date] [Time]

🟢 Traffic
🟢 Capacity Utilization

System KPIs:

TSYS Mainframe
• Average TPS over the weekend: [value]
• Peak TPS during the weekend: [value] @[timestamp]
• Average Capacity Utilization: [value]%

HPNS
• Average TPS over the weekend: [value]
• Peak TPS during the weekend: [value] @[timestamp]
• Average Capacity Utilization: [value]%

Performance Trends
• [Trend line 1]
• [Trend line 2]
• [Trend line 3]

Link to monitoring dashboard (edited)
```

### 5.2 Jinja2 Template

```jinja2
{{ user_name }} {{ timestamp }}

**Peak season reporting for TSYS Real Time Inquiry/Update System {{ report_date }} {{ report_time }}**

{{ traffic_status }} Traffic
{{ capacity_status }} Capacity Utilization

**System KPIs:**

**TSYS Mainframe**
• Average TPS over the weekend: **{{ tsys_avg_tps }}**
• Peak TPS during the weekend: **{{ tsys_peak_tps }}** @{{ tsys_peak_time }}
• Average Capacity Utilization: **{{ tsys_avg_capacity }}%**

**HPNS**
• Average TPS over the weekend: **{{ hpns_avg_tps }}**
• Peak TPS during the weekend: **{{ hpns_peak_tps }}** @{{ hpns_peak_time }}
• Average Capacity Utilization: **{{ hpns_avg_capacity }}%**

**Performance Trends**
{{ trends }}

[Link to monitoring dashboard]({{ dashboard_url }})
```

### 5.3 Dynamic Date and Time Formatting

```python
from datetime import datetime
import pytz

def get_report_date_time(timezone='US/Eastern'):
    """Get current date and time for report title"""
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    
    # Format: "November 13, 2025" and "10:00 AM ET"
    report_date = now.strftime("%B %d, %Y")
    report_time = now.strftime("%-I:%M %p ET")
    
    return report_date, report_time

# Example usage:
# report_date, report_time = get_report_date_time()
# report_date = "November 13, 2025"
# report_time = "10:00 AM ET"
# 
# Title becomes:
# "Peak season reporting for TSYS Real Time Inquiry/Update System November 13, 2025 10:00 AM ET"
```

---

## 6. Implementation Options

### 6.1 Option A: Python Script with Scheduled Execution

**Pros:**
- Full control over logic
- Easy to test and debug
- Portable across environments
- Rich ecosystem for data analysis

**Cons:**
- Requires hosting/scheduling infrastructure
- Manual dependency management

**Code Structure:**
```
newrelic-tps-automation/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration & thresholds
│   ├── secrets.py             # Unified secrets management interface
│   ├── newrelic_client.py     # New Relic Dashboard API integration
│   ├── analysis.py            # Intelligent trend analysis engine
│   ├── report_generator.py    # Template rendering
│   └── delivery.py            # Secure delivery (Slack, O365, SMTP)
├── templates/
│   └── tps_report.j2          # Jinja2 template
├── tests/
│   ├── test_secrets.py
│   ├── test_newrelic_client.py
│   ├── test_analysis.py
│   └── test_report_generator.py
├── requirements.txt
├── Dockerfile
├── .env.example               # Template for non-sensitive config
├── .gitignore
├── README.md
└── main.py                    # Entry point
```

**Key Dependencies:**
```txt
# Core dependencies
requests==2.31.0
pytz==2023.3
jinja2==3.1.2
python-dotenv==1.0.0

# New Relic API
# No specific client library needed - using requests directly

# Security & Secrets Management
boto3==1.34.0  # AWS SDK (for Secrets Manager)
botocore==1.34.0
hvac==2.1.0  # HashiCorp Vault client
azure-identity==1.15.0  # Azure authentication
azure-keyvault-secrets==4.7.0  # Azure Key Vault

# Email delivery with OAuth
msal==1.26.0  # Microsoft Authentication Library (for O365 OAuth)

# Slack delivery (incoming webhooks use requests)

# Optional: Data analysis (if doing historical trending)
pandas==2.1.0
numpy==1.24.0
```

### 6.2 Option B: GitHub Actions Workflow

**Pros:**
- No infrastructure to manage
- Built-in scheduling (cron)
- Version control integrated
- Free for reasonable usage

**Cons:**
- 6-hour job timeout
- Public repos expose workflow logic
- Limited to scheduled or event-triggered execution

**Workflow Example:**
```yaml
name: Generate TPS Report - Peak Season

on:
  schedule:
    # Run 4 times daily during peak season
    - cron: '0 14 * * *'  # 10 AM ET (14:00 UTC)
    - cron: '0 17 * * *'  # 1 PM ET (17:00 UTC)
    - cron: '0 20 * * *'  # 4 PM ET (20:00 UTC)
    - cron: '0 23 * * *'  # 7 PM ET (23:00 UTC)
  workflow_dispatch:  # Allow manual triggers

jobs:
  generate-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Generate and send report
        env:
          NEW_RELIC_API_KEY: ${{ secrets.NEW_RELIC_API_KEY }}
          NEW_RELIC_ACCOUNT_ID: ${{ secrets.NEW_RELIC_ACCOUNT_ID }}
          DASHBOARD_GUID: ${{ secrets.DASHBOARD_GUID }}
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
        run: |
          python main.py --delivery slack
```

### 6.3 Option C: AWS Lambda with EventBridge

**Pros:**
- Serverless - no infrastructure management
- Auto-scaling
- Pay per execution
- Integrates with AWS ecosystem

**Cons:**
- AWS-specific
- Cold start latency
- More complex deployment

**Lambda Handler:**
```python
import json
import os
from src.newrelic_client import NewRelicClient
from src.data_processor import DataProcessor
from src.report_generator import ReportGenerator
from src.delivery import SlackDelivery

def lambda_handler(event, context):
    """AWS Lambda handler for TPS report generation"""
    
    # Parse event for date range (if provided)
    start_date = event.get('start_date')
    end_date = event.get('end_date')
    
    # Initialize components
    nr_client = NewRelicClient(
        api_key=os.getenv('NEW_RELIC_API_KEY'),
        account_id=os.getenv('NEW_RELIC_ACCOUNT_ID')
    )
    
    processor = DataProcessor()
    generator = ReportGenerator()
    delivery = SlackDelivery(webhook_url=os.getenv('SLACK_WEBHOOK_URL'))
    
    # Execute workflow
    raw_data = nr_client.fetch_metrics(start_date, end_date)
    processed_data = processor.analyze(raw_data)
    report = generator.generate(processed_data)
    delivery.send(report)
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Report generated successfully'})
    }
```

**EventBridge Rule:**
```json
{
  "scheduleExpression": "cron(0 14 ? * MON *)",
  "description": "Trigger TPS report generation every Monday at 10 AM ET"
}
```

### 6.4 Option D: Containerized Solution with Kubernetes CronJob

**Pros:**
- Highly portable
- Works in any Kubernetes environment
- Easy to scale and monitor
- Good for complex workflows

**Cons:**
- Requires Kubernetes cluster
- More operational overhead

**CronJob Manifest:**
```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: tps-report-generator
spec:
  schedule: "0 14 * * 1"  # Every Monday 10 AM ET
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: tps-reporter
            image: your-registry/tps-automation:latest
            env:
            - name: NEW_RELIC_API_KEY
              valueFrom:
                secretKeyRef:
                  name: newrelic-credentials
                  key: api-key
            - name: SLACK_WEBHOOK_URL
              valueFrom:
                secretKeyRef:
                  name: slack-credentials
                  key: webhook-url
          restartPolicy: OnFailure
```

---

## 7. Detailed Implementation: Python Script Approach

### 7.1 Configuration Management

**config.py:**
```python
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class NewRelicConfig:
    api_key: str
    account_id: str
    dashboard_guid: Optional[str] = None
    
    @classmethod
    def from_env(cls):
        return cls(
            api_key=os.getenv('NEW_RELIC_API_KEY'),
            account_id=os.getenv('NEW_RELIC_ACCOUNT_ID'),
            dashboard_guid=os.getenv('DASHBOARD_GUID')
        )

@dataclass
class MetricThresholds:
    tsys_max_capacity: int = 10000  # TPS
    hpns_max_capacity: int = 5000   # TPS
    capacity_warning: float = 60.0  # %
    capacity_critical: float = 80.0  # %
    ratio_min: float = 30.0  # %
    ratio_max: float = 60.0  # %

@dataclass
class ReportConfig:
    timezone: str = 'US/Eastern'
    event_name: str = 'Weekend Performance Report'
    dashboard_url: str = 'https://one.newrelic.com/...'
    user_name: str = 'Ani'
    
    @classmethod
    def from_env(cls):
        return cls(
            timezone=os.getenv('REPORT_TIMEZONE', 'US/Eastern'),
            event_name=os.getenv('EVENT_NAME', 'Weekend Performance Report'),
            dashboard_url=os.getenv('DASHBOARD_URL', ''),
            user_name=os.getenv('REPORT_USER_NAME', 'SRE Team')
        )
```

### 7.2 New Relic Client

**newrelic_client.py:**
```python
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class NewRelicClient:
    """Client for interacting with New Relic NerdGraph API"""
    
    NERDGRAPH_URL = "https://api.newrelic.com/graphql"
    
    def __init__(self, api_key: str, account_id: str):
        self.api_key = api_key
        self.account_id = account_id
        self.session = requests.Session()
        self.session.headers.update({
            'API-Key': api_key,
            'Content-Type': 'application/json'
        })
    
    def execute_nrql(self, query: str) -> Dict:
        """Execute NRQL query via NerdGraph"""
        graphql_query = """
        query($accountId: Int!, $nrql: Nrql!) {
          actor {
            account(id: $accountId) {
              nrql(query: $nrql) {
                results
              }
            }
          }
        }
        """
        
        variables = {
            'accountId': int(self.account_id),
            'nrql': query
        }
        
        try:
            response = self.session.post(
                self.NERDGRAPH_URL,
                json={'query': graphql_query, 'variables': variables}
            )
            response.raise_for_status()
            data = response.json()
            
            if 'errors' in data:
                logger.error(f"NerdGraph errors: {data['errors']}")
                raise Exception(f"NerdGraph query failed: {data['errors']}")
            
            return data['data']['actor']['account']['nrql']['results']
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise
    
    def fetch_tps_metrics(self, app_name: str, start_time: datetime, end_time: datetime) -> Dict:
        """Fetch TPS metrics for specific application"""
        
        # Average TPS
        avg_query = f"""
        SELECT average(newrelic.timeslice.value) as 'avg_tps'
        FROM Metric
        WHERE metricTimesliceName = 'HttpDispatcher'
        AND appName = '{app_name}'
        SINCE '{start_time.isoformat()}' UNTIL '{end_time.isoformat()}'
        """
        
        # Peak TPS with timestamp
        peak_query = f"""
        SELECT max(newrelic.timeslice.value) as 'peak_tps'
        FROM Metric
        WHERE metricTimesliceName = 'HttpDispatcher'
        AND appName = '{app_name}'
        SINCE '{start_time.isoformat()}' UNTIL '{end_time.isoformat()}'
        """
        
        # Time series data for peak timestamp identification
        timeseries_query = f"""
        SELECT rate(count(*), 1 second) as 'tps'
        FROM Transaction
        WHERE appName = '{app_name}'
        SINCE '{start_time.isoformat()}' UNTIL '{end_time.isoformat()}'
        TIMESERIES 1 minute
        """
        
        avg_result = self.execute_nrql(avg_query)
        peak_result = self.execute_nrql(peak_query)
        timeseries_result = self.execute_nrql(timeseries_query)
        
        return {
            'avg_tps': avg_result[0]['avg_tps'] if avg_result else 0,
            'peak_tps': peak_result[0]['peak_tps'] if peak_result else 0,
            'timeseries': timeseries_result
        }
    
    def fetch_capacity_utilization(self, app_name: str, start_time: datetime, end_time: datetime) -> float:
        """Fetch average capacity utilization"""
        query = f"""
        SELECT average(apm.service.cpu.usertime.utilization) * 100 as 'utilization'
        FROM Metric
        WHERE appName = '{app_name}'
        SINCE '{start_time.isoformat()}' UNTIL '{end_time.isoformat()}'
        """
        
        result = self.execute_nrql(query)
        return result[0]['utilization'] if result else 0.0
    
    def fetch_all_metrics(self, start_time: datetime, end_time: datetime) -> Dict:
        """Fetch all required metrics for both TSYS and HPNS"""
        logger.info(f"Fetching metrics from {start_time} to {end_time}")
        
        tsys_tps = self.fetch_tps_metrics('TSYS', start_time, end_time)
        hpns_tps = self.fetch_tps_metrics('HPNS', start_time, end_time)
        
        tsys_capacity = self.fetch_capacity_utilization('TSYS', start_time, end_time)
        hpns_capacity = self.fetch_capacity_utilization('HPNS', start_time, end_time)
        
        return {
            'tsys': {
                **tsys_tps,
                'capacity_utilization': tsys_capacity
            },
            'hpns': {
                **hpns_tps,
                'capacity_utilization': hpns_capacity
            },
            'start_time': start_time,
            'end_time': end_time
        }
```

### 7.3 Data Processor

**data_processor.py:**
```python
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import pytz
import logging

logger = logging.getLogger(__name__)

class DataProcessor:
    """Process and analyze New Relic metrics"""
    
    def __init__(self, thresholds: 'MetricThresholds'):
        self.thresholds = thresholds
    
    def find_peak_timestamp(self, timeseries_data: List[Dict]) -> Tuple[float, datetime]:
        """Find peak value and its timestamp from timeseries data"""
        if not timeseries_data:
            return 0.0, datetime.now()
        
        peak_value = 0.0
        peak_time = None
        
        for datapoint in timeseries_data:
            value = datapoint.get('tps', 0)
            timestamp = datapoint.get('endTimeSeconds')
            
            if value > peak_value:
                peak_value = value
                peak_time = datetime.fromtimestamp(timestamp) if timestamp else None
        
        return peak_value, peak_time or datetime.now()
    
    def calculate_wow_change(self, current: float, previous: float) -> float:
        """Calculate week-over-week percentage change"""
        if previous == 0:
            return 0.0
        return round(((current - previous) / previous) * 100, 1)
    
    def calculate_tps_ratio(self, hpns_tps: float, total_tps: float) -> float:
        """Calculate HPNS/Total TPS ratio"""
        if total_tps == 0:
            return 0.0
        return round((hpns_tps / total_tps) * 100, 1)
    
    def get_capacity_status(self, utilization: float) -> str:
        """Get status indicator based on capacity utilization"""
        if utilization >= self.thresholds.capacity_critical:
            return '🔴'
        elif utilization >= self.thresholds.capacity_warning:
            return '🟡'
        else:
            return '🟢'
    
    def format_timestamp(self, dt: datetime, timezone: str = 'US/Eastern') -> str:
        """Format timestamp in specified timezone"""
        tz = pytz.timezone(timezone)
        local_dt = dt.astimezone(tz)
        return local_dt.strftime('%-I:%M %p ET on %b %dth, %Y')
    
    def generate_trend_narrative(self, 
                                 tsys_change: float, 
                                 hpns_change: float, 
                                 tps_ratio: float,
                                 tsys_capacity: float,
                                 hpns_capacity: float) -> List[str]:
        """Generate performance trend narratives"""
        
        trends = []
        
        # TPS Trend
        tsys_desc = self._get_change_description(tsys_change, "TSYS Mainframe")
        hpns_desc = self._get_change_description(hpns_change, "HPNS", include_prefix=False)
        
        trends.append(
            f"The TPS is {tsys_desc} for TSYS Mainframe; HPNS is running about {hpns_desc}."
        )
        
        # Ratio Analysis
        trends.append(
            f"Requests that require data from HPNS have been approx. {tps_ratio:.1f}% of total, "
            f"which is in line with what we have been seeing since last week."
        )
        
        # Capacity Assessment
        if tsys_capacity > self.thresholds.capacity_warning or hpns_capacity > self.thresholds.capacity_warning:
            trends.append(
                f"Capacity utilization is elevated. TSYS at {tsys_capacity:.1f}%, HPNS at {hpns_capacity:.1f}%. "
                f"Monitoring closely for scaling needs."
            )
        else:
            trends.append(
                "Growth is closely matching last week's behavior. There are no capacity concerns at this time."
            )
        
        return trends
    
    def _get_change_description(self, change: float, service: str = "", include_prefix: bool = True) -> str:
        """Get human-readable change description"""
        prefix = f"{service} is " if include_prefix and service else ""
        
        if abs(change) < 1:
            return f"{prefix}stable"
        elif change > 0:
            return f"{prefix}{abs(change):.1f}% higher than last week"
        else:
            return f"{prefix}{abs(change):.1f}% lower than last week"
    
    def process_metrics(self, 
                       current_data: Dict, 
                       previous_data: Dict = None) -> Dict:
        """Process and analyze metrics data"""
        
        logger.info("Processing metrics data")
        
        # Extract current period metrics
        tsys_avg = round(current_data['tsys']['avg_tps'])
        hpns_avg = round(current_data['hpns']['avg_tps'])
        
        # Find peak timestamps
        tsys_peak, tsys_peak_time = self.find_peak_timestamp(
            current_data['tsys']['timeseries']
        )
        hpns_peak, hpns_peak_time = self.find_peak_timestamp(
            current_data['hpns']['timeseries']
        )
        
        # Capacity utilization
        tsys_capacity = round(current_data['tsys']['capacity_utilization'], 1)
        hpns_capacity = round(current_data['hpns']['capacity_utilization'], 1)
        
        # Calculate TPS ratio
        tps_ratio = self.calculate_tps_ratio(hpns_avg, tsys_avg)
        
        # Calculate WoW changes if previous data provided
        tsys_change = 0.0
        hpns_change = 0.0
        if previous_data:
            prev_tsys_avg = round(previous_data['tsys']['avg_tps'])
            prev_hpns_avg = round(previous_data['hpns']['avg_tps'])
            
            tsys_change = self.calculate_wow_change(tsys_avg, prev_tsys_avg)
            hpns_change = self.calculate_wow_change(hpns_avg, prev_hpns_avg)
        
        # Generate status indicators
        traffic_status = '🟢'  # Could be dynamic based on thresholds
        capacity_status = self.get_capacity_status(max(tsys_capacity, hpns_capacity))
        
        # Generate trend narratives
        trends = self.generate_trend_narrative(
            tsys_change, hpns_change, tps_ratio, tsys_capacity, hpns_capacity
        )
        
        return {
            'tsys': {
                'avg_tps': tsys_avg,
                'peak_tps': round(tsys_peak),
                'peak_time': self.format_timestamp(tsys_peak_time),
                'capacity_utilization': tsys_capacity,
                'wow_change': tsys_change
            },
            'hpns': {
                'avg_tps': hpns_avg,
                'peak_tps': round(hpns_peak),
                'peak_time': self.format_timestamp(hpns_peak_time),
                'capacity_utilization': hpns_capacity,
                'wow_change': hpns_change
            },
            'tps_ratio': tps_ratio,
            'traffic_status': traffic_status,
            'capacity_status': capacity_status,
            'trends': trends,
            'start_time': current_data['start_time'],
            'end_time': current_data['end_time']
        }
```

### 7.4 Report Generator

**report_generator.py:**
```python
from datetime import datetime
from typing import Dict
import pytz
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generate formatted reports from processed metrics"""
    
    TEMPLATE = """{{ user_name }} {{ timestamp }}

**TSYS Real Time Inquiry/Update System Status for {{ event_name }} - {{ date_range }}**

{{ traffic_status }} Traffic
{{ capacity_status }} Capacity Utilization

**System KPIs:**

**TSYS Mainframe**
• Average TPS over the weekend: **{{ tsys_avg_tps }}**
• Peak TPS during the weekend: **{{ tsys_peak_tps }}** @{{ tsys_peak_time }}
• Average Capacity Utilization: **{{ tsys_capacity }}%**

**HPNS**
• Average TPS over the weekend: **{{ hpns_avg_tps }}**
• Peak TPS during the weekend: **{{ hpns_peak_tps }}** @{{ hpns_peak_time }}
• Average Capacity Utilization: **{{ hpns_capacity }}%**

**Performance Trends**
{% for trend in trends %}• {{ trend }}
{% endfor %}
[Link to monitoring dashboard]({{ dashboard_url }})
"""
    
    def __init__(self, report_config: 'ReportConfig'):
        self.config = report_config
        self.template = Template(self.TEMPLATE)
    
    def format_date_range(self, start_time: datetime, end_time: datetime) -> str:
        """Format date range for report header"""
        tz = pytz.timezone(self.config.timezone)
        
        start = start_time.astimezone(tz)
        end = end_time.astimezone(tz)
        
        # Format: "Nov 7th 2025, 7 PM ET through Nov 10th 10AM ET"
        start_str = start.strftime('%b %dth %Y, %-I %p ET')
        end_str = end.strftime('%b %dth %-I%p ET')
        
        return f"{start_str} through {end_str}"
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp for report header"""
        tz = pytz.timezone(self.config.timezone)
        now = datetime.now(tz)
        return now.strftime('%-I:%M %p')
    
    def generate(self, processed_data: Dict) -> str:
        """Generate formatted report from processed data"""
        
        logger.info("Generating report")
        
        date_range = self.format_date_range(
            processed_data['start_time'],
            processed_data['end_time']
        )
        
        report = self.template.render(
            user_name=self.config.user_name,
            timestamp=self.get_current_timestamp(),
            event_name=self.config.event_name,
            date_range=date_range,
            traffic_status=processed_data['traffic_status'],
            capacity_status=processed_data['capacity_status'],
            tsys_avg_tps=processed_data['tsys']['avg_tps'],
            tsys_peak_tps=processed_data['tsys']['peak_tps'],
            tsys_peak_time=processed_data['tsys']['peak_time'],
            tsys_capacity=processed_data['tsys']['capacity_utilization'],
            hpns_avg_tps=processed_data['hpns']['avg_tps'],
            hpns_peak_tps=processed_data['hpns']['peak_tps'],
            hpns_peak_time=processed_data['hpns']['peak_time'],
            hpns_capacity=processed_data['hpns']['capacity_utilization'],
            trends=processed_data['trends'],
            dashboard_url=self.config.dashboard_url
        )
        
        return report
```

### 7.5 Secure Delivery Module

**delivery.py:**
```python
import requests
from typing import Optional, List
import logging
from msal import ConfidentialClientApplication

logger = logging.getLogger(__name__)

class SlackDelivery:
    """Deliver reports to Slack via incoming webhook"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send(self, message: str, thread_ts: Optional[str] = None) -> bool:
        """Send message to Slack using incoming webhook"""
        
        payload = {
            "text": message,
            "mrkdwn": True
        }
        
        # Incoming webhooks don't support threading via payload
        # Thread support requires using the Web API with a bot token
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            logger.info("Report sent to Slack successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send to Slack: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            return False

class O365EmailDelivery:
    """Deliver reports via Microsoft 365 using OAuth 2.0 and Microsoft Graph"""
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str, sender_email: str):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.sender_email = sender_email
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        
        self.app = ConfidentialClientApplication(
            client_id,
            authority=self.authority,
            client_credential=client_secret
        )
    
    def _get_access_token(self) -> str:
        """Get access token for Microsoft Graph"""
        
        # Try to get token from cache
        result = self.app.acquire_token_silent(self.scope, account=None)
        
        if not result:
            # Acquire new token
            result = self.app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" in result:
            logger.info("Successfully acquired access token")
            return result["access_token"]
        else:
            error = result.get("error_description", "Unknown error")
            logger.error(f"Failed to acquire access token: {error}")
            raise Exception(f"Failed to get access token: {error}")
    
    def send(self, 
             subject: str, 
             body: str, 
             recipients: List[str],
             body_type: str = "HTML") -> bool:
        """Send email via Microsoft Graph API"""
        
        try:
            # Get access token
            token = self._get_access_token()
            
            # Construct email message
            email_msg = {
                "message": {
                    "subject": subject,
                    "body": {
                        "contentType": body_type,
                        "content": body
                    },
                    "toRecipients": [
                        {"emailAddress": {"address": email}} 
                        for email in recipients
                    ]
                },
                "saveToSentItems": "true"
            }
            
            # Send via Microsoft Graph
            endpoint = f"https://graph.microsoft.com/v1.0/users/{self.sender_email}/sendMail"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(endpoint, json=email_msg, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Report sent to {recipients} successfully via O365")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send email via O365: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"Error in email delivery: {e}")
            return False
    
    def _convert_markdown_to_html(self, markdown: str) -> str:
        """Convert basic Markdown to HTML for email"""
        
        html = markdown.replace('**', '<strong>', 1)
        html = html.replace('**', '</strong>', 1)
        
        # Convert bullet points
        lines = html.split('\n')
        html_lines = []
        in_list = False
        
        for line in lines:
            if line.strip().startswith('•'):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{line.strip()[1:].strip()}</li>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<p>{line}</p>')
        
        if in_list:
            html_lines.append('</ul>')
        
        return '\n'.join(html_lines)

class SMTPEmailDelivery:
    """
    Deliver reports via SMTP with TLS (fallback option)
    
    SECURITY NOTE: Only use this if OAuth is not available.
    Credentials MUST be retrieved from enterprise secrets manager at runtime.
    """
    
    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
        logger.warning(
            "Using SMTP basic auth. Consider migrating to OAuth 2.0 for better security."
        )
    
    def send(self, 
             subject: str, 
             body: str, 
             recipients: List[str],
             sender: Optional[str] = None) -> bool:
        """Send email via SMTP with TLS"""
        
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        sender = sender or self.username
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            
            # Convert Markdown to HTML
            html_body = self._convert_markdown_to_html(body)
            
            # Attach both plain text and HTML versions
            msg.attach(MIMEText(body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
            
            # Connect with TLS
            with smtplib.SMTP(self.host, self.port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
            
            logger.info(f"Report sent to {recipients} successfully via SMTP")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email via SMTP: {e}")
            return False
    
    def _convert_markdown_to_html(self, markdown: str) -> str:
        """Basic Markdown to HTML conversion"""
        html = markdown.replace('**', '<strong>').replace('**', '</strong>')
        html = html.replace('\n', '<br>\n')
        html = f"<html><body><pre style='font-family: Arial, sans-serif;'>{html}</pre></body></html>"
        return html

class WebhookDelivery:
    """Deliver reports to generic webhook endpoints"""
    
    def __init__(self, webhook_url: str, headers: Optional[dict] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {'Content-Type': 'application/json'}
    
    def send(self, payload: dict) -> bool:
        """Send payload to webhook"""
        try:
            response = requests.post(
                self.webhook_url, 
                json=payload, 
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            logger.info("Report sent to webhook successfully")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send to webhook: {e}")
            return False

# Factory for creating delivery clients
def create_delivery_clients(secrets_manager) -> dict:
    """Create delivery clients using secrets from secrets manager"""
    
    clients = {}
    
    # Slack delivery (if configured)
    try:
        slack_webhook = secrets_manager.get_slack_webhook()
        clients['slack'] = SlackDelivery(slack_webhook)
        logger.info("Slack delivery configured")
    except Exception as e:
        logger.warning(f"Slack delivery not configured: {e}")
    
    # Email delivery (prefer O365 OAuth)
    try:
        # Try O365 OAuth first
        o365_creds = secrets_manager.get_secret('prod/o365/oauth')
        clients['email'] = O365EmailDelivery(
            tenant_id=o365_creds['tenant_id'],
            client_id=o365_creds['client_id'],
            client_secret=o365_creds['client_secret'],
            sender_email=o365_creds.get('sender_email', 'reports@company.com')
        )
        logger.info("Email delivery configured with OAuth 2.0")
    except Exception:
        # Fallback to SMTP if OAuth not available
        try:
            smtp_creds = secrets_manager.get_smtp_credentials()
            clients['email'] = SMTPEmailDelivery(
                host=smtp_creds['host'],
                port=int(smtp_creds['port']),
                username=smtp_creds['username'],
                password=smtp_creds['password']
            )
            logger.info("Email delivery configured with SMTP")
        except Exception as e:
            logger.warning(f"Email delivery not configured: {e}")
    
    return clients
```

### 7.6 Main Entry Point (Simplified)

**main.py:**
```python
#!/usr/bin/env python3
"""
New Relic TPS/Capacity Monitoring Automation
Main entry point for report generation
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional
import argparse
import pytz

from src.config import MetricThresholds, ReportConfig
from src.newrelic_client import NewRelicDashboardClient
from src.analysis import TrendAnalyzer
from src.report_generator import ReportGenerator
from src.delivery import create_delivery_clients
from src.secrets import get_secrets_provider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('tps_automation.log')
    ]
)

logger = logging.getLogger(__name__)

def parse_arguments():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Generate TPS/Capacity reports from New Relic Dashboard'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date in YYYY-MM-DD format (default: 3 days ago)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date in YYYY-MM-DD format (default: now)'
    )
    
    parser.add_argument(
        '--event-name',
        type=str,
        help='Event name for report header'
    )
    
    parser.add_argument(
        '--delivery',
        choices=['slack', 'email', 'both', 'console'],
        default='slack',
        help='Delivery method for report'
    )
    
    parser.add_argument(
        '--compare-previous',
        action='store_true',
        help='Include week-over-week comparison'
    )
    
    parser.add_argument(
        '--secrets-provider',
        choices=['aws', 'vault', 'azure'],
        default='aws',
        help='Secrets management provider'
    )
    
    return parser.parse_args()

def get_date_range(start_date_str: Optional[str], 
                   end_date_str: Optional[str]) -> tuple[datetime, datetime]:
    """Get date range for report"""
    
    tz = pytz.timezone('US/Eastern')
    
    if end_date_str:
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        end_date = tz.localize(end_date.replace(hour=23, minute=59, second=59))
    else:
        end_date = datetime.now(tz)
    
    if start_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        start_date = tz.localize(start_date.replace(hour=0, minute=0, second=0)
---

## Appendix A: Quick Start Guide

### Initial Setup

```bash
# Clone repository
git clone <repo-url>
cd tps-automation

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment (non-sensitive config only)
cp .env.example .env
# Edit .env with non-sensitive configuration
```

### Configure Secrets (One-Time Setup)

**Option 1: AWS Secrets Manager**
```bash
# Store New Relic API key
aws secretsmanager create-secret \
    --name prod/newrelic/api-key \
    --secret-string "NRAK-XXXXXXXXXXXXX"

# Store Slack webhook
aws secretsmanager create-secret \
    --name prod/slack/tps-webhook \
    --secret-string "https://hooks.slack.com/services/XXX/YYY/ZZZ"

# Store O365 OAuth credentials
aws secretsmanager create-secret \
    --name prod/o365/oauth \
    --secret-string '{
      "tenant_id":"xxx",
      "client_id":"yyy",
      "client_secret":"zzz",
      "sender_email":"reports@company.com"
    }'
```

### Run Tests

```bash
# Test secrets retrieval
python -c "from src.secrets import get_secrets_provider; \
           s = get_secrets_provider('aws'); \
           print('Secrets OK')"

# Run with console output (no delivery)
python main.py --delivery console

# Run with Slack delivery
python main.py --delivery slack

# Run with custom date range and comparison
python main.py \
  --start-date 2025-11-07 \
  --end-date 2025-11-10 \
  --event-name "Tower/T-Mobile Launch" \
  --delivery slack \
  --compare-previous \
  --secrets-provider aws
```

### Scheduled Execution Setup

**GitHub Actions (Recommended):**
```yaml
# .github/workflows/tps-report.yml
name: Generate TPS Report

on:
  schedule:
    - cron: '0 14 * * 1'  # Every Monday 10 AM ET (14:00 UTC)
  workflow_dispatch:

jobs:
  generate-report:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # For AWS OIDC
      contents: read
    
    steps:
      - uses: actions/checkout@v3
      
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::ACCOUNT:role/github-actions-tps-automation
          aws-region: us-east-1
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Generate report
        run: |
          python main.py \
            --delivery slack \
            --compare-previous \
            --secrets-provider aws
        env:
          NEW_RELIC_ACCOUNT_ID: ${{ secrets.NEW_RELIC_ACCOUNT_ID }}
          DASHBOARD_GUID: ${{ secrets.DASHBOARD_GUID }}
```

### Troubleshooting

**Secrets Access Issues:**
```bash
# Test AWS credentials
aws sts get-caller-identity

# Test secrets retrieval
aws secretsmanager get-secret-value --secret-id prod/newrelic/api-key

# Check IAM permissions
aws iam get-user-policy --user-name your-user --policy-name SecretsAccess
```

**Dashboard Data Issues:**
```bash
# Test New Relic API connectivity
python -c "from src.newrelic_client import NewRelicDashboardClient; \
           from src.secrets import get_secrets_provider; \
           s = get_secrets_provider(); \
           creds = s.get_newrelic_credentials(); \
           print('Connection OK')"
```
 if 'email' in delivery_clients:
                    recipients = os.getenv('EMAIL_RECIPIENTS', '').split(',')
                    if recipients:
                        subject = f"TPS Report: {report_config.event_name}"
                        delivery_clients['email'].send(subject, report, recipients)
                    else:
                        logger.warning("EMAIL_RECIPIENTS not configured")
                else:
                    logger.warning("Email delivery requested but not configured")
        
        logger.info("Report generation completed successfully")
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
```

---

## 8. Deployment & Operations

### 8.1 Environment Variables

**Non-sensitive configuration** (can be in `.env` or environment):

```bash
# New Relic Configuration (non-sensitive)
NEW_RELIC_ACCOUNT_ID=1234567
DASHBOARD_GUID=XXX-YYY-ZZZ

# Report Configuration
REPORT_TIMEZONE=US/Eastern
EVENT_NAME=Weekend Performance Report
DASHBOARD_URL=https://one.newrelic.com/...
REPORT_USER_NAME=Ani

# Secrets Provider Selection
SECRETS_PROVIDER=aws  # Options: aws, vault, azure

# Delivery Configuration (non-sensitive)
EMAIL_RECIPIENTS=team@company.com,manager@company.com

# AWS Secrets Manager (if using AWS)
AWS_REGION=us-east-1

# Azure Key Vault (if using Azure)
AZURE_KEY_VAULT_URL=https://my-keyvault.vault.azure.net/

# HashiCorp Vault (if using Vault)
VAULT_ADDR=https://vault.company.com
# Note: VAULT_TOKEN or VAULT_ROLE_ID/SECRET_ID retrieved via IAM/auth method

# Metric Thresholds (optional overrides)
TSYS_MAX_CAPACITY=10000
HPNS_MAX_CAPACITY=5000
CAPACITY_WARNING=60
CAPACITY_CRITICAL=80
```

**Sensitive credentials** (MUST be in secrets manager):

These should NEVER be in environment variables or config files:
- `prod/newrelic/api-key` - New Relic API Key
- `prod/slack/tps-webhook` - Slack incoming webhook URL
- `prod/o365/oauth` - O365 OAuth credentials (tenant_id, client_id, client_secret)
- `prod/smtp/credentials` - SMTP credentials (if OAuth not available)

**Example `.env` file:**
```bash
# .env.example - Template for configuration
# Copy to .env and customize for your environment
# NEVER commit .env to version control

# === Non-Sensitive Configuration ===
NEW_RELIC_ACCOUNT_ID=1234567
DASHBOARD_GUID=abc-123-def-456
REPORT_TIMEZONE=US/Eastern
DASHBOARD_URL=https://one.newrelic.com/dashboards/abc123
REPORT_USER_NAME=SRE Team

# === Secrets Provider ===
SECRETS_PROVIDER=aws
AWS_REGION=us-east-1

# === Delivery Settings ===
EMAIL_RECIPIENTS=ops-team@company.com,management@company.com

# === Threshold Overrides (Optional) ===
# CAPACITY_WARNING=60
# CAPACITY_CRITICAL=80
```

### 8.2 Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .

# Set timezone
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Run as non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "main.py"]
```

**Build and run:**
```bash
# Build image
docker build -t tps-automation:latest .

# Run with environment file
docker run --env-file .env tps-automation:latest

# Run with custom date range
docker run --env-file .env tps-automation:latest \
  --start-date 2025-11-07 \
  --end-date 2025-11-10 \
  --event-name "Tower/T-Mobile Launch"
```

### 8.3 Scheduled Execution

**Execution Schedule:**
The automation runs **4 times per day** during peak season at:
- **10:00 AM ET** (14:00 UTC)
- **01:00 PM ET** (17:00 UTC)
- **04:00 PM ET** (20:00 UTC)
- **07:00 PM ET** (23:00 UTC)

**Using cron:**
```bash
# Edit crontab
crontab -e

# Add entries for all four daily runs (times in UTC for server)
0 14 * * * cd /path/to/tps-automation && /usr/bin/python3 main.py --delivery slack >> /var/log/tps-automation.log 2>&1
0 17 * * * cd /path/to/tps-automation && /usr/bin/python3 main.py --delivery slack >> /var/log/tps-automation.log 2>&1
0 20 * * * cd /path/to/tps-automation && /usr/bin/python3 main.py --delivery slack >> /var/log/tps-automation.log 2>&1
0 23 * * * cd /path/to/tps-automation && /usr/bin/python3 main.py --delivery slack >> /var/log/tps-automation.log 2>&1
```

**Using systemd timer:**

**/etc/systemd/system/tps-report.service:**
```ini
[Unit]
Description=TPS Report Generation
After=network.target

[Service]
Type=oneshot
User=appuser
WorkingDirectory=/opt/tps-automation
EnvironmentFile=/opt/tps-automation/.env
ExecStart=/usr/bin/python3 /opt/tps-automation/main.py --delivery slack
```

**/etc/systemd/system/tps-report.timer:**
```ini
[Unit]
Description=TPS Report Timer - 4x Daily
Requires=tps-report.service

[Timer]
# Run at 10 AM ET (14:00 UTC)
OnCalendar=*-*-* 14:00:00
# Run at 1 PM ET (17:00 UTC)
OnCalendar=*-*-* 17:00:00
# Run at 4 PM ET (20:00 UTC)
OnCalendar=*-*-* 20:00:00
# Run at 7 PM ET (23:00 UTC)
OnCalendar=*-*-* 23:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:
```bash
sudo systemctl enable tps-report.timer
sudo systemctl start tps-report.timer
sudo systemctl status tps-report.timer
```

### 8.4 Monitoring & Alerting

**Health Check Endpoint (Optional):**

Add Flask/FastAPI endpoint for health monitoring:

```python
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'last_run': get_last_run_time(),
        'next_run': get_next_scheduled_run()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
```

**Dead Man's Switch:**

Implement heartbeat monitoring:

```python
import requests

def send_heartbeat():
    """Send heartbeat to monitoring service"""
    heartbeat_url = os.getenv('HEARTBEAT_URL')
    if heartbeat_url:
        try:
            requests.get(heartbeat_url)
        except:
            pass

# Add to main() after successful execution
send_heartbeat()
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

**tests/test_data_processor.py:**
```python
import pytest
from datetime import datetime
from src.data_processor import DataProcessor
from src.config import MetricThresholds

@pytest.fixture
def processor():
    return DataProcessor(MetricThresholds())

def test_calculate_wow_change(processor):
    assert processor.calculate_wow_change(110, 100) == 10.0
    assert processor.calculate_wow_change(90, 100) == -10.0
    assert processor.calculate_wow_change(100, 0) == 0.0

def test_calculate_tps_ratio(processor):
    assert processor.calculate_tps_ratio(400, 1000) == 40.0
    assert processor.calculate_tps_ratio(0, 1000) == 0.0
    assert processor.calculate_tps_ratio(500, 0) == 0.0

def test_get_capacity_status(processor):
    assert processor.get_capacity_status(50) == '🟢'
    assert processor.get_capacity_status(70) == '🟡'
    assert processor.get_capacity_status(85) == '🔴'

def test_format_timestamp(processor):
    dt = datetime(2025, 11, 8, 12, 5, 0)
    formatted = processor.format_timestamp(dt)
    assert 'Nov' in formatted
    assert '2025' in formatted
```

### 9.2 Integration Tests

**tests/test_newrelic_client.py:**
```python
import pytest
from unittest.mock import Mock, patch
from src.newrelic_client import NewRelicClient
from datetime import datetime, timedelta

@pytest.fixture
def mock_client():
    return NewRelicClient('fake-api-key', '123456')

@patch('requests.Session.post')
def test_execute_nrql(mock_post, mock_client):
    # Mock successful response
    mock_response = Mock()
    mock_response.json.return_value = {
        'data': {
            'actor': {
                'account': {
                    'nrql': {
                        'results': [{'avg_tps': 2500}]
                    }
                }
            }
        }
    }
    mock_post.return_value = mock_response
    
    result = mock_client.execute_nrql("SELECT average(tps)")
    assert result[0]['avg_tps'] == 2500
```

### 9.3 End-to-End Test

```python
def test_full_workflow():
    """Test complete workflow with mocked data"""
    
    # Mock New Relic client
    mock_data = {
        'tsys': {
            'avg_tps': 2810,
            'peak_tps': 4830,
            'capacity_utilization': 30.0,
            'timeseries': []
        },
        'hpns': {
            'avg_tps': 1260,
            'peak_tps': 2110,
            'capacity_utilization': 35.9,
            'timeseries': []
        },
        'start_time': datetime.now() - timedelta(days=3),
        'end_time': datetime.now()
    }
    
    processor = DataProcessor(MetricThresholds())
    processed = processor.process_metrics(mock_data)
    
    assert processed['tsys']['avg_tps'] == 2810
    assert processed['hpns']['avg_tps'] == 1260
    assert 'trends' in processed
    assert len(processed['trends']) > 0
```

---

## 10. Extensibility & Future Enhancements

### 10.1 Phase 2 Features

**Anomaly Detection:**
```python
def detect_anomalies(current_value, historical_values):
    """Detect anomalies using statistical methods"""
    mean = np.mean(historical_values)
    std = np.std(historical_values)
    
    z_score = (current_value - mean) / std
    
    if abs(z_score) > 3:
        return 'anomaly', z_score
    elif abs(z_score) > 2:
        return 'warning', z_score
    else:
        return 'normal', z_score
```

**Predictive Capacity Planning:**
```python
def predict_capacity_breach(timeseries_data, days_ahead=7):
    """Predict when capacity will be breached"""
    # Linear regression on trend
    # Return estimated date of capacity breach
    pass
```

**Dashboard Screenshot Attachment:**
```python
from selenium import webdriver

def capture_dashboard_screenshot(dashboard_url):
    """Capture screenshot of New Relic dashboard"""
    # Use Selenium to capture dashboard
    # Attach to report
    pass
```

### 10.2 Configuration UI

Build simple web UI for configuration:
- Date range picker
- Metric threshold adjustments
- Delivery channel selection
- Event name customization

### 10.3 Multi-Dashboard Support

Extend to support multiple dashboards:
```python
DASHBOARDS = {
    'card_core': {
        'guid': 'XXX-YYY-ZZZ',
        'services': ['TSYS', 'HPNS']
    },
    'payment_gateway': {
        'guid': 'AAA-BBB-CCC',
        'services': ['Gateway', 'Processor']
    }
}
```

---

## 11. Enterprise Security Architecture

### 11.1 Security Principles

**Core Requirements:**
- ✅ No credentials stored in code or configuration files
- ✅ All secrets retrieved from enterprise secrets management at runtime
- ✅ Principle of least privilege for all API access
- ✅ Audit logging for all secret access
- ✅ Automatic secret rotation support
- ✅ Encryption at rest and in transit

### 11.2 Secrets Management Options

#### Option A: AWS Secrets Manager (Recommended for AWS environments)

**Setup:**
```bash
# Store New Relic API key
aws secretsmanager create-secret \
    --name prod/newrelic/api-key \
    --description "New Relic API Key for TPS Automation" \
    --secret-string "NRAK-XXXXXXXXXXXXX"

# Store email credentials (if using SMTP)
aws secretsmanager create-secret \
    --name prod/smtp/credentials \
    --description "SMTP credentials for report delivery" \
    --secret-string '{"username":"reports@company.com","password":"xxx","host":"smtp.office365.com","port":"587"}'

# Store Slack webhook
aws secretsmanager create-secret \
    --name prod/slack/tps-webhook \
    --description "Slack webhook for TPS reports" \
    --secret-string "https://hooks.slack.com/services/XXX/YYY/ZZZ"
```

**Runtime Retrieval:**
```python
import boto3
import json
from botocore.exceptions import ClientError

class SecretsManager:
    """Retrieve secrets from AWS Secrets Manager"""
    
    def __init__(self, region_name='us-east-1'):
        self.client = boto3.client('secretsmanager', region_name=region_name)
    
    def get_secret(self, secret_name: str) -> dict:
        """Retrieve secret by name"""
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            
            # Parse secret string
            if 'SecretString' in response:
                secret = response['SecretString']
                try:
                    return json.loads(secret)
                except json.JSONDecodeError:
                    return {'value': secret}
            else:
                # Binary secret
                return {'value': base64.b64decode(response['SecretBinary'])}
        
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                raise Exception(f"Secret {secret_name} not found")
            else:
                raise Exception(f"Error retrieving secret: {e}")
    
    def get_newrelic_credentials(self) -> dict:
        """Get New Relic credentials"""
        api_key = self.get_secret('prod/newrelic/api-key')
        return {
            'api_key': api_key['value'],
            'account_id': os.getenv('NEW_RELIC_ACCOUNT_ID')  # Non-sensitive, can be env var
        }
    
    def get_smtp_credentials(self) -> dict:
        """Get SMTP credentials for email delivery"""
        return self.get_secret('prod/smtp/credentials')
    
    def get_slack_webhook(self) -> str:
        """Get Slack webhook URL"""
        secret = self.get_secret('prod/slack/tps-webhook')
        return secret['value']

# Usage in application
secrets_mgr = SecretsManager()
nr_creds = secrets_mgr.get_newrelic_credentials()
nr_client = NewRelicClient(nr_creds['api_key'], nr_creds['account_id'])
```

**IAM Policy for Lambda/EC2:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:prod/newrelic/*",
        "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:prod/smtp/*",
        "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:prod/slack/*"
      ]
    }
  ]
}
```

#### Option B: HashiCorp Vault (Recommended for multi-cloud)

**Setup:**
```bash
# Enable KV secrets engine
vault secrets enable -path=secret kv-v2

# Store New Relic credentials
vault kv put secret/prod/newrelic \
    api_key="NRAK-XXXXXXXXXXXXX" \
    account_id="1234567"

# Store SMTP credentials
vault kv put secret/prod/smtp \
    host="smtp.office365.com" \
    port="587" \
    username="reports@company.com" \
    password="xxx"

# Store Slack webhook
vault kv put secret/prod/slack \
    webhook_url="https://hooks.slack.com/services/XXX/YYY/ZZZ"
```

**Runtime Retrieval:**
```python
import hvac
import os

class VaultSecretsManager:
    """Retrieve secrets from HashiCorp Vault"""
    
    def __init__(self, vault_addr: str = None, vault_token: str = None):
        self.vault_addr = vault_addr or os.getenv('VAULT_ADDR')
        self.vault_token = vault_token or os.getenv('VAULT_TOKEN')
        
        self.client = hvac.Client(
            url=self.vault_addr,
            token=self.vault_token
        )
        
        if not self.client.is_authenticated():
            raise Exception("Failed to authenticate with Vault")
    
    def get_secret(self, path: str) -> dict:
        """Retrieve secret from Vault"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point='secret'
            )
            return response['data']['data']
        except Exception as e:
            raise Exception(f"Error retrieving secret from {path}: {e}")
    
    def get_newrelic_credentials(self) -> dict:
        """Get New Relic credentials"""
        return self.get_secret('prod/newrelic')
    
    def get_smtp_credentials(self) -> dict:
        """Get SMTP credentials"""
        return self.get_secret('prod/smtp')
    
    def get_slack_webhook(self) -> str:
        """Get Slack webhook URL"""
        secret = self.get_secret('prod/slack')
        return secret['webhook_url']

# Usage with AppRole authentication (more secure than token)
class VaultAppRoleAuth(VaultSecretsManager):
    """Authenticate to Vault using AppRole"""
    
    def __init__(self, vault_addr: str, role_id: str, secret_id: str):
        self.vault_addr = vault_addr
        self.client = hvac.Client(url=vault_addr)
        
        # Authenticate using AppRole
        response = self.client.auth.approle.login(
            role_id=role_id,
            secret_id=secret_id
        )
        
        self.client.token = response['auth']['client_token']
        
        if not self.client.is_authenticated():
            raise Exception("AppRole authentication failed")
```

#### Option C: Azure Key Vault (For Azure/O365 environments)

**Setup:**
```bash
# Create key vault
az keyvault create \
    --name tps-automation-kv \
    --resource-group prod-rg \
    --location eastus

# Store secrets
az keyvault secret set \
    --vault-name tps-automation-kv \
    --name newrelic-api-key \
    --value "NRAK-XXXXXXXXXXXXX"

az keyvault secret set \
    --vault-name tps-automation-kv \
    --name smtp-credentials \
    --value '{"username":"reports@company.com","password":"xxx","host":"smtp.office365.com","port":"587"}'

az keyvault secret set \
    --vault-name tps-automation-kv \
    --name slack-webhook \
    --value "https://hooks.slack.com/services/XXX/YYY/ZZZ"
```

**Runtime Retrieval:**
```python
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
import json

class AzureSecretsManager:
    """Retrieve secrets from Azure Key Vault"""
    
    def __init__(self, vault_url: str = None):
        self.vault_url = vault_url or os.getenv('AZURE_KEY_VAULT_URL')
        self.credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=self.vault_url, credential=self.credential)
    
    def get_secret(self, secret_name: str) -> dict:
        """Retrieve secret from Key Vault"""
        try:
            secret = self.client.get_secret(secret_name)
            
            # Try to parse as JSON
            try:
                return json.loads(secret.value)
            except json.JSONDecodeError:
                return {'value': secret.value}
        
        except Exception as e:
            raise Exception(f"Error retrieving secret {secret_name}: {e}")
    
    def get_newrelic_credentials(self) -> dict:
        """Get New Relic credentials"""
        api_key = self.get_secret('newrelic-api-key')
        return {
            'api_key': api_key['value'],
            'account_id': os.getenv('NEW_RELIC_ACCOUNT_ID')
        }
    
    def get_smtp_credentials(self) -> dict:
        """Get SMTP credentials"""
        return self.get_secret('smtp-credentials')
    
    def get_slack_webhook(self) -> str:
        """Get Slack webhook URL"""
        secret = self.get_secret('slack-webhook')
        return secret['value']
```

### 11.3 Unified Secrets Interface

Create a unified interface for any secrets backend:

```python
from abc import ABC, abstractmethod
from typing import Dict

class SecretsProvider(ABC):
    """Abstract base class for secrets providers"""
    
    @abstractmethod
    def get_newrelic_credentials(self) -> Dict:
        pass
    
    @abstractmethod
    def get_smtp_credentials(self) -> Dict:
        pass
    
    @abstractmethod
    def get_slack_webhook(self) -> str:
        pass

# Factory pattern for provider selection
def get_secrets_provider(provider_type: str = None) -> SecretsProvider:
    """Factory to get appropriate secrets provider"""
    
    provider_type = provider_type or os.getenv('SECRETS_PROVIDER', 'aws')
    
    if provider_type == 'aws':
        return SecretsManager()
    elif provider_type == 'vault':
        return VaultSecretsManager()
    elif provider_type == 'azure':
        return AzureSecretsManager()
    else:
        raise ValueError(f"Unknown secrets provider: {provider_type}")

# Usage in application
secrets = get_secrets_provider()
nr_creds = secrets.get_newrelic_credentials()
```

### 11.4 Email Security Best Practices

**For Enterprise Email (O365/Gmail):**

**Option 1: OAuth 2.0 with Modern Auth (Recommended)**
```python
from msal import ConfidentialClientApplication
import requests

class O365OAuth:
    """Authenticate to O365 using OAuth 2.0"""
    
    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        self.authority = f"https://login.microsoftonline.com/{tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        
        self.app = ConfidentialClientApplication(
            client_id,
            authority=self.authority,
            client_credential=client_secret
        )
    
    def get_access_token(self) -> str:
        """Get access token for Microsoft Graph"""
        result = self.app.acquire_token_silent(self.scope, account=None)
        
        if not result:
            result = self.app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception(f"Failed to get access token: {result.get('error_description')}")
    
    def send_email(self, token: str, subject: str, body: str, recipients: list):
        """Send email via Microsoft Graph API"""
        
        endpoint = "https://graph.microsoft.com/v1.0/users/reports@company.com/sendMail"
        
        email_msg = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body
                },
                "toRecipients": [
                    {"emailAddress": {"address": email}} for email in recipients
                ]
            },
            "saveToSentItems": "true"
        }
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(endpoint, json=email_msg, headers=headers)
        response.raise_for_status()

# Usage with secrets manager
secrets = get_secrets_provider()
o365_creds = secrets.get_secret('prod/o365/oauth')

oauth = O365OAuth(
    tenant_id=o365_creds['tenant_id'],
    client_id=o365_creds['client_id'],
    client_secret=o365_creds['client_secret']
)

token = oauth.get_access_token()
oauth.send_email(token, "TPS Report", report_body, ["team@company.com"])
```

**Option 2: Service Account with App Password (Legacy)**
Only use if OAuth is not available. Never store in code:
```python
# Credentials ONLY from secrets manager
smtp_creds = secrets.get_smtp_credentials()

# Use with TLS
server = smtplib.SMTP(smtp_creds['host'], int(smtp_creds['port']))
server.starttls()
server.login(smtp_creds['username'], smtp_creds['password'])
```

### 11.5 Network Security

**Egress Controls:**
```python
# Whitelist only necessary endpoints
ALLOWED_ENDPOINTS = [
    'api.newrelic.com',
    'hooks.slack.com',
    'smtp.office365.com',
    'secretsmanager.us-east-1.amazonaws.com'
]

def validate_endpoint(url: str) -> bool:
    """Validate outbound connection is allowed"""
    from urllib.parse import urlparse
    
    domain = urlparse(url).netloc
    return any(domain.endswith(allowed) for allowed in ALLOWED_ENDPOINTS)
```

**TLS/SSL Enforcement:**
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.ssl_ import create_urllib3_context

class TLSAdapter(HTTPAdapter):
    """Enforce TLS 1.2+"""
    
    def init_poolmanager(self, *args, **kwargs):
        context = create_urllib3_context()
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

# Use in all HTTPS requests
session = requests.Session()
session.mount('https://', TLSAdapter())
```

### 11.6 Audit Logging

**Log all secret access:**
```python
import logging
import json
from datetime import datetime

class AuditLogger:
    """Audit logger for secret access"""
    
    def __init__(self, log_file: str = '/var/log/tps-automation/audit.log'):
        self.logger = logging.getLogger('audit')
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_secret_access(self, secret_name: str, action: str, user: str = None):
        """Log secret access"""
        
        audit_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': 'secret_access',
            'secret_name': secret_name,
            'action': action,
            'user': user or os.getenv('USER'),
            'source_ip': self._get_source_ip()
        }
        
        self.logger.info(json.dumps(audit_entry))
    
    def _get_source_ip(self) -> str:
        """Get source IP for audit"""
        try:
            return requests.get('https://api.ipify.org').text
        except:
            return 'unknown'

# Usage
audit = AuditLogger()
secrets = get_secrets_provider()

audit.log_secret_access('prod/newrelic/api-key', 'retrieve')
nr_creds = secrets.get_newrelic_credentials()
```

### 11.7 Secret Rotation

**Automated rotation support:**
```python
def rotate_newrelic_api_key():
    """Rotate New Relic API key"""
    
    # 1. Generate new key via New Relic API
    new_key = generate_new_newrelic_key()
    
    # 2. Store new key in secrets manager
    secrets_client = boto3.client('secretsmanager')
    secrets_client.update_secret(
        SecretId='prod/newrelic/api-key',
        SecretString=new_key
    )
    
    # 3. Test new key
    test_client = NewRelicClient(new_key, account_id)
    test_client.test_connection()
    
    # 4. Revoke old key
    revoke_old_key()
    
    # 5. Audit log
    audit.log_secret_access('prod/newrelic/api-key', 'rotate')
```

### 11.8 Security Checklist

- [ ] All secrets stored in enterprise secrets manager (AWS/Vault/Azure)
- [ ] No credentials in code, config files, or environment variables
- [ ] IAM policies follow principle of least privilege
- [ ] TLS 1.2+ enforced for all connections
- [ ] Audit logging enabled for all secret access
- [ ] Secret rotation policy defined and implemented
- [ ] Network egress controls in place
- [ ] OAuth 2.0 used for email (not basic auth)
- [ ] Regular security reviews scheduled
- [ ] Incident response plan documented

---

## 12. Cost Analysis

### 12.1 New Relic API Usage

- NerdGraph queries: Free within plan limits
- Typical report: ~6-10 API calls
- Monthly cost: Negligible (within free tier)

### 12.2 Infrastructure Costs

**GitHub Actions:**
- Free for public repos
- $0.008/minute for private repos
- ~2 minutes per run = $0.016/run
- Weekly schedule = ~$0.06/month

**AWS Lambda:**
- $0.20 per 1M requests
- $0.0000166667 per GB-second
- Typical execution: 512MB, 30 seconds
- Cost per run: ~$0.0001
- Weekly schedule = ~$0.0004/month

**Docker on EC2:**
- t3.micro: $0.0104/hour = $7.49/month
- Includes compute for other workloads

**Recommendation:** GitHub Actions for simplicity and cost

---

## 13. Implementation Roadmap

### Phase 1: MVP (Week 1-2)
- [ ] Set up Python project structure
- [ ] Implement New Relic API client
- [ ] Build data processor with basic calculations
- [ ] Create report template
- [ ] Implement Slack delivery
- [ ] Add basic error handling
- [ ] Test with sample data

### Phase 2: Production Hardening (Week 3)
- [ ] Add comprehensive error handling
- [ ] Implement retries and backoff
- [ ] Add logging and monitoring
- [ ] Write unit tests
- [ ] Create Dockerfile
- [ ] Set up CI/CD pipeline
- [ ] Document deployment process

### Phase 3: Enhanced Features (Week 4)
- [ ] Add week-over-week comparison
- [ ] Implement trend analysis
- [ ] Add anomaly detection
- [ ] Support email delivery
- [ ] Create health check endpoint
- [ ] Add configuration validation

### Phase 4: Scale & Optimize (Week 5+)
- [ ] Optimize API calls
- [ ] Add caching layer
- [ ] Support multiple dashboards
- [ ] Build configuration UI
- [ ] Implement advanced analytics
- [ ] Add dashboard screenshots

---

## 14. Success Metrics

**Operational Metrics:**
- Report generation time: < 2 minutes
- API success rate: > 99.9%
- Delivery success rate: > 99.5%
- Uptime: > 99.9%

**Business Metrics:**
- Time saved per report: ~15 minutes
- Weekly time savings: ~1 hour
- Annual time savings: ~52 hours
- Accuracy improvement: 100% (no manual errors)

**Adoption Metrics:**
- Number of stakeholders receiving reports
- Report view/read rate
- Action items generated from reports
- Feedback from stakeholders

---

## 15. Support & Maintenance

### 15.1 Runbook

**Common Issues:**

1. **API Authentication Failure**
   - Check API key validity
   - Verify account ID
   - Confirm key permissions

2. **No Data Returned**
   - Verify NRQL queries
   - Check date ranges
   - Confirm service names

3. **Delivery Failure**
   - Test webhook URLs
   - Verify network connectivity
   - Check credentials

### 15.2 Maintenance Schedule

- **Weekly:** Review logs for errors
- **Monthly:** Update dependencies
- **Quarterly:** Review and update thresholds
- **Annually:** API key rotation

---

## 16. Conclusion & Recommendations

This automation eliminates manual report generation by **directly extracting** dashboard widget data and **translating** it into formatted narratives. The approach is intentionally simple - no complex calculations, no historical data queries, no statistical analysis. Just parse what's already displayed and convert it to natural language.

### Why This Approach Works

**1. Dashboard Already Has Everything**
- New Relic dashboard displays current values
- Dashboard shows trend arrows (↗ ↘)
- Dashboard calculates percentage changes
- We just need to read and translate

**2. Simple = Reliable**
- Fewer components = fewer failure points
- No complex calculations = less chance for errors
- Direct mapping = easy to debug
- Clear logic = easy to maintain

**3. Enterprise-Secure by Design**
- Secrets in enterprise vaults, not in code
- OAuth for email, not basic auth
- Audit logging built-in
- Zero credentials in config files

### Recommended Implementation Path

**Phase 1 (Week 1): Core Functionality**
1. Set up AWS Secrets Manager (or Vault/Azure)
2. Implement dashboard widget parser
3. Build simple translation engine
4. Create report template renderer
5. Implement Slack webhook delivery
6. Test with real dashboard data

**Phase 2 (Week 2): Security & Delivery**
1. Implement OAuth 2.0 for O365 email
2. Add comprehensive error handling
3. Set up audit logging
4. Write unit tests for translation logic
5. Create deployment pipeline
6. Document runbook

**Phase 3 (Week 3): Production**
1. Deploy to staging
2. Run parallel with manual reports
3. Validate accuracy
4. Fine-tune narratives
5. Deploy to production
6. Set up monitoring

### Expected Outcomes

**Time Savings:**
- Manual report generation: ~20 minutes/week
- Annual time savings: ~17 hours
- Plus elimination of manual errors

**Quality Improvements:**
- 100% consistent formatting
- No transcription errors
- Real-time availability
- Professional presentation

**Security Improvements:**
- All credentials in enterprise vault
- OAuth instead of passwords
- Audit trail for compliance
- No secrets in code or config

### Technology Stack Recommendation

**For PwC Environment:**
- **Language:** Python 3.11+
- **Secrets:** AWS Secrets Manager
- **Deployment:** GitHub Actions (simple) or AWS Lambda (enterprise)
- **Email:** O365 OAuth via Microsoft Graph API
- **Slack:** Incoming webhooks
- **Monitoring:** CloudWatch + existing observability

### Success Criteria

✅ Reports generated automatically on schedule  
✅ Dashboard values extracted accurately  
✅ Narratives match expected format  
✅ All credentials in secrets manager  
✅ Zero manual intervention for 30 days  
✅ Stakeholders prefer automated reports  

### Next Steps

1. **Review & Approve** this design document
2. **Provision Access** to New Relic API and secrets manager
3. **Create Repository** and set up CI/CD
4. **Begin Development** starting with widget parser
5. **Schedule Reviews** for weekly progress checks

---

**Document Version:** 2.0 (Revised for Simplified Dashboard Approach)  
**Last Updated:** November 13, 2025  
**Author:** Ani (with Claude)  
**Status:** Ready for Implementation  

### Change Log

**v2.0 (2025-11-13):**
- Simplified approach using dashboard data extraction instead of custom NRQL queries
- Enhanced security section with enterpris
---

## Complete End-to-End Example

### Input: Dashboard Widgets

```
Dashboard State at 2025-11-10 10:00 AM ET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Widget 1: Total TPS (TSYS)
┌─────────────────────┐
│  2.48k  ↗ 10.2%    │
└─────────────────────┘

Widget 2: HPNS TPS
┌──────────────�
**Document Version:** 2.1 (Clarified Simple Approach)  
**Last Updated:** November 13, 2025  
**Author:** Ani (with Claude)  
**Status:** Ready for Implementation  

### Change Log

**v2.1 (2025-11-13 - Final Clarification):**
- ✅ Clarified that dashboard ALREADY contains all trend indicators (arrows, percentages)
- ✅ Simplified "analysis" to just translation logic (arrows → words)
- ✅ Emphasized: NO calculations, NO historical queries, NO complexity
- ✅ Added complete end-to-end example showing the simple flow
- ✅ Made it crystal clear: just parse → translate → format → deliver

**v2.0 (2025-11-13):**
- Simplified approach using dashboard data extraction instead of custom NRQL queries
- Enhanced security section with enterprise secrets management patterns
- Added OAuth 2.0 email delivery via Microsoft Graph
- Removed NRQL query appendix (no longer needed)

**v1.0 (Initial):**
- Original complex approach with NRQL query building
arison_pct': 4.7,
        'trend': 'down'  # from ↘
    },
    'tsys_capacity': {
        'current_value': 26.2,
        'comparison_pct': 10.2,
        'trend': 'up'
    },
    'hpns_capacity': {
        'current_value': 28.3,
        'comparison_pct': 4.7,
        'trend': 'down'
    },
    'tps_ratio': {
        'current_value': 39.9,
        'comparison_pct': 13.2,
        'trend': 'down'
    }
}
```

### Step 2: Translate → Generate Narratives

```python
translator = TrendTranslator()
analysis = translator.translate_all(parsed_data)

# Output:
analysis = {
    'trends': [
        "The TPS is 10.2% higher than last week for TSYS Mainframe; HPNS is running about 4.7% lower than last week.",
        "Requests that require data from HPNS have been approx. 39.9% of total, which is 13.2% lower than last week.",
        "Growth is closely matching last week's behavior. There are no capacity concerns at this time."
    ],
    'traffic_status': '🟢',
    'capacity_status': '🟢'
}
```

### Step 3: Generate Report → Fill Template

```
Ani 10:00 AM

TSYS Real Time Inquiry/Update System Status for Tower/T-Mobile Launch - 
Nov 7th 2025, 7 PM ET through Nov 10th 10AM ET

🟢 Traffic
🟢 Capacity Utilization

System KPIs:

TSYS Mainframe
• Average TPS over the weekend: 2810
• Peak TPS during the weekend: 4830 @12:05 PM ET on Nov 08th, 2025
• Average Capacity Utilization: 30%

HPNS
• Average TPS over the weekend: 1260
• Peak TPS during the weekend: 2110 @12:05 PM ET on Nov 08th, 2025
• Average Capacity Utilization: 35.9%

Performance Trends
• The TPS is 10.2% higher than last week for TSYS Mainframe; HPNS is running about 4.7% lower than last week.
• Requests that require data from HPNS have been approx. 39.9% of total, which is 13.2% lower than last week.
• Growth is closely matching last week's behavior. There are no capacity concerns at this time.

Link to monitoring dashboard
```

### Step 4: Deliver → Slack/Email

**Slack:**
POST to webhook → Message appears in channel

**Email:**
OAuth to Microsoft Graph → Email sent to recipients

---

## Summary: The Complete Flow

```
┌─────────────────────────┐
│  New Relic Dashboard    │
│  (has all the data)     │
└───────────┬─────────────┘
            │
            │ API Call: Fetch widgets
            ▼
┌─────────────────────────┐
│  Parse Widget Data      │
│  • Extract values       │
│  • Extract arrows       │
│  • Extract percentages  │
└───────────┬─────────────┘
            │
            │ Parsed data dict
            ▼
┌─────────────────────────┐
│  Translate to Text      │
│  • ↗ → "higher"        │
│  • ↘ → "lower"         │
│  • Generate narratives  │
└───────────┬─────────────┘
            │
            │ Analysis dict
            ▼
┌─────────────────────────┐
│  Fill Template          │
│  • Plug in values       │
│  • Format for delivery  │
└───────────┬─────────────┘
            │
            │ Formatted report
            ▼
┌─────────────────────────┐
│  Deliver Securely       │
│  • Slack webhook        │
│  • O365 OAuth email     │
└─────────────────────────┘
```

**No calculations. No complex queries. Just:**
1. **Fetch** what's already on the dashboard
2. **Parse** the displayed values and indicators
3. **Translate** arrows/percentages to words
4. **Plug** into template
5. **Deliver** securely

**Simple. Reliable. Maintainable.**
