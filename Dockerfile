# =============================================================================
# Argus - AI-Powered Security Testing Platform
# Multi-stage Docker build
# =============================================================================

# ---- Base Stage ----
FROM python:3.11-slim AS base

LABEL org.opencontainers.image.title="Argus"
LABEL org.opencontainers.image.description="AI-Powered Security Testing Platform"
LABEL org.opencontainers.image.url="https://github.com/iamaworker-github/argus"
LABEL org.opencontainers.image.source="https://github.com/iamaworker-github/argus"
LABEL org.opencontainers.image.licenses="Apache-2.0"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    git \
    gnupg \
    unzip \
    xz-utils \
    openssh-client \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# ---- Builder Stage ----
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt setup.py pyproject.toml MANIFEST.in ./
COPY argus/ ./argus/
COPY argus_security.egg-info/ ./argus_security.egg-info/ 2>/dev/null || true

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /wheels -r requirements.txt \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /wheels .

# ---- Runtime Stage ----
FROM base AS runtime

# Copy Python wheels from builder
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r /wheels/requirements.txt 2>/dev/null; \
    pip install --no-cache-dir --no-index --find-links=/wheels argus-security 2>/dev/null; \
    rm -rf /wheels

# Copy source code
COPY . .

# Install the package
RUN pip install --no-cache-dir -e .[web]

# Install Playwright browsers
RUN python -m playwright install chromium --with-deps 2>/dev/null || true

# Create working directories
RUN mkdir -p /root/.argus /app/argus_results

# Copy entrypoint
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set up environment
ENV HOME=/root \
    ARGUS_HOME=/root/.argus \
    OUTPUT_DIR=/app/argus_results

EXPOSE 8484
VOLUME ["/root/.argus", "/app/argus_results"]

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["--help"]

# ---- Full Stage (with heavy security tools) ----
FROM runtime AS full

RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    masscan \
    netcat-openbsd \
    dnsutils \
    whois \
    && rm -rf /var/lib/apt/lists/*

# Install Go-based tools
RUN wget -q https://go.dev/dl/go1.22.0.linux-amd64.tar.gz -O /tmp/go.tar.gz \
    && tar -C /usr/local -xzf /tmp/go.tar.gz \
    && rm /tmp/go.tar.gz

ENV PATH=/usr/local/go/bin:/root/go/bin:$PATH

# Install nuclei
RUN go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest \
    && nuclei -update-templates

# Install httpx
RUN go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest

# Install subfinder
RUN go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Install ffuf
RUN go install -v github.com/ffuf/ffuf/v2@latest

# Install assetfinder
RUN go install -v github.com/tomnomnom/assetfinder@latest

# Install waybackurls
RUN go install -v github.com/tomnomnom/waybackurls@latest

# Install gau
RUN go install -v github.com/lc/gau/v2/cmd/gau@latest

# Install naabu
RUN go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest

# Install dnsx
RUN go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest

# Install interactsh
RUN go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest

# Clean up Go cache
RUN rm -rf /root/go/pkg /root/.cache/go-build

# Install Python extras
RUN pip install --no-cache-dir "argus-security[all]"

# Update nuclei templates
RUN nuclei -update-templates 2>/dev/null || true

# Default to full mode
ENV ARGUS_FULL=true

LABEL org.opencontainers.image.description="Argus Full Image - AI-Powered Security Testing with all tools pre-installed"
