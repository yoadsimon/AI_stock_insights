FROM apache/airflow:2.7.1

# Install Python dependencies
# install playwright first to avoid run after every change in requirements.txt
USER root
RUN apt update
RUN python3 -m pip install playwright
RUN python3 -m playwright install
RUN python3 -m playwright install --with-deps
USER airflow
RUN python3 -m pip install playwright
RUN python3 -m playwright install
RUN #python3 -m playwright install --with-deps
ENV PLAYWRIGHT_BROWSERS_PATH=/home/airflow/.cache/ms-playwright
RUN mkdir -p /home/airflow/.cache && \
    chown -R airflow: /home/airflow/.cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER root
# Install necessary dependencies and fonts
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        imagemagick \
        fonts-dejavu-core \
        fonts-dejavu-extra \
        fonts-liberation \
        fontconfig \
        ghostscript \
        gsfonts && \
    rm -rf /var/lib/apt/lists/* 

# Adjust ImageMagick policy.xml to allow text rendering (if necessary)
RUN sed -i 's/rights="none"/rights="read|write"/g' /etc/ImageMagick-6/policy.xml
USER airflow
RUN pip install ffmpeg-python imageio_ffmpeg
