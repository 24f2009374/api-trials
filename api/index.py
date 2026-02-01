from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json
import numpy as np
from pathlib import Path

app = FastAPI()

# ---- CORS (manual, Vercel-safe) ----
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# ---- Load telemetry once ----
TELEMETRY_PATH = Path(__file__).parent.parent / "telemetry.json"

with open(TELEMETRY_PATH, "r") as f:
    telemetry = json.load(f)

@app.options("/api")
@app.options("/api/index")
async def preflight():
    return JSONResponse(status_code=200, content={})

@app.post("/api")
@app.post("/api/index")
async def metrics(request: Request):
    body = await request.json()

    regions = body.get("regions", [])
    threshold = body.get("threshold_ms")

    result = {}

    for region in regions:
        records = [r for r in telemetry if r["region"] == region]

        if not records:
            continue

        latencies = np.array([r["latency_ms"] for r in records])
        uptimes = np.array([r["uptime_pct"] for r in records])

        result[region] = {
            "avg_latency": round(float(latencies.mean()), 2),
            "p95_latency": round(float(np.percentile(latencies, 95)), 2),
            "avg_uptime": round(float(uptimes.mean()), 2),
            "breaches": int((latencies > threshold).sum())
        }

    return JSONResponse(content=result)
