---
title: "Release 2405 Regional Approval Routing"
document_type: "release_note"
version: "2405"
date: "2024-05-17"
region: "eu"
product_area: "quote_to_cash"
team: "product_ops"
source_authority: "high"
---

# Release 2405 Regional Approval Routing

## Overview
Release 2405 introduced cleaner routing for region-specific approval queues.

## What changed
Germany and EU accounts now enter dedicated queue branches before final approval evaluation.
This was intended to improve local ownership and reduce routing ambiguity.

## Support impact
Support should verify whether the case entered the correct regional queue before escalating.
Legacy support guidance may not describe the new queue names.

## Notes
Manual override eligibility remained unchanged in this release.
