import json
import os
import re
from typing import Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

try:
    from langchain_core.output_parsers import PydanticOutputParser
    from langchain_core.prompts import PromptTemplate
    from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
except ImportError:
    ChatHuggingFace = None
    HuggingFaceEndpoint = None
    PromptTemplate = None
    PydanticOutputParser = None


load_dotenv()


class SemanticMapping(BaseModel):
    semantic_class: str = Field(
        description="One of: cart, search, auth, menu, profile, close, none"
    )
    confidence: float = Field(
        description="Confidence from 0.0 to 1.0 for the semantic mapping decision"
    )
    reasoning: str = Field(
        description="A short explanation of why the text maps or does not map"
    )


class UIAuditor:
    def __init__(self, baseline_file="ui_baseline_rules.json"):
        if not os.path.exists(baseline_file):
            print(f"Error: {baseline_file} not found. Please run analyzer.py first.")
            self.baselines = {}
        else:
            with open(baseline_file, "r", encoding="utf-8") as file:
                self.baselines = json.load(file)

        self.ux_keyword_map = {
            "cart": "cart",
            "basket": "cart",
            "bag": "cart",
            "checkout": "cart",
            "add to cart": "cart",
            "view cart": "cart",
            "search": "search",
            "find": "search",
            "menu": "menu",
            "categories": "menu",
            "category": "menu",
            "browse": "menu",
            "profile": "profile",
            "account": "profile",
            "my account": "profile",
            "user": "profile",
            "avatar": "profile",
            "login": "auth",
            "log in": "auth",
            "sign in": "auth",
            "signin": "auth",
            "sign up": "auth",
            "signup": "auth",
            "register": "auth",
            "join": "auth",
            "close": "close",
            "dismiss": "close",
            "cancel": "close",
        }

        self.icon_map = {
            "icon_cart": "cart",
            "icon_menu": "menu",
            "icon_search": "search",
            "icon_profile": "profile",
            "icon_close": "close",
        }

        self.generic_classes = {
            "general_button",
            "general_link",
            "general_input",
            "general_dropdown",
            "general_label",
            "general_checkbox",
            "general_radio",
            "general_textarea",
            "general_menu_item",
            "general_slider",
            "general_image",
        }

        self.universal_zones = {
            "specific_cart": {"min_x": 0.72, "max_y": 0.32},
            "specific_auth": {"min_x": 0.68, "max_y": 0.32},
            "specific_menu": {"max_x": 0.35, "max_y": 0.32},
            "specific_search": {"min_x": 0.15, "max_x": 0.85, "max_y": 0.42},
            "specific_profile": {"min_x": 0.68, "max_y": 0.32},
            "specific_close": {"min_x": 0.65, "max_y": 0.35},
        }

        self.semantic_cache: Dict[str, Optional[str]] = {}
        self.mapping_parser = None
        self.mapping_prompt = None
        self.mapping_model = None
        self._setup_llm_mapper()

    def _setup_llm_mapper(self):
        if not all([ChatHuggingFace, HuggingFaceEndpoint, PromptTemplate, PydanticOutputParser]):
            return

        hf_token = os.getenv("HUGGINGFACEHUB_ACCESS_TOKEN")
        if not hf_token:
            return

        try:
            self.mapping_parser = PydanticOutputParser(pydantic_object=SemanticMapping)
            self.mapping_prompt = PromptTemplate(
                template=(
                    "You map OCR text from UI screenshots into strict semantic UI intents.\n"
                    "Allowed semantic classes: cart, search, auth, menu, profile, close, none.\n"
                    "Rules:\n"
                    "- Return 'none' for product names, fashion categories, promo text, banners, sale text, prices, and generic CTAs like 'shop now'.\n"
                    "- Return 'cart' only for text that clearly means cart/bag/basket/checkout/add to cart/view cart.\n"
                    "- Return 'search' only for clear search/find text.\n"
                    "- Return 'auth' only for login/sign in/sign up/register/join account access.\n"
                    "- Return 'menu' only for menu/navigation/category browser intent.\n"
                    "- Return 'profile' only for profile/account/user/avatar intent.\n"
                    "- Return 'close' only for close/dismiss/cancel intent.\n"
                    "- If OCR is messy or ambiguous, prefer 'none'.\n\n"
                    "YOLO class: {yolo_class}\n"
                    "OCR text: {ocr_text}\n\n"
                    "{format_instructions}"
                ),
                input_variables=["yolo_class", "ocr_text"],
                partial_variables={
                    "format_instructions": self.mapping_parser.get_format_instructions()
                },
            )

            endpoint = HuggingFaceEndpoint(
                repo_id="meta-llama/Meta-Llama-3-8B-Instruct",
                task="text-generation",
                huggingfacehub_api_token=hf_token,
                max_new_tokens=220,
                temperature=0.1,
            )
            self.mapping_model = ChatHuggingFace(llm=endpoint)
        except Exception:
            self.mapping_parser = None
            self.mapping_prompt = None
            self.mapping_model = None

    def normalize_text(self, text):
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def fuzzy_contains(self, text, keyword):
        text = self.normalize_text(text)
        keyword = self.normalize_text(keyword)

        if not text or not keyword:
            return False

        if keyword in text:
            return True

        collapsed_text = text.replace(" ", "")
        collapsed_keyword = keyword.replace(" ", "")
        if collapsed_keyword in collapsed_text:
            return True

        words = text.split()
        key_words = keyword.split()

        if len(key_words) == 1:
            target = key_words[0]
            for word in words:
                if word.startswith(target[: max(2, len(target) - 2)]):
                    return True
                if len(word) >= 4 and len(target) >= 4:
                    overlap = sum(1 for a, b in zip(word, target) if a == b)
                    if overlap >= max(3, min(len(word), len(target)) - 2):
                        return True

        return False

    def get_llm_semantic_class(self, yolo_class, ocr_text=""):
        ocr_clean = self.normalize_text(ocr_text)
        if not ocr_clean or not self.mapping_model or not self.mapping_prompt or not self.mapping_parser:
            return None

        cache_key = f"{yolo_class}::{ocr_clean}"
        if cache_key in self.semantic_cache:
            return self.semantic_cache[cache_key]

        try:
            prompt = self.mapping_prompt.format(yolo_class=yolo_class, ocr_text=ocr_clean)
            response = self.mapping_model.invoke(prompt)
            parsed = self.mapping_parser.parse(response.content)
            semantic = parsed.semantic_class.strip().lower()

            if semantic == "none" or parsed.confidence < 0.70:
                self.semantic_cache[cache_key] = None
                return None

            if semantic in {"cart", "search", "auth", "menu", "profile", "close"}:
                mapped = f"specific_{semantic}"
                self.semantic_cache[cache_key] = mapped
                return mapped
        except Exception:
            pass

        self.semantic_cache[cache_key] = None
        return None

    def get_semantic_class(self, yolo_class, ocr_text=""):
        if yolo_class in self.icon_map:
            return f"specific_{self.icon_map[yolo_class]}"

        llm_semantic = self.get_llm_semantic_class(yolo_class, ocr_text)
        if llm_semantic:
            return llm_semantic

        ocr_clean = self.normalize_text(ocr_text)
        if not ocr_clean:
            return None

        for keyword, semantic in self.ux_keyword_map.items():
            if self.fuzzy_contains(ocr_clean, keyword):
                return f"specific_{semantic}"

        return None

    def is_in_safe_zone(self, semantic_class, x_center):
        if semantic_class not in self.universal_zones:
            return False

        zone = self.universal_zones[semantic_class]
        if "min_x" in zone and x_center < zone["min_x"]:
            return False
        if "max_x" in zone and x_center > zone["max_x"]:
            return False
        return True

    def get_threshold(self, sample_size, confidence):
        if sample_size >= 100:
            threshold = 0.14
        elif sample_size >= 30:
            threshold = 0.18
        elif sample_size >= 10:
            threshold = 0.24
        else:
            threshold = 0.30

        if confidence < 0.45:
            threshold += 0.05
        elif confidence < 0.60:
            threshold += 0.03

        return min(threshold, 0.36)

    def audit_against_baseline(self, category, baseline_key, x_center, confidence, semantic=False):
        if category not in self.baselines:
            return None

        category_rules = self.baselines[category]
        if baseline_key not in category_rules:
            if semantic:
                return f"ARCHITECTURAL ANOMALY: '{baseline_key}' is unusual for '{category}'."
            return None

        baseline = category_rules[baseline_key]
        baseline_x = baseline["avg_x_center"]
        sample_size = baseline.get("sample_size", 0)
        deviation = abs(baseline_x - x_center)
        threshold = self.get_threshold(sample_size, confidence)

        if deviation <= threshold:
            label = "semantic pattern" if semantic else "layout baseline"
            return f"PASS: Matches {label} for '{category}'. (Deviation: {deviation:.4f})"

        if semantic and self.is_in_safe_zone(baseline_key, x_center):
            return f"PASS: Deviates from '{category}' baseline but sits in a universal safe zone. (X: {x_center:.4f})"

        severity = "SEVERE ANOMALY" if semantic else "LAYOUT ANOMALY"
        return (
            f"{severity}: Expected '{baseline_key}' near X:{baseline_x:.4f} for '{category}', "
            f"found at X:{x_center:.4f}."
        )

    def audit_element(self, predicted_categories, yolo_class, x_center, ocr_text="", confidence=100.0):
        categories = predicted_categories or []
        if not categories:
            return "ERROR: No website category selected."

        if confidence > 1.0:
            confidence = confidence / 100.0

        semantic_class = self.get_semantic_class(yolo_class, ocr_text)

        if semantic_class:
            primary_error = None
            for category in categories:
                result = self.audit_against_baseline(
                    category=category,
                    baseline_key=semantic_class,
                    x_center=x_center,
                    confidence=confidence,
                    semantic=True,
                )
                if not result:
                    continue
                if result.startswith("PASS:"):
                    return result
                if primary_error is None:
                    primary_error = result
            if primary_error:
                return primary_error

        if yolo_class in self.generic_classes:
            for category in categories:
                result = self.audit_against_baseline(
                    category=category,
                    baseline_key=yolo_class,
                    x_center=x_center,
                    confidence=confidence,
                    semantic=False,
                )
                if result and result.startswith("PASS:"):
                    if semantic_class:
                        return f"{result} Semantic hint: '{semantic_class}'."
                    return result

            for category in categories:
                result = self.audit_against_baseline(
                    category=category,
                    baseline_key=yolo_class,
                    x_center=x_center,
                    confidence=confidence,
                    semantic=False,
                )
                if result:
                    if semantic_class:
                        return f"{result} Semantic hint: '{semantic_class}'."
                    return result

            if ocr_text:
                return f"PASS: Detected generic element with OCR '{ocr_text}', but no category baseline exists for '{yolo_class}'."
            return f"PASS: Generic element detected, but no category baseline exists for '{yolo_class}'."

        return "PASS: No matching audit rule was triggered for this element."
