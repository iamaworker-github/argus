#!/usr/bin/env bash
# =============================================================================
# Argus - AI-Powered Security Testing Platform
# One-line installer
# =============================================================================
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/argus/main/scripts/install.sh | bash
#   bash scripts/install.sh [--global | --project | --full | --uninstall | --update | --status | --help]
# =============================================================================

set -euo pipefail

VERSION="2.0.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_URL="https://github.com/yourusername/argus.git"
AGENTS_SRC="${SCRIPT_DIR}/../argus/skills"
GLOBAL_DIR="${HOME}/.claude/agents"
PROJECT_DIR=".claude/agents"
SKIP_AGENTS=false

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

banner() {
    echo -e "${CYAN}"
    echo "     █████╗ ██████╗  ██████╗ ██╗   ██╗███████╗"
    echo "    ██╔══██╗██╔══██╗██╔════╝ ██║   ██║██╔════╝"
    echo "    ███████║██████╔╝██║  ███╗██║   ██║███████╗"
    echo "    ██╔══██║██╔══██╗██║   ██║██║   ██║╚════██║"
    echo "    ██║  ██║██║  ██║╚██████╔╝╚██████╔╝███████║"
    echo "    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝  ╚═════╝ ╚══════╝"
    echo -e "${NC}"
    echo -e "  ${BOLD}v${VERSION}${NC}${CYAN} - AI-Powered Security Testing Platform${NC}"
    echo "  See Everything. Miss Nothing."
    echo ""
}

count_agents() {
    local dir="$1"
    if [ -d "$dir" ]; then
        find "$dir" -maxdepth 1 -name "*.md" ! -name "_*" -type f 2>/dev/null | wc -l
    else
        echo 0
    fi
}

bootstrap_from_curl() {
    if ! command -v git &>/dev/null; then
        echo -e "${RED}Error: git is required for the one-line installer.${NC}"
        echo "  Install git first, or clone the repo manually."
        exit 1
    fi
    local tmp
    tmp=$(mktemp -d -t argus-XXXXXX)
    echo -e "${CYAN}Bootstrapping installer...${NC} (cloning ${REPO_URL})"
    if ! git clone --depth=1 --quiet "$REPO_URL" "$tmp/argus"; then
        echo -e "${RED}Error: git clone failed.${NC}"
        echo "  Check the repository URL or clone manually:"
        echo "    git clone ${REPO_URL}"
        rm -rf "$tmp"
        exit 1
    fi
    local args=("$@")
    [ ${#args[@]} -eq 0 ] && args=(--full)
    exec bash "$tmp/argus/scripts/install.sh" "${args[@]}"
}

check_prereqs() {
    if [ ! -d "$AGENTS_SRC" ]; then
        bootstrap_from_curl "$@"
    fi
}

install_agents_global() {
    echo -e "${BOLD}Installing Argus agents globally...${NC}"
    mkdir -p "$GLOBAL_DIR"

    local installed=0 updated=0 skipped=0
    for agent in "${AGENTS_SRC}"/*.md; do
        local name
        name=$(basename "$agent")
        # Only install files with Claude Code agent frontmatter (tools: field)
        if ! grep -q '^tools:' "$agent" 2>/dev/null; then
            continue
        fi
        local dest="${GLOBAL_DIR}/${name}"

        if [ -f "$dest" ]; then
            if ! diff -q "$agent" "$dest" &>/dev/null; then
                cp "$agent" "$dest"
                updated=$((updated + 1))
                echo -e "  ${YELLOW}updated${NC}  ${name}"
            else
                skipped=$((skipped + 1))
            fi
        else
            cp "$agent" "$dest"
            installed=$((installed + 1))
            echo -e "  ${GREEN}installed${NC} ${name}"
        fi
    done

    local total
    total=$(count_agents "$GLOBAL_DIR")
    echo ""
    echo -e "${GREEN}Done.${NC} ${total} agents available globally."
    [ $installed -gt 0 ] && echo -e "  ${GREEN}${installed} new${NC}"
    [ $updated -gt 0 ] && echo -e "  ${YELLOW}${updated} updated${NC}"
    [ $skipped -gt 0 ] && echo -e "  ${skipped} unchanged"
    echo ""
    echo -e "  Location: ${CYAN}${GLOBAL_DIR}${NC}"
    echo "  Agents are available in all Claude Code sessions."
}

install_agents_project() {
    echo -e "${BOLD}Installing Argus agents for this project...${NC}"
    mkdir -p "$PROJECT_DIR"

    local installed=0
    for agent in "${AGENTS_SRC}"/*.md; do
        local name
        name=$(basename "$agent")
        if ! grep -q '^tools:' "$agent" 2>/dev/null; then
            continue
        fi
        cp "$agent" "${PROJECT_DIR}/${name}"
        installed=$((installed + 1))
        echo -e "  ${GREEN}installed${NC} ${name}"
    done

    echo ""
    echo -e "${GREEN}Done.${NC} ${installed} agents installed to ${CYAN}${PROJECT_DIR}${NC}"
    echo "  Agents are available only in this directory."
}

install_full() {
    echo -e "${BOLD}Installing Argus platform...${NC}"
    echo ""

    if [ "$SKIP_AGENTS" = false ]; then
        install_agents_global
        echo ""
    fi

    local argus_root
    argus_root="$(cd "$SCRIPT_DIR/.." && pwd)"

    # Detect OS
    case "$(uname -s)" in
        Linux*)   OS="Linux" ;;
        Darwin*)  OS="macOS" ;;
        *)        OS="Unknown" ;;
    esac
    echo -e "  OS: ${CYAN}${OS}${NC}"

    # Check Python
    local PYTHON="${PYTHON:-python3}"
    if ! command -v "$PYTHON" &>/dev/null; then
        echo -e "${RED}Error: Python 3.8+ required. Install it first.${NC}"
        exit 1
    fi
    PYVER=$($PYTHON --version 2>&1 | awk '{print $2}')
    echo -e "  Python: ${CYAN}${PYVER}${NC}"

    # Create venv
    local VENV_DIR="${argus_root}/venv"
    if [ ! -d "$VENV_DIR" ]; then
        echo ""
        echo -e "  ${CYAN}Creating virtual environment...${NC}"
        $PYTHON -m venv "$VENV_DIR"
    fi

    source "$VENV_DIR/bin/activate"

    echo -e "  ${CYAN}Upgrading pip...${NC}"
    pip install --upgrade pip -q

    echo -e "  ${CYAN}Installing dependencies...${NC}"
    pip install -r "${argus_root}/requirements.txt" -q
    pip install -e "${argus_root}" -q
    
    echo -e "  ${CYAN}Installing Playwright browsers...${NC}"
    python -m playwright install chromium 2>/dev/null || true

    # Setup .env
    if [ ! -f "${argus_root}/.env" ]; then
        cp "${argus_root}/.env.example" "${argus_root}/.env"
        echo -e "  ${YELLOW}Created .env — edit it to add your API keys${NC}"
    fi

    # Create runtime directories
    mkdir -p "${argus_root}/argus_results"
    mkdir -p ~/.argus/sessions
    mkdir -p ~/.argus/graph_memory
    mkdir -p ~/.argus/plugins/agents
    mkdir -p ~/.argus/plugins/tools

    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Argus installed successfully!       ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
    echo ""
    echo "  Quick start:"
    echo "    cd ${argus_root}"
    echo "    source venv/bin/activate"
    echo "    argus --help"
    echo "    argus strix --target https://example.com"
    echo ""
    echo "  Claude Code agents installed at:"
    echo "    ${GLOBAL_DIR}"
    echo "  Available agents: $(count_agents "$GLOBAL_DIR")"
    echo ""
    echo "  Edit .env to add API keys, then:"
    echo "    argus strix --target example.com -m quick"
    echo ""
}

uninstall() {
    echo -e "${BOLD}Uninstalling Argus...${NC}"
    echo ""

    local removed=0

    # Remove global agents
    if [ -d "$GLOBAL_DIR" ]; then
        for agent in "${AGENTS_SRC}"/*.md; do
            local name
            name=$(basename "$agent")
            if ! grep -q '^tools:' "$agent" 2>/dev/null; then
                continue
            fi
            if [ -f "${GLOBAL_DIR}/${name}" ]; then
                rm "${GLOBAL_DIR}/${name}"
                removed=$((removed + 1))
                echo -e "  ${RED}removed${NC}  ${GLOBAL_DIR}/${name}"
            fi
        done
    fi

    # Remove project agents
    if [ -d "$PROJECT_DIR" ]; then
        for agent in "${AGENTS_SRC}"/*.md; do
            local name
            name=$(basename "$agent")
            if ! grep -q '^tools:' "$agent" 2>/dev/null; then
                continue
            fi
            if [ -f "${PROJECT_DIR}/${name}" ]; then
                rm "${PROJECT_DIR}/${name}"
                removed=$((removed + 1))
                echo -e "  ${RED}removed${NC}  ${PROJECT_DIR}/${name}"
            fi
        done
    fi

    if [ $removed -eq 0 ]; then
        echo "  No Argus agents found to remove."
    else
        echo ""
        echo -e "${GREEN}Done.${NC} Removed ${removed} agent files."
    fi

    echo ""
    echo -e "${YELLOW}Note:${NC} To remove the Python venv, run:"
    echo "  rm -rf venv/"
    echo ""
    echo "  To uninstall the Python package:"
    echo "  pip uninstall argus-security -y"
}

show_status() {
    echo -e "${BOLD}Argus Installation Status${NC}"
    echo ""

    local global_count
    global_count=$(count_agents "$GLOBAL_DIR")
    if [ "$global_count" -gt 0 ]; then
        echo -e "  Claude Code agents: ${GREEN}${global_count}${NC} in ${GLOBAL_DIR}"
    else
        echo -e "  Claude Code agents: ${YELLOW}not installed${NC}"
    fi

    if [ -d "$PROJECT_DIR" ]; then
        local project_count
        project_count=$(count_agents "$PROJECT_DIR")
        if [ "$project_count" -gt 0 ]; then
            echo -e "  Project agents: ${GREEN}${project_count}${NC} in ${PROJECT_DIR}"
        fi
    fi

    local source_count
    source_count=$(count_agents "$AGENTS_SRC")
    echo -e "  Available in repo: ${CYAN}${source_count} skills${NC}"

    if command -v argus &>/dev/null; then
        echo -e "  Argus CLI: ${GREEN}available${NC}"
    else
        echo -e "  Argus CLI: ${YELLOW}not in PATH${NC} (activate venv first)"
    fi

    if [ -d "venv" ]; then
        echo -e "  Virtual env: ${GREEN}present${NC}"
    else
        echo -e "  Virtual env: ${YELLOW}not created${NC}"
    fi
    echo ""
}

usage() {
    echo -e "${BOLD}Usage:${NC} ./install.sh [option]"
    echo ""
    echo "Options:"
    echo "  --full        Full install: agents + Python platform (default)"
    echo "  --global      Install agents globally (~/.claude/agents/) only"
    echo "  --project     Install agents for current project (.claude/agents/) only"
    echo "  --uninstall   Remove all Argus agents"
    echo "  --update      Update existing global agents"
    echo "  --status      Show installation status"
    echo "  --no-agents   Skip agent installation during full install"
    echo "  --help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  curl -fsSL https://raw.githubusercontent.com/argus/main/scripts/install.sh | bash"
    echo "  bash scripts/install.sh --full"
    echo "  bash scripts/install.sh --global"
    echo "  bash scripts/install.sh --status"
    echo ""
}

interactive() {
    echo "What would you like to do?"
    echo ""
    echo "  1) Full install (agents + Python platform)  ${BOLD}[Recommended]${NC}"
    echo "  2) Install agents globally only"
    echo "  3) Install agents for this project only"
    echo "  4) Show installation status"
    echo "  5) Uninstall agents"
    echo ""

    read -rp "Choice [1-5]: " choice

    case "$choice" in
        1) install_full ;;
        2) install_agents_global ;;
        3) install_agents_project ;;
        4) show_status ;;
        5) uninstall ;;
        *) echo "Invalid choice."; exit 1 ;;
    esac
}

# --- Main ---
banner
check_prereqs "$@"

# Parse flags
for arg in "$@"; do
    if [ "$arg" = "--no-agents" ]; then
        SKIP_AGENTS=true
    fi
done

PRIMARY=""
for arg in "$@"; do
    if [ "$arg" != "--no-agents" ]; then
        PRIMARY="$arg"
        break
    fi
done

case "${PRIMARY:-}" in
    --full|--install)  install_full ;;
    --global)          install_agents_global ;;
    --project)         install_agents_project ;;
    --uninstall)       uninstall ;;
    --update)          install_agents_global ;;
    --status)          show_status ;;
    --help|-h)         usage ;;
    "")                interactive ;;
    *)                 echo -e "${RED}Unknown option: ${PRIMARY}${NC}"; usage; exit 1 ;;
esac
