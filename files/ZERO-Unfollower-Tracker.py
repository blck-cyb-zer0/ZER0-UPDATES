#!/usr/bin/env python3
# ZERO Unfollower Tracker - Works offline with YOUR OWN Instagram data
# No login, no shady app. You use the data Instagram gives you.
import json, os, glob

print("=== ZERO Unfollower Tracker ===")
print("1. Go to Instagram > Settings > Download Your Information > Download")
print("2. Unzip it and put followers_1.json and following.json in SAME folder as this script")
print("3. Run this script\n")

def load_names(path):
    try:
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        names = set()
        # Instagram format varies, handle both
        items = data if isinstance(data, list) else data.get('relationships_following', []) + data.get('relationships_followers', [])
        for item in items:
            # New format: {"string_list_data":[{"value":"username"}]}
            if 'string_list_data' in item:
                for s in item['string_list_data']:
                    names.add(s['value'])
            # Old format: {"title":"username"}
            elif 'title' in item:
                names.add(item['title'])
        return names
    except FileNotFoundError:
        return None

followers = load_names('followers_1.json')
following = load_names('following.json')

if followers is None:
    print("ERROR: followers_1.json not found in this folder.")
elif following is None:
    print("ERROR: following.json not found in this folder.")
else:
    not_back = sorted(following - followers)
    fans = sorted(followers - following)
    print(f"Followers: {len(followers)} | Following: {len(following)}")
    print(f"\n--- NOT FOLLOWING YOU BACK ({len(not_back)}) ---")
    for u in not_back:
        print(f"@{u}")
    print(f"\n--- FANS - Follow you, you don't follow back ({len(fans)}) ---")
    for u in fans:
        print(f"@{u}")
    with open('unfollower-result.txt','w',encoding='utf-8') as out:
        out.write("NOT FOLLOWING YOU BACK:\n" + "\n".join(not_back))
    print("\nSaved to unfollower-result.txt")

input("\nPress Enter to close...")
