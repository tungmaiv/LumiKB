#!/bin/bash
# LumiKB Demo Knowledge Base Seeding Script
#
# This script sets up the demo KB with sample documents and pre-computed embeddings.
# It is idempotent - running it multiple times will not create duplicate data.
#
# Usage:
#   ./seed-data.sh              # Full seeding (requires all services running)
#   ./seed-data.sh --skip-embeddings  # Skip Qdrant vector insertion
#   ./seed-data.sh --skip-minio       # Skip MinIO file upload
#
# Prerequisites:
#   - PostgreSQL running and migrations applied
#   - MinIO running (unless --skip-minio)
#   - Qdrant running (unless --skip-embeddings)
#   - Python virtual environment with dependencies installed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_DIR="$BACKEND_DIR/.venv"

echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   LumiKB Demo Knowledge Base Seeding Script    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_DIR${NC}"
    echo "Please run: cd backend && python -m venv .venv && pip install -e ."
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Check if required packages are installed
python -c "import sqlalchemy" 2>/dev/null || {
    echo -e "${RED}Error: sqlalchemy not installed. Run: pip install -e .[all]${NC}"
    exit 1
}

python -c "import argon2" 2>/dev/null || {
    echo -e "${RED}Error: argon2-cffi not installed. Run: pip install argon2-cffi${NC}"
    exit 1
}

# Check if embeddings file exists, generate if not
EMBEDDINGS_FILE="$PROJECT_ROOT/infrastructure/seed/demo-embeddings.json"
if [ ! -f "$EMBEDDINGS_FILE" ]; then
    echo -e "${YELLOW}Embeddings file not found, generating placeholder embeddings...${NC}"
    python "$SCRIPT_DIR/generate-embeddings.py" --placeholder
fi

# Run seed script with any provided arguments
echo ""
echo -e "${YELLOW}Running seed-data.py...${NC}"
echo ""

cd "$PROJECT_ROOT"
python "$SCRIPT_DIR/seed-data.py" "$@"

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Seeding Complete!                     ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "Demo user credentials:"
echo -e "  Email:    demo@lumikb.local"
echo -e "  Password: ${DEMO_USER_PASSWORD:-demo123}"
echo ""
echo -e "You can now log in and explore the Sample Knowledge Base."
