# New Relic TPS Automation

Enterprise-ready automation that fetches KPI widgets from a New Relic dashboard, parses displayed values and trend arrows, translates them into natural-language status, fills a Slack-friendly template, and delivers via Slack webhook and/or Microsoft 365 email.

## Highlights
- Simple, robust pipeline: Fetch → Parse → Translate → Format → Deliver
- Reads widget trend data and derives peak value/time from the chart series
- Enterprise secrets support (AWS Secrets Manager, HashiCorp Vault, Azure Key Vault)
- Clean OOP design and Python best practices
- Ready for scheduled runs (GitHub Actions) and containerization later

## Architecture
- **Client**: NerdGraph query for dashboard pages/widgets.
- **Parser**: Extracts `current_value`, `comparison_pct`, `trend`, and from trend charts the `peak_value` and `peak_time`.
- **Translator**: Converts arrows/percentages to human-readable narratives and status lights.
- **Reporting**: Builds context and renders `templates/tps_report.j2`.
- **Delivery**: Slack webhook and Microsoft Graph email.

```
Dashboard → Widgets → Parse KPIs → Translate → Render (Jinja) → Deliver
```

## Directory Structure
```
NRReporting/
├─ src/
│  └─ newrelic_tps_automation/
│     ├─ clients/newrelic_client.py
│     ├─ services/
│     │  ├─ widget_parser.py
│     │  └─ trend_translator.py
│     ├─ reporting/
│     │  ├─ context.py
│     │  └─ renderer.py
│     ├─ delivery.py
│     ├─ pipeline.py
│     ├─ config.py
│     └─ secrets.py
├─ templates/
│  └─ tps_report.j2
├─ requirements.txt
├─ main.py
├─ README.md
└─ newrelic-tps-automation-design.md (design reference)
```

## Requirements
- Python 3.11+
- Access to the New Relic NerdGraph API and a Dashboard GUID
- One of: AWS Secrets Manager, Vault, or Azure Key Vault (for runtime secrets)

Install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration
Non-sensitive config via env or `.env` (see `.env.example`).

Required:
- `NEW_RELIC_ACCOUNT_ID`: your New Relic account ID
- `DASHBOARD_GUID`: GUID of the dashboard to read
- `SECRETS_PROVIDER`: `aws` | `vault` | `azure`

Optional:
- `REPORT_TIMEZONE` (default `US/Eastern`)
- `EVENT_NAME`, `DASHBOARD_URL`, `REPORT_USER_NAME`
- `EMAIL_RECIPIENTS`: comma-separated emails for O365 delivery
- Secret IDs (if you customize paths): `SECRET_ID_NEW_RELIC_API_KEY`, `SECRET_ID_SLACK_WEBHOOK`, `SECRET_ID_O365_CREDENTIALS`

### Secrets
Provide secrets at runtime via your provider:
- New Relic API Key JSON with key `api_key` (or `key`)
- Slack Webhook JSON with key `url` (or a raw URL string)
- O365 JSON: `tenant_id`, `client_id`, `client_secret`, `sender_email`

Provider-specific env:
- AWS: `AWS_REGION`
- Vault: `VAULT_ADDR`, `VAULT_TOKEN`, [`VAULT_MOUNT`]
- Azure: `AZURE_KEY_VAULT_URL`

## Running
Console only:
```bash
python main.py --delivery console
```
Slack:
```bash
python main.py --delivery slack
```
Email (Graph API):
```bash
python main.py --delivery email
```
Override event name and templates directory if needed:
```bash
python main.py --event-name "Peak Weekend Report" --templates-dir templates
```

## What the parser reads
- From each relevant widget:
  - `current_value`, `comparison_pct`, `trend`
  - Trend-series points from `data.raw` / `data.visualization`
  - Derives `peak_value` and human-friendly `peak_time` (ET)

## Delivery
- Slack: Incoming webhook (mrkdwn formatted)
- Email: Microsoft Graph using client credentials; HTML generated from the rendered Markdown

## Scheduling (GitHub Actions)
Example (run Mondays 10 AM ET):
```yaml
on:
  schedule:
    - cron: '0 14 * * 1'
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt
      - run: python main.py --delivery slack
        env:
          NEW_RELIC_ACCOUNT_ID: ${{ secrets.NEW_RELIC_ACCOUNT_ID }}
          DASHBOARD_GUID: ${{ secrets.DASHBOARD_GUID }}
          SECRETS_PROVIDER: aws
          AWS_REGION: us-east-1
```

## Security Practices
- No secrets in code or `.env`; all fetched from the configured provider at runtime
- Minimal scopes and least-privilege
- Logging avoids secret content

## Troubleshooting
- If widgets parse empty, verify the Dashboard GUID and that widgets contain numeric data.
- If peaks show `--`, ensure the widgets expose a time series in their `data` payload.
- If Slack/Email doesn’t deliver, verify secret paths and provider access.

## License
Internal project (adjust as needed).
