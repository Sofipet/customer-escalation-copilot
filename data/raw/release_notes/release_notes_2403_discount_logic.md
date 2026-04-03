---
title: "Release 2403 Discount Logic Update"
document_type: "release_note"
version: "2403"
date: "2024-03-18"
region: "global"
product_area: "quote_to_cash"
team: "pricing_ops"
source_authority: "high"
---

# Release 2403 Discount Logic Update

## Overview
Release 2403 improved validation of discount-based approval routing.

## What changed
The pricing service now flags discount values above threshold earlier in the workflow.
This reduced downstream failures but increased visible validation errors for some support users.

## Support impact
Support should verify the actual discount percent before assuming that routing failed incorrectly.
Older tickets that describe silent failures may not match the new behavior.

## Notes
No manual override restriction was introduced in this release.
