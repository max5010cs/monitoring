import time
import os
import requests
from datetime import datetime
from PIL import Image, ImageChops
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram_photo(photo_path, caption=""):
    try:
        with open(photo_path, "rb") as photo:
            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
                data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
                files={"photo": photo}
            )
        if response.status_code == 200:
            print(f"[📲] Telegram alert sent!")
        else:
            print(f"[⚠️] Telegram error: {response.text}")
    except Exception as e:
        print(f"[❌] Telegram send error: {e}")

def crop_july_area(image_path, crop_path=None):
    image = Image.open(image_path)
    # adjust these coordinates as needed based on your layout
    july_crop = image.crop((180, 480, 1130, 790)) # (left, top, right, bottom)

    if crop_path:
        july_crop.save(crop_path)
        print(f"[🖼️] July crop saved: {crop_path}")

    return july_crop

def images_are_different(img1, img2):
    diff = ImageChops.difference(img1, img2)
    return diff.getbbox() is not None

# selenium setup
options = Options()
options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=options)

# foldersetup
screenshot_dir = "screenshots"
os.makedirs(screenshot_dir, exist_ok=True)

# monitoring
interval = 60  # check every 60 seconds
previous_july_crop = None

print(" Visa Calendar Monitor with July detection")
print(f" Screenshots folder: {screenshot_dir}")
print(f" Refreshing every {interval} seconds\n")

while True:
    try:
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        full_image_path = os.path.join(screenshot_dir, f"calendar_{timestamp}.png")
        crop_image_path = os.path.join(screenshot_dir, f"july_{timestamp}.png")

        print(f"[{now.strftime('%H:%M:%S')}]  Refreshing page...")
        driver.refresh()
        time.sleep(4)

        print(f"[{now.strftime('%H:%M:%S')}]  Clicking calendar field...")
        calendar_field = driver.find_element(By.ID, "appointments_consulate_appointment_date")
        calendar_field.click()
        time.sleep(1.5)

        driver.save_screenshot(full_image_path)
        print(f"[] Full screenshot saved: {full_image_path}")

        # Crop and save July section
        current_crop = crop_july_area(full_image_path, crop_image_path)

        if previous_july_crop is None:
            previous_july_crop = current_crop
            print(f"[] First crop stored, skipping alert.")
        elif images_are_different(previous_july_crop, current_crop):
            print(f"[] July calendar changed — sending alert!")
            send_telegram_photo(crop_image_path, f" JULY updated at {timestamp}")
            previous_july_crop = current_crop
        else:
            print(f"[] July unchanged, skipping Telegram alert...")

        # Countdown
        for i in range(interval, 0, -1):
            print(f"   Next refresh in {i} sec...", end="\r")
            time.sleep(1)

    except Exception as e:
        print(f"[] Error occurred: {e}")
        print(" Retrying in 60 seconds...\n")
        time.sleep(60)

