import csv
import requests
import statistics
import base64
import re
from collections import defaultdict
from datetime import datetime

# CONFIG

API_KEY = "{api key here}"
BASE_URL = "https://api.close.com/api/v1/"

auth_string = f"{API_KEY}:"
encoded = base64.b64encode(auth_string.encode()).decode()

HEADERS = {
    "Authorization": f"Basic {encoded}",
    "Content-Type": "application/json"
}

# HELPERS

def parse_date(date_str):
    try:
        dt = datetime.strptime(date_str.strip(), "%d.%m.%Y")
        return dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    except:
        return None


def parse_revenue(revenue_str):
    try:
        cleaned = revenue_str.replace("$", "").replace(",", "").strip()
        return float(cleaned)
    except:
        return None


def parse_multiline_field(value):
    if not value:
        return []
    return [line.strip() for line in value.splitlines() if line.strip()]


# CUSTOM FIELDS

def get_custom_field_ids():
    resp = requests.get(
        BASE_URL + "custom_field/lead/",
        headers=HEADERS
    )

    fields = resp.json()["data"]
    return {field["name"]: field["id"] for field in fields}



# A: IMPORT LEADS/CONTACTS

def import_leads_from_csv(csv_file):

    custom_ids = get_custom_field_ids()

    # Group contacts by company name
    companies = defaultdict(list)

    with open(csv_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            company_name = row["Company"].strip()
            contact_name = row["Contact Name"].strip()

            emails = parse_multiline_field(row["Contact Emails"])
            phones = parse_multiline_field(row["Contact Phones"])

            founded_raw = row["custom.Company Founded"]
            founded_date = parse_date(founded_raw)

            revenue_raw = row["custom.Company Revenue"]
            state = row["Company US State"].strip()

            # Discard invalid rows
            if not company_name:
                continue

            if founded_date is None:
                continue

            if not emails and not phones:
                continue

            companies[company_name].append({
                "contact_name": contact_name,
                "emails": emails,
                "phones": phones,
                "founded": founded_date,
                "revenue": revenue_raw,
                "state": state,
            })

    print(f"Valid companies found: {len(companies)}")

    for company_name, contacts in companies.items():

        first = contacts[0]
        custom_ids = get_custom_field_ids()
        lead_payload = {
            "name": company_name,
            "custom": {
                custom_ids["Company Founded"]: first["founded"],
                custom_ids["Company Revenue"]: first["revenue"],
                custom_ids["Company US State"]: first["state"],
            },
            "contacts": [],
        }

        # Add all contacts under this lead
        for c in contacts:
            if not c["emails"] and not c["phones"]:
                continue
            lead_payload["contacts"].append({
                "name": c["contact_name"],
                "emails": [{"email": e} for e in c["emails"]],
                "phones": [{"phone": p} for p in c["phones"]],
            })

        # Create lead via API
        resp = requests.post(
            BASE_URL + "lead/",
            headers=HEADERS,
            json=lead_payload
        )

        if resp.status_code == 200:
            print(f"Created lead: {company_name}")
        else:
            print(f"Failed lead {company_name}: {resp.text}")



# B: FIND DATE RANGE

def find_leads_in_date_range():
    start_input = input("Enter start date (DD.MM.YYYY): ")
    end_input = input("Enter end date (DD.MM.YYYY): ")

    start_date = parse_date(start_input)
    end_date = parse_date(end_input)

    if not start_date or not end_date:
        print("Invalid date format.")
        return []

    founded_field = 'Company Founded'

    resp = requests.get(BASE_URL + "lead/", headers=HEADERS, params={"_limit": 100})
    leads = resp.json().get("data", [])

    results = []

    for lead in leads:
        custom = lead.get("custom", {})
        founded_date = custom.get(founded_field)
        if start_date <= founded_date <= end_date:
            results.append(lead)

    print(f"Leads found in range: {len(results)}")
    return results



# C: SEGMENT BY STATE

def segment_leads_by_state(leads):
    state_map = defaultdict(list)

    for lead in leads:
        custom = lead.get("custom", {})

        state = custom.get('Company US State')
        revenue = custom.get('Company Revenue')

        if not state or revenue is None:
            continue

        state_map[state].append({
            "name": lead["name"],
            "revenue": revenue,
        })

    with open("state_report.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "State",
            "Total Leads",
            "Top Revenue Lead",
            "Total Revenue",
            "Median Revenue",
        ])

        for state, entries in state_map.items():

            # Sort leads by revenue descending
            entries.sort(key=lambda x: x["revenue"], reverse=True)

            revenues = [e["revenue"] for e in entries]

            total_leads = len(entries)
            top_lead = entries[0]["name"]
            total_revenue = sum(revenues)
            median_revenue = statistics.median(revenues)

            writer.writerow([
                state,
                total_leads,
                top_lead,
                total_revenue,
                median_revenue,
            ])

    print("State report saved as state_report.csv")


if __name__ == "__main__":

    # A
    import_leads_from_csv("companies.csv")

    # B
    leads_in_range = find_leads_in_date_range()

    # C
    segment_leads_by_state(leads_in_range)