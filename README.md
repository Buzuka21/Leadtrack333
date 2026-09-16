# leadtrack

A lightweight command-line CRM for business development and sales prospecting.

Most CRMs are overkill for solo BDMs, freelancers, or small teams tracking a
few dozen leads — they need a login, a browser tab, and a subscription just
to remember who to follow up with. `leadtrack` fills that gap: it's a single
Python CLI, backed by a local SQLite database, that lets you manage your
entire pipeline from the terminal in seconds.

## Features

- Add and manage leads with company, email, phone, and pipeline stage
- Log timestamped notes against any lead (calls, emails, meeting outcomes)
- Set and query follow-up dates so nothing falls through the cracks
- Filter/search leads by stage, name, company, or email
- Export your whole pipeline to CSV for reporting or sharing
- Quick stats view of your pipeline by stage
- Zero setup beyond `pip install` — no server, no account, no internet required

## Installation

```bash
pip install leadtrack
```

Or from source:

```bash
git clone https://github.com/Buzuka21/leadtrack.git
cd leadtrack
pip install -e .
```

## Usage

```bash
# Add a lead
leadtrack add "Rahul Sharma" --company "Acme Corp" --email rahul@acme.com --stage contacted

# List all leads
leadtrack list

# Filter by stage or search
leadtrack list --stage meeting
leadtrack list --search acme

# View full detail + notes for a lead
leadtrack show 1

# Update stage, follow-up date, or contact info
leadtrack update 1 --stage proposal --followup 2026-10-01

# Log a note
leadtrack note 1 "Sent proposal, following up next week"

# See what's due
leadtrack followups
leadtrack followups --days 7   # due within the next week

# Quick pipeline summary
leadtrack stats

# Export everything to CSV
leadtrack export pipeline.csv

# Delete a lead
leadtrack delete 1
```

## Pipeline stages

`new → contacted → meeting → proposal → won / lost`

## Data storage

All data lives locally in `~/.leadtrack/leads.db` (SQLite). Nothing is sent
anywhere — this tool is fully offline and private by design.

## Running tests

```bash
pip install -e ".[dev]"
pytest
```

## Contributing

Issues and PRs welcome. This started as a personal tool for managing BD
outreach and grew into something others doing similar work might find
useful — happy to take feature requests (e.g. reminders/notifications,
multiple pipelines, tagging).

## License

MIT
