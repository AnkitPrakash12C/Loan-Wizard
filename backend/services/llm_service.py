# """
# backend/services/llm_service.py
# LLM intelligence layer using Anthropic Claude.
# Responsibilities:
#   1. Extract structured fields from raw transcript
#   2. Classify customer (risk band, persona)
#   3. Generate explanation for loan decision
# """
# import json
# from loguru import logger
# from anthropic import AsyncAnthropic
# from backend.config import get_settings
#
# settings = get_settings()
# client = AsyncAnthropic(api_key=settings.anthropic_api_key)
#
#
# # ─────────────────────────────────────────────────────────────────
# EXTRACTION_PROMPT = """
# You are a loan application assistant. Extract structured information
# from this customer call transcript. Return ONLY valid JSON with these keys:
#
# {
#   "full_name": "<string or null>",
#   "employment_type": "<salaried|self_employed|business|unemployed|null>",
#   "monthly_income": <number in INR or null>,
#   "loan_purpose": "<string or null>",
#   "requested_amount": <number in INR or null>,
#   "declared_age": <integer or null>,
#   "verbal_consent": <true|false>
# }
#
# Rules:
# - verbal_consent = true ONLY if the customer explicitly agrees to terms during the call.
# - Convert any amounts like "5 lakhs" to 500000, "10k" to 10000, etc.
# - If a field is not mentioned, use null.
#
# Transcript:
# \"\"\"
# {transcript}
# \"\"\"
# """
#
# CLASSIFICATION_PROMPT = """
# You are a loan underwriting intelligence engine. Based on the customer profile below,
# classify the customer and return ONLY valid JSON:
#
# {
#   "risk_band": "<low|medium|high|very_high>",
#   "persona": "<string - short label like 'young_professional' or 'small_business_owner'>",
#   "confidence": <float 0-1>,
#   "summary": "<2-3 sentence summary of customer profile and key risk factors>",
#   "red_flags": [<list of concern strings, empty if none>]
# }
#
# Customer Profile:
# {profile}
# """
#
# DECISION_EXPLANATION_PROMPT = """
# You are a fair-lending compliance officer. Write a clear, empathetic explanation
# for the loan decision below. Keep it under 100 words and avoid jargon.
#
# Decision: {decision}
# Reason codes: {reasons}
# Customer name: {name}
# """
#
#
# class LLMService:
#
#     async def extract_application_fields(self, transcript: str) -> dict:
#         """Parse raw transcript → structured application fields."""
#         prompt = EXTRACTION_PROMPT.format(transcript=transcript)
#         try:
#             resp = await client.messages.create(
#                 model=settings.llm_model,
#                 max_tokens=512,
#                 messages=[{"role": "user", "content": prompt}],
#             )
#             raw = resp.content[0].text.strip()
#             return json.loads(raw)
#         except Exception as e:
#             logger.error(f"LLM extraction failed: {e}")
#             return {}
#
#     async def classify_customer(self, profile: dict) -> dict:
#         """Given application data dict, return classification."""
#         profile_str = json.dumps(profile, indent=2)
#         prompt = CLASSIFICATION_PROMPT.format(profile=profile_str)
#         try:
#             resp = await client.messages.create(
#                 model=settings.llm_model,
#                 max_tokens=512,
#                 messages=[{"role": "user", "content": prompt}],
#             )
#             raw = resp.content[0].text.strip()
#             return json.loads(raw)
#         except Exception as e:
#             logger.error(f"LLM classification failed: {e}")
#             return {
#                 "risk_band": "unknown",
#                 "persona": "unknown",
#                 "confidence": 0.0,
#                 "summary": "Classification unavailable.",
#                 "red_flags": [],
#             }
#
#     async def generate_decision_explanation(
#         self, decision: str, reasons: list[str], name: str
#     ) -> str:
#         """Generate a human-friendly decision explanation."""
#         prompt = DECISION_EXPLANATION_PROMPT.format(
#             decision=decision,
#             reasons=", ".join(reasons),
#             name=name or "Customer",
#         )
#         try:
#             resp = await client.messages.create(
#                 model=settings.llm_model,
#                 max_tokens=200,
#                 messages=[{"role": "user", "content": prompt}],
#             )
#             return resp.content[0].text.strip()
#         except Exception as e:
#             logger.error(f"LLM explanation failed: {e}")
#             return "We were unable to process your application at this time."
#
#     async def run_conversational_turn(
#         self,
#         history: list[dict],
#         user_message: str,
#         system_prompt: str = "",
#     ) -> str:
#         """
#         Generic multi-turn conversation helper.
#         history: list of {"role": "user"|"assistant", "content": "..."}
#         """
#         messages = history + [{"role": "user", "content": user_message}]
#         try:
#             resp = await client.messages.create(
#                 model=settings.llm_model,
#                 max_tokens=512,
#                 system=system_prompt or "You are a helpful loan onboarding assistant.",
#                 messages=messages,
#             )
#             return resp.content[0].text.strip()
#         except Exception as e:
#             logger.error(f"LLM conversation turn failed: {e}")
#             return "I'm having trouble understanding. Could you please repeat that?"

"""
backend/services/llm_service.py
LLM intelligence layer using Google Gemini.
Responsibilities:
  1. Extract structured fields from raw transcript
  2. Classify customer (risk band, persona)
  3. Generate explanation for loan decision
"""
import json
from loguru import logger
import google.generativeai as genai
from backend.config import get_settings

settings = get_settings()
genai.configure(api_key=settings.gemini_api_key)


# ─────────────────────────────────────────────────────────────────
EXTRACTION_PROMPT = """
You are a loan application assistant. Extract structured information
from this customer call transcript. Return ONLY valid JSON with these keys:

{{
  "full_name": "<string or null>",
  "employment_type": "<salaried|self_employed|business|unemployed|null>",
  "monthly_income": <number in INR or null>,
  "loan_purpose": "<string or null>",
  "requested_amount": <number in INR or null>,
  "declared_age": <integer or null>,
  "verbal_consent": <true|false>
}}

Rules:
- verbal_consent = true ONLY if the customer explicitly agrees to terms during the call.
- Convert any amounts like "5 lakhs" to 500000, "10k" to 10000, etc.
- If a field is not mentioned, use null.

Transcript:
\"\"\"
{transcript}
\"\"\"
"""

CLASSIFICATION_PROMPT = """
You are a loan underwriting intelligence engine. Based on the customer profile below,
classify the customer and return ONLY valid JSON:

{{
  "risk_band": "<low|medium|high|very_high>",
  "persona": "<string - short label like 'young_professional' or 'small_business_owner'>",
  "confidence": <float 0-1>,
  "summary": "<2-3 sentence summary of customer profile and key risk factors>",
  "red_flags": [<list of concern strings, empty if none>]
}}

Customer Profile:
{profile}
"""

DECISION_EXPLANATION_PROMPT = """
You are a fair-lending compliance officer. Write a clear, empathetic explanation
for the loan decision below. Keep it under 100 words and avoid jargon.

Decision: {decision}
Reason codes: {reasons}
Customer name: {name}
"""


class LLMService:

    def _get_model(self):
        return genai.GenerativeModel(settings.llm_model)

    def _clean_json(self, text: str) -> str:
        """Strip markdown fences if Gemini wraps response in ```json ... ```"""
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return text.strip()

    async def extract_application_fields(self, transcript: str) -> dict:
        """Parse raw transcript → structured application fields."""
        prompt = EXTRACTION_PROMPT.format(transcript=transcript)
        try:
            model = self._get_model()
            response = model.generate_content(prompt)
            raw = self._clean_json(response.text)
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Gemini extraction failed: {e}")
            return {}

    async def classify_customer(self, profile: dict) -> dict:
        """Given application data dict, return classification."""
        profile_str = json.dumps(profile, indent=2)
        prompt = CLASSIFICATION_PROMPT.format(profile=profile_str)
        try:
            model = self._get_model()
            response = model.generate_content(prompt)
            raw = self._clean_json(response.text)
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Gemini classification failed: {e}")
            return {
                "risk_band": "unknown",
                "persona": "unknown",
                "confidence": 0.0,
                "summary": "Classification unavailable.",
                "red_flags": [],
            }

    async def generate_decision_explanation(
        self, decision: str, reasons: list[str], name: str
    ) -> str:
        """Generate a human-friendly decision explanation."""
        prompt = DECISION_EXPLANATION_PROMPT.format(
            decision=decision,
            reasons=", ".join(reasons),
            name=name or "Customer",
        )
        try:
            model = self._get_model()
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini explanation failed: {e}")
            return "We were unable to process your application at this time."

    async def run_conversational_turn(
        self,
        history: list[dict],
        user_message: str,
        system_prompt: str = "",
    ) -> str:
        """
        Generic multi-turn conversation helper.
        history: list of {"role": "user"|"model", "parts": ["..."]}
        Note: Gemini uses "model" instead of "assistant", and "parts" instead of "content"
        """
        try:
            model = self._get_model()
            # Convert history to Gemini format
            gemini_history = []
            for msg in history:
                role = "model" if msg.get("role") == "assistant" else msg.get("role", "user")
                gemini_history.append({
                    "role": role,
                    "parts": [msg.get("content", "")]
                })

            chat = model.start_chat(history=gemini_history)
            full_message = f"{system_prompt}\n\n{user_message}" if system_prompt else user_message
            response = chat.send_message(full_message)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini conversation turn failed: {e}")
            return "I'm having trouble understanding. Could you please repeat that?"
