---
title: "Release 2409 Approval Workflow Change"
document_type: "release_note"
version: "2409"
date: "2024-09-10"
region: "global"
product_area: "quote_to_cash"
team: "product_ops"
source_authority: "high"
---

# Release 2409 Approval Workflow Change

## Overview
Release 2409 changed approval workflow behavior for selected quote categories and introduced tighter controls around manual override.

## What changed
Manual override availability was restricted for strategic renewals and for cases entering protected regional routing paths.
Germany and EU accounts affected by the new routing logic may no longer display or permit override in scenarios that were previously eligible.
The workflow now treats protected renewal cases as non-overridable by support.

## Affected cases
The highest impact is expected for:
- strategic renewals,
- Germany and EU accounts with protected routing,
- deals above €100,000 annual contract value,
- cases previously handled through local support override.

## Support impact
Older support KB articles may no longer fully apply.
Support should verify deal classification, region, and release context before recommending override.
For affected cases, support should follow current policy and route the case to Revenue Operations when required.

## Recommended action
Consult updated policy guidance and incident summaries for Germany-specific approval failures after 2409.
