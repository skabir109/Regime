# Regime Feature Inventory

This document tracks the current product surface of Regime as implemented in the repository.

## Core Product

- Secure login and registration with hashed credentials and session cookies
- User-scoped workspace, watchlist storage, delivery preferences, and briefing history
- FastAPI backend serving a terminal-style web application
- Dark terminal-inspired interface with multiple workspaces and live clock

## Monitor Workspace

- Current regime classification with confidence ladder
- Plain-English regime interpretation and glossary
- Market state pack:
  breadth, volatility state, trend strength, and cross-asset confirmation
- Supporting signals, conflicting signals, and change-since-yesterday summaries
- Regime transition history
- Leaders and laggards panel
- Sector breadth panel
- Trader alerts panel
- Catalyst tape from current market headlines

## Markets Workspace

- Cross-asset market panels
- Mini trend charts
- Selected-market detail view
- Coverage for SPY, GLD, USO, GBP/USD, and VIX when data is available

## Signals Workspace

- Trending bullish, bearish, and neutral stock signals
- Per-signal detail panel with score, price action, and drivers
- True user watchlist with add/remove actions
- Watchlist intelligence for saved symbols:
  stance, score, price, 1D/20D moves, reasons, and leading catalyst
- Watchlist news panel with matched symbols
- Catalyst calendar panel
- Watchlist detail panel:
  signal summary, related headlines, and symbol-specific calendar items

## Briefing Workspace

- Personalized pre-market briefing
- Checklist and risk summary
- Watchlist focus list
- Session catalysts panel
- Briefing history

## News Workspace

- Live market news stream from RSS sources when available
- Search and source filtering
- Watchlist-only filter lane
- Report detail panel with source links
- Headline tagging:
  Macro, Rates, Earnings, Geopolitics, Energy, Volatility, and AI

## System Workspace

- Model metadata
- Threshold display
- Training coverage, split sizes, class balance, weights, and metrics
- Feature-importance panel
- Subscription summary and tier comparison
- Demo plan control for upgrading or downgrading account entitlements
- Service map / endpoint inventory
- Delivery preferences editor

## Intelligence and Modeling

- Regime model trained on cross-asset feature set
- Expanded feature coverage using multi-horizon momentum, drawdowns, volatility, and cross-asset spreads
- Model metadata persisted with feature importance and training metrics
- Session-level catalyst synthesis from regime state, watchlist headlines, and risk conditions

## Calendar and Event Layer

- Session catalyst calendar driven by:
  regime conflicts, volatility state, watchlist headlines, and intraday checkpoints
- Optional verified calendar integration foundation
- Support for Alpha Vantage free-tier earnings calendar integration via `ALPHA_VANTAGE_API_KEY`
- Provider selection via `REGIME_CALENDAR_PROVIDER`
- Offline fallback to internal catalyst calendar when external APIs are unavailable

## Personalization and Workflow

- User-specific watchlists
- User-specific alerts
- User-specific briefing history
- User-specific delivery preferences
- Tier-based product entitlements
- Command palette for workspace navigation and actions

## Shared Workspace

- Desk-tier shared workspace creation
- Invite-code-based workspace joining
- Shared desk watchlist
- Shared desk notes
- Shared desk alerts generated from the workspace watchlist
- Saved desk briefing snapshots for team coordination
- Shared workspace membership and role display
- Shared collaboration controls surfaced in the System workspace

## Subscription Tiers

- `Free`
  watchlist limit 5, fallback catalyst calendar, email preferences, limited briefing history
- `Pro`
  watchlist limit 25, verified calendar access when Alpha Vantage is configured, webhook delivery, longer history
- `Desk`
  watchlist limit 100, same premium intelligence features with larger capacity for heavier usage

## Billing Foundation

- Persisted user tier on account record
- `GET /billing/tiers` to enumerate product tiers
- `PUT /billing/tier` for demo plan switching
- Watchlist limit enforcement by tier
- Webhook delivery gating by tier
- Verified calendar gating by tier
- Briefing history retention capped by tier
- Desk-tier gating for shared workspace collaboration

## Operational Notes

- Verified calendar APIs require environment configuration:
  `ALPHA_VANTAGE_API_KEY`
- Calendar integration is designed to degrade gracefully in offline or demo environments
- The app can still function without external market-news or calendar access
