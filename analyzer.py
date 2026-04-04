import os
import json
from pathlib import Path
from collections import defaultdict

def build_baseline_rules(input_dir="yolo_dataset", output_file="ui_baseline_rules.json"):
    print("Starting Two-Path UI Pattern Analysis...")
    
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Error: Directory '{input_dir}' not found.")
        return

    # Store raw normalized coordinates: data[category][element_type] = [(x, y, w, h), ...]
    raw_data = defaultdict(lambda: defaultdict(list))
    
    # --- PATH A: Visual Icon Dictionary ---
    # Maps native YOLO visual detections directly to semantic classes
    icon_map = {
        'icon_cart': 'cart',
        'icon_menu': 'menu',
        'icon_search': 'search',
        'icon_profile': 'profile',
        'icon_close': 'close'
    }

    # --- PATH B: Text-Based Overlap Dictionary ---
    # Maps generic shapes (buttons/links) to semantic classes based on their text/ARIA labels
    ux_keyword_map = {
        'cart': 'cart',
        'checkout': 'cart',
        'search': 'search',
        'login': 'auth',
        'sign in': 'auth',
        'log in': 'auth',
        'sign up': 'auth',
        'register': 'auth',
        'menu': 'menu',
        'profile': 'profile',
        'account': 'profile'
    }
    
    # CHANGED: Using rglob (recursive search) to find metadata files anywhere in the dataset folder
    json_files = list(input_path.rglob('*_meta.json'))
    print(f"Found {len(json_files)} metadata files to process.")
    
    if not json_files:
        print("No files to process. Exiting.")
        return

    # 1. READ AND ROUTE DATA
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                
            category = meta.get('category', 'unknown')
            
            image_size = meta.get('image_size', {})
            img_w = image_size.get('width', 0)
            img_h = image_size.get('height', 0)
            
            if img_w <= 0 or img_h <= 0:
                continue
            
            for element in meta.get('elements', []):
                coords = element.get('coordinates', {})
                if not all(k in coords for k in ('x1', 'y1', 'x2', 'y2')):
                    continue
                    
                class_name = element.get('class_name', 'unknown')
                desc_label = element.get('descriptive_label', '').lower()
                
                # Calculate normalized center points and dimensions (0.0 to 1.0)
                x_center = ((coords['x1'] + coords['x2']) / 2) / img_w
                y_center = ((coords['y1'] + coords['y2']) / 2) / img_h
                width = (coords['x2'] - coords['x1']) / img_w
                height = (coords['y2'] - coords['y1']) / img_h
                
                coord_tuple = (x_center, y_center, width, height)
                
                # ALWAYS store the raw YOLO detection position (Fixing the double 'general_' prefix bug)
                raw_data[category][class_name].append(coord_tuple)
                
                # --- TRAFFIC COP LOGIC ---
                
                # ROUTE A: It's a specific visual icon
                if class_name in icon_map:
                    unified_class = icon_map[class_name]
                    raw_data[category][f"specific_{unified_class}"].append(coord_tuple)
                    
                # ROUTE B: It's a generic shape, check the text/ARIA label
                else:
                    for keyword, unified_class in ux_keyword_map.items():
                        if keyword in desc_label:
                            raw_data[category][f"specific_{unified_class}"].append(coord_tuple)
                            break # Break to prevent double-counting
                            
        except json.JSONDecodeError:
            print(f"Error: {file_path.name} is not a valid JSON file.")
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    # 2. CALCULATE STATISTICAL AVERAGES
    print("Calculating baseline rules...")
    baseline_rules = defaultdict(dict)
    
    for category, elements in raw_data.items():
        for elem_type, coords_list in elements.items():
            sample_size = len(coords_list)
            
            # Skip statistically insignificant samples to prevent noisy baselines
            if sample_size < 3:
                continue 
                
            x_vals, y_vals, w_vals, h_vals = zip(*coords_list)
            
            baseline_rules[category][elem_type] = {
                "avg_x_center": round(sum(x_vals) / sample_size, 4),
                "avg_y_center": round(sum(y_vals) / sample_size, 4),
                "avg_width": round(sum(w_vals) / sample_size, 4),
                "avg_height": round(sum(h_vals) / sample_size, 4),
                "sample_size": sample_size
            }

    # 3. EXPORT TO JSON
    try:
        with open(output_file, 'w', encoding='utf-8') as out_f:
            json.dump(baseline_rules, out_f, indent=4)
        print(f"Analysis complete. Results saved to '{output_file}'.")
    except IOError as e:
        print(f"Error saving output file: {e}")

if __name__ == "__main__":
    build_baseline_rules()