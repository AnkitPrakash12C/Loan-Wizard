"""
backend/services/vision_service.py
Computer Vision: age estimation from a video frame (JPEG/PNG bytes).
Uses DeepFace (built on top of TensorFlow + OpenCV).
"""
import io
import asyncio
import numpy as np
from loguru import logger


class VisionService:
    """
    Accepts a single frame (bytes) and returns:
      - estimated_age   (int)
      - confidence      (float 0-1)
      - face_detected   (bool)
      - fraud_signals   (list[str])  e.g. ["multiple_faces", "poor_lighting"]
    """

    async def estimate_age(self, frame_bytes: bytes) -> dict:
        """Run DeepFace analysis in thread pool (CPU-bound)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._analyze_sync, frame_bytes)

    def _analyze_sync(self, frame_bytes: bytes) -> dict:
        try:
            from PIL import Image
            import deepface
            from deepface import DeepFace

            # Convert bytes → numpy array
            image = Image.open(io.BytesIO(frame_bytes)).convert("RGB")
            img_array = np.array(image)

            results = DeepFace.analyze(
                img_path=img_array,
                actions=["age", "emotion"],
                enforce_detection=True,
                detector_backend="opencv",  # fast; swap to "retinaface" for accuracy
            )

            # DeepFace may return a list (multiple faces)
            if isinstance(results, list):
                if len(results) > 1:
                    return self._fraud_result("multiple_faces_detected")
                result = results[0]
            else:
                result = results

            estimated_age = int(result.get("age", 0))
            region = result.get("region", {})
            face_w = region.get("w", 0)
            face_h = region.get("h", 0)

            fraud_signals = []
            if face_w < 80 or face_h < 80:
                fraud_signals.append("face_too_small")

            # Simple confidence proxy: larger face region → higher confidence
            confidence = min(1.0, (face_w * face_h) / (200 * 200))

            return {
                "estimated_age": estimated_age,
                "confidence": round(confidence, 3),
                "face_detected": True,
                "fraud_signals": fraud_signals,
            }

        except Exception as e:
            logger.warning(f"DeepFace analysis failed: {e}")
            return {
                "estimated_age": None,
                "confidence": 0.0,
                "face_detected": False,
                "fraud_signals": ["face_not_detected"],
            }

    def validate_age(
        self,
        estimated_age: int,
        declared_age: int,
        min_age: int = 21,
        max_age: int = 65,
        tolerance: int = 8,
    ) -> dict:
        """
        Cross-check estimated vs declared age and policy thresholds.
        Returns eligibility decision + reason.
        """
        if estimated_age is None:
            return {"ok": False, "reason": "face_not_detected"}

        if declared_age < min_age or declared_age > max_age:
            return {
                "ok": False,
                "reason": f"declared_age_{declared_age}_out_of_policy_range_{min_age}_{max_age}",
            }

        if abs(estimated_age - declared_age) > tolerance:
            return {
                "ok": False,
                "reason": f"age_mismatch_estimated_{estimated_age}_declared_{declared_age}",
            }

        return {"ok": True, "reason": "age_validated"}

    # ── helpers ─────────────────────────────────────────────────

    @staticmethod
    def _fraud_result(signal: str) -> dict:
        return {
            "estimated_age": None,
            "confidence": 0.0,
            "face_detected": True,
            "fraud_signals": [signal],
        }
