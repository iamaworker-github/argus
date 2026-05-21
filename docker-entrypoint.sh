#!/bin/bash
# Argus Docker Entrypoint — Shannon-grade
set -e

# Build args from environment
ARGS=()

# Auth profile
if [ -n "$AUTH_PROFILE" ]; then
    ARGS+=("--profile" "$AUTH_PROFILE")
fi

# Strict PoC mode
if [ -n "$STRICT_POC" ]; then
    ARGS+=("--strict-poc" "$STRICT_POC")
fi

# Checkpointing
if [ "$CHECKPOINT_ENABLED" = "true" ]; then
    ARGS+=("--checkpoint")
fi

case "${1}" in
    api|serve)
        exec argus api --host 0.0.0.0 --port "${ARGUS_API_PORT:-8484}"
        ;;
    repl)
        exec argus repl
        ;;
    monitor)
        shift
        exec argus monitor "$@"
        ;;
    campaign)
        shift
        exec argus campaign "$@"
        ;;
    graph)
        shift
        exec argus graph "$@"
        ;;
    deep)
        # Deep+Slow+Accurate mode — Shannon's "quality over quantity"
        shift
        exec argus strix --scan-mode deep --strict-poc strict "${ARGS[@]}" "$@"
        ;;
    quick)
        # Quick scan — fast pass
        shift
        exec argus strix --scan-mode quick "$@"
        ;;
    whitebox)
        # White-box scan with source-sink analysis
        shift
        exec argus strix --sub-mode whitebox --scan-mode deep --strict-poc strict "${ARGS[@]}" "$@"
        ;;
    scan|strix)
        exec argus "$@" "${ARGS[@]}"
        ;;
    shell|bash)
        exec /bin/bash
        ;;
    "")
        echo "Argus — AI-Powered Security Testing Platform"
        echo ""
        echo "Usage: docker run argus [COMMAND] [OPTIONS]"
        echo ""
        echo "Commands:"
        echo "  argus strix --target <url>     Standard scan"
        echo "  deep    --target <url>          Deep+Slow+Accurate mode"
        echo "  quick   --target <url>          Quick pass"
        echo "  whitebox --target <dir>         White-box source-sink analysis"
        echo "  api                              Start API server"
        echo "  repl                             Interactive shell"
        echo ""
        echo "Environment:"
        echo "  STRICT_POC=strict|shadow|off     No Exploit No Report policy"
        echo "  AUTH_PROFILE=<name>              Auth profile from ~/.argus/auth-profiles/"
        echo "  CHECKPOINT_ENABLED=true           Enable workspace resume"
        echo "  SCAN_DEPTH=deep|standard|quick    Scan depth"
        echo ""
        exec argus --help
        ;;
    *)
        exec argus "$@"
        ;;
esac
