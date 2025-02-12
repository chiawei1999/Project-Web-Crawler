import os
import json
import pandas as pd
from multiprocessing import Process
import sys
import atexit
import glob

# Import functions from the comment scraper
from comment_scraper import kill_chrome_processes, init_driver, scrape_reviews

# Clean up all temporary files
def cleanup_temp_files():
    temp_files = glob.glob("temp_crawled_*.json")
    for temp_file in temp_files:
        try:
            os.remove(temp_file)
            print(f"Cleaned temporary file: {temp_file}")
        except Exception as e:
            print(f"Failed to clean temporary file: {temp_file}, Error: {e}")

# Execute single scraper process
def run_scraper_process(df_chunk, folder_name):
    pid = os.getpid()
    driver = init_driver()
    try:
        for index, row in df_chunk.iterrows():
            place_id = row['Place ID']
            print(f"Process {pid} starts scraping Place ID: {place_id}")

            try:
                # Check if file already exists
                file_path = os.path.join(folder_name, f"{place_id}.json")
                if not os.path.exists(file_path):
                    success = scrape_reviews(driver, place_id, folder_name=folder_name)
                    if success:
                        print(f"Successfully scraped Place ID: {place_id}")
                else:
                    print(f"Place ID {place_id} already exists, skipping")
            except Exception as e:
                print(f"Process {pid} failed to scrape Place ID {place_id}, Error: {e}")
    finally:
        driver.quit()

# Main parallel scraping control function
def parallel_scrape(input_file, num_processes, is_restaurant=True):
    # Register cleanup function
    atexit.register(cleanup_temp_files)

    # Clean up possible residual files
    cleanup_temp_files()

    # Clean up residual processes
    kill_chrome_processes()

    # Read Excel file
    print(f"Reading input file: {input_file}")
    df = pd.read_excel(input_file)

    # Set folder name based on data type
    folder_name = "餐廳評論爬蟲" if is_restaurant else "景點評論爬蟲"

    # Check existing files
    if os.path.exists(folder_name):
        crawled_files = {file.replace(".json", "") for file in os.listdir(folder_name) if file.endswith(".json")}
    else:
        crawled_files = set()
        os.makedirs(folder_name)

    # Filter already scraped Place IDs
    df = df[~df['Place ID'].isin(crawled_files)]
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
        p = Process(target=run_scraper_process, args=(chunk, folder_name))
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