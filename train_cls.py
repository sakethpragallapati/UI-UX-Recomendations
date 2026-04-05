import os
import sys
from pathlib import Path
from ultralytics import YOLO
from tqdm import tqdm

def train_website_classifier(
    data_dir="website_dataset", # Path to the folder created by scraper_classify.py
    model_size="n",             # n=nano (Best for CPU)
    epochs=30,                  
    image_size=224,             # Standard optimal size for classification
    device="cpu"                # Safe CPU execution
):
    print("\n🔍 Verifying Classification Dataset...")
    if not Path(data_dir).exists():
        print(f"❌ Error: Dataset folder '{data_dir}' not found. Run scraper_classify.py first.")
        sys.exit(1)

    print(f"🚀 Initializing YOLOv8{model_size}-cls on {device.upper()}...")
    try:
        # Load the Classification specific base model
        model = YOLO(f'yolov8{model_size}-cls.pt')

        results = model.train(
            data=data_dir,
            epochs=epochs,
            imgsz=image_size,
            device=device,
            workers=0,       # CRITICAL FOR CPU
            name='website_classifier',
            optimizer='Adam',
            lr0=0.001
        )

        print("\n✅ Classification Training completed!")
        print(f"Model saved in: {results.save_dir}")
        print("Your CLASSIFICATION weights file is at: runs/classify/website_classifier/weights/best.pt")

    except KeyboardInterrupt:
        print("\n🛑 Training manually interrupted.")
    except Exception as e:
        print(f"\n❌ A training error occurred: {e}")

if __name__ == "__main__":
    train_website_classifier()