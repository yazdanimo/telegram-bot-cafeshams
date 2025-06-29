import json
import os
import hashlib

STATS_FILE = "data/stats.json"

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {"seen_hashes": [], "sent_count": 0}
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def save_stats(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

def get_hash(link, summary):
    return hashlib.sha256((link + summary).encode('utf-8')).hexdigest()

def has_been_sent(link, summary, stats):
    return get_hash(link, summary) in stats.get("seen_hashes", [])

def mark_as_sent(link, summary, stats):
    content_hash = get_hash(link, summary)
    if content_hash not in stats["seen_hashes"]:
        stats["seen_hashes"].append(content_hash)
        stats["sent_count"] += 1
        save_stats(stats)
