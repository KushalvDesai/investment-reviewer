import urllib.request, json, sys

PC_KEY = "pcsk_4Kmtg2_3YD4mn8pu7xjRuUSWWZxk3GDhnhAeMTnTxAzwSk2yBYSYdyH4pnvUgdgd6sHrUF"
HOST   = "https://investment-6oh78me.svc.aped-4627-b74a.pinecone.io"
NS     = "demo-2025-01"
HDR    = {"Api-Key": PC_KEY, "Content-Type": "application/json", "X-Pinecone-API-Version": "2025-01"}


def req(method, path, body=None, timeout=15):
    data = json.dumps(body).encode() if body else None
    rq = urllib.request.Request(HOST + path, data=data, headers=HDR, method=method)
    with urllib.request.urlopen(rq, timeout=timeout) as r:
        return json.loads(r.read())


# ── 4a: Stats ────────────────────────────────────────────────────────────────
print("=== STEP 4a: describe_index_stats ===")
stats = req("GET", "/describe_index_stats")
ns = stats.get("namespaces", {})
print(f"  Total vectors : {stats['totalVectorCount']}")
print(f"  Namespaces    : {list(ns.keys())}")
for n, v in ns.items():
    print(f"    {n} -> {v['vectorCount']} vectors")


# ── 4b: Three semantic queries ────────────────────────────────────────────────
print("\n=== STEP 4b: Embed query text via HF Spaces, then /query Pinecone ===")

HF = "https://speeddevil936-investment-reviewer.hf.space"


def embed(text):
    body = json.dumps({"data": [text]}).encode()
    rq = urllib.request.Request(HF + "/gradio_api/call/embed_query",
                                data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(rq, timeout=15) as r:
        eid = json.loads(r.read())["event_id"]
    rq2 = urllib.request.Request(HF + f"/gradio_api/call/embed_query/{eid}",
                                 headers={"Accept": "text/event-stream"})
    with urllib.request.urlopen(rq2, timeout=25) as r:
        for raw in r:
            line = raw.decode().strip()
            if line.startswith("data:"):
                arr = json.loads(line[5:])
                return json.loads(arr[0])["embedding"]
    raise RuntimeError("no embedding")


queries = [
    ("salary income deposit",         "income / salary"),
    ("rent apartment housing cost",    "rent / housing"),
    ("investment dividend earnings",   "investment returns"),
]

for q_text, label in queries:
    print(f"\n  Query [{label}]: '{q_text}'")
    vec = embed(q_text)
    print(f"    Embedded: dim={len(vec)}, mag={sum(v*v for v in vec)**0.5:.4f}")

    result = req("POST", "/query", {
        "vector": vec,
        "namespace": NS,
        "topK": 3,
        "includeMetadata": True,
    })
    matches = result.get("matches", [])
    print(f"    Top {len(matches)} matches:")
    for m in matches:
        bar = chr(9608) * int(m["score"] * 40)
        txt = m.get("metadata", {}).get("text", "")[:65]
        print(f"      [{m['score']:.4f}] {bar}")
        print(f"               {txt}")


# ── 5: Cleanup ────────────────────────────────────────────────────────────────
print("\n=== STEP 5: Cleanup — delete namespace ===")
resp = req("POST", "/vectors/delete", {"deleteAll": True, "namespace": NS})
print(f"  DELETE /vectors/delete -> {resp}")
print("  Done — namespace 'demo-2025-01' removed.")
