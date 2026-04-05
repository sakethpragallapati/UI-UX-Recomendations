import json
import os

class UIAuditor:
    def __init__(self, baseline_file="ui_baseline_rules.json"):
        if not os.path.exists(baseline_file):
            print(f"Error: {baseline_file} not found. Please run analyzer.py first.")
            self.baselines = {}
        else:
            with open(baseline_file, 'r', encoding='utf-8') as f:
                self.baselines = json.load(f)
            
        self.ux_keyword_map = {
            'cart': 'cart', 'checkout': 'cart', 'basket': 'cart',
            'search': 'search',
            'login': 'auth', 'sign in': 'auth', 'log in': 'auth', 'sign up': 'auth', 'register': 'auth',
            'menu': 'menu',
            'profile': 'profile', 'account': 'profile'
        }
        
        self.icon_map = {
            'icon_cart': 'cart', 'icon_menu': 'menu', 'icon_search': 'search', 
            'icon_profile': 'profile', 'icon_close': 'close'
        }

        # UNIVERSAL SAFE ZONES: Industry standard fallbacks if data is skewed
        self.universal_zones = {
            'specific_cart': {'min_x': 0.75, 'max_y': 0.30},   # Carts belong Top-Right
            'specific_auth': {'min_x': 0.70, 'max_y': 0.30},   # Logins belong Top-Right
            'specific_menu': {'max_x': 0.35, 'max_y': 0.30},   # Menus belong Top-Left
            'specific_search': {'min_x': 0.20, 'max_x': 0.80, 'max_y': 0.40} # Search is Top-Center
        }

    def is_in_safe_zone(self, semantic_class, x_center):
        """Checks if the element is in a universally acceptable UX location."""
        if semantic_class not in self.universal_zones:
            return False
            
        zone = self.universal_zones[semantic_class]
        if 'min_x' in zone and x_center < zone['min_x']: return False
        if 'max_x' in zone and x_center > zone['max_x']: return False
        return True

    def audit_element(self, predicted_categories, yolo_class, x_center, ocr_text="", confidence=100.0):
        """
        predicted_categories: A list of the top 3 category guesses from the classifier.
        """
        specific_semantic_class = None

        # --- 1. SMART OCR FILTERING ---
        if yolo_class in self.icon_map:
            specific_semantic_class = f"specific_{self.icon_map[yolo_class]}"
            
        elif ocr_text:
            ocr_clean = ocr_text.lower().strip()
            # UI buttons are rarely paragraphs. Limit to 3 words.
            word_count = len(ocr_clean.split())
            
            if word_count <= 3:
                for keyword, semantic in self.ux_keyword_map.items():
                    # Strict bounding to prevent partial matches (e.g., "research" triggering "search")
                    if keyword == ocr_clean or f" {keyword} " in f" {ocr_clean} ":
                        specific_semantic_class = f"specific_{semantic}"
                        break

        # Pass if it's just a generic blob of text or a normal image
        if not specific_semantic_class:
            return "PASS: Generic element (No semantic rule triggered)."

        # --- 2. THE MULTI-CLASS FORGIVING LOOP ---
        primary_error_msg = ""
        
        for category in predicted_categories:
            # Skip if we don't have baseline data for this category guess
            if category not in self.baselines:
                continue

            # Check Contextual Anomaly (Does this element belong on this type of site?)
            if specific_semantic_class not in self.baselines[category]:
                if not primary_error_msg:
                    primary_error_msg = f"❌ ARCHITECTURAL ANOMALY: '{specific_semantic_class}' is unusual for '{predicted_categories[0]}'."
                continue

            # Grab the mathematical truth
            baseline_x = self.baselines[category][specific_semantic_class]["avg_x_center"]
            deviation = abs(baseline_x - x_center)
            
            # Dynamic Threshold: Be forgiving if the AI classifier wasn't confident
            threshold = 0.20 if confidence >= 60.0 else 0.35
            
            # --- VALIDATION ---
            # Condition A: It passes the statistical math for this category
            if deviation <= threshold:
                return f"✅ PASS: Matches UX standards for '{category}'. (Deviation: {deviation:.4f})"
                
            # Condition B: It failed the math, but sits in an industry-standard safe zone
            if self.is_in_safe_zone(specific_semantic_class, x_center):
                return f"✅ PASS: Deviated from '{category}' data, but falls in Universal Safe Zone. (X:{x_center:.4f})"
                
            # Condition C: It failed everything. Save the error for the primary Top-1 guess.
            if not primary_error_msg:
                primary_error_msg = f"🚨 SEVERE ANOMALY: Expected '{specific_semantic_class}' near X:{baseline_x:.4f} (for {predicted_categories[0]}), found at X:{x_center:.4f}."

        # If it failed to pass ANY of the 3 category guesses, throw the primary error.
        return primary_error_msg if primary_error_msg else "ERROR: Baseline lookup failed."