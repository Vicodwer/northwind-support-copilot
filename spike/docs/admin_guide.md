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