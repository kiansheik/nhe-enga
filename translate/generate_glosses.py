from collections import defaultdict
import json, gzip, os
import requests
from ratelimit import limits, sleep_and_retry
import sqlite3
from tqdm import tqdm
import random
import time
from queue import Queue
from threading import Thread, Lock

NUM_WORKERS = 5  # can scale based on cores / quota

# load the dictionary file in ../docs/dict-conjugated.json.gz
with gzip.open("/Users/kian/code/nhe-enga/docs/dict-conjugated.json.gz", "rt") as f:
    dictionary = json.load(f)
    # rename


ban = [
    "NOTA",
    "Daí",
    "De",
    "OBSERVAÇÃO",
    "Daí,",
    "aba",
    "-ab",
    "abatiputá",
    "-agûama",
    "a'ebé",
    "agûaîxima",
    "agûaragûasu",
    "agûy",
    "ambûer",
    "apyrĩ",
    "ambype",
    "gûaîá",
    "eno-",
    "îabotimirĩ",
    "îapĩ",
    "Maíra",
    "memetipó",
    "moro-",
    "muresi",
    "pyru'ã",
    "POROROCA",
    "sybyamumbyaré",
    "Muitos",
    "Há",
    "O",
    "Cardim,",
]

dicc_dict = {i: v for i, v in enumerate(dictionary)}
tupi_only = []
include = False
adjectives = []
for i, vbt in dicc_dict.items():
    if vbt["f"] == "ã":
        include = True
    if include and vbt["f"] not in ban:
        vbt["id"] = i
        tupi_only.append(vbt)
    if vbt["f"] == "'yura":
        include = False

job_queue = Queue()
db_lock = Lock()  # to prevent sqlite write collisions

USAGE_FILE = "/Users/kian/code/nhe-enga/translate/api_usage_log.json"
# Define rate limits
ONE_MINUTE = 60
ONE_HOUR = 60 * ONE_MINUTE
ONE_DAY = 24 * ONE_HOUR
DB_PATH = os.path.abspath("/Users/kian/code/nhe-enga/translate/tupi_only.db")

final_keys = []


def get_google_api_resp(prompt, sys_prompt, key=None, model="gemini-2.5-flash-lite"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    request_body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": sys_prompt}]},
        "safetySettings": [
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ],
    }
    response = requests.post(url, json=request_body)
    return response


def test_google_api_key(key, model):
    """Test if the provided Google API key is valid for a specific model."""
    ping_prompt = "send me a pong message back with nothing else but the word 'pong'"
    try:
        response = get_google_api_resp(
            ping_prompt, sys_prompt=ping_prompt, key=key, model=model
        )
    except Exception as e:
        print(f"⚠️ Error with key {key}, model {model}: {e}")
        return False

    if response.status_code == 200:
        return True

    if response.status_code == 429:
        error = response.json().get("error", {})
        details = error.get("details", [])
        for item in details:
            metadata = item.get("metadata", {})
            if metadata.get("quota_limit_value") == "0":
                # Permanently dead for this model
                return False
            if item.get("@type") == "type.googleapis.com/google.rpc.QuotaFailure":
                for v in item.get("violations", []):
                    if "FreeTier" in v.get("quotaId", ""):
                        # Temporarily exhausted for today
                        return False
        # Unknown 429 cause → skip
        return False

    if response.status_code == 403:
        return False  # Forbidden → likely revoked

    # Other failure types
    return False


MODEL_LIMITS = {
    "gemini-2.5-pro": {"rpm": 5, "rpd": 100},
    "gemini-2.5-flash": {"rpm": 10, "rpd": 250},
    "gemini-2.5-flash-lite": {"rpm": 15, "rpd": 1000},
    "gemini-2.0-flash": {"rpm": 15, "rpd": 200},
    "gemini-2.0-flash-lite": {"rpm": 30, "rpd": 200},
    "gemini-1.5-flash": {"rpm": 15, "rpd": 50},
    "gemini-1.5-flash-8b": {"rpm": 15, "rpd": 50},
}

class ApiKeyMultiplexer:
    def __init__(self, keys, test_func):
        self.test_func = test_func
        self.valid_combos = []

        print("🔍 Validating key+model combos...")
        for key in tqdm(set(keys)):
            for model in MODEL_LIMITS.keys():
                # if test_func(key, model):
                self.valid_combos.append((key, model))

        self.index = 0
        self.disabled = {}  # (key, model): re-enable timestamp
        self.usage_minute = defaultdict(list)
        self.usage_day = defaultdict(list)
        self.lock = Lock()

        self._load_usage_data()
        print(f"✅ {len(self.valid_combos)} working key+model combinations.")

    def _load_usage_data(self):
        if os.path.exists(USAGE_FILE):
            with open(USAGE_FILE, "r") as f:
                saved = json.load(f)
                now = time.time()

                for k_model, timestamps in saved.get("usage_day", {}).items():
                    key, model = k_model.split("||")
                    self.usage_day[(key, model)] = [t for t in timestamps if now - t < 86400]

                for k_model, timestamps in saved.get("usage_minute", {}).items():
                    key, model = k_model.split("||")
                    self.usage_minute[(key, model)] = [t for t in timestamps if now - t < 60]

    def _save_usage_data(self):
        def key_tuple_to_str(t): return f"{t[0]}||{t[1]}"
        data = {
            "usage_day": {
                key_tuple_to_str(k): v for k, v in self.usage_day.items()
            },
            "usage_minute": {
                key_tuple_to_str(k): v for k, v in self.usage_minute.items()
            },
        }
        with open(USAGE_FILE, "w") as f:
            json.dump(data, f)

    def disable_combo_for_a_day(self, key, model):
        with self.lock:
            self.disabled[(key, model)] = time.time() + 24 * 3600

    def get_next(self):
        """Round-robin select a valid, not disabled, not over-limit (key, model) pair."""
        while True:
            with self.lock:
                now = time.time()
                start_index = self.index

                for _ in range(len(self.valid_combos)):
                    key, model = self.valid_combos[self.index]
                    self.index = (self.index + 1) % len(self.valid_combos)

                    # Skip disabled
                    if (key, model) in self.disabled:
                        if now >= self.disabled[(key, model)]:
                            del self.disabled[(key, model)]
                        else:
                            continue

                    # Clean expired usage
                    self.usage_minute[(key, model)] = [t for t in self.usage_minute[(key, model)] if now - t < 60]
                    self.usage_day[(key, model)] = [t for t in self.usage_day[(key, model)] if now - t < 86400]

                    limits = MODEL_LIMITS[model]
                    if (len(self.usage_minute[(key, model)]) < limits["rpm"] and
                        len(self.usage_day[(key, model)]) < limits["rpd"]):

                        # Register usage
                        self.usage_minute[(key, model)].append(now)
                        self.usage_day[(key, model)].append(now)
                        self._save_usage_data()
                        return key, model

            # All combos exhausted — wait a little and try again
            print("⚠️ All key+model combinations are rate-limited. Sleeping 60s...")
            time.sleep(60)

with open("/Users/kian/code/nhe-enga/translate/google_api_keys.json", "r") as f:
    greenlit = json.load(f)

APIMux = ApiKeyMultiplexer(greenlit, test_google_api_key)

# final_keys += APIMux.keys

# print(f"Final API keys: \n{json.dumps(final_keys, indent=2)}")

system_prompt = (
    "Read this Portuguese dictionary definition for an indigenous tupi-guarani language and give me a comma separated"
    "list of simple glosses which encompass the core definitions well. I will ingest this answer pragmatically so "
    'DO NOT return anything except a comma separated string which can easily be processed with string.split(", ")'
    "to get the individual glosses. I want one copy in English and another copy in Portuguese separated by a newline."
)


def get_ai_response(prompt, system_prompt):
    while True:
        try:
            key, model = APIMux.get_next()
        except Exception as e:
            print("⚠️ All models are currently rate-limited. Sleeping for 5 seconds...")
            time.sleep(5)
            continue

        response = get_google_api_resp(
            prompt, sys_prompt=system_prompt, key=key, model=model
        )

        if response.status_code == 200:
            data = response.json()
            if "candidates" not in data or not data["candidates"]:
                print(f"⚠️ No candidates returned for key {key} on model {model}.")
                continue
            if "content" not in data["candidates"][0] or "parts" not in data["candidates"][0]["content"]:
                print(f"⚠️ Invalid response structure for key {key} on model {model}.")
                continue
            return data["candidates"][0]["content"]["parts"][0]["text"]

        elif response.status_code == 429:
            print(f"Rate limit or quota hit: disabling {key} on {model} for 24h.")
            APIMux.disable_combo_for_a_day(key, model)
            continue

        else:
            try:
                response.raise_for_status()
            except Exception as e:
                print(f"Error: disabling {key} on {model} — {e}")
                APIMux.disable_combo_for_a_day(key, model)
                continue


# Make a sqlite3 db locally to store the tupi_only data and keep track of what still needs to be translated
with sqlite3.connect(DB_PATH) as conn:
    c = conn.cursor()
    c.execute(
        """
    CREATE TABLE IF NOT EXISTS tupi_only (
        id INTEGER PRIMARY KEY,
        vid INTEGER,
        first_word TEXT,
        definition TEXT,
        gloss_language TEXT,
        gloss TEXT,
        human_verified INTEGER DEFAULT 0
    ) 
    """
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_vid ON tupi_only(vid)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_first_word ON tupi_only(first_word)")
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_gloss_language ON tupi_only(gloss_language)"
    )
    c.execute("CREATE INDEX IF NOT EXISTS idx_gloss ON tupi_only(gloss)")
    c.execute(
        "CREATE INDEX IF NOT EXISTS idx_human_verified ON tupi_only(human_verified)"
    )

def worker():
    # function to check if a word is already in the database based on first word and definition
    def is_word_in_db(first_word, definition):
        with db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute(
                    "SELECT COUNT(*) FROM tupi_only WHERE first_word = ? AND definition = ?",
                    (first_word, definition),
                )
                count = c.fetchone()[0]
            return count > 0
    while True:
        vbt = job_queue.get()
        if vbt is None:
            break  # exit signal

        first_word = vbt["f"]
        definition = vbt["d"]
        vid = vbt["id"]

        if is_word_in_db(first_word, definition):
            job_queue.task_done()
            continue

        try:
            resp = get_ai_response(f"{first_word} - {definition}", system_prompt)
            lines = resp.strip().split("\n")
        except Exception as e:
            print(f"❌ Error for {first_word}: {e}")
            job_queue.task_done()
            continue

        with db_lock:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                for lang, gloss_line in zip(["en", "pt"], lines[:2]):
                    for gloss in gloss_line.split(","):
                        gloss = gloss.strip()
                        if gloss:
                            c.execute(
                                "INSERT INTO tupi_only (vid, first_word, definition, gloss_language, gloss) VALUES (?, ?, ?, ?, ?)",
                                (vid, first_word, definition, lang, gloss),
                            )

        job_queue.task_done()

if __name__ == "__main__":
    random.shuffle(tupi_only)

    # Fill queue
    for vbt in tupi_only:
        job_queue.put(vbt)

    # Start worker threads
    threads = []
    for _ in range(NUM_WORKERS):
        t = Thread(target=worker)
        t.start()
        threads.append(t)

    # Track progress
    with tqdm(total=len(tupi_only), desc="Processing Tupi words") as pbar:
        while not job_queue.empty():
            prev_unfinished = job_queue.unfinished_tasks
            time.sleep(0.5)
            finished = prev_unfinished - job_queue.unfinished_tasks
            pbar.update(finished)

    # Stop workers
    for _ in threads:
        job_queue.put(None)
    for t in threads:
        t.join()
