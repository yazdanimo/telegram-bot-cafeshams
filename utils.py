import json
import os

STATS_FILE = "data/stats.json"

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {"seen_links": [], "sent_count": 0}
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

def has_been_sent(link, stats):
    return link in stats["seen_links"]

def mark_as_sent(link, stats):
    stats["seen_links"].append(link)
    stats["sent_count"] += 1
    save_stats(stats)
