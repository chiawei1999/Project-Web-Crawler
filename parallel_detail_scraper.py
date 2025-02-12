import os
import json
import pandas as pd
from multiprocessing import Process
import re
import atexit
import glob
from multi_element_scraper import init_driver, scrape_store_data, save_to_json

# Clean up all temporary files
def cleanup_temp_files():
    temp_files = glob.glob("temp_crawled_detail_*.json")
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
            print(f"Cleaned temporary file: {temp_file}")
        except Exception as e:
            print(f"Failed to clean temporary file: {temp_file}, Error: {e}")

# Save progress to main record file
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

# Execute single scraper process
def run_scraper_process(df_chunk, output_folder, progress_file):
    pid = os.getpid()
    driver = init_driver()

    try:
        for index, row in df_chunk.iterrows():
            place_id = row['Place ID']
            print(f"Process {pid} starts scraping Place ID: {place_id}")

            try:
                place_url = f"https://www.google.com/maps/place/?q=place_id:{place_id}"
                print(f"Process {pid} accessing URL: {place_url}")

                result = scrape_store_data(driver, place_url, place_id)

                if result['店名']:
                    valid_filename = re.sub(r'[\\/*?:"<>|]', "", place_id)[:100]
                    filename = os.path.join(output_folder, f"{valid_filename}.json")
                    save_to_json(result, filename)
                    print(f"Process {pid} data saved to: {filename}")
                    save_progress(place_id, pid, progress_file)
                else:
                    print(f"Process {pid} Place ID: {place_id} failed to extract name, skipping")

            except Exception as e:
                print(f"Process {pid} failed to scrape Place ID {place_id}, Error: {e}")
    finally:
        driver.quit()
        print(f"Process {pid} browser closed")

# Main parallel scraping control function
def parallel_scrape(input_file, num_processes, is_restaurant=True):
    # Register cleanup function
    atexit.register(cleanup_temp_files)

    # Clean up possible residual files
    cleanup_temp_files()

    # Read Excel file
    print(f"Reading input file: {input_file}")
    df = pd.read_excel(input_file)

    # Set folder and progress file names based on data type
    output_folder = "餐廳詳細資訊" if is_restaurant else "景點詳細資訊"
    progress_file = "爬過的餐廳ID.json" if is_restaurant else "爬過的景點ID.json"
    os.makedirs(output_folder, exist_ok=True)

    # Read crawled Place IDs
    if os.path.exists(progress_file):
        with open(progress_file, "r", encoding="utf-8") as f:
            crawled_ids = json.load(f)
        print(f"Loaded crawled IDs, total: {len(crawled_ids)}")
    else:
        crawled_ids = []
        print("No existing record found, starting from scratch")

    # Filter already scraped Place IDs
    df = df[~df['Place ID'].isin(crawled_ids)]
    print(f"Remaining locations to scrape: {len(df)}")

    if len(df) == 0:
        print("No locations to scrape, program ends")
        return

    # Split data into chunks
    chunk_size = max(1, len(df) // num_processes)
    chunks = [df[i:i + chunk_size] for i in range(0, len(df), chunk_size)]

    # Create and start processes
    processes = []
    for chunk in chunks:
        p = Process(target=run_scraper_process, args=(chunk, output_folder, progress_file))
        processes.append(p)
        p.start()

    # Wait for all processes to complete
    for p in processes:
        p.join()

    print("All scraping processes completed!")

if __name__ == "__main__":
    # Get script directory path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Configure input file and process count
    input_file = os.path.join(script_dir, "完整_台北_新北_地點清單.xlsx")
    num_processes = 6
    is_restaurant = True  # Set to False for attractions

    print(f"Starting parallel scraping")
    print(f"Input file: {input_file}")
    print(f"Number of processes: {num_processes}")
    print(f"Data type: {'Restaurant' if is_restaurant else 'Attraction'}")

    parallel_scrape(input_file, num_processes, is_restaurant)