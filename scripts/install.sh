#!/usr/bin/env bash
# =============================================================================
# Argus — AI-Powered Security Testing Platform
# One-line installer: curl -fsSL https://raw.githubusercontent.com/your-org/argus/main/scripts/install.sh | bash
#
# Modes:
#   1. Docker (recommended) — zero dependencies, everything pre-baked
#   2. Native — direct Python install (requires Python 3.11+)
# =============================================================================

set -euo pipefail

VERSION="3.0.0"
REPO="argus-security/argus"
REPO_URL="https://github.com/${REPO}.git"
RAW_URL="https://raw.githubusercontent.com/${REPO}/main"
DOCKER_IMAGE="ghcr.io/${REPO}:latest"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

banner() {
    echo -e "${CYAN}"
    echo "     █████╗ ██████╗  ██████╗ ██╗   ██╗███████╗"
    echo "    ██╔══██╗██╔══██╗██╔════╝ ██║   ██║██╔════╝"
    echo "    ███████║██████╔╝██║  ███╗██║   ██║███████╗"
    echo "    ██╔══██║██╔══██╗██║   ██║██║   ██║╚════██║"
    echo "    ██║  ██║██║  ██║╚██████╔╝╚██████╔╝███████║"
    echo "    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝"
    echo -e "${NC}"
    echo -e "  ${BOLD}v${VERSION}${NC}${CYAN} — AI-Powered Security Testing Platform${NC}"
    echo -e "  ${CYAN}80+ integrated tools • Zero dependency issues${NC}"
    echo ""
}

info()  { echo -e "${CYAN}INFO${NC}  $1"; }
ok()    { echo -e "${GREEN}OK${NC}    $1"; }
warn()  { echo -e "${YELLOW}WARN${NC}  $1"; }
err()   { echo -e "${RED}ERROR${NC} $1"; }

check_docker() {
    if command -v docker &>/dev/null; then
        if docker info &>/dev/null; then
            return 0
        fi
    fi
    return 1
}

install_docker() {
    info "Docker not found. Installing Docker..."
    curl -fsSL https://get.docker.com | bash
    if ! check_docker; then
        err "Docker installation failed. Install manually: https://docs.docker.com/engine/install/"
        exit 1
    fi
    ok "Docker installed successfully"
}

pull_image() {
    info "Pulling Argus Docker image (${DOCKER_IMAGE})..."
    if docker pull "${DOCKER_IMAGE}" 2>/dev/null; then
        ok "Image pulled: ${DOCKER_IMAGE}"
    else
        warn "Pre-built image not found. Building locally (this may take a while)..."
        build_local
    fi
}

build_local() {
    if [ ! -d "argus" ]; then
        info "Cloning repository..."
        git clone --depth=1 "${REPO_URL}" /tmp/argus-build
        cd /tmp/argus-build
    fi
    info "Building Docker image..."
    docker build -t "${DOCKER_IMAGE}" .
    ok "Image built: ${DOCKER_IMAGE}"
}

setup_docker_alias() {
    local alias_file="${HOME}/.bashrc"
    if [ -f "${HOME}/.zshrc" ]; then
        alias_file="${HOME}/.zshrc"
    fi

    if ! grep -q "alias argus=" "${alias_file}" 2>/dev/null; then
        cat >> "${alias_file}" << 'EOF'

# Argus — Docker-based security testing
alias argus='docker run --rm -it \
  -v "${PWD}:/work" \
  -v "${HOME}/.argus:/root/.argus" \
  -e LLM_API_KEY="${LLM_API_KEY:-}" \
  -e OPENAI_API_KEY="${OPENAI_API_KEY:-}" \
  -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-}" \
  -e OPENCODE_API_KEY="${OPENCODE_API_KEY:-}" \
  --network host \
  ghcr.io/argus-security/argus:latest'
EOF
        ok "Alias added to ${alias_file}"
        info "Run: source ${alias_file}"
    else
        ok "Alias already configured"
    fi

    info "Usage: argus strix --target https://example.com"
    info "Usage: argus --help"
}

install_native() {
    info "Installing Argus natively (requires Python 3.11+)..."

    if ! command -v python3 &>/dev/null; then
        err "Python 3.11+ required. Install it first."
        exit 1
    fi

    PYVER=$(python3 --version 2>&1 | awk '{print $2}')
    info "Python version: ${PYVER}"

    if [ ! -d "argus" ]; then
        git clone --depth=1 "${REPO_URL}" /tmp/argus-native
        cd /tmp/argus-native
    fi

    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    pip install -e . -q
    python -m playwright install chromium 2>/dev/null || true

    # Create directories
    mkdir -p ~/.argus/sessions ~/.argus/graph_memory ~/.argus/plugins/agents ~/.argus/plugins/tools

    ok "Argus installed natively"
    info "Activate: source venv/bin/activate"
    info "Run: argus strix --target https://example.com"
}

show_usage() {
    echo ""
    echo -e "${BOLD}Quick usage:${NC}"
    echo ""
    echo "  # Web recon (subfinder → httpx → nuclei)"
    echo "  argus strix --target https://example.com -m quick"
    echo ""
    echo "  # Deep pentest (full chain)"
    echo "  argus strix --target example.com -m deep"
    echo ""
    echo "  # OSINT — email investigation"
    echo "  argus holehe user@example.com"
    echo ""
    echo "  # OSINT — username search"
    echo "  argus maigret johndoe"
    echo ""
    echo "  # Secret scanning"
    echo "  argus trufflehog /path/to/repo"
    echo ""
    echo "  # TLS audit"
    echo "  argus testssl example.com:443"
    echo ""
    echo -e "${BOLD}All tools auto-use Docker — no dependency issues.${NC}"
    echo ""
    echo "  Docs: https://github.com/${REPO}"
}

# =============================================================================
# Main
# =============================================================================
banner

# Parse --native flag
MODE="docker"
for arg in "$@"; do
    if [ "$arg" = "--native" ] || [ "$arg" = "--local" ]; then
        MODE="native"
    fi
    if [ "$arg" = "--help" ] || [ "$arg" = "-h" ]; then
        echo "Usage: curl -fsSL ${RAW_URL}/scripts/install.sh | bash"
        echo "       curl -fsSL ${RAW_URL}/scripts/install.sh | bash -s -- --native"
        echo "       curl -fsSL ${RAW_URL}/scripts/install.sh | bash -s -- --help"
        exit 0
    fi
done

if [ "$MODE" = "docker" ]; then
    info "Mode: Docker (recommended — zero dependencies)"
    echo ""

    if ! check_docker; then
        install_docker
    fi

    pull_image
    setup_docker_alias

    echo ""
    ok "Argus v${VERSION} ready via Docker!"
    show_usage
else
    install_native
    echo ""
    ok "Argus v${VERSION} installed natively!"
    show_usage
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   Argus installed successfully!             ║${NC}"
echo -e "${GREEN}║   See Everything. Miss Nothing.             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
