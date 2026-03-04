# Regime Builder Checklist

Use this file as the implementation checklist after the MVP scaffold is in place.

## Product Tasks

- Write a sharper one-sentence value proposition for the demo landing page.
- Decide who the primary demo user is: trader, allocator, or retail investor.
- Finalize the regime names you want to present publicly. `HighVol` is technically clear, but not polished language.
- Prepare one strong example narrative for each regime so the demo feels concrete.

## Data And Model Tasks

- Replace the static CSV refresh process with a repeatable ingestion script.
- Confirm the exact symbol mapping for VIX and FX data sources.
- Add a basic evaluation summary you can show during judging: sample size, date range, class balance, and holdout performance.
- Review the labeling logic in [training/train.py](/mnt/c/Users/shahk/visual studio projects/regime/training/train.py) and decide whether the thresholds are acceptable for the hackathon demo.
- Save one or two sample prediction payloads for testing and demo backup.

## API Tasks

- Add CORS configuration once you connect a frontend.
- Add a `/regime/history` endpoint if you want a chart-ready response for the UI.
- Add structured logging before deployment.
- Add a startup check that fails cleanly if model artifacts are stale or missing.

## Frontend Tasks

- Build a small dashboard that shows current regime, confidence, and probability breakdown.
- Add a short explanation panel for what each regime means in plain English.
- Add a simple historical trend or last-n-days card so the product feels alive.

## Demo And Submission Tasks

- Record a clean demo path: open app, show current regime, explain why it matters, show API response.
- Prepare the DigitalOcean architecture slide or screenshot.
- Add deployment instructions for whichever DigitalOcean product you choose.
- Write the final Devpost submission copy from [product-overview.md](/mnt/c/Users/shahk/visual studio projects/regime/docs/product-overview.md).

## Cleanup Tasks

- Add tests for feature generation and inference response shape.
- Add a `.gitignore` if you do not want local artifacts committed.
- Remove stale generated files such as `__pycache__` before submission.
