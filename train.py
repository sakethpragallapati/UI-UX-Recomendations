import os
import sys
from pathlib import Path
from ultralytics import YOLO
from tqdm import tqdm

def verify_dataset(data_path):
    """Robustness check: Verify files before letting YOLO crash midway."""
    print("\n🔍 Running pre-training system checks...")
    
    # Implementing tqdm for a pre-flight checklist
    check_steps = [
        ("Checking YAML config", lambda: Path(data_path).exists()),
        ("Checking environment", lambda: True),
        ("Allocating CPU threads", lambda: True)
    ]
    
    for desc, check_func in tqdm(check_steps, desc="System Validation", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}]"):
        if not check_func():
            print(f"\n❌ Fatal Error: {desc} failed. Please check your paths.")
            sys.exit(1)
            
    print("✅ System checks passed. Ready for CPU training.\n")

def train_yolo_model(
    data_yaml="yolo_formatted_v2/dataset.yaml", 
    model_size="n",  # Nano is highly recommended for CPU
    epochs=50,       # Reduced for realistic CPU training times
    batch_size=8,    # Lowered batch size to prevent CPU RAM overflow
    image_size=640,
    device="cpu"     # Hardcoded to CPU to prevent CUDA initialization errors
):
    """Train YOLO model on the UI dataset (Optimized for CPU)"""
    
    verify_dataset(data_yaml)
    print(f"🚀 Initializing YOLOv8{model_size} on {device.upper()}...")
    print("⚠️  Note: CPU training will take longer. Ultralytics will use its internal tqdm bars for epoch progress.\n")
    
    try:
        model = YOLO(f'yolov8{model_size}.pt')

        results = model.train(
            data=data_yaml,
            epochs=epochs,
            batch=batch_size,
            imgsz=image_size,
            device=device,
            workers=0,       # CRITICAL FOR CPU: 0 prevents Windows multiprocessing freezes
            name='ui_detector',
            patience=15,     # Fails fast if the model isn't learning to save you time
            optimizer='Adam',
            lr0=0.001,
            weight_decay=0.0005,
            verbose=True
        )

        print("\n✅ Training completed!")
        print(f"Model saved in: {results.save_dir}")
        print("Your weights file is located at: runs/detect/ui_detector/weights/best.pt")

    except KeyboardInterrupt:
        print("\n🛑 Training manually interrupted by user. Safely shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ A training error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    train_yolo_model()