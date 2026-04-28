"""
backend/services/risk_service.py
Risk & Policy evaluation engine.
Combines rule-based policy checks with ML risk scoring.
"""
import json
from pathlib import Path
from loguru import logger


# ─── Load policy config ──────────────────────────────────────────
POLICY_PATH = Path(__file__).parent.parent.parent / "config" / "policy.json"


def _load_policy() -> dict:
    if POLICY_PATH.exists():
        with open(POLICY_PATH) as f:
            return json.load(f)
    # Defaults if file missing
    return {
        "min_age": 21,
        "max_age": 65,
        "min_income": 15000,
        "max_loan_income_multiple": 10,
        "min_loan_amount": 10000,
        "max_loan_amount": 5000000,
        "allowed_employment_types": ["salaried", "self_employed", "business"],
        "max_risk_score": 0.65,
    }


POLICY = _load_policy()


class RiskService:
    """
    Two-layer evaluation:
      Layer 1 – Hard policy rules (instant reject/pass)
      Layer 2 – ML risk score (probabilistic reject if score > threshold)
    """

    def evaluate(self, app_data: dict) -> dict:
        """
        app_data fields:
          declared_age, employment_type, monthly_income,
          requested_amount, verbal_consent, age_match_ok,
          estimated_age, llm_risk_band, fraud_signals (list)

        Returns:
          {
            "is_eligible": bool,
            "risk_score": float,
            "propensity_score": float,
            "rejection_reasons": list[str],
            "passed_policy": bool,
          }
        """
        reasons = []

        # ── Hard rules ──────────────────────────────────────────
        age = app_data.get("declared_age") or 0
        if age < POLICY["min_age"] or age > POLICY["max_age"]:
            reasons.append(f"age_{age}_outside_policy")

        if not app_data.get("verbal_consent"):
            reasons.append("verbal_consent_not_captured")

        emp = app_data.get("employment_type", "")
        if emp not in POLICY["allowed_employment_types"]:
            reasons.append(f"employment_type_{emp}_not_allowed")

        income = app_data.get("monthly_income") or 0
        if income < POLICY["min_income"]:
            reasons.append(f"monthly_income_{income}_below_minimum")

        req_amt = app_data.get("requested_amount") or 0
        if req_amt < POLICY["min_loan_amount"] or req_amt > POLICY["max_loan_amount"]:
            reasons.append(f"requested_amount_{req_amt}_out_of_range")

        if income > 0 and req_amt > income * POLICY["max_loan_income_multiple"]:
            reasons.append("requested_amount_exceeds_income_multiple")

        if not app_data.get("age_match_ok", True):
            reasons.append("age_mismatch_between_declared_and_estimated")

        fraud_signals = app_data.get("fraud_signals", [])
        if fraud_signals:
            reasons.extend([f"fraud_signal:{s}" for s in fraud_signals])

        passed_policy = len(reasons) == 0

        # ── ML risk score ────────────────────────────────────────
        risk_score = self._compute_risk_score(app_data)
        propensity_score = self._compute_propensity(app_data)

        if passed_policy and risk_score > POLICY["max_risk_score"]:
            reasons.append(f"ml_risk_score_{risk_score:.2f}_exceeds_threshold")
            passed_policy = False

        # LLM risk band can add soft signal
        if app_data.get("llm_risk_band") == "very_high":
            if passed_policy:
                reasons.append("llm_flagged_very_high_risk")
                passed_policy = False

        return {
            "is_eligible": passed_policy,
            "risk_score": round(risk_score, 4),
            "propensity_score": round(propensity_score, 4),
            "rejection_reasons": reasons,
            "passed_policy": passed_policy,
        }

    # ── ML placeholders – replace with joblib.load() in production ──

    def _compute_risk_score(self, data: dict) -> float:
        """
        Simple heuristic risk model (replace with trained sklearn model).
        Higher = riskier.
        """
        score = 0.3  # base

        income = data.get("monthly_income") or 0
        req_amt = data.get("requested_amount") or 1

        if income > 0:
            dti = req_amt / (income * 12)
            score += min(0.3, dti * 0.5)  # debt-to-income proxy

        age = data.get("declared_age") or 35
        if age < 25:
            score += 0.05
        if age > 58:
            score += 0.05

        emp = data.get("employment_type", "")
        if emp == "salaried":
            score -= 0.05
        elif emp == "self_employed":
            score += 0.05

        llm_band = data.get("llm_risk_band", "medium")
        band_delta = {"low": -0.1, "medium": 0.0, "high": 0.1, "very_high": 0.2}
        score += band_delta.get(llm_band, 0.0)

        return min(1.0, max(0.0, score))

    def _compute_propensity(self, data: dict) -> float:
        """Likelihood customer will accept the offer (0–1)."""
        score = 0.6
        if data.get("loan_purpose") in ["home_renovation", "education", "medical"]:
            score += 0.1
        if (data.get("monthly_income") or 0) > 50000:
            score += 0.1
        return min(1.0, score)
