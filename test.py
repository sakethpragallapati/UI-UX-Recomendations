import os
import cv2
import numpy as np
from ultralytics import YOLO
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from tqdm import tqdm
import joblib

# ---------------- CONFIG ----------------
DATASET_PATH = "website_dataset/train"
YOLO_WEIGHTS = "runs/detect/ui_detector/weights/best.pt"
MODEL_SAVE_PATH = "layout_classifier.pkl"

# UI classes you expect from YOLO
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
# ---------------- LOAD YOLO ----------------
print("🚀 Loading YOLO model...")
yolo_model = YOLO(YOLO_WEIGHTS)

# ---------------- FEATURE EXTRACTION ----------------
def extract_features(image_path):
    results = yolo_model(image_path, verbose=False)
    
    # Initialize feature dict
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

    # Aggregate
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

# ---------------- BUILD DATASET ----------------
X = []
y = []

print("📦 Building dataset...")

class_labels = [
    label for label in os.listdir(DATASET_PATH)
    if os.path.isdir(os.path.join(DATASET_PATH, label))
]

for label in tqdm(class_labels, desc="Classes", unit="class"):
    class_path = os.path.join(DATASET_PATH, label)
 
    print(f"Processing class: {label}")

    img_names = os.listdir(class_path)

    for img_name in tqdm(img_names, desc=label, unit="img", leave=False):
        img_path = os.path.join(class_path, img_name)

        try:
            features = extract_features(img_path)
            X.append(features)
            y.append(label)
        except Exception as e:
            print(f"Skipping {img_path}: {e}")

X = np.array(X)

# ---------------- ENCODE LABELS ----------------
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# ---------------- TRAIN/TEST SPLIT ----------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y_encoded, test_size=0.2, random_state=42
)

# ---------------- TRAIN MODEL ----------------
print("🧠 Training Random Forest...")
clf = RandomForestClassifier(
    n_estimators=200,
    max_depth=10,
    random_state=42
)

clf.fit(X_train, y_train)

# ---------------- EVALUATE ----------------
y_pred = clf.predict(X_test)

print("\n📊 Classification Report:")
print(classification_report(
    y_test,
    y_pred,
    labels=np.arange(len(le.classes_)),
    target_names=le.classes_,
    zero_division=0
))

# ---------------- SAVE MODEL ----------------
joblib.dump((clf, le), MODEL_SAVE_PATH)

print(f"\n✅ Model saved at: {MODEL_SAVE_PATH}")
