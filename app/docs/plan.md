# ETL Redesign Plan

## Domain
Sustainable tourism plays a key role in how cities prepare for global events. We will analyze a curated list of host cities, the sustainability challenge they face, and a paragraph describing their local initiative.

## Pipeline Overview
1. **Extract**: Load structured rows from `data/raw_city_innovations.csv` (CSV in the repo). Each row contains the city, focus area, and a free-text description of the initiative (there is a template to when the api key is missing).
2. **Transform**: Summarize each initiative into a crisp headline and insight using HuggingFace's inference API (default model: `facebook/bart-large-cnn`). When the `HUGGINGFACE_API_TOKEN` env var is absent, fall back to a lightweight heuristic summarizer so the pipeline still runs offline.
3. **Load**: Persist enriched insights into `data/enriched_city_innovations.json` (JSON). The backend serves this file and the frontend consumes it dynamically.

## Backend
- Built with FastAPI and HTTPX.
- Endpoints:
  - `GET /insights`: returns the latest enriched dataset (runs a lazy ETL execution if the JSON file is missing).
  - `POST /etl/run`: triggers the ETL pipeline on-demand and returns metadata (rows processed, duration, errors).
- Serves static frontend assets from `frontend/` under the `GET /` route.

## Frontend
- Plain HTML/CSS/JS animated dashboard.
- Fetches `/insights` and renders flipping cards with CSS keyframe animations + gradient theme inspired by Santander Dev Week.
- Includes CTA button that triggers `/etl/run` to refresh the dataset without leaving the page.

## Tooling
- Python 3.11+, FastAPI, Uvicorn, HTTPX.
- Optional: `python-dotenv` for local `.env` file to store the HuggingFace token.
- No databases; everything stays in versioned JSON/CSV for reproducibility.
