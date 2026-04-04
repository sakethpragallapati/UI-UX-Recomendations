import os
import shutil
import random
from pathlib import Path
import yaml

def prepare_yolo_dataset(input_dir="yolo_dataset", output_dir="yolo_formatted", train_ratio=0.8, val_ratio=0.1):
    """Prepare YOLO dataset from scraper output"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Set seed for reproducibility (keeps splits consistent across runs)
    random.seed(42)

    # Create output directories
    for split in ['train', 'val', 'test']:
        (output_path / split / 'images').mkdir(parents=True, exist_ok=True)
        (output_path / split / 'labels').mkdir(parents=True, exist_ok=True)

    # Get all images
    images = list(input_path.glob('images/*.png'))
    random.shuffle(images)

    # Split dataset
    n_images = len(images)
    n_train = int(n_images * train_ratio)
    n_val = int(n_images * val_ratio)

    splits = {
        'train': images[:n_train],
        'val': images[n_train:n_train + n_val],
        'test': images[n_train + n_val:]
    }

    # Copy files
    for split, split_images in splits.items():
        for img_path in split_images:
            # Copy image
            shutil.copy2(
                img_path, 
                output_path / split / 'images' / img_path.name
            )
            
            # Copy corresponding YOLO .txt label file
            label_path = input_path / 'labels' / f"{img_path.stem}.txt"
            if label_path.exists():
                shutil.copy2(
                    label_path,
                    output_path / split / 'labels' / label_path.name
                )
            
            # Copy corresponding _meta.json file
            meta_path = input_path / 'labels' / f"{img_path.stem}_meta.json"
            if meta_path.exists():
                shutil.copy2(
                    meta_path,
                    output_path / split / 'labels' / meta_path.name
                )

    # Create YAML config
    with open(input_path / 'classes.txt', 'r') as f:
        classes = [line.strip() for line in f.readlines()]

    yaml_content = {
        'path': str(output_path.absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'names': {i: name for i, name in enumerate(classes)},
        'nc': len(classes)
    }

    with open(output_path / 'dataset.yaml', 'w') as f:
        yaml.dump(yaml_content, f, sort_keys=False)

    print(f"Dataset prepared in {output_path}")
    print(f"Training images: {len(splits['train'])}")
    print(f"Validation images: {len(splits['val'])}")
    print(f"Test images: {len(splits['test'])}")

if __name__ == "__main__":
    prepare_yolo_dataset()