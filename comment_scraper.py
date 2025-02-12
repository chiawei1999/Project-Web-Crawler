import os
import json
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import psutil
import re

# Clean up residual Chrome and Chromedriver processes
def kill_chrome_processes():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] in ['chrome', 'chromedriver']:
            proc.kill()
    print("Cleaned up residual Chrome and Chromedriver processes")

# Initialize Selenium WebDriver
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--incognito")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return webdriver.Chrome(options=options)

# Add random delay to avoid detection
def random_delay(min_delay=3, max_delay=5):
    delay = random.uniform(min_delay, max_delay)
    print(f"Random delay {delay:.2f} seconds")
    time.sleep(delay)

# Wait for element to be present
def wait_for_element(driver, xpath, timeout=30):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))

# Main scraping function
def scrape_reviews(driver, place_id, folder_name):
    url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
    print(f"Accessing URL: {url}")

    try:
        driver.get(url)
        random_delay(7, 10)

        # Get location name
        try:
            location_name_element = wait_for_element(driver, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[1]/h1')
            location_name = location_name_element.text.strip()
            location_name = re.sub(r'[\\/:*?"<>|]', '_', location_name)
            print(f"Location name extracted: {location_name}")
        except Exception as e:
            print("Failed to get location name, using default name", e)
            location_name = place_id

        # Create output folder if not exists
        file_path = os.path.join(folder_name, f"{place_id}.json")
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

        # Click reviews button
        reviews_button = wait_for_element(driver, "//button[.//div[contains(text(), '評論')]]")
        reviews_button.click()
        random_delay()

        # Scroll reviews area
        scrollable_div = wait_for_element(driver, '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]')
        previous_reviews_count = 0

        # Keep scrolling until no more reviews
        while True:
            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable_div)
            random_delay()

            reviews = driver.find_elements(By.XPATH, "//div[contains(@class, 'jftiEf')]//span[@class='wiI7pd']")
            review_dates = driver.find_elements(By.XPATH, "//div[contains(@class, 'jftiEf')]//span[@class='rsqaWe']")
            if len(reviews) == previous_reviews_count:
                break
            previous_reviews_count = len(reviews)

        # Collect reviews and dates
        reviews_dict = {}
        for i, (review, review_date) in enumerate(zip(reviews, review_dates), 1):
            review_text = review.text.strip()
            review_date_text = review_date.text.strip()
            reviews_dict[f"評論 {i}"] = {"內容": review_text, "日期": review_date_text}

        # Save to JSON file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(reviews_dict, f, ensure_ascii=False, indent=4)
        print(f"Reviews saved to {file_path}")
        return True

    except Exception as e:
        print(f"Scraping failed: {place_id}, Error: {e}")
        return False

if __name__ == "__main__":
    # Get script directory path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Input file path - can be modified based on data type
    input_file = os.path.join(script_dir, "完整_台北_新北_地點清單.xlsx")
    
    # Folder name parameter - can be modified based on data type
    folder_name = "景點評論爬蟲"  # or "餐廳評論爬蟲"

    # Clean residual processes
    kill_chrome_processes()

    # Read location list
    df = pd.read_excel(input_file)

    # Check existing files
    if os.path.exists(folder_name):
        crawled_files = {file.replace(".json", "") for file in os.listdir(folder_name) if file.endswith(".json")}
    else:
        crawled_files = set()

    # Filter list to keep only non-scraped Place IDs
    df = df[~df['Place ID'].isin(crawled_files)]
    print(f"Remaining locations to scrape: {len(df)}")

    # Initialize WebDriver and start scraping
    driver = init_driver()
    try:
        for index, row in df.iterrows():
            place_id = row['Place ID']
            print(f"Start scraping Place ID: {place_id}")
            success = scrape_reviews(driver, place_id, folder_name)
            if success:
                print(f"Successfully scraped Place ID: {place_id}")
    finally:
        driver.quit()