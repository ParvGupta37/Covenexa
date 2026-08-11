"""
Sprint 3 Pipeline Runner.
Executes all intelligence engines (Financial, Health Score, Covenant Monitor, Default Predictor, Recommendations, Alerts)
sequentially for a given borrower.
"""
from __future__ import annotations

import structlog
from typing import Dict, Any

from ai.engines.financial_engine import FinancialEngine
from ai.engines.health_score_engine import HealthScoreEngine
from ai.engines.covenant_monitor import CovenantMonitor
from ai.engines.default_predictor import DefaultPredictor
from ai.engines.recommendation_engine import RecommendationEngine
from ai.engines.alert_engine import AlertEngine

logger = structlog.get_logger(__name__)


class RiskIntelligencePipeline:
    """Orchestrates all risk intelligence calculations for a borrower."""

    async def run_full_pipeline(self, session, borrower_id: str) -> Dict[str, Any]:
        logger.info("risk_pipeline.start", borrower_id=borrower_id)

        # 1. Financial Engine
        fin_engine = FinancialEngine()
        fin_res = await fin_engine.compute_and_persist(session, borrower_id)

        # 2. Covenant Monitor
        cov_monitor = CovenantMonitor()
        cov_res = await cov_monitor.evaluate_borrower_covenants(session, borrower_id)

        # 3. Health Score Engine
        health_engine = HealthScoreEngine()
        health_res = await health_engine.calculate_and_persist(session, borrower_id)

        # 4. Default Predictor
        default_engine = DefaultPredictor()
        default_res = await default_engine.predict_and_persist(session, borrower_id)

        # 5. Recommendation Engine
        rec_engine = RecommendationEngine()
        rec_res = await rec_engine.generate_recommendations(session, borrower_id)

        # 6. Alert Engine
        alert_engine = AlertEngine()
        alert_res = await alert_engine.check_and_generate_alerts(session, borrower_id)

        logger.info("risk_pipeline.completed", borrower_id=borrower_id, health_score=health_res.score, default_prob=default_res["default_probability"])

        return {
            "borrower_id": borrower_id,
            "financial_metrics": fin_res.to_summary() if fin_res else None,
            "covenants_monitored": len(cov_res),
            "health_score": health_res.score,
            "health_category": health_res.category,
            "default_probability": default_res["default_probability"],
            "recommendations": len(rec_res),
            "alerts": len(alert_res)
        }
