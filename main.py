import cv2
import easyocr
from ultralytics import YOLO
from auditor import UIAuditor

def run_ui_audit(image_path, predicted_category, yolo_weights_path="runs/detect/ui_detector/weights/best.pt"):
    print(f"\n🚀 Starting AI UI Audit for: {image_path}")
    print(f"📂 Website Category: {predicted_category}")
    
    # 1. Initialize AI Models & Logic Engine
    print("Loading AI Models (YOLO & OCR)...")
    try:
        model = YOLO(yolo_weights_path)
    except Exception as e:
        print(f"Error loading YOLO weights. Did you run train.py first? Details: {e}")
        return

    reader = easyocr.Reader(['en'], gpu=False) # Set gpu=True if you have an NVIDIA GPU
    auditor = UIAuditor()
    
    # Load image with OpenCV for cropping later
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not read image at {image_path}")
        return

    # 2. Run YOLO Inference
    print("\n🔍 Scanning image for UI elements...")
    results = model(image_path, verbose=False)
    
    anomalies_found = []
    
    # 3. Loop through every detected bounding box
    for box in results[0].boxes:
        # Get normalized center X coordinate (0.0 to 1.0)
        x_center = float(box.xywhn[0][0])
        
        # Get predicted YOLO class
        class_id = int(box.cls[0])
        yolo_class = model.names[class_id]
        
        ocr_text = ""
        
        # 4. PATH B: If the shape is generic, we must read the text
        if "general_" in yolo_class:
            # Extract exact pixel coordinates for cropping
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # Crop the bounding box out of the original image
            cropped_img = img[y1:y2, x1:x2]
            
            # Prevent OCR from crashing on tiny 0-pixel boxes
            if cropped_img.size != 0:
                # Read the text (detail=0 returns just the string, not the bounding boxes)
                ocr_results = reader.readtext(cropped_img, detail=0)
                ocr_text = " ".join(ocr_results).lower()
        
        # 5. Feed extracted data to the Auditor
        audit_result = auditor.audit_element(
            predicted_category=predicted_category,
            yolo_class=yolo_class,
            x_center=x_center,
            ocr_text=ocr_text
        )
        
        # Format the output for the terminal report
        display_text = f"[{ocr_text}]" if ocr_text else "[Visual Icon]"
        report_line = f"- Detected '{yolo_class}' {display_text} -> {audit_result}"
        
        if "🚨" in audit_result or "❌" in audit_result:
            anomalies_found.append(report_line)
        else:
            print(report_line)

    # 6. Print Final Report
    print("\n" + "="*50)
    print("📊 FINAL UX AUDIT REPORT")
    print("="*50)
    if not anomalies_found:
        print("🎉 No severe UX structural anomalies detected! Great design.")
    else:
        print(f"⚠️ Found {len(anomalies_found)} Severe UX Anomalies:\n")
        for anomaly in anomalies_found:
            print(anomaly)
    print("="*50)

if __name__ == "__main__":
    # Example Usage: Replace with a real screenshot from your test set!
    TEST_IMAGE = "test_images/sample_homepage.png" 
    CATEGORY = "e_commerce" # This would eventually come from your Classifier Model
    
    # run_ui_audit(TEST_IMAGE, CATEGORY)
    print("Main script ready. Update TEST_IMAGE path and uncomment the run function to test.")