"""
backend/services/offer_service.py
Generates personalised loan offer(s) based on risk, policy, and LLM signals.
"""
import math
from loguru import logger


# ─── Base rate table by risk band ────────────────────────────────
RATE_TABLE = {
    "low": 10.5,
    "medium": 13.5,
    "high": 17.0,
    "very_high": None,  # not offered
}

TENURE_OPTIONS = [12, 24, 36, 48, 60]  # months
PROCESSING_FEE_PCT = 0.02  # 2 %


def _emi(principal: float, annual_rate: float, months: int) -> float:
    """Standard EMI formula: P × r × (1+r)^n / ((1+r)^n – 1)"""
    if annual_rate == 0:
        return principal / months
    r = annual_rate / 100 / 12
    emi = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    return round(emi, 2)


class OfferService:
    def generate_offers(
        self,
        application_data: dict,
        risk_result: dict,
        llm_classification: dict,
    ) -> list[dict]:
        """
        Returns a list of offer dicts (one per tenure option).
        Empty list if ineligible.
        """
        if not risk_result.get("is_eligible"):
            return []

        income = application_data.get("monthly_income") or 0
        requested = application_data.get("requested_amount") or 0
        risk_band = llm_classification.get("risk_band", "medium")

        annual_rate = RATE_TABLE.get(risk_band)
        if annual_rate is None:
            logger.warning(f"Risk band {risk_band} not offerable")
            return []

        # Eligible amount = min(requested, 10× monthly income, 5 lakhs)
        max_by_income = income * 10
        eligible_amount = min(requested or max_by_income, max_by_income, 500_000)
        eligible_amount = round(eligible_amount / 1000) * 1000  # round to nearest 1k

        offers = []
        for tenure in TENURE_OPTIONS:
            emi_val = _emi(eligible_amount, annual_rate, tenure)
            # Only offer if EMI ≤ 40% of monthly income (FOIR rule)
            if income > 0 and emi_val > income * 0.40:
                continue
            offers.append(
                {
                    "loan_amount": eligible_amount,
                    "tenure_months": tenure,
                    "annual_interest_rate": annual_rate,
                    "emi": emi_val,
                    "processing_fee": round(eligible_amount * PROCESSING_FEE_PCT, 2),
                    "offer_type": "standard" if risk_band != "high" else "conditional",
                }
            )

        return offers
