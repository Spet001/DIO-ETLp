from __future__ import annotations

import asyncio
import csv
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import httpx

from .config import ENRICHED_DATA_PATH, RAW_DATA_PATH, get_settings


@dataclass
class Insight:
    city: str
    focus_area: str
    headline: str
    insight: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "city": self.city,
            "focus_area": self.focus_area,
            "headline": self.headline,
            "insight": self.insight,
        }


class HuggingFaceSummarizer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.api_url = (
            f"https://api-inference.huggingface.co/models/{self.settings.huggingface_model}"
        )

    async def summarize(self, *, city: str, focus_area: str, text: str) -> Insight:
        payload = {
            "inputs": text,
            "parameters": {
                "max_length": self.settings.max_summary_tokens,
                "min_length": self.settings.min_summary_tokens,
                "do_sample": False,
            },
        }

        if not self.settings.huggingface_api_token:
            return self._fallback(city=city, focus_area=focus_area, text=text)

        headers = {
            "Authorization": f"Bearer {self.settings.huggingface_api_token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.settings.api_timeout) as client:
                response = await client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                data: List[Dict[str, Any]] = response.json()
        except (httpx.HTTPError, ValueError):
            return self._fallback(city=city, focus_area=focus_area, text=text)

        summary_text = data[0].get("summary_text") if data else None
        if not summary_text:
            return self._fallback(city=city, focus_area=focus_area, text=text)

        return Insight(
            city=city,
            focus_area=focus_area,
            headline=f"{city}: {focus_area} em ação",
            insight=summary_text.strip(),
        )

    def _fallback(self, *, city: str, focus_area: str, text: str) -> Insight:
        sentences = [sentence.strip() for sentence in text.split(".") if sentence.strip()]
        headline = f"{city} acelera {focus_area.lower()}"
        if sentences:
            insight = sentences[0]
            if len(sentences) > 1:
                insight += f". {sentences[1]}"
        else:
            insight = "Iniciativa descrita, mas sem detalhes suficientes para resumo."
        return Insight(city=city, focus_area=focus_area, headline=headline, insight=insight)


class ETLPipeline:
    def __init__(self, raw_path: Path = RAW_DATA_PATH, output_path: Path = ENRICHED_DATA_PATH) -> None:
        self.raw_path = raw_path
        self.output_path = output_path
        self.summarizer = HuggingFaceSummarizer()

    def extract(self) -> List[Dict[str, str]]:
        with self.raw_path.open("r", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            return [row for row in reader]

    async def transform(self, rows: List[Dict[str, str]]) -> List[Insight]:
        insights: List[Insight] = []
        for row in rows:
            insight = await self.summarizer.summarize(
                city=row["city"], focus_area=row["focus_area"], text=row["initiative_description"]
            )
            insights.append(insight)
        return insights

    def load(self, insights: List[Insight]) -> None:
        payload = [insight.to_dict() for insight in insights]
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with self.output_path.open("w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)

    async def run(self) -> Dict[str, Any]:
        started_at = time.perf_counter()
        rows = self.extract()
        insights = await self.transform(rows)
        self.load(insights)
        return {
            "rows_processed": len(rows),
            "output_file": str(self.output_path),
            "duration_seconds": round(time.perf_counter() - started_at, 3),
        }

    def load_cached_output(self) -> List[Dict[str, Any]]:
        if not self.output_path.exists():
            return []
        with self.output_path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    async def ensure_output(self) -> None:
        if not self.output_path.exists():
            await self.run()


def run_pipeline() -> None:
    asyncio.run(ETLPipeline().run())


if __name__ == "__main__":
    run_pipeline()
