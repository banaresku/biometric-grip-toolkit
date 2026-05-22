FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Install deps first (cached layer — only invalidated when versions change)
RUN pip install --no-cache-dir \
    "opencv-contrib-python-headless>=4.8.0" \
    "mediapipe>=0.10.0" \
    "numpy>=1.24.0"

# Copy project (volume mount at runtime overrides these for development)
COPY . /workspace/

# Default entrypoint — override args at docker run
ENTRYPOINT ["python", "1_biometriscan/analyze_photo.py"]
CMD ["--help"]
