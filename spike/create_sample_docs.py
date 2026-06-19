#!/usr/bin/env python3
"""
spike/create_sample_docs.py
===========================
Generates 10 realistic Northwind B2B SaaS support documents in spike/docs/.

Run this ONLY if you don't have your own real documents.
Real, domain-specific documents will always give better spike results.

Usage:
    python spike/create_sample_docs.py
"""

from pathlib import Path

DOCS_DIR = Path("spike/docs")
DOCS_DIR.mkdir(parents=True, exist_ok=True)

DOCUMENTS = {

"refund_policy.md": """
# Northwind Refund Policy

Last updated: January 2025

## Overview
Northwind offers refunds under the conditions described in this document.
All refund requests must be submitted through the support portal or by
contacting your account manager directly.

## Annual Subscriptions
Customers on annual plans are eligible for a full refund within 30 days
of the subscription start date. After 30 days, annual subscriptions are
non-refundable. Customers who cancel after the 30-day window will retain
access to the platform until the end of their billing cycle.

## Monthly Subscriptions
Monthly subscriptions may be cancelled at any time. The cancellation takes
effect at the end of the current billing month. No partial refunds are
issued for unused days within a monthly billing cycle.

## Refund Processing Time
Approved refunds are processed within 5–10 business days. The time for
the credit to appear on your statement depends on your card issuer, but
typically takes an additional 3–5 business days after processing. Total
wait time from approval to credit: 8–15 business days.

## How to Request a Refund
1. Log in to the Northwind support portal at support.northwind.io
2. Navigate to Billing > Refund Request
3. Select the invoice and reason for the refund
4. Submit the request
Your account manager will review the request within 2 business days.

## Non-Refundable Items
- Professional services and implementation fees
- Add-on modules purchased separately
- Overage charges for API usage above the plan limit
- Training and onboarding sessions already delivered

## Disputes
If a refund is denied and you believe the decision is incorrect, escalate
by emailing billing-disputes@northwind.io with your account ID and the
original refund request number.
""",

"pricing_and_plans.md": """
# Northwind Pricing and Plans

Last updated: January 2025

## Plan Overview

### Starter Plan — $99/month
- Up to 5 users
- Core product features
- Email support (48-hour SLA)
- 10 GB data storage
- Standard API access (1,000 calls/day)
- No integrations

### Pro Plan — $299/month
- Up to 25 users
- All Starter features
- Priority email support (24-hour SLA)
- 100 GB data storage
- Extended API access (10,000 calls/day)
- Integrations: Salesforce, HubSpot, Slack, Zapier, Google Workspace
- Custom reporting dashboards

### Enterprise Plan — Custom pricing
- Unlimited users
- All Pro features
- Dedicated support engineer (4-hour SLA for critical issues)
- Unlimited storage
- Unlimited API calls
- Custom integrations via REST API
- SSO / SAML authentication
- Data residency options (US, EU, APAC)
- SLA-backed uptime guarantee (99.9%)
- Quarterly business reviews

## Annual vs Monthly Billing
All plans are available on monthly or annual billing.
Annual billing provides a 20% discount versus the monthly rate.
Annual plans require upfront payment for the full year.

## Upgrading and Downgrading
- Upgrades take effect immediately; the price difference is prorated.
- Downgrades take effect at the next renewal date.
- Switching from annual to monthly billing is only possible at renewal.
""",

"billing_faq.md": """
# Billing FAQ

Last updated: January 2025

## Can I switch from annual to monthly billing mid-cycle?
No. Switching from annual to monthly billing is only possible at the time
of renewal. If you are on an annual plan and wish to switch to monthly,
your account manager will apply the change at the end of your current
annual term. Contact support at billing@northwind.io at least 30 days
before your renewal date to initiate this change.

## Can I switch from monthly to annual billing at any time?
Yes. You can upgrade from monthly to annual billing at any time. The
remaining days on your current monthly cycle will be prorated and credited
toward the annual subscription cost.

## What payment methods are accepted?
Northwind accepts Visa, Mastercard, American Express, and ACH bank
transfers (US only). Enterprise customers may arrange invoice-based payment
with Net-30 terms upon credit approval.

## What happens if my payment fails?
If a payment fails, Northwind will retry the charge after 3 days, then
again after 7 days. If payment is not received within 14 days, your account
will be suspended (read-only access). Your data is retained for 60 days
following suspension before permanent deletion.

## How do I update my billing information?
Log in to your account, navigate to Settings > Billing > Payment Methods,
and update your card details. Changes take effect at the next billing cycle.

## Can I get a copy of my invoice?
All invoices are available in the Billing section of your account dashboard.
You can download PDF copies for any billing period. For accounts that need
invoices sent to a specific email address, configure this under
Settings > Billing > Invoice Recipients.

## Do you offer non-profit or educational discounts?
Yes. Northwind offers a 30% discount for registered non-profits and
accredited educational institutions. Contact sales@northwind.io with
proof of eligibility.
""",

"admin_guide.md": """
# Administrator Guide

Last updated: January 2025

## Overview
This guide covers common administrative tasks in the Northwind platform.
Admin access is required for all tasks described here. Admins are assigned
by the account owner during onboarding.

## Resetting a User Password
To reset a user's password:
1. Log in to the admin panel at app.northwind.io/admin
2. Navigate to Users > All Users
3. Search for the user by name or email address
4. Click the three-dot menu next to the user's name
5. Select "Reset Password"
6. Choose whether to send a reset link via email or set a temporary password manually
7. Click Confirm

The user will receive a password reset email valid for 24 hours.
If the user does not receive the email, check that their email address is
correct and ask them to check their spam folder.

## Deactivating a User
To deactivate a user without deleting their data:
1. Navigate to Users > All Users
2. Find the user and open their profile
3. Click "Deactivate Account"
4. Confirm the action

Deactivated users cannot log in but their data remains accessible to admins.

## Granting and Revoking Admin Permissions
1. Navigate to Users > All Users
2. Open the user profile
3. Under the "Role" dropdown, select Admin, Member, or Viewer
4. Save changes

Only the account owner can grant or revoke admin permissions for other admins.

## Viewing Audit Logs
Audit logs track all admin actions. To view:
1. Navigate to Settings > Audit Log
2. Filter by date range, user, or action type
3. Export as CSV if needed

Audit logs are retained for 12 months (Enterprise) or 90 days (Pro/Starter).
""",

"user_management.md": """
# User Management Guide

Last updated: January 2025

## Adding a New Team Member to an Existing Workspace

### Step-by-step instructions
1. Log in to your Northwind account
2. Navigate to Settings > Team Members
3. Click the "Invite Member" button in the top-right corner
4. Enter the new member's email address
5. Select their role: Admin, Member, or Viewer
6. (Optional) Assign them to specific Projects or Workspaces
7. Click "Send Invitation"

The invited user will receive an email with a link to create their account.
The invitation link expires after 7 days. If it expires, you can resend it
from Settings > Team Members > Pending Invitations.

### User Roles
- **Admin**: Full access including billing and user management
- **Member**: Can create, edit, and delete content within assigned workspaces
- **Viewer**: Read-only access; cannot create or modify content

### Seat Limits by Plan
- Starter: Up to 5 users
- Pro: Up to 25 users
- Enterprise: Unlimited users

If you are at your seat limit, you will need to upgrade your plan or
deactivate an existing user before sending a new invitation.

## Removing a Team Member
1. Navigate to Settings > Team Members
2. Find the member and click their name
3. Click "Remove from workspace"
4. Confirm the action

Removed members lose access immediately. Any content they created remains
and is reassigned to the workspace admin.
""",

"data_retention_policy.md": """
# Data Retention and Deletion Policy

Last updated: January 2025

## What Happens to Customer Data When an Account is Cancelled

When a customer cancels their Northwind subscription, the following applies:

### During the Grace Period (0–30 days after cancellation)
- The account enters read-only mode immediately
- All data remains accessible to admins for export
- No new data can be written to the account
- Integrations are paused

### After the Grace Period (30–90 days)
- The account is archived
- Data is retained but not accessible through the application
- Data can still be restored if the customer resubscribes within 90 days
- A written request to dataprotection@northwind.io can retrieve a full export

### After 90 Days
- All customer data is permanently deleted from Northwind servers
- Deletion is irreversible
- Northwind retains anonymised, aggregated usage statistics only (no PII)

## Backup Copies
Northwind maintains encrypted backups for disaster recovery purposes.
Backup copies of deleted accounts are purged within 30 days of account deletion.

## GDPR and Data Subject Requests
Customers may submit a Right to Erasure (GDPR Article 17) request at any time
by emailing privacy@northwind.io. Erasure requests are fulfilled within
30 days of verification.

## Data Export Before Cancellation
We strongly recommend exporting all data before cancelling. See the
Data Export Guide for full instructions.
""",

"support_sla.md": """
# Support SLA and Response Times

Last updated: January 2025

## Support Tiers and SLA Targets

### Priority Levels
Northwind classifies support tickets into four priority levels:

| Priority | Description | First Response | Resolution Target |
|----------|-------------|----------------|-------------------|
| Critical | System completely unavailable; data loss risk | 1 hour | 4 hours |
| High     | Major feature broken; significant business impact | 4 hours | 24 hours |
| Medium   | Feature degraded; workaround available | 8 hours | 72 hours |
| Low      | General questions; minor cosmetic issues | 24 hours | 10 business days |

Response times are measured during business hours: Monday–Friday, 09:00–18:00
in the customer's primary timezone.

Enterprise plan customers have 24/7 support for Critical and High priority issues.

## How to Set Ticket Priority
When submitting a ticket via support.northwind.io, you can select the priority
level. Northwind reserves the right to reclassify priority based on actual impact.

## SLA Credits
If Northwind fails to meet the First Response SLA for a Critical issue,
Enterprise customers are eligible for a service credit of 5% of their
monthly subscription fee per incident, up to a maximum of 30% per month.
SLA credits must be requested within 30 days of the incident.

## Escalation Path
If you are not satisfied with the progress on an open ticket:
1. Reply to the ticket and request escalation
2. Contact your dedicated account manager (Enterprise) or
   email escalations@northwind.io (Pro/Starter)
3. Request a call with the engineering team for Critical issues
""",

"data_export_guide.md": """
# Data Export Guide

Last updated: January 2025

## How to Export Your Data from Northwind

Northwind allows customers to export all their data at any time.
We support exports in CSV, JSON, and XML formats depending on the data type.

## Full Account Export

### Step-by-step
1. Log in to your account as an Admin
2. Navigate to Settings > Data Management > Export
3. Click "Request Full Export"
4. Select the data types to include:
   - Users and roles
   - Projects and content
   - Activity and audit logs
   - Custom fields and configurations
5. Choose the file format (CSV or JSON recommended)
6. Click "Start Export"

You will receive an email when the export is ready (typically within 1–4 hours
for accounts under 10 GB; up to 24 hours for larger accounts).
The download link is valid for 7 days.

## Exporting Specific Data Types

### Exporting Users
Settings > Team Members > Export CSV

### Exporting Project Data
Open the project > Settings > Export Project

### Exporting Audit Logs
Settings > Audit Log > Export CSV

## Before Cancelling
If you are planning to cancel your account, we recommend completing a
Full Account Export at least 5 business days before your cancellation date
to allow enough time for large exports to complete.

After account cancellation, data is accessible in read-only mode for 30 days,
during which you can still run a data export. After 30 days, the account is
archived and export requires contacting dataprotection@northwind.io.
""",

"system_requirements.md": """
# System Requirements

Last updated: January 2025

## Web Application
The Northwind web application runs in all modern browsers. Supported browsers:
- Google Chrome 110 or later (recommended)
- Mozilla Firefox 110 or later
- Microsoft Edge 110 or later
- Apple Safari 16 or later

Internet Explorer is not supported.
Minimum recommended internet speed: 5 Mbps download.

## Desktop Application (Windows)
- Operating System: Windows 10 (64-bit) or later
- RAM: 4 GB minimum, 8 GB recommended
- Disk space: 500 MB free for installation
- Display: 1280 × 768 minimum resolution
- Internet connection required

## Desktop Application (macOS)
- Operating System: macOS 12 Monterey or later
- RAM: 4 GB minimum, 8 GB recommended
- Disk space: 500 MB free
- Display: 1280 × 768 minimum resolution
- Apple Silicon (M1/M2) and Intel processors both supported

## Mobile Application
- iOS: Version 15 or later (iPhone and iPad)
- Android: Version 10 or later

## API Access
- HTTPS connections only (TLS 1.2 or later)
- IP allowlisting available for Enterprise customers
- API rate limits: see your plan documentation

## Firewall and Network Requirements
Northwind requires access to the following domains:
- app.northwind.io (main application)
- api.northwind.io (API endpoints)
- cdn.northwind.io (static assets)
- auth.northwind.io (authentication)
Allow outbound HTTPS (port 443) to these domains.
""",

"api_documentation.md": """
# Northwind API Documentation — Overview

Last updated: January 2025

## Authentication
The Northwind REST API uses API keys for authentication.
All requests must include your API key in the Authorization header:

    Authorization: Bearer YOUR_API_KEY

API keys are generated in Settings > Integrations > API Keys.
Keep your API key secret. Do not expose it in client-side code.

## Base URL
    https://api.northwind.io/v2

All endpoints are available over HTTPS only.

## Rate Limits

| Plan       | Requests per Day | Requests per Minute |
|------------|-----------------|---------------------|
| Starter    | 1,000           | 10                  |
| Pro        | 10,000          | 60                  |
| Enterprise | Unlimited       | 600                 |

When you exceed the rate limit, the API returns HTTP 429 Too Many Requests.
The response includes a Retry-After header indicating when to retry.

## Common Endpoints

### List Users
GET /v2/users

### Get User
GET /v2/users/{user_id}

### Create Project
POST /v2/projects
Body: { "name": "string", "description": "string" }

### Get Audit Log
GET /v2/audit-log?from=2025-01-01&to=2025-01-31

## Error Codes
- 400 Bad Request — malformed request body
- 401 Unauthorized — invalid or missing API key
- 403 Forbidden — insufficient permissions
- 404 Not Found — resource does not exist
- 429 Too Many Requests — rate limit exceeded
- 500 Internal Server Error — contact support

## Webhooks
Northwind supports webhooks for real-time event notifications.
Configure webhook endpoints under Settings > Integrations > Webhooks.
Events supported: user.created, project.created, subscription.renewed,
subscription.cancelled, payment.failed.
""",

}


def main() -> None:
    created = 0
    for filename, content in DOCUMENTS.items():
        path = DOCS_DIR / filename
        path.write_text(content.strip(), encoding="utf-8")
        print(f"  ✅  Created {path}")
        created += 1

    print(f"\n📄  {created} sample documents written to {DOCS_DIR}/")
    print("    These are realistic but synthetic.")
    print("    Replace with your own real documents for better spike results.\n")
    print("    Next step:  python spike/spike.py")


if __name__ == "__main__":
    main()