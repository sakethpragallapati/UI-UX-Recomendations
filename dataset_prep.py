import argparse
import json
import random
import shutil
from collections import Counter
from pathlib import Path

import yaml


DEFAULT_CLASS_CAPS = {
    "general_link": 10,
}


def load_classes(classes_path):
    if classes_path.exists():
        with open(classes_path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file.readlines() if line.strip()]

    print("Warning: 'classes.txt' not found. Using fallback 21-class ontology.")
    return [
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
        "general_video",
        "general_iframe",
        "general_form",
        "general_table",
        "general_clickable",
        "icon_cart",
        "icon_menu",
        "icon_search",
        "icon_profile",
        "icon_close",
    ]


def parse_class_caps(raw_caps):
    if not raw_caps:
        return DEFAULT_CLASS_CAPS.copy()

    caps = {}
    for item in raw_caps.split(","):
        item = item.strip()
        if not item:
            continue
        if "=" not in item:
            raise ValueError(f"Invalid class cap '{item}'. Use class_name=count.")

        class_name, count = item.split("=", 1)
        class_name = class_name.strip()
        count = int(count.strip())
        if count < 0:
            raise ValueError(f"Class cap for '{class_name}' must be >= 0.")
        caps[class_name] = count

    return caps


def parse_label_records(label_path, meta_path):
    records = []
    label_lines = []

    if label_path.exists():
        with open(label_path, "r", encoding="utf-8") as file:
            label_lines = [line.strip() for line in file.readlines() if line.strip()]

    meta_payload = None
    meta_elements = []
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as file:
            meta_payload = json.load(file)
            meta_elements = meta_payload.get("elements", [])

    for index, line in enumerate(label_lines):
        parts = line.split()
        if len(parts) != 5:
            continue

        class_id = int(parts[0])
        xc, yc, width, height = map(float, parts[1:])
        meta_element = meta_elements[index] if index < len(meta_elements) else None

        records.append(
            {
                "index": index,
                "line": line,
                "class_id": class_id,
                "width": width,
                "height": height,
                "area": width * height,
                "meta_element": meta_element,
                "keep": True,
            }
        )

    meta_aligned = meta_payload is not None and len(meta_elements) == len(label_lines)
    return records, meta_payload, meta_aligned


def score_record(record):
    area_score = record["area"]
    meta_element = record["meta_element"] or {}
    content = meta_element.get("content", {})
    accessibility = meta_element.get("accessibility", {})

    text_bits = [
        content.get("text"),
        content.get("placeholder"),
        content.get("value"),
        content.get("name"),
        accessibility.get("aria_label"),
        accessibility.get("title"),
        accessibility.get("alt_text"),
    ]
    text_length = sum(len((bit or "").strip()) for bit in text_bits)

    # Favor larger and more descriptive elements when we need to trim extras.
    return area_score + min(text_length, 80) * 0.0001


def apply_class_caps(records, classes, class_caps):
    before_counts = Counter(classes[record["class_id"]] for record in records)

    records_by_class = {}
    for record in records:
        class_name = classes[record["class_id"]]
        records_by_class.setdefault(class_name, []).append(record)

    for class_name, max_count in class_caps.items():
        class_records = records_by_class.get(class_name, [])
        if max_count >= len(class_records):
            continue

        ranked = sorted(class_records, key=score_record, reverse=True)
        keep_indexes = {record["index"] for record in ranked[:max_count]}

        for record in class_records:
            if record["index"] not in keep_indexes:
                record["keep"] = False

    kept_records = [record for record in records if record["keep"]]
    after_counts = Counter(classes[record["class_id"]] for record in kept_records)
    return kept_records, before_counts, after_counts


def write_filtered_annotations(target_label_path, target_meta_path, kept_records, meta_payload, meta_aligned):
    with open(target_label_path, "w", encoding="utf-8") as file:
        for record in kept_records:
            file.write(f"{record['line']}\n")

    if meta_payload is None:
        return

    if not meta_aligned:
        print(f"Warning: meta/label count mismatch for '{target_label_path.stem}'. Copying original meta file unchanged.")
        with open(target_meta_path, "w", encoding="utf-8") as file:
            json.dump(meta_payload, file, indent=2)
        return

    filtered_meta = dict(meta_payload)
    filtered_meta["elements"] = [record["meta_element"] for record in kept_records]
    with open(target_meta_path, "w", encoding="utf-8") as file:
        json.dump(filtered_meta, file, indent=2)


def prepare_yolo_dataset(
    input_dir="yolo_dataset",
    output_dir="yolo_formatted",
    train_ratio=0.8,
    val_ratio=0.1,
    class_caps=None,
):
    """
    Takes the raw scraper output, optionally trims overrepresented classes per image,
    shuffles the data, splits it into train/val/test sets, and generates dataset.yaml.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    images_dir = input_path / "images"
    labels_dir = input_path / "labels"

    print("Starting dataset preparation and split...")

    if not images_dir.exists() or not labels_dir.exists():
        print(f"Error: Could not find 'images' or 'labels' folder inside '{input_dir}'.")
        return

    random.seed(42)
    images = list(images_dir.glob("*.png"))

    if not images:
        print(f"Error: No PNG images found in '{images_dir}'.")
        return

    classes = load_classes(input_path / "classes.txt")
    class_caps = class_caps or DEFAULT_CLASS_CAPS.copy()

    print(f"Found {len(images)} images. Shuffling and splitting into train/val/test...")
    print(f"Per-image class caps: {class_caps}")

    random.shuffle(images)

    n_images = len(images)
    n_train = int(n_images * train_ratio)
    n_val = int(n_images * val_ratio)

    splits = {
        "train": images[:n_train],
        "val": images[n_train : n_train + n_val],
        "test": images[n_train + n_val :],
    }

    global_before = Counter()
    global_after = Counter()

    for split_name, split_images in splits.items():
        target_img_dir = output_path / split_name / "images"
        target_label_dir = output_path / split_name / "labels"

        target_img_dir.mkdir(parents=True, exist_ok=True)
        target_label_dir.mkdir(parents=True, exist_ok=True)

        for img_path in split_images:
            shutil.copy2(img_path, target_img_dir / img_path.name)

            label_path = labels_dir / f"{img_path.stem}.txt"
            meta_path = labels_dir / f"{img_path.stem}_meta.json"

            if not label_path.exists():
                print(f"Warning: Missing label file for {img_path.name}")
                continue

            records, meta_payload, meta_aligned = parse_label_records(label_path, meta_path)
            kept_records, before_counts, after_counts = apply_class_caps(records, classes, class_caps)

            global_before.update(before_counts)
            global_after.update(after_counts)

            write_filtered_annotations(
                target_label_dir / label_path.name,
                target_label_dir / meta_path.name,
                kept_records,
                meta_payload,
                meta_aligned,
            )

    yaml_content = {
        "path": str(output_path.absolute()),
        "train": "train/images",
        "val": "val/images",
        "test": "test/images",
        "nc": len(classes),
        "names": {i: name for i, name in enumerate(classes)},
    }

    with open(output_path / "dataset.yaml", "w", encoding="utf-8") as file:
        yaml.dump(yaml_content, file, sort_keys=False)

    print(f"\nDataset successfully prepared in '{output_path}'")
    print("-" * 40)
    print(f"Training images:   {len(splits['train'])}")
    print(f"Validation images: {len(splits['val'])}")
    print(f"Test images:       {len(splits['test'])}")
    print("-" * 40)

    print("\nClass counts before/after filtering:")
    for class_name in classes:
        before = global_before.get(class_name, 0)
        after = global_after.get(class_name, 0)
        if before != after:
            print(f"  {class_name}: {before} -> {after}")

    print("\nReady for YOLO training.")
    print(f"yolo task=detect mode=train data={output_dir}/dataset.yaml model=yolov8n.pt epochs=100 imgsz=640")


def build_arg_parser():
    parser = argparse.ArgumentParser(description="Prepare raw scraper output into YOLO format.")
    parser.add_argument("--input-dir", default="yolo_dataset")
    parser.add_argument("--output-dir", default="yolo_formatted")
    parser.add_argument("--train-ratio", type=float, default=0.8)
    parser.add_argument("--val-ratio", type=float, default=0.1)
    parser.add_argument(
        "--class-caps",
        default="general_link=10",
        help="Comma-separated per-image caps, for example: general_link=10,general_image=12",
    )
    return parser


if __name__ == "__main__":
    args = build_arg_parser().parse_args()
    prepare_yolo_dataset(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        class_caps=parse_class_caps(args.class_caps),
    )
