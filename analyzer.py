import os
import json
from pathlib import Path
from collections import defaultdict

def analyze_ui_patterns(input_dir="yolo_dataset/labels", output_file="ui_baseline_rules.json"):
    print("Starting UI Pattern Analysis...")
    
    # Check if input directory exists
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Error: Directory '{input_dir}' not found.")
        return

    # Store raw normalized coordinates: data[category][element_type] = [(x, y, w, h), ...]
    raw_data = defaultdict(lambda: defaultdict(list))
    
    # --- DEDUPLICATION DICTIONARIES ---
    # Map synonyms to a single, unique semantic class
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
    
    # Map redundant categories to a standard unique name
    category_map = {
        'news': 'news_and_journalism'
    }
    
    # 1. Read all metadata files
    json_files = list(input_path.glob('*_meta.json'))
    print(f"Found {len(json_files)} metadata files to process.")
    
    if not json_files:
        print("No files to process. Exiting.")
        return

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                
            raw_category = meta.get('category', 'unknown')
            # Standardize category name
            category = category_map.get(raw_category, raw_category)
            
            image_size = meta.get('image_size', {})
            img_w = image_size.get('width', 0)
            img_h = image_size.get('height', 0)
            
            # Prevent division by zero
            if img_w <= 0 or img_h <= 0:
                print(f"Skipping {file_path.name}: Invalid image dimensions.")
                continue
            
            for element in meta.get('elements', []):
                coords = element.get('coordinates', {})
                
                # Ensure all coordinate keys exist
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
                
                # Store general class positioning
                raw_data[category][f"general_{class_name}"].append(coord_tuple)
                
                # Store specific semantic positioning (Mapped to unique classes)
                for keyword, unified_class in ux_keyword_map.items():
                    if keyword in desc_label:
                        raw_data[category][f"specific_{unified_class}"].append(coord_tuple)
                        break # Prevent double-counting if a label contains multiple keywords
                        
        except json.JSONDecodeError:
            print(f"Error: {file_path.name} is not a valid JSON file.")
        except Exception as e:
            print(f"Error processing {file_path.name}: {e}")

    # 2. Calculate Averages
    print("Calculating baseline rules...")
    baseline_rules = defaultdict(dict)
    
    for category, elements in raw_data.items():
        for elem_type, coords_list in elements.items():
            sample_size = len(coords_list)
            
            # Skip statistically insignificant samples
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

    # 3. Export to JSON
    try:
        with open(output_file, 'w', encoding='utf-8') as out_f:
            json.dump(baseline_rules, out_f, indent=4)
        print(f"Analysis complete. Results saved to '{output_file}'.")
    except IOError as e:
        print(f"Error saving output file: {e}")

if __name__ == "__main__":
    analyze_ui_patterns()