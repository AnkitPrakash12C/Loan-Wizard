"""
backend/services/stt_service.py
Speech-to-Text: Whisper (local) or Deepgram (cloud)
"""
import os
import tempfile
import asyncio
from pathlib import Path
from loguru import logger
from backend.config import get_settings

settings = get_settings()


# ─── Key fields we want to extract from the transcript ──────────
EXTRACTION_SCHEMA = {
    "full_name": None,
    "employment_type": None,      # salaried / self-employed / business
    "monthly_income": None,       # in INR
    "loan_purpose": None,
    "requested_amount": None,
    "declared_age": None,
    "verbal_consent": False,
}


class STTService:
    """
    Converts audio bytes to text and extracts structured loan fields.
    Uses Whisper locally by default; switch to Deepgram by setting
    STT_PROVIDER=deepgram in .env.
    """

    def __init__(self):
        self._whisper_model = None  # lazy load

    # ── public API ──────────────────────────────────────────────

    async def transcribe(self, audio_bytes: bytes, mime: str = "audio/webm") -> str:
        """Transcribe raw audio bytes to text string."""
        if settings.stt_provider == "deepgram":
            return await self._transcribe_deepgram(audio_bytes, mime)
        return await self._transcribe_whisper(audio_bytes)

    async def extract_fields(self, transcript: str) -> dict:
        """
        Use the LLM service to parse structured fields from transcript.
        Imported here to avoid circular imports.
        """
        from backend.services.llm_service import LLMService
        llm = LLMService()
        return await llm.extract_application_fields(transcript)

    # ── Whisper ─────────────────────────────────────────────────

    async def _transcribe_whisper(self, audio_bytes: bytes) -> str:
        """Run Whisper in a thread pool to avoid blocking the event loop."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._whisper_sync, audio_bytes)

    def _whisper_sync(self, audio_bytes: bytes) -> str:
        import whisper

        if self._whisper_model is None:
            logger.info("Loading Whisper base model …")
            self._whisper_model = whisper.load_model("base")

        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name

        try:
            result = self._whisper_model.transcribe(tmp_path, language="en")
            return result["text"].strip()
        finally:
            os.unlink(tmp_path)

    # ── Deepgram ────────────────────────────────────────────────

    async def _transcribe_deepgram(self, audio_bytes: bytes, mime: str) -> str:
        try:
            from deepgram import DeepgramClient, PrerecordedOptions

            client = DeepgramClient(settings.deepgram_api_key)
            options = PrerecordedOptions(
                model="nova-2",
                smart_format=True,
                language="en-IN",
            )
            payload = {"buffer": audio_bytes, "mimetype": mime}
            response = await client.listen.asyncprerecorded.v("1").transcribe_file(
                payload, options
            )
            return response.results.channels[0].alternatives[0].transcript
        except Exception as e:
            logger.error(f"Deepgram failed, falling back to Whisper: {e}")
            return await self._transcribe_whisper(audio_bytes)
