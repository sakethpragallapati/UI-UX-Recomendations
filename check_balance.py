import os
import glob
from collections import Counter
import yaml

base_dir = r"d:\Acadamics\CBIT\UI UX Internship\UI Elements detection\UI Replication (but better)"
dataset_yaml = os.path.join(base_dir, "yolo_formatted_v2", "dataset.yaml")

with open(dataset_yaml, 'r', encoding='utf-8') as f:
    data = yaml.safe_load(f)
    names = data.get('names', {})

print("Class Names:")
print(names)
print("---")

def count_labels(label_dirs):
    counts = Counter()
    for d in label_dirs:
        for f in glob.glob(os.path.join(d, '*.txt')):
            with open(f, 'r', encoding='utf-8') as file:
                for line in file:
                    parts = line.strip().split()
                    if parts:
                        try:
                            counts[int(parts[0])] += 1
                        except ValueError:
                            pass
    return counts

# Formatted v2
formatted_dirs = [
    os.path.join(base_dir, "yolo_formatted_v2", "train", "labels"),
    os.path.join(base_dir, "yolo_formatted_v2", "val", "labels"),
    os.path.join(base_dir, "yolo_formatted_v2", "test", "labels")
]
formatted_counts = count_labels(formatted_dirs)

print("yolo_formatted_v2 (Balanced & Re-Formatted) counts:")
for i in sorted(names.keys()):
    print(f"{i} ({names.get(i, 'Unknown')}): {formatted_counts.get(i, 0)}")

