import requests
import json
import os
import sys
import time

# Add script_dir
script_dir = os.path.dirname(os.path.abspath(__file__))

# Load item names from all_items_filtered_unique.json (excludes potions, enchanted books, suspicious stews)
with open(os.path.join(script_dir, "all_items_filtered_unique.txt"), "r") as f:
    minecraft_items = [line.strip() for line in f if line.strip()]
sys.path.append(os.path.join(script_dir, 'libs'))

def generate_request_list():
    """Generate and save a list of all requests that will be made"""
    request_list = []
    processed_combinations = set()

    # Combine every item with every other item (including itself)
    for i, item1 in enumerate(minecraft_items):
        for j, item2 in enumerate(minecraft_items):
            # Skip if we've already processed this combination (order doesn't matter)
            combination_key = tuple(sorted([item1, item2]))
            if combination_key in processed_combinations:
                continue

            processed_combinations.add(combination_key)
            combination = f"{item1} + {item2}"

            request_list.append({
                "combination": combination,
                "item1": item1,
                "item2": item2
            })

        # Progress update every 100 items
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{len(minecraft_items)} items...")

    # Save request list
    output_file = os.path.join(script_dir, "request_list.json")
    with open(output_file, "w") as f:
        json.dump(request_list, f, indent=4)

    print(f"\nRequest list saved to request_list.json")
    print(f"Total unique combinations: {len(request_list)}")
    print(f"Formula: n*(n+1)/2 where n={len(minecraft_items)}")
    print(f"Expected: {len(minecraft_items) * (len(minecraft_items) + 1) // 2}")
    return request_list

def execute_requests(limit=None):
    """Execute the requests from the saved request list"""
    request_list_file = os.path.join(script_dir, "request_list.json")

    if not os.path.exists(request_list_file):
        print("Error: request_list.json not found. Run generate_request_list() first.")
        return

    with open(request_list_file, "r") as f:
        request_list = json.load(f)

    # If limit is specified, only process that many requests
    if limit:
        request_list = request_list[:limit]
        print(f"Limited to first {limit} requests for testing")

    start_time = time.time()

    for i, request_info in enumerate(request_list):
        combination = request_info["combination"]

        try:
            # Send request to /gen (server handles saving to items.json)
            response = requests.post("http://localhost:17707/gen", json={"recipe": combination}, timeout=30)
            if response.status_code != 200:
                print(f"Error for {combination}: {response.status_code}")
                continue

            data = response.json()
            new_item = data.get("item", "Unknown")

            # Now get icon
            description = data.get("description", "")
            color = data.get("color", "gray")
            icon_response = requests.get("http://localhost:17707/img", params={"itemDescription": f"{new_item} - {description}", "itemColor": color}, timeout=30)
            if icon_response.status_code == 200:
                icon_data = icon_response.json()
                icon_base64 = icon_data.get("image", "")
            else:
                icon_base64 = ""
                print(f"Icon error for {new_item}")

            # Progress update every 10 requests
            if (i + 1) % 10 == 0:
                elapsed = time.time() - start_time
                rate = (i + 1) / elapsed  # requests per second
                remaining = len(request_list) - (i + 1)
                eta_seconds = remaining / rate if rate > 0 else 0

                print(f"[{i+1}/{len(request_list)}] Generated: {combination} -> {new_item}")
                print(f"  Rate: {rate:.2f} req/sec | ETA: {eta_seconds/3600:.2f} hours ({eta_seconds/60:.1f} minutes, {eta_seconds:.1f} seconds) | Elapsed: {elapsed/60:.1f} minutes")
            else:
                print(f"[{i+1}/{len(request_list)}] Generated: {combination} -> {new_item}")

        except Exception as e:
            print(f"Exception for {combination}: {e}")
            continue

    total_elapsed = time.time() - start_time
    print(f"\nCompleted {len(request_list)} requests in {total_elapsed/60:.1f} minutes")

if __name__ == "__main__":
    # For now, just generate the request list
    generate_request_list()

    # Uncomment the line below when you're ready to execute the requests
    # execute_requests(limit=None)
