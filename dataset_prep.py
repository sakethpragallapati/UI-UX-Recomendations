import os
import shutil
import random
from pathlib import Path
import yaml

def prepare_yolo_dataset(input_dir="yolo_dataset", output_dir="yolo_formatted", train_ratio=0.8, val_ratio=0.1):
    """
    Takes the raw scraper output, shuffles the data, splits it into 
    train/val/test sets, and generates the YOLOv8 dataset.yaml config.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    images_dir = input_path / 'images'
    labels_dir = input_path / 'labels'

    print("🔄 Starting Dataset Preparation & Splitting...")

    # Check if input directory exists
    if not images_dir.exists() or not labels_dir.exists():
        print(f"❌ Error: Could not find 'images' or 'labels' folder inside '{input_dir}'. Did the scraper run successfully?")
        return

    # Set seed for reproducibility (keeps your splits consistent if you rerun this script)
    random.seed(42)

    # Get all images from the raw scraper output
    images = list(images_dir.glob('*.png'))
    
    if not images:
        print(f"❌ Error: No PNG images found in '{images_dir}'.")
        return
        
    print(f"📸 Found {len(images)} images. Shuffling and splitting into Train/Val/Test...")
    
    # Shuffle to ensure all website categories are evenly distributed across splits
    random.shuffle(images)

    # Calculate split indices
    n_images = len(images)
    n_train = int(n_images * train_ratio)
    n_val = int(n_images * val_ratio)

    splits = {
        'train': images[:n_train],
        'val': images[n_train:n_train + n_val],
        'test': images[n_train + n_val:]
    }

    # Create output directories and copy files
    for split_name, split_images in splits.items():
        # Define target paths for this split
        target_img_dir = output_path / split_name / 'images'
        target_label_dir = output_path / split_name / 'labels'
        
        # Create the directories
        target_img_dir.mkdir(parents=True, exist_ok=True)
        target_label_dir.mkdir(parents=True, exist_ok=True)

        for img_path in split_images:
            # 1. Copy the image
            shutil.copy2(img_path, target_img_dir / img_path.name)
            
            # 2. Copy the corresponding YOLO .txt label file
            label_path = labels_dir / f"{img_path.stem}.txt"
            if label_path.exists():
                shutil.copy2(label_path, target_label_dir / label_path.name)
            else:
                print(f"⚠️ Warning: Missing label file for {img_path.name}")
            
            # 3. Copy the corresponding _meta.json file 
            # (Keeping this here ensures analyzer.py can still read the split data if needed)
            meta_path = labels_dir / f"{img_path.stem}_meta.json"
            if meta_path.exists():
                shutil.copy2(meta_path, target_label_dir / meta_path.name)

    # --- Generate dataset.yaml ---
    classes_path = input_path / 'classes.txt'
    
    # Attempt to load the exact classes the scraper used
    if classes_path.exists():
        with open(classes_path, 'r') as f:
            classes = [line.strip() for line in f.readlines() if line.strip()]
    else:
        print("⚠️ Warning: 'classes.txt' not found. Reverting to default 21-Class Two-Path Ontology.")
        # Fallback to our agreed 21-class ontology
        classes = [
            'general_button', 'general_link', 'general_input', 'general_dropdown', 
            'general_label', 'general_checkbox', 'general_radio', 'general_textarea', 
            'general_menu_item', 'general_slider', 'general_image', 'general_video', 
            'general_iframe', 'general_form', 'general_table', 'general_clickable',
            'icon_cart', 'icon_menu', 'icon_search', 'icon_profile', 'icon_close'
        ]

    # YOLOv8 requires absolute paths for the root directory to prevent relative path errors during training
    yaml_content = {
        'path': str(output_path.absolute()), 
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'nc': len(classes),
        'names': {i: name for i, name in enumerate(classes)}
    }

    with open(output_path / 'dataset.yaml', 'w') as f:
        yaml.dump(yaml_content, f, sort_keys=False)

    print(f"\n✅ Dataset successfully prepared in '{output_path}'")
    print("-" * 40)
    print(f"📊 Training images:   {len(splits['train'])}")
    print(f"📊 Validation images: {len(splits['val'])}")
    print(f"📊 Test images:       {len(splits['test'])}")
    print("-" * 40)
    print("\n🚀 Ready for YOLO training! Run the following command:")
    print(f"yolo task=detect mode=train data={output_dir}/dataset.yaml model=yolov8n.pt epochs=100 imgsz=640")

if __name__ == "__main__":
    prepare_yolo_dataset()