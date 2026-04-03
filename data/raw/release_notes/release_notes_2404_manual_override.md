---
title: "Release 2404 Manual Override Behavior"
document_type: "release_note"
version: "2404"
date: "2024-04-22"
region: "global"
product_area: "quote_to_cash"
team: "support_ops"
source_authority: "high"
---

# Release 2404 Manual Override Behavior

## Overview
Release 2404 standardized visibility of the manual override control in support tooling.

## What changed
The override button is displayed only when the case appears eligible based on deal type and active restrictions.
Some users may see the button disappear when a case is classified as renewal-related.

## Support impact
Support should not assume that a missing button is a UI defect.
If the control is not shown, the case may be ineligible for override based on policy or deal metadata.

## Notes
This change was a UI and eligibility refinement, not a regional restriction.
