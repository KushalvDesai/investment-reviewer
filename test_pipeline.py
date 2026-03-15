"""
Final end-to-end test using:
  - HF Spaces /gradio_api/call/embed_query  (real 1024-dim embeddings)
  - Pinecone /vectors/upsert + /query       (store & retrieve)

Run: python test_pipeline.py
"""
import json
import sys
import time
import urllib.request
import urllib.error

HF_URL  = "https://speeddevil936-investment-reviewer.hf.space"
PC_KEY  = "pcsk_4Kmtg2_3YD4mn8pu7xjRuUSWWZxk3GDhnhAeMTnTxAzwSk2yBYSYdyH4pnvUgdgd6sHrUF"
PC_API  = "https://api.pinecone.io"
IDX     = "investment"
NS      = "pipeline-test"

BOLD="\033[1m"; OK="\033[92m"; ERR="\033[91m"; WARN="\033[93m"; RST="\033[0m"

def http(method, url, body=None, headers=None, timeout=30):
    data = json.dumps(body).encode() if body else None
    h = {"Content-Type": "application/json", **(headers or {})}
    rq = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(rq, timeout=timeout) as r:
            raw = r.read()
            return r.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")

def step(n, t):
    print(f"\n{BOLD}{'─'*62}{RST}\n{BOLD}STEP {n}: {t}{RST}\n{BOLD}{'─'*62}{RST}")

# ─── helper: call Gradio 5 queue API and stream result via SSE ────────────────
def gradio_embed(text: str) -> list[float] | None:
    """
    Call /gradio_api/call/embed_query with {"data":[text]}.
    Returns the embedding list (floats) or None on failure.
    """
    # 1. Submit job
    submit_url = f"{HF_URL}/gradio_api/call/embed_query"
    s, r = http("POST", submit_url, {"data": [text]}, timeout=20)
    if s != 200 or not isinstance(r, dict) or "event_id" not in r:
        print(f"  {ERR}Submit failed {s}: {str(r)[:150]}{RST}")
        return None

    event_id = r["event_id"]
    print(f"  Submitted → event_id: {event_id}")

    # 2. Stream result via SSE
    sse_url = f"{HF_URL}/gradio_api/call/embed_query/{event_id}"
    rq = urllib.request.Request(sse_url, headers={"Accept": "text/event-stream"})
    try:
        with urllib.request.urlopen(rq, timeout=45) as r:
            for raw in r:
                line = raw.decode(errors="replace").strip()
                if line.startswith("data:"):
                    payload = json.loads(line[5:])
                    # embed_query returns a single JSON string of the embedding
                    # Shape can be: [embedding_json_str] or [[float,...]]
                    if isinstance(payload, list) and payload:
                        first = payload[0]
                        if isinstance(first, list):         # direct float list
                            return first
                        if isinstance(first, str):          # JSON-stringified list
                            parsed = json.loads(first)
                            if isinstance(parsed, list):
                                return parsed
                            # might be {"embedding": [...]}
                            if isinstance(parsed, dict):
                                for v in parsed.values():
                                    if isinstance(v, list): return v
    except Exception as e:
        print(f"  {WARN}SSE stream error: {e}{RST}")
    return None


# ═══════════════════════════════════════════════════════════════════════════════
step(1, "HF Spaces — Confirm Gradio API schema")

s1, info = http("GET", f"{HF_URL}/gradio_api/info", timeout=12)
print(f"  Status: {s1}")
if isinstance(info, dict):
    for ep, meta in info.get("named_endpoints", {}).items():
        inputs  = [p.get("parameter_name") for p in meta.get("parameters", [])]
        outputs = [r.get("label","?") for r in meta.get("returns", [])]
        print(f"  {OK}✓{RST} Endpoint '{ep}' | inputs={inputs} | outputs={outputs}")


# ═══════════════════════════════════════════════════════════════════════════════
step(2, "HF Spaces — Generate embedding for 3 texts via /gradio_api/call/embed_query")

texts = [
    "January salary deposit 3500 USD from ACME Corp payroll",
    "January rent 1200 USD paid to City Apartments landlord",
    "February performance bonus 800 USD from employer ACME Corp",
]
embeddings = []

for i, txt in enumerate(texts):
    print(f"\n  [{i+1}] '{txt[:55]}…'")
    emb = gradio_embed(txt)
    if emb:
        print(f"  {OK}✓ dim={len(emb)}{RST} | min={min(emb):.4f} max={max(emb):.4f}")
        print(f"    first 5 values: {[round(v,4) for v in emb[:5]]}")
        embeddings.append({"text": txt, "vec": emb})
    else:
        print(f"  {WARN}Failed — skipping this text{RST}")

print(f"\n  Obtained {len(embeddings)}/{len(texts)} embeddings")


# ═══════════════════════════════════════════════════════════════════════════════
step(3, "Pinecone — Get index host")

pc_hdrs = {"Api-Key": PC_KEY, "X-Pinecone-API-Version": "2025-01"}
s3, idx = http("GET", f"{PC_API}/indexes/{IDX}", headers=pc_hdrs)
if s3 != 200:
    print(f"{ERR}✗ Index lookup failed: {idx}{RST}"); sys.exit(1)

HOST = f"https://{idx['host']}"
print(f"{OK}✓ {IDX} @ {HOST}{RST}")
print(f"  dim={idx['dimension']} | model={idx.get('embed',{}).get('model','—')} | state={idx['status']['state']}")

vec_hdrs = {"Api-Key": PC_KEY, "Content-Type": "application/json",
            "X-Pinecone-API-Version": "2025-01"}


# ═══════════════════════════════════════════════════════════════════════════════
step(4, "Pinecone — Upsert embeddings (POST /vectors/upsert)")

if not embeddings:
    print(f"{ERR}No embeddings — cannot upsert. Exiting.{RST}"); sys.exit(1)

vectors = [
    {"id": f"hf-{i}", "values": e["vec"], "metadata": {"text": e["text"]}}
    for i, e in enumerate(embeddings)
]
print(f"  Upserting {len(vectors)} vectors into namespace '{NS}'")
print(f"  POST {HOST}/vectors/upsert")

s4, r4 = http("POST", f"{HOST}/vectors/upsert",
              {"vectors": vectors, "namespace": NS}, vec_hdrs, timeout=30)
print(f"  Status: {s4} | {r4}")

if s4 in (200, 201):
    print(f"{OK}✓ Upserted {r4.get('upsertedCount','?')} vectors{RST}")
else:
    print(f"{ERR}✗ Upsert failed{RST}"); sys.exit(1)

print("  Waiting 4s for index to settle…")
time.sleep(4)


# ═══════════════════════════════════════════════════════════════════════════════
step(5, "Pinecone — Describe index stats (confirm namespace)")

s5, stats = http("GET", f"{HOST}/describe_index_stats", headers=vec_hdrs)
ns_data = stats.get("namespaces", {}) if isinstance(stats,dict) else {}
print(f"  Total vectors : {stats.get('totalVectorCount','?')}")
print(f"  Namespaces    : {sorted(ns_data.keys())}")
if NS in ns_data:
    print(f"  {OK}✓ '{NS}' has {ns_data[NS].get('vectorCount','?')} vectors{RST}")


# ═══════════════════════════════════════════════════════════════════════════════
step(6, "Pinecone — Similarity search with real HF embedding as query")

# Generate a query embedding
query = "What salary income did I receive?"
print(f"  Query text: '{query}'")
q_emb = gradio_embed(query)

if q_emb:
    print(f"  {OK}✓ Query embedding dim={len(q_emb)}{RST}")
    print(f"  POST {HOST}/query  (top_k=3, namespace={NS})")
    s6, r6 = http("POST", f"{HOST}/query",
                  {"vector": q_emb, "topK": 3, "namespace": NS,
                   "includeMetadata": True},
                  vec_hdrs, timeout=30)
    print(f"  Status: {s6}\n")
    if s6 == 200 and isinstance(r6,dict):
        for hit in r6.get("matches", []):
            score = hit.get("score", 0)
            text  = hit.get("metadata",{}).get("text","")
            bar   = "█" * int(score * 40)
            print(f"  {OK}[{score:.4f}]{RST} {bar}")
            print(f"           {text[:70]}\n")
    else:
        print(f"  {ERR}Query failed: {r6}{RST}")
else:
    print(f"  {WARN}Could not embed query — skipping similarity search{RST}")


# ═══════════════════════════════════════════════════════════════════════════════
step(7, "Cleanup — delete test namespace")

s7, r7 = http("POST", f"{HOST}/vectors/delete",
              {"deleteAll": True, "namespace": NS}, vec_hdrs, timeout=15)
print(f"  /vectors/delete → {s7}: {r7}")
if s7 in (200, 201):
    print(f"{OK}✓ Namespace '{NS}' deleted{RST}")

print(f"\n{BOLD}{'═'*62}{RST}")
print(f"{OK}{BOLD}End-to-end pipeline test COMPLETE.{RST}")
print(f"{BOLD}{'═'*62}{RST}\n")
