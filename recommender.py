"""
LLM-powered recommendation engine for UI Audit Studio.

Takes structured audit results (YOLO detections + baseline verdicts) and generates
actionable, human-readable UX improvement recommendations via HuggingFace LLM.
"""

import json
import os
import re
from typing import Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()


# ── Output Schema ──────────────────────────────────────────────────────────────

class ElementRecommendation(BaseModel):
    element_class: str = Field(description="The UI element type, e.g. 'specific_cart', 'general_button'")
    severity: str = Field(description="One of: critical, medium, low")
    issue: str = Field(description="Concise description of the UX problem")
    recommendation: str = Field(description="Specific, actionable fix suggestion")
    ux_principle: str = Field(description="The UX principle or heuristic being violated")


class AuditRecommendation(BaseModel):
    overall_score: int = Field(description="Overall UX score from 0 to 100")
    summary: str = Field(description="2-3 sentence summary of the audit findings")
    strengths: List[str] = Field(description="List of things the UI does well")
    recommendations: List[ElementRecommendation] = Field(
        description="Per-element recommendations for each issue found"
    )
    priority_actions: List[str] = Field(
        description="Top 3-5 highest-priority actions to fix first"
    )


# ── Recommendation Engine ─────────────────────────────────────────────────────

class RecommendationEngine:
    """Generates LLM-powered UX recommendations from audit results using HuggingFace."""

    def __init__(self):
        self.model = None
        self._setup_client()

    def _setup_client(self):
        """Initialize the HuggingFace LLM endpoint."""
        hf_token = os.getenv("HUGGINGFACEHUB_ACCESS_TOKEN", "").strip()
        if not hf_token:
            return

        try:
            from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

            endpoint = HuggingFaceEndpoint(
                repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
                task="text-generation",
                huggingfacehub_api_token=hf_token,
                max_new_tokens=1500,
                temperature=0.3,
                top_p=0.9,
                repetition_penalty=1.1,
            )
            self.model = ChatHuggingFace(llm=endpoint)
        except ImportError:
            print("Warning: langchain-huggingface not installed.")
        except Exception as e:
            print(f"Warning: Failed to initialize HuggingFace model: {e}")

    @property
    def is_available(self) -> bool:
        return self.model is not None

    def _build_prompt(
        self,
        detections: List[Dict],
        category: str,
        baselines: Dict,
        image_width: int,
        image_height: int,
    ) -> str:
        """Build the structured analysis prompt."""

        # Separate anomalies and passes
        anomalies = []
        passes = []
        for det in detections:
            entry = (
                f"  - Element: {det['yolo_class']}, "
                f"Confidence: {det['confidence']:.2f}, "
                f"Position: ({det['xyxy'][0]}, {det['xyxy'][1]}) to ({det['xyxy'][2]}, {det['xyxy'][3]}), "
                f"OCR: '{det.get('ocr_text', '')}', "
                f"Verdict: {det['audit_result']}"
            )
            if "ANOMALY" in det["audit_result"] or "ERROR" in det["audit_result"]:
                anomalies.append(entry)
            else:
                passes.append(entry)

        # Get category baselines for context
        category_baselines = baselines.get(category, {})
        baseline_summary = []
        for elem_type, stats in list(category_baselines.items())[:12]:
            baseline_summary.append(
                f"  - {elem_type}: expected X={stats['avg_x_center']:.4f}, "
                f"Y={stats['avg_y_center']:.4f}, samples={stats.get('sample_size', 0)}"
            )

        prompt = f"""You are a senior UI/UX auditor. Analyze the automated audit results below and provide actionable recommendations.

CONTEXT:
- Website category: {category}
- Image size: {image_width}x{image_height}px
- Elements detected: {len(detections)}
- Anomalies: {len(anomalies)}
- Passing: {len(passes)}

ANOMALIES (elements violating baseline patterns):
{chr(10).join(anomalies) if anomalies else "  None found."}

PASSING ELEMENTS:
{chr(10).join(passes[:8]) if passes else "  None."}

CATEGORY BASELINES (expected positions for '{category}'):
{chr(10).join(baseline_summary) if baseline_summary else "  No baselines available."}

UX PRINCIPLES:
- Jakob's Law: match common design conventions
- Fitts's Law: important targets should be large and accessible
- F-Pattern: users scan left-to-right, top-to-bottom
- Visual Hierarchy: size/position convey importance
- Consistency: similar elements should look/behave similarly

RESPOND WITH ONLY valid JSON (no markdown, no extra text):
{{
  "overall_score": <0-100>,
  "summary": "<2-3 sentence assessment>",
  "strengths": ["<strength 1>", "<strength 2>"],
  "recommendations": [
    {{
      "element_class": "<element type>",
      "severity": "<critical|medium|low>",
      "issue": "<problem>",
      "recommendation": "<fix>",
      "ux_principle": "<principle violated>"
    }}
  ],
  "priority_actions": ["<action 1>", "<action 2>", "<action 3>"]
}}

RULES:
- critical = breaks core user flow, medium = confusing but usable, low = polish
- If no anomalies, score high and focus on strengths
- Be specific to the '{category}' category
- Include 2-4 strengths even if issues exist
- priority_actions = top 3 most impactful fixes"""

        return prompt

    def _parse_response(self, raw_text: str) -> Optional[AuditRecommendation]:
        """Parse the LLM response into a structured AuditRecommendation."""
        try:
            # Strip markdown code fences if present
            cleaned = raw_text.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
                cleaned = re.sub(r"\s*```$", "", cleaned)

            data = json.loads(cleaned)
            return AuditRecommendation(**data)
        except (json.JSONDecodeError, Exception):
            pass

        # Attempt to find JSON block within the response
        json_match = re.search(r"\{[\s\S]*\}", raw_text)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return AuditRecommendation(**data)
            except Exception:
                pass

        return None

    def generate_recommendations(
        self,
        detections: List[Dict],
        category: str,
        baselines: Dict,
        image_path: Optional[str] = None,
        image_width: int = 1920,
        image_height: int = 1080,
    ) -> Optional[AuditRecommendation]:
        """
        Generate UX recommendations from audit results.

        Args:
            detections: List of detection dicts with yolo_class, confidence, xyxy, ocr_text, audit_result.
            category: Website category (e.g., 'e_commerce').
            baselines: The full baselines dict from ui_baseline_rules.json.
            image_path: Path to the screenshot (unused for HuggingFace text-only, kept for API compat).
            image_width: Image width in pixels.
            image_height: Image height in pixels.

        Returns:
            AuditRecommendation or None if generation failed.
        """
        if not self.is_available:
            return self._fallback_recommendations(detections, category)

        prompt = self._build_prompt(
            detections=detections,
            category=category,
            baselines=baselines,
            image_width=image_width,
            image_height=image_height,
        )

        try:
            response = self.model.invoke(prompt)

            if response and response.content:
                parsed = self._parse_response(response.content)
                if parsed:
                    return parsed
        except Exception as e:
            print(f"LLM recommendation generation failed: {e}")

        # Fall back to rule-based if LLM response was unparseable
        return self._fallback_recommendations(detections, category)

    def _fallback_recommendations(
        self, detections: List[Dict], category: str
    ) -> AuditRecommendation:
        """
        Generate rule-based recommendations when the LLM is unavailable or fails.
        Uses the existing audit verdicts to produce basic suggestions.
        """
        anomalies = [
            d for d in detections
            if "ANOMALY" in d.get("audit_result", "") or "ERROR" in d.get("audit_result", "")
        ]
        passes = [d for d in detections if d not in anomalies]

        recommendations = []
        for det in anomalies:
            verdict = det["audit_result"]
            yolo_class = det["yolo_class"]

            if "SEVERE ANOMALY" in verdict or "ARCHITECTURAL ANOMALY" in verdict:
                severity = "critical"
            else:
                severity = "medium"

            issue = verdict.split(":")[1].strip() if ":" in verdict else verdict
            rec = self._get_rule_based_suggestion(yolo_class, category, verdict)

            recommendations.append(
                ElementRecommendation(
                    element_class=yolo_class,
                    severity=severity,
                    issue=issue,
                    recommendation=rec,
                    ux_principle="Jakob's Law — match common design conventions",
                )
            )

        total = len(detections)
        passing = len(passes)
        score = int((passing / max(total, 1)) * 100) if total > 0 else 50

        strengths = []
        if passing > 0:
            strengths.append(f"{passing} out of {total} elements match expected layout patterns.")
        if any("general_button" in d["yolo_class"] for d in passes):
            strengths.append("Button placements follow standard conventions.")
        if any("search" in d.get("yolo_class", "") for d in passes):
            strengths.append("Search functionality is placed in an expected location.")
        if not strengths:
            strengths.append("The interface contains recognizable standard UI elements.")

        priority_actions = [r.recommendation for r in recommendations[:3]]
        if not priority_actions:
            priority_actions = ["No critical issues detected — continue refining visual polish."]

        return AuditRecommendation(
            overall_score=score,
            summary=f"Detected {total} UI elements with {len(anomalies)} anomalies for a '{category}' website. "
                    + ("Several elements deviate from expected positions." if anomalies else "Layout closely matches expected patterns."),
            strengths=strengths,
            recommendations=recommendations,
            priority_actions=priority_actions,
        )

    def _get_rule_based_suggestion(self, yolo_class: str, category: str, verdict: str) -> str:
        """Return a rule-based suggestion for common anomaly types."""
        suggestions = {
            "specific_cart": "Move the cart/bag icon to the upper-right corner of the header — this is where 90%+ of e-commerce users expect it.",
            "specific_search": "Position the search bar in the top-center or upper area of the page. Users follow an F-pattern and expect search near the top.",
            "specific_auth": "Place login/sign-up buttons in the top-right header area where users habitually look for account access.",
            "specific_menu": "Navigation menus should be in the top-left or as a horizontal bar across the top. Unconventional placement increases cognitive load.",
            "specific_profile": "User/profile icons are conventionally placed in the top-right area, near auth and cart elements.",
            "specific_close": "Close/dismiss buttons should be in the top-right corner of their container (modal, popup, or panel).",
            "general_button": "Ensure primary action buttons are visually prominent and placed in the natural reading flow (F-pattern or Z-pattern).",
            "general_link": "Navigation links should follow a consistent layout and be grouped logically.",
            "general_input": "Form inputs should be clearly labeled, properly sized (min 44px touch target), and grouped in a logical flow.",
            "general_image": "Images should support the content hierarchy, not obstruct key interactive elements.",
        }

        if "ARCHITECTURAL" in verdict:
            return f"This element type ('{yolo_class}') is unusual for '{category}' websites. Consider whether it's truly needed or if users might find it confusing."

        return suggestions.get(
            yolo_class,
            "Review this element's placement against competitor websites in the same category to ensure it meets user expectations."
        )
