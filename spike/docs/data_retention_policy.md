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