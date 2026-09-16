"""leadtrack: a lightweight command-line CRM for BD/sales prospecting."""
import csv
import sys
from datetime import date, datetime

import click

from leadtrack import db

STAGE_COLORS = {
    "new": "white",
    "contacted": "cyan",
    "meeting": "yellow",
    "proposal": "magenta",
    "won": "green",
    "lost": "red",
}


@click.group()
def cli():
    """leadtrack — a lightweight CLI CRM for BD/sales prospecting.

    Track leads, log outreach notes, and never miss a follow-up,
    all from your terminal, backed by a local SQLite database.
    """
    db.init_db()


@cli.command()
@click.argument("name")
@click.option("--company", "-c", default=None, help="Company name")
@click.option("--email", "-e", default=None, help="Contact email")
@click.option("--phone", "-p", default=None, help="Contact phone")
@click.option(
    "--stage", "-s", default="new", type=click.Choice(db.STAGES), help="Pipeline stage"
)
def add(name, company, email, phone, stage):
    """Add a new lead."""
    lead_id = db.add_lead(name, company, email, phone, stage)
    click.secho(f"Added lead #{lead_id}: {name}", fg="green")


@cli.command(name="list")
@click.option("--stage", "-s", default=None, type=click.Choice(db.STAGES), help="Filter by stage")
@click.option("--search", "-q", default=None, help="Search name/company/email")
def list_cmd(stage, search):
    """List leads, optionally filtered by stage or search text."""
    leads = db.list_leads(stage=stage, search=search)
    if not leads:
        click.echo("No leads found.")
        return
    for lead in leads:
        color = STAGE_COLORS.get(lead["stage"], "white")
        followup = f" | follow-up: {lead['followup_date']}" if lead["followup_date"] else ""
        click.echo(
            f"#{lead['id']:<4} "
            + click.style(f"[{lead['stage']:^9}]", fg=color)
            + f" {lead['name']:<25} {lead['company'] or '':<20}{followup}"
        )


@cli.command()
@click.argument("lead_id", type=int)
def show(lead_id):
    """Show full detail for a single lead, including notes."""
    lead = db.get_lead(lead_id)
    if not lead:
        click.secho(f"No lead with id {lead_id}", fg="red")
        sys.exit(1)
    click.echo(f"#{lead['id']} — {lead['name']}")
    click.echo(f"  Company:   {lead['company'] or '-'}")
    click.echo(f"  Email:     {lead['email'] or '-'}")
    click.echo(f"  Phone:     {lead['phone'] or '-'}")
    click.echo(f"  Stage:     {lead['stage']}")
    click.echo(f"  Follow-up: {lead['followup_date'] or '-'}")
    click.echo(f"  Created:   {lead['created_at']}")
    click.echo(f"  Updated:   {lead['updated_at']}")
    notes = db.get_notes(lead_id)
    if notes:
        click.echo("  Notes:")
        for n in notes:
            click.echo(f"    [{n['created_at']}] {n['note']}")


@cli.command()
@click.argument("lead_id", type=int)
@click.option("--stage", "-s", type=click.Choice(db.STAGES), help="New pipeline stage")
@click.option("--followup", "-f", help="Follow-up date, YYYY-MM-DD")
@click.option("--company", "-c", help="Update company")
@click.option("--email", "-e", help="Update email")
@click.option("--phone", "-p", help="Update phone")
def update(lead_id, stage, followup, company, email, phone):
    """Update fields on an existing lead."""
    if not db.get_lead(lead_id):
        click.secho(f"No lead with id {lead_id}", fg="red")
        sys.exit(1)
    fields = {}
    if stage:
        fields["stage"] = stage
    if followup:
        try:
            datetime.strptime(followup, "%Y-%m-%d")
        except ValueError:
            click.secho("followup date must be YYYY-MM-DD", fg="red")
            sys.exit(1)
        fields["followup_date"] = followup
    if company is not None:
        fields["company"] = company
    if email is not None:
        fields["email"] = email
    if phone is not None:
        fields["phone"] = phone
    if not fields:
        click.echo("Nothing to update. Pass --stage, --followup, --company, --email, or --phone.")
        return
    db.update_lead(lead_id, **fields)
    click.secho(f"Updated lead #{lead_id}", fg="green")


@cli.command()
@click.argument("lead_id", type=int)
@click.confirmation_option(prompt="Are you sure you want to delete this lead?")
def delete(lead_id):
    """Delete a lead permanently."""
    if not db.get_lead(lead_id):
        click.secho(f"No lead with id {lead_id}", fg="red")
        sys.exit(1)
    db.delete_lead(lead_id)
    click.secho(f"Deleted lead #{lead_id}", fg="yellow")


@cli.command()
@click.argument("lead_id", type=int)
@click.argument("note")
def note(lead_id, note):
    """Attach a timestamped note to a lead (e.g. a call summary)."""
    if not db.get_lead(lead_id):
        click.secho(f"No lead with id {lead_id}", fg="red")
        sys.exit(1)
    db.add_note(lead_id, note)
    click.secho(f"Note added to lead #{lead_id}", fg="green")


@cli.command()
@click.option("--days", "-d", default=0, help="Include follow-ups due within N days from today")
def followups(days):
    """List leads with a follow-up due today or earlier (+N days ahead)."""
    target = date.today()
    if days:
        from datetime import timedelta

        target = target + timedelta(days=days)
    rows = db.get_followups_due(target.isoformat())
    if not rows:
        click.echo("No follow-ups due.")
        return
    click.secho(f"Follow-ups due by {target.isoformat()}:", fg="yellow")
    for lead in rows:
        click.echo(
            f"#{lead['id']:<4} {lead['name']:<25} {lead['company'] or '':<20} "
            f"due {lead['followup_date']} [{lead['stage']}]"
        )


@cli.command()
@click.argument("filepath", type=click.Path())
def export(filepath):
    """Export all leads to a CSV file."""
    leads = db.list_leads()
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["id", "name", "company", "email", "phone", "stage", "followup_date", "created_at", "updated_at"]
        )
        for lead in leads:
            writer.writerow(
                [
                    lead["id"], lead["name"], lead["company"], lead["email"], lead["phone"],
                    lead["stage"], lead["followup_date"], lead["created_at"], lead["updated_at"],
                ]
            )
    click.secho(f"Exported {len(leads)} leads to {filepath}", fg="green")


@cli.command()
def stats():
    """Show a quick pipeline summary."""
    s = db.stats()
    click.echo(f"Total leads: {s['total']}")
    for stage in db.STAGES:
        count = s["by_stage"].get(stage, 0)
        color = STAGE_COLORS.get(stage, "white")
        bar = "█" * count
        click.echo(click.style(f"  {stage:<10}", fg=color) + f"{count:<5} {bar}")


if __name__ == "__main__":
    cli()
