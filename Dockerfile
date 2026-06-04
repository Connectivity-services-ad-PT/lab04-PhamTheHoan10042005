FROM python:3.11-alpine

WORKDIR /app

# Sao chép và cài đặt các thư viện dependencies trước để tối ưu cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ thư mục src (bao gồm iot_app) vào trong container
COPY src/ ./src/

# Thiết lập biến môi trường đường dẫn hệ thống cho Python
ENV PYTHONPATH=/app

# Tạo user không có đặc quyền root để bảo mật hệ thống theo yêu cầu bài Lab
RUN adduser -D appuser && chown -R appuser:appuser /app
USER appuser

# Gọi chính xác đường dẫn module phân cấp thực tế: src.iot_app.main:app
CMD ["uvicorn", "src.iot_app.main:app", "--host", "0.0.0.0", "--port", "8000"]
