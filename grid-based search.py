import requests
import pandas as pd
import time
from dotenv import dotenv_values

config = dotenv_values(".env")
# Google API Key
API_KEY = config["API_KEY"]

# 定義範圍：台北與新北
bounds = {
    "north": 25.188,  # 北邊界
    "south": 24.951,  # 南邊界
    "east": 121.665,  # 東邊界
    "west": 121.380,  # 西邊界
}


radius = 500  # 每次查詢的半徑 (單位: 公尺)
PLACES_API_URL = config["PLACES_API_URL"]

# 要查詢的地點類型
place_types = [
    "art_gallery", "tourist_attraction", "school", "market", "store", "library", "park", "gym", "night_club"
]

# 儲存結果
results = []

step = 0.01  
grid = []
lat = bounds["south"]
while lat <= bounds["north"]:
    lng = bounds["west"]
    while lng <= bounds["east"]:
        grid.append({"lat": lat, "lng": lng})
        lng += step
    lat += step

# 查詢單個網格點，處理分頁
def fetch_places(location, place_type):
    next_page_token = None
    while True:
        params = {
            "location": f"{location['lat']},{location['lng']}",
            "radius": radius,
            "type": place_type,
            "key": API_KEY,
        }
        if next_page_token:
            params["pagetoken"] = next_page_token

        response = requests.get(PLACES_API_URL, params=params)
        data = response.json()

        # 儲存結果
        for place in data.get("results", []):
            results.append({
                "名稱": place.get("name"),
                "地址": place.get("vicinity"),
                "評分": place.get("rating"),
                "評論數": place.get("user_ratings_total"),
                "Place ID": place.get("place_id"),
                "類型": place_type,
                "經度": place["geometry"]["location"]["lng"],
                "緯度": place["geometry"]["location"]["lat"],
            })

        # 檢查是否有下一頁
        next_page_token = data.get("next_page_token")
        if not next_page_token:
            break

        # 分頁查詢需要延遲
        time.sleep(2)

# 查詢所有網格點和類型
for place_type in place_types:
    for i, loc in enumerate(grid):
        print(f"正在查詢類型 {place_type}，網格點 {i + 1}/{len(grid)}: {loc}")
        fetch_places(loc, place_type)

# 去重處理
df = pd.DataFrame(results).drop_duplicates(subset=["Place ID"])

# 將結果輸出為 Excel
df.to_excel("完整_台北_新北_地點清單.xlsx", index=False)
print("資料已儲存至 完整_台北_新北_地點清單.xlsx")
