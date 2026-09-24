import json, os, glob, time, sys

# === Config ===
RT_LIST    = "/opt/cliproxyapi/rt_list.json"
AUTH_DIR   = "/opt/cliproxyapi/auth"
AUTH_403   = "/opt/cliproxyapi/auth_403"
PREFIX     = "ag_"
BATCH_SIZE = 200
BATCH_WAIT = 1  # seconds

# === Parse rt_list.json (handles concatenated JSON) ===
raw = open(RT_LIST, "r").read()
all_accounts = []
decoder = json.JSONDecoder()
pos = 0
while pos < len(raw):
    stripped = raw[pos:].lstrip()
    if not stripped:
        break
    pos = len(raw) - len(stripped)
    try:
        obj, end = decoder.raw_decode(raw, pos)
        if isinstance(obj, list):
            all_accounts.extend(obj)
        elif isinstance(obj, dict):
            all_accounts.append(obj)
        pos += end
    except json.JSONDecodeError:
        pos += 1

print(f"Parsed {len(all_accounts)} accounts from rt_list.json")

# === Deduplicate by email in rt_list ===
def get_email(acc):
    """Extract email from various possible locations in account json."""
    # Top-level email
    e = acc.get("email", "")
    if e:
        return e.strip().lower()
    # metadata.email
    meta = acc.get("metadata", {})
    if isinstance(meta, dict):
        e = meta.get("email", "")
        if e:
            return e.strip().lower()
    return ""

seen_emails = set()
unique = []
for acc in all_accounts:
    email = get_email(acc)
    if not email:
        # No email - fall back to refresh_token dedup
        rt = acc.get("refresh_token", "")
        if rt and rt not in seen_emails:
            seen_emails.add(rt)
            unique.append(acc)
        continue
    if email not in seen_emails:
        seen_emails.add(email)
        unique.append(acc)

print(f"Unique accounts after dedup: {len(unique)}")

# === Collect existing emails from auth/ ===
existing_emails = set()
max_num = 0
for f in glob.glob(os.path.join(AUTH_DIR, "*.json")):
    try:
        data = json.load(open(f))
        email = get_email(data)
        if email:
            existing_emails.add(email)
        else:
            rt = data.get("refresh_token", "")
            if rt:
                existing_emails.add(rt)
    except:
        pass
    try:
        basename = os.path.basename(f)
        num_str = basename.replace(PREFIX, "").replace(".json", "")
        num = int(num_str)
        if num > max_num:
            max_num = num
    except:
        pass

print(f"Existing in auth/: {len(existing_emails)} accounts, max_num={max_num}")

# === Collect emails from auth_403/ (blocked, never re-add) ===
blocked_emails = set()
if os.path.isdir(AUTH_403):
    for f in glob.glob(os.path.join(AUTH_403, "*.json")):
        try:
            data = json.load(open(f))
            email = get_email(data)
            if email:
                blocked_emails.add(email)
            else:
                rt = data.get("refresh_token", "")
                if rt:
                    blocked_emails.add(rt)
        except:
            pass

print(f"Blocked in auth_403/: {len(blocked_emails)} accounts")

# === Filter: not in auth/ AND not in auth_403/ ===
new_accs = []
for acc in unique:
    email = get_email(acc)
    key = email if email else acc.get("refresh_token", "")
    if not key:
        continue
    if key in existing_emails or key in blocked_emails:
        continue
    new_accs.append(acc)

print(f"New to add: {len(new_accs)}")

if len(new_accs) == 0:
    print("Nothing to do.")
    sys.exit(0)

# === Write new auth files ===
os.makedirs(AUTH_DIR, exist_ok=True)
added = 0
for i, acc in enumerate(new_accs):
    acc["type"] = "antigravity"
    acc["project_id"] = "aicode-consumers"
    filename = f"{PREFIX}{max_num + 1 + i:06d}.json"
    filepath = os.path.join(AUTH_DIR, filename)
    with open(filepath, "w") as f:
        json.dump(acc, f, indent=2)
    added += 1
    if added % BATCH_SIZE == 0:
        time.sleep(BATCH_WAIT)
        if added % 10000 == 0:
            print(f"  Written {added}/{len(new_accs)}...")

print(f"Done: {added} written, starting from {PREFIX}{max_num+1:06d}.json")
