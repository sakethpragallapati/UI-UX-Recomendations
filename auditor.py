import json
import os

class UIAuditor:
    def __init__(self, baseline_file="ui_baseline_rules.json"):
        # Load the statistical baseline dictionary
        if not os.path.exists(baseline_file):
            print(f"Error: {baseline_file} not found. Please run analyzer.py first.")
            self.baselines = {}
        else:
            with open(baseline_file, 'r', encoding='utf-8') as f:
                self.baselines = json.load(f)
            
        # Path B: OCR Text Translation Map
        self.ux_keyword_map = {
            'cart': 'cart', 'checkout': 'cart',
            'search': 'search',
            'login': 'auth', 'sign in': 'auth', 'log in': 'auth', 'sign up': 'auth', 'register': 'auth',
            'menu': 'menu',
            'profile': 'profile', 'account': 'profile'
        }
        
        # Path A: Visual Icon Translation Map
        self.icon_map = {
            'icon_cart': 'cart',
            'icon_menu': 'menu',
            'icon_search': 'search',
            'icon_profile': 'profile',
            'icon_close': 'close'
        }

    def audit_element(self, predicted_category, yolo_class, x_center, ocr_text=""):
        specific_semantic_class = None

        # --- 1. THE ROUTING LOGIC (Traffic Cop) ---
        if yolo_class in self.icon_map:
            specific_semantic_class = f"specific_{self.icon_map[yolo_class]}"
            
        elif ocr_text:
            ocr_clean = ocr_text.lower().strip()
            for keyword, semantic in self.ux_keyword_map.items():
                if keyword in ocr_clean:
                    specific_semantic_class = f"specific_{semantic}"
                    break

        # If it's a generic element with no matching OCR keyword, we pass it safely
        if not specific_semantic_class:
            return "PASS: Generic element (No semantic rule triggered)."

        # --- 2. THE VALIDATION LOGIC (Math Check) ---
        if predicted_category not in self.baselines:
            return f"ERROR: Category '{predicted_category}' not found in baselines."

        if specific_semantic_class not in self.baselines[predicted_category]:
            return f"❌ ARCHITECTURAL ANOMALY: A '{specific_semantic_class}' is highly unusual for a '{predicted_category}' website."

        # Calculate the math
        baseline_x = self.baselines[predicted_category][specific_semantic_class]["avg_x_center"]
        deviation = abs(baseline_x - x_center)
        
        # The Anomaly Threshold (15% of screen width)
        threshold = 0.15 
        
        if deviation > threshold:
            return f"🚨 SEVERE ANOMALY: Expected '{specific_semantic_class}' at X:{baseline_x:.4f}, but found it at X:{x_center:.4f}. (Deviation: {deviation:.4f})"
        else:
            return f"✅ PASS: '{specific_semantic_class}' position is within UX standards. (Deviation: {deviation:.4f})"