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