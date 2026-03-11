"""
Model loading and classification service.

Loads the binary and multiclass Random Forest models once and exposes
a `classify` function used by the middleware.
"""

import logging
from dataclasses import dataclass, field

import joblib
import numpy as np
import shap

from server.config import FEATURE_NAMES, MODEL_DIR

logger = logging.getLogger("ids")

# Number of top contributing features to include in explanations
TOP_N_FEATURES = 5


@dataclass
class ClassificationResult:
    binary_label: str                        # "Normal" or "Attack"
    explanation: list[dict] = field(default_factory=list)
    # [{"feature": "...", "value": ..., "shap_value": ...}, ...]


class IDSClassifier:
    """Wraps the binary Random Forest classification pipeline."""

    def __init__(self) -> None:
        logger.info("Loading binary classification model …")
        self.binary_model = joblib.load(MODEL_DIR / "rf_model.joblib")

        logger.info("Initialising SHAP explainer …")
        self.explainer = shap.TreeExplainer(self.binary_model)

        logger.info("Models loaded successfully.")

    def classify(self, features: dict[str, float | int]) -> ClassificationResult:
        """
        Run binary classification on extracted features.

        1. Binary model → Normal / Attack
        2. SHAP → top-N feature contributions for the prediction
        """
        feature_vector = np.array(
            [[features[name] for name in FEATURE_NAMES]]
        )

        binary_pred = self.binary_model.predict(feature_vector)[0]
        binary_label = "Attack" if binary_pred == 1 else "Normal"

        explanation = self._explain(feature_vector, features)

        return ClassificationResult(
            binary_label=binary_label,
            explanation=explanation,
        )

    def _explain(
        self,
        feature_vector: np.ndarray,
        features: dict[str, float | int],
    ) -> list[dict]:
        """Return the top-N features by absolute SHAP contribution."""
        try:
            # shap_values shape: (1, n_features) for binary output
            shap_values = self.explainer.shap_values(feature_vector)

            # Handle SHAP API differences across versions:
            #   older SHAP  → list of 2 arrays, each (n_samples, n_features)
            #   newer SHAP  → single ndarray of shape (n_samples, n_features, n_classes)
            if isinstance(shap_values, list):
                values = shap_values[1][0]
            elif shap_values.ndim == 3:
                values = shap_values[0, :, 1]
            else:
                values = shap_values[0]

            ranked = sorted(
                zip(FEATURE_NAMES, values),
                key=lambda x: abs(x[1]),
                reverse=True,
            )

            return [
                {
                    "feature": name,
                    "value": round(features[name], 6) if isinstance(features[name], float) else features[name],
                    "shap_value": round(float(sv), 6),
                }
                for name, sv in ranked[:TOP_N_FEATURES]
            ]
        except Exception as exc:
            logger.warning("SHAP explanation failed: %s", exc)
            return []
