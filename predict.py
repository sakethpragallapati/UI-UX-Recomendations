import joblib
import numpy as np
from ultralytics import YOLO

# ---------------- CONFIG ----------------
MODEL_PATH = "layout_classifier.pkl"
YOLO_WEIGHTS = "runs/detect/ui_detector/weights/best.pt"
IMAGE_PATH = "test_images/flipkart.png"

# Same classes used during training
UI_CLASSES = [
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
    "icon_close"
]

# ---------------- LOAD MODELS ----------------
print("🚀 Loading models...")
clf, le = joblib.load(MODEL_PATH)
yolo_model = YOLO(YOLO_WEIGHTS)

# ---------------- FEATURE EXTRACTION ----------------
def extract_features(image_path):
    results = yolo_model(image_path, verbose=False)

    features = {}
    for cls in UI_CLASSES:
        features[f"{cls}_count"] = 0
        features[f"{cls}_avg_x"] = 0
        features[f"{cls}_avg_y"] = 0
        features[f"{cls}_avg_w"] = 0
        features[f"{cls}_avg_h"] = 0

    temp_storage = {cls: [] for cls in UI_CLASSES}

    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        cls_name = yolo_model.names[cls_id]

        if cls_name not in UI_CLASSES:
            continue

        x, y, w, h = box.xywhn[0].tolist()
        temp_storage[cls_name].append((x, y, w, h))

    for cls in UI_CLASSES:
        elems = temp_storage[cls]
        if len(elems) > 0:
            elems = np.array(elems)
            features[f"{cls}_count"] = len(elems)
            features[f"{cls}_avg_x"] = elems[:, 0].mean()
            features[f"{cls}_avg_y"] = elems[:, 1].mean()
            features[f"{cls}_avg_w"] = elems[:, 2].mean()
            features[f"{cls}_avg_h"] = elems[:, 3].mean()

    return list(features.values())

# ---------------- PREDICTION ----------------
print(f"\n🔍 Predicting for: {IMAGE_PATH}")

features = extract_features(IMAGE_PATH)

if sum(features) == 0:
    print("⚠️ Warning: No UI elements detected. Prediction may be unreliable.")

pred = clf.predict([features])
category = le.inverse_transform(pred)[0]

print(f"\n🎯 Predicted Website Category: {category}")