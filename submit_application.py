#!/usr/bin/env python3

import json
import hmac
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, timezone
import os
import sys


# ---- Configuration ----

B12_ENDPOINT = "https://b12.io/apply/submission"


# ---- Validate environment ----

required_env_vars = [
    "B12_SIGNING_SECRET",
    "GITHUB_RUN_URL",
]

missing = [v for v in required_env_vars if v not in os.environ]
if missing:
    print(f"Missing required environment variables: {', '.join(missing)}", file=sys.stderr)
    sys.exit(1)


SIGNING_SECRET = os.environ["B12_SIGNING_SECRET"].encode("utf-8")


# ---- Generate timestamp (ISO 8601) ----

timestamp = (
    datetime.now(timezone.utc)
    .isoformat(timespec="milliseconds")
    .replace("+00:00", "Z")
)


# ---- Build payload ----

payload = {
    "timestamp": timestamp,
    "name": "James Thomas",
    "email": "jamesjacobthomas7@gmail.com",
    "resume_link": "https://www.linkedin.com/in/james-thomas007/",
    "repository_link": "https://github.com/jtx007/b12-application",
    "action_run_link": os.environ["GITHUB_RUN_URL"],
}


# ---- Canonical JSON (sorted keys, compact, UTF-8) ----

canonical_json = json.dumps(
    payload,
    separators=(",", ":"),
    sort_keys=True,
    ensure_ascii=False,
)


# ---- HMAC-SHA256 signature ----

digest = hmac.new(
    SIGNING_SECRET,
    canonical_json.encode("utf-8"),
    hashlib.sha256,
).hexdigest()

signature_header = f"sha256={digest}"


# ---- HTTP POST ----

request = urllib.request.Request(
    url=B12_ENDPOINT,
    data=canonical_json.encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "X-Signature-256": signature_header,
    },
    method="POST",
)

try:
    with urllib.request.urlopen(request) as response:
        response_body = response.read().decode("utf-8")
except urllib.error.HTTPError as e:
    print("HTTP error:", e.code, e.read().decode("utf-8"), file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print("Request failed:", str(e), file=sys.stderr)
    sys.exit(1)


# ---- Parse response ----

try:
    parsed = json.loads(response_body)
except json.JSONDecodeError:
    print("Invalid JSON response:", response_body, file=sys.stderr)
    sys.exit(1)


# ---- Success output ----

if parsed.get("success") is True and "receipt" in parsed:
    print("Submission receipt:", parsed["receipt"])
else:
    print("Unexpected response:", parsed, file=sys.stderr)
    sys.exit(1)
