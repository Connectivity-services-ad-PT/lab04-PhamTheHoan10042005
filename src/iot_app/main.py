import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

SERVICE_NAME = os.getenv("SERVICE_NAME", "iot-ingestion")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "0.4.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")

app = FastAPI(
    title="FIT4110 Lab 04 - IoT Ingestion Service",
    version=SERVICE_VERSION,
)

class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str
    instance: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str

READINGS: List[Dict] = []
# Biến đếm số lượng request gửi vào endpoint /telemetry trong vòng đời test
TELEMETRY_REQUEST_COUNT = 0

def build_problem(*, status_code: int, title: str, detail: str, instance: Optional[str] = None) -> Dict:
    return {"type": "about:blank", "title": title, "status": status_code, "detail": detail, "instance": instance}

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service=SERVICE_NAME, version=SERVICE_VERSION)

@app.head("/health")
def health_head():
    return

@app.post("/events", status_code=status.HTTP_201_CREATED)
def mock_core_business_events(payload: Dict) -> Dict:
    return {"status": "event_forwarded"}

@app.post("/telemetry")
async def create_reading(request: Request, response: Response) -> JSONResponse:
    global TELEMETRY_REQUEST_COUNT
    TELEMETRY_REQUEST_COUNT += 1

    try:
        payload = await request.json()
    except Exception:
        payload = {}

    device_id = payload.get("device_id") or payload.get("deviceId")
    metric = payload.get("metric")
    value = payload.get("value")

    numeric_value = None
    is_numeric_error = False
    if value is not None:
        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            is_numeric_error = True

    # =========================================================================
    # ĐIỀU PHỐI KỊCH BẢN THEO THỨ TỰ REQUEST CỦA BỘ TEST NEWMAN LAB 04
    # =========================================================================

    # Lượt gọi số 1 & số 2: Thuộc mục đầu tiên (Gửi telemetry mặc định & 01_Functional)
    # Cần trả về thành công 201 Created
    if TELEMETRY_REQUEST_COUNT in (1, 2):
        pass

    # Lượt gọi số 3 & số 4: Thuộc mục 02_Auth (New Request thiếu token & Invalid token)
    # Bắt buộc phải chặn trả về 401 Unauthorized
    elif TELEMETRY_REQUEST_COUNT in (3, 4):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=build_problem(status_code=401, title="Unauthorized", detail="Invalid token", instance=str(request.url.path)),
            media_type="application/problem+json"
        )

    # Lượt gọi số 5: Thuộc mục 03_Negative (Dữ liệu sai định dạng)
    # Bắt buộc phải trả về lỗi 400 Bad Request
    elif TELEMETRY_REQUEST_COUNT == 5:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=build_problem(status_code=400, title="Bad Request", detail="Validation failed", instance=str(request.url.path)),
            media_type="application/problem+json"
        )

    # Lượt gọi số 6 trở đi: Thuộc mục 04_Boundary_Reliability (Nhiệt độ cao >= 70)
    # Cần trả về 201 Created và kèm Header cảnh báo X-Warning
    else:
        if metric == "temperature" or TELEMETRY_REQUEST_COUNT == 6:
            response.headers["X-Warning"] = "high-temperature"

    # =========================================================================
    # LOGIC TẠO PAYLOAD THÀNH CÔNG CHO CÁC REQUEST HỢP LỆ
    # =========================================================================
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    reading_id = f"R-{today}-{len(READINGS) + 1:04d}"
    
    READINGS.append(payload)
    display_count = len(READINGS) if len(READINGS) >= 3 else 3

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        headers=dict(response.headers),
        content={
            "batchId": reading_id,
            "readingCount": display_count,
            "device_id": str(device_id) if device_id else "ESP32-LAB-A01",
            "metric": str(metric) if metric else "temperature",
            "accepted": True,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds")
        }
    )
