import os
import json
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import re

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
    time.sleep(delay)

# Wait for element to be present
def wait_for_element(driver, xpath, timeout=20):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.XPATH, xpath)))

# Extract checked items from specific sections
def extract_checked_items_with_log(driver, label):
    try:
        print(f"Detected【{label}】")

        # Locate title area
        title_xpath = f'//h2[contains(text(), "{label}")]'
        title_element = driver.find_element(By.XPATH, title_xpath)
        
        # Locate parent container ul
        ul_element = title_element.find_element(By.XPATH, './following-sibling::ul[contains(@class, "ZQ6we")]')
        
        # Locate all li child elements
        items = ul_element.find_elements(By.XPATH, './/li[contains(@class, "hpLkke")]')

        # Filter elements without checkmark
        checked_items = []
        for item in items:
            if "" in item.text:
                clean_text = item.text.replace("", "").replace("\n", "").strip() #定位打勾元素
                checked_items.append(clean_text)
            else:
                print(f"Not provided: {item.text.replace('', '')}") #不抓取叉叉元素
        
        if checked_items:
            print(f"Confirmed【{label}】: {', '.join(checked_items)}")
            return checked_items
        else:
            print("No checked elements")
            return []
    except Exception:
        print(f"{label} extraction failed")
        return []

# Save progress to JSON file
def save_progress(place_id, pid, progress_file):
    try:
        if os.path.exists(progress_file):
            with open(progress_file, "r", encoding="utf-8") as f:
                crawled_ids = json.load(f)
        else:
            crawled_ids = []

        if place_id not in crawled_ids:
            crawled_ids.append(place_id)
            with open(progress_file, "w", encoding="utf-8") as f:
                json.dump(list(set(crawled_ids)), f, ensure_ascii=False, indent=4)
            print(f"Process {pid} updated main record: {place_id}")
    except Exception as e:
        print(f"Failed to update progress file: {e}")
        # Save to temporary file as backup
        temp_file = f"temp_crawled_detail_{pid}.json"
        try:
            if os.path.exists(temp_file):
                with open(temp_file, "r", encoding="utf-8") as f:
                    temp_ids = json.load(f)
            else:
                temp_ids = []

            if place_id not in temp_ids:
                temp_ids.append(place_id)
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(temp_ids, f, ensure_ascii=False, indent=4)
            print(f"Process {pid} updated temporary record: {place_id}")
        except Exception as e:
            print(f"Failed to update temporary record: {e}")

# Main scraping function
def scrape_store_data(driver, url, place_id):
    driver.get(url)
    random_delay()

    store_data = {
        "店名": "",
        "Place ID": place_id,  
        "評分": "",
        "種類": "",
        "地址": "",
        "開始營業時間": {},
        "平均每人消費": "",
        "電話": "",
        "簡介": "",
        "無障礙程度": [],
        "服務項目": [],
        "產品/服務": [],
        "用餐選擇": [],
        "設施": [],
        "客層族群": [],
        "氛圍": [],
        "付款方式": [],
        "兒童": [],
        "停車場": [],
    }

    try:
        # Extract name
        try:
            name_xpath = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[1]/h1'
            store_name = wait_for_element(driver, name_xpath).text.strip()
            store_data["店名"] = store_name
            print(f"Successfully extracted name: {store_name}")
        except Exception:
            print("Failed to extract name")

        # Extract rating
        try:
            rating_xpath = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[1]/div[2]/span[1]/span[1]'
            rating_element = driver.find_element(By.XPATH, rating_xpath)
            store_data["評分"] = rating_element.text.strip()
            print(f"Successfully extracted rating: {store_data['評分']}")
        except Exception:
            print("Failed to extract rating")

        # Extract type
        try:
            type_xpath = '//button[contains(@class, "DkEaL")]'
            store_type = driver.find_element(By.XPATH, type_xpath).text.strip()
            store_data["種類"] = store_type
            print(f"Successfully extracted type: {store_type}")
        except Exception:
            print("Failed to extract type")

        # Extract address
        try:
            address_xpath = '//button[contains(@aria-label, "地址")]'
            address = driver.find_element(By.XPATH, address_xpath).text.strip()
            address = address.replace("\n", "")
            store_data["地址"] = address
            print(f"Successfully extracted address: {address}")
        except Exception:
            print("Failed to extract address")

        # Extract average cost
        try:
            avg_xpath = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div/div[1]/div[2]/div/div[1]/span/span/span/span[2]/span/span'
            avg_cost = driver.find_element(By.XPATH, avg_xpath).text.strip()
            store_data["平均每人消費"] = avg_cost
            print(f"Successfully extracted average cost: {avg_cost}")
        except Exception:
            print("Failed to extract average cost")

        # Extract business hours
        try:
            hours_button_xpath = '//div[contains(@class, "OqCZI fontBodyMedium WVXvdc")]'
            hours_button = driver.find_element(By.XPATH, hours_button_xpath)
            driver.execute_script("arguments[0].click();", hours_button)
            random_delay()
            
            hours_xpath = '//div[contains(@aria-label, "星期一")]'
            hours_element = driver.find_element(By.XPATH, hours_xpath)
            full_hours = hours_element.get_attribute("aria-label").strip()
            clean_hours = full_hours.replace("隱藏本週營業時間", "").strip()
            
            hours_dict = {}
            for day_hours in clean_hours.split("; "):
                day, time = day_hours.split("、", 1)
                hours_dict[day] = time.replace("到", "~").strip()
            
            store_data["開始營業時間"] = hours_dict
            print(f"Successfully extracted business hours: {hours_dict}")
        except Exception:
            print("Failed to extract business hours")

        # Extract phone number
        try:
            phone_xpath = '//button[contains(@aria-label, "電話號碼")]'
            phone_element = driver.find_element(By.XPATH, phone_xpath)
            phone_number = phone_element.get_attribute("aria-label").split("電話號碼:")[-1].strip()
            store_data["電話"] = phone_number
            print(f"Successfully extracted phone number: {store_data['電話']}")
        except Exception:
            print("Failed to extract phone number")

        # Extract introduction
        try:
            intro_button_xpath = '//button[contains(@aria-label, "簡介")]'
            intro_button = driver.find_element(By.XPATH, intro_button_xpath)
            driver.execute_script("arguments[0].click();", intro_button)
            random_delay()
            
            intro_xpath = '//*[@id="QA0Szd"]/div/div/div[1]/div[2]/div/div[1]/div/div/div[2]/div[2]/p/span/span'
            intro_element = driver.find_element(By.XPATH, intro_xpath)
            intro_text = intro_element.text.strip()
            store_data["簡介"] = intro_text
            print(f"Successfully extracted introduction: {intro_text}")
        except Exception:
            print("No introduction available")

        # Extract checked items from sections
        sections = [
            "無障礙程度", "服務項目", "產品/服務", "用餐選擇", "設施",
            "客層族群", "氛圍", "付款方式", "兒童", "停車場"
        ]

        for label in sections:
            store_data[label] = extract_checked_items_with_log(driver, label)

    except Exception as e:
        print(f"Error while scraping data: {e}")

    return store_data

# Format and save data to JSON
def save_to_json(data, filename):
    def format_single_line_lists(json_str):
        import re
        return re.sub(r'\[\s*(.*?)\s*\]', 
                      lambda m: '[' + ', '.join(i.strip() for i in m.group(1).split(',')) + ']', 
                      json_str, flags=re.DOTALL)

    formatted_json = json.dumps(data, ensure_ascii=False, indent=4)
    formatted_json = format_single_line_lists(formatted_json)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(formatted_json)

if __name__ == "__main__":
    # Get script directory path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Configure parameters
    input_file = os.path.join(script_dir, "完整_台北_新北_地點清單.xlsx")
    output_folder = "location_details"  # Can be modified based on data type
    progress_file = "crawled_locations.json"  # Can be modified based on data type
    
    os.makedirs(output_folder, exist_ok=True)

    # Read Place ID list
    df = pd.read_excel(input_file)
    place_ids = df['Place ID'].dropna().tolist()

    # Get already crawled IDs
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            crawled_ids = json.load(f)
        print(f"Loaded crawled locations, total: {len(crawled_ids)}")
    else:
        crawled_ids = []
        print("No existing record found, starting from scratch")

    # Filter out already crawled Place IDs
    remaining_place_ids = [pid for pid in place_ids if pid not in crawled_ids]
    print(f"Remaining locations to crawl: {len(remaining_place_ids)}")

    driver = init_driver()
    processed_count = 0

    try:
        for place_id in remaining_place_ids:
            print(f"Processing Place ID: {place_id}")
            place_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
            print(f"Accessing URL: {place_url}")

            result = scrape_store_data(driver, place_url, place_id)

            if result['店名']:
                filename = os.path.join(output_folder, f"{place_id}.json")
                save_to_json(result, filename)
                print(f"Data saved to: {filename}")
                save_progress(place_id, os.getpid(), progress_file)
                processed_count += 1
                print(f"Completed scraping location {processed_count}")
            else:
                print(f"Place ID: {place_id} - Failed to extract name, skipping")

            random_delay(3, 6)

    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        print(f"Total processed locations: {processed_count}")
        driver.quit()
        print("Browser closed")