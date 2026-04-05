import cv2
import easyocr
import os
from ultralytics import YOLO
from auditor import UIAuditor

def run_ui_audit(
    image_path, 
    cls_weights_path="runs/classify/website_classifier/weights/best.pt",
    det_weights_path="runs/detect/ui_detector/weights/best.pt" # Double check your ui_detector folder number!
):
    print(f"\n🚀 Starting Full AI UI Audit for: {image_path}")
    
    # --- MODEL 1: CLASSIFY THE WEBSITE ---
    print("🧠 Step 1: Loading Website Classifier...")
    if not os.path.exists(cls_weights_path):
        print("⚠️ Classifier weights not found. Defaulting to 'e_commerce'.")
        predicted_categories = ["e_commerce"]
        confidence = 100.0
    else:
        cls_model = YOLO(cls_weights_path)
        cls_results = cls_model(image_path, verbose=False)
        
        # Extract the Top 3 predictions to give the Auditor a safety net
        top3_indices = cls_results[0].probs.top5[:3] 
        predicted_categories = [cls_results[0].names[i] for i in top3_indices]
        confidence = cls_results[0].probs.top1conf.item() * 100
        
        print(f"📂 Top 3 Category Guesses: {predicted_categories} (Top-1 Conf: {confidence:.1f}%)")

    # --- MODEL 2 & 3: DETECTION AND OCR ---
    print("\n🧠 Step 2: Loading UI Detector & OCR...")
    try:
        det_model = YOLO(det_weights_path)
    except Exception as e:
        print(f"❌ Error loading YOLO detection weights: {e}")
        return

    # gpu=False ensures it runs smoothly on your CPU
    reader = easyocr.Reader(['en'], gpu=False) 
    auditor = UIAuditor()
    
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Error: Could not read image at {image_path}")
        return

    print("\n🔍 Scanning image for UI elements...")
    det_results = det_model(image_path, verbose=False)
    
    anomalies_found = []
    
    # --- LOOP THROUGH DETECTIONS ---
    for box in det_results[0].boxes:
        x_center = float(box.xywhn[0][0])
        class_id = int(box.cls[0])
        yolo_class = det_model.names[class_id]
        ocr_text = ""
        
        # OCR for generic shapes
        if "general_" in yolo_class:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cropped_img = img[y1:y2, x1:x2]
            
            if cropped_img.size != 0:
                ocr_results = reader.readtext(cropped_img, detail=0)
                ocr_text = " ".join(ocr_results).lower().strip()
        
        # --- AUDIT (Passing the Top 3 List) ---
        audit_result = auditor.audit_element(
            predicted_categories=predicted_categories,
            yolo_class=yolo_class,
            x_center=x_center,
            ocr_text=ocr_text,
            confidence=confidence
        )
        
        display_text = f"[{ocr_text}]" if ocr_text else "[Visual Icon]"
        report_line = f"- Detected '{yolo_class}' {display_text} -> {audit_result}"
        
        # Collect severe anomalies for the final summary
        if "🚨" in audit_result or "❌" in audit_result:
            anomalies_found.append(report_line)
        else:
            print(report_line)

    # --- FINAL REPORT ---
    print("\n" + "="*60)
    print("📊 FINAL UX AUDIT REPORT")
    print("="*60)
    if not anomalies_found:
        print("🎉 No severe UX structural anomalies detected! Great design.")
    else:
        print(f"⚠️ Found {len(anomalies_found)} Severe UX Anomalies:\n")
        for anomaly in anomalies_found:
            print(anomaly)
    print("="*60)


if __name__ == "__main__":
    test_folder = "test_images"
    
    if not os.path.exists(test_folder):
        print(f"❌ Error: The folder '{test_folder}' was not found.")
    else:
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp')
        image_files = [f for f in os.listdir(test_folder) if f.lower().endswith(valid_extensions)]
        
        if not image_files:
            print(f"⚠️ No images found in '{test_folder}'.")
        else:
            print(f"🚀 Found {len(image_files)} images in '{test_folder}'. Starting batch audit...\n")
            
            for filename in image_files:
                image_path = os.path.join(test_folder, filename)
                
                print("\n\n" + "#"*70)
                print(f"🆕 AUDITING NEW IMAGE: {filename}")
                print("#"*70)
                
                run_ui_audit(image_path)
                
            print("\n✅ Batch audit complete!")