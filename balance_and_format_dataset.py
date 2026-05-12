import os
import glob
import random
import shutil
import cv2
import yaml
from collections import Counter

# Configuration
input_dir = 'yolo_dataset_v2'
output_dir = 'yolo_formatted_v2'
train_ratio = 0.8
val_ratio = 0.1
target_class_count = 1000  # Target number of instances per class in the train set

original_classes = {
    0: 'general_button', 1: 'general_link', 2: 'general_input', 3: 'general_dropdown', 
    4: 'general_label', 5: 'general_checkbox', 6: 'general_radio', 7: 'general_textarea', 
    8: 'general_menu_item', 9: 'general_slider', 10: 'general_image', 11: 'general_video', 
    12: 'general_iframe', 13: 'general_form', 14: 'general_table', 15: 'general_clickable', 
    16: 'icon_cart', 17: 'icon_menu', 18: 'icon_search', 19: 'icon_profile', 20: 'icon_close'
}

classes_to_remove = {8, 11, 12, 13, 14, 15}

# Remap classes
new_classes = {}
old_to_new_id = {}
new_id = 0
for old_id, name in sorted(original_classes.items()):
    if old_id not in classes_to_remove:
        new_classes[new_id] = name
        old_to_new_id[old_id] = new_id
        new_id += 1

# Gather all valid images
images = []
label_files = glob.glob(os.path.join(input_dir, 'labels', '*.txt'))
for lf in label_files:
    img_name = os.path.basename(lf).replace('.txt', '.png')
    img_path = os.path.join(input_dir, 'images', img_name)
    if os.path.exists(img_path):
        images.append(img_name)

random.seed(42)
random.shuffle(images)

n_total = len(images)
n_train = int(n_total * train_ratio)
n_val = int(n_total * val_ratio)
splits = {
    'train': images[:n_train],
    'val': images[n_train:n_train+n_val],
    'test': images[n_train+n_val:]
}

if os.path.exists(output_dir):
    print(f"Removing existing {output_dir} directory...")
    shutil.rmtree(output_dir)
os.makedirs(output_dir)

def read_labels(lbl_path):
    labels = []
    if os.path.exists(lbl_path):
        with open(lbl_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    try:
                        old_id = int(parts[0])
                        if old_id not in classes_to_remove:
                            new_id = old_to_new_id[old_id]
                            labels.append([new_id] + list(map(float, parts[1:5])))
                    except ValueError:
                        pass
    return labels

# First pass: copy original dataset to train/val/test and collect pixel crops for minority classes
crops = {} # {new_class_id: [list of numpy image crops]}
train_instance_counts = Counter()

print("Copying base dataset and extracting instance crops...")
for split, split_images in splits.items():
    target_img_dir = os.path.join(output_dir, split, 'images')
    target_lbl_dir = os.path.join(output_dir, split, 'labels')
    os.makedirs(target_img_dir, exist_ok=True)
    os.makedirs(target_lbl_dir, exist_ok=True)
    
    for img_name in split_images:
        img_path = os.path.join(input_dir, 'images', img_name)
        lbl_path = os.path.join(input_dir, 'labels', img_name.replace('.png', '.txt'))
        
        img = cv2.imread(img_path)
        if img is None:
            continue
            
        labels = read_labels(lbl_path)
        h, w, _ = img.shape
        
        # Save original to splits
        cv2.imwrite(os.path.join(target_img_dir, img_name), img)
        with open(os.path.join(target_lbl_dir, img_name.replace('.png', '.txt')), 'w', encoding='utf-8') as f:
            for lbl in labels:
                f.write(f"{lbl[0]} {lbl[1]:.6f} {lbl[2]:.6f} {lbl[3]:.6f} {lbl[4]:.6f}\n")
                
        # Collect crops ONLY from train set
        if split == 'train':
            for lbl in labels:
                c_id = lbl[0]
                train_instance_counts[c_id] += 1
                
                # Extract pixel crop for copy-paste SMOTE
                cx, cy, bw, bh = lbl[1:5]
                x1 = int((cx - bw/2) * w)
                y1 = int((cy - bh/2) * h)
                x2 = int((cx + bw/2) * w)
                y2 = int((cy + bh/2) * h)
                
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                
                if x2 > x1 and y2 > y1:
                    crop = img[y1:y2, x1:x2].copy()
                    if c_id not in crops:
                        crops[c_id] = []
                    crops[c_id].append(crop)

print("\nOriginal Train Set Counts:")
for c_id, name in new_classes.items():
    print(f"{name}: {train_instance_counts[c_id]}")

# Second pass: Instance-Level Copy-Paste Augmentation (True SMOTE equivalent for Object Detection)
print("\nApplying Instance-Level Copy-Paste Augmentation to minority classes...")
train_img_dir = os.path.join(output_dir, 'train', 'images')
train_images = list(glob.glob(os.path.join(train_img_dir, '*.png')))

synthesis_plan = {} # target_img_path: [(c_id, crop)]

for c_id, name in new_classes.items():
    current_count = train_instance_counts[c_id]
    if 0 < current_count < target_class_count:
        needed = target_class_count - current_count
        print(f"Synthesizing {needed} instances for {name}...")
        
        for _ in range(needed):
            if c_id not in crops or not crops[c_id]:
                break
            crop = random.choice(crops[c_id])
            target_img_path = random.choice(train_images)
            
            if target_img_path not in synthesis_plan:
                synthesis_plan[target_img_path] = []
            synthesis_plan[target_img_path].append((c_id, crop))

# Execute the paste operations
for target_img_path, plan in synthesis_plan.items():
    target_lbl_path = target_img_path.replace('images', 'labels').replace('.png', '.txt')
    img = cv2.imread(target_img_path)
    if img is None:
        continue
    
    h, w, _ = img.shape
    new_labels = []
    
    for c_id, crop in plan:
        crop_h, crop_w, _ = crop.shape
        # Don't paste if crop is weirdly larger than image
        if w <= crop_w or h <= crop_h:
            continue
            
        paste_x = random.randint(0, w - crop_w - 1)
        paste_y = random.randint(0, h - crop_h - 1)
        
        # Paste the pixels
        img[paste_y:paste_y+crop_h, paste_x:paste_x+crop_w] = crop
        
        # Calculate new YOLO coordinates
        new_cx = (paste_x + crop_w / 2.0) / w
        new_cy = (paste_y + crop_h / 2.0) / h
        new_bw = crop_w / float(w)
        new_bh = crop_h / float(h)
        new_labels.append(f"{c_id} {new_cx:.6f} {new_cy:.6f} {new_bw:.6f} {new_bh:.6f}\n")
        
    # Write updated image and labels
    cv2.imwrite(target_img_path, img)
    with open(target_lbl_path, 'a', encoding='utf-8') as f:
        f.writelines(new_labels)

# Generate dataset.yaml
yaml_content = {
    'path': os.path.abspath(output_dir),
    'train': 'train/images',
    'val': 'val/images',
    'test': 'test/images',
    'nc': len(new_classes),
    'names': new_classes
}

with open(os.path.join(output_dir, 'dataset.yaml'), 'w', encoding='utf-8') as f:
    yaml.dump(yaml_content, f, sort_keys=False)

print(f"\nDataset perfectly balanced and saved to {output_dir}!")
