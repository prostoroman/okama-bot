"""
Analysis Engine

Uses the LLM service to interpret computed results and provide human-readable
insights and recommendations.
"""

from __future__ import annotations

from typing import Dict
from yandexgpt_service import YandexGPTService


class AnalysisEngine:
    def __init__(self):
        self.llm = YandexGPTService()

    def summarize(self, analysis_type: str, results: Dict, user_query: str) -> str:
        return self.llm.enhance_analysis_results(analysis_type, results, user_query)

