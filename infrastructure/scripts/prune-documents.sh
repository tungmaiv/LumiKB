#!/bin/bash
# Document Pruning Script
# Deletes documents and all related artifacts (vectors, storage, traces, events)
#
# Usage:
#   ./prune-documents.sh <doc_id>     # Prune specific document
#   ./prune-documents.sh --all        # Prune all documents
#   ./prune-documents.sh --help       # Show help

# Note: not using set -e as we need to handle empty results gracefully

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
POSTGRES_CONTAINER="lumikb-postgres"
REDIS_CONTAINER="lumikb-redis"
MINIO_CONTAINER="lumikb-minio"
QDRANT_HOST="localhost"
QDRANT_PORT="6333"
DB_USER="lumikb"
DB_NAME="lumikb"
MINIO_BUCKET="lumikb-documents"
MINIO_ACCESS_KEY="${MINIO_ROOT_USER:-lumikb}"
MINIO_SECRET_KEY="${MINIO_ROOT_PASSWORD:-lumikb_dev_password}"

# Setup MinIO alias
setup_minio() {
    docker exec "$MINIO_CONTAINER" mc alias set myminio http://localhost:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY" >/dev/null 2>&1 || true
}

show_help() {
    echo -e "${BLUE}Document Pruning Script${NC}"
    echo ""
    echo "Deletes documents and all related artifacts:"
    echo "  - PostgreSQL records (documents, drafts, traces, spans, events)"
    echo "  - Qdrant vectors"
    echo "  - MinIO stored files"
    echo "  - Redis cached data"
    echo ""
    echo "Usage:"
    echo "  $0 <document_id>   Prune specific document by UUID"
    echo "  $0 --all           Prune ALL documents (requires confirmation)"
    echo "  $0 --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 550e8400-e29b-41d4-a716-446655440000"
    echo "  $0 --all"
}

confirm_action() {
    local message="$1"
    echo -e "${YELLOW}WARNING: $message${NC}"
    echo -e "${RED}This action is IRREVERSIBLE!${NC}"
    read -p "Type 'yes' to confirm: " confirmation
    if [[ "$confirmation" != "yes" ]]; then
        echo "Operation cancelled."
        exit 0
    fi
}

run_psql() {
    docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "$1" 2>/dev/null
}

prune_single_document() {
    local doc_id="$1"

    # Setup MinIO alias
    setup_minio

    echo -e "${BLUE}=== Pruning document: $doc_id ===${NC}"

    # Get document info
    local doc_info=$(run_psql "SELECT name, kb_id, file_path FROM documents WHERE id = '$doc_id';")

    if [[ -z "$doc_info" || "$doc_info" == *"0 rows"* ]]; then
        echo -e "${RED}Document not found: $doc_id${NC}"
        exit 1
    fi

    local kb_id=$(run_psql "SELECT kb_id FROM documents WHERE id = '$doc_id';" | tr -d ' ')
    local file_path=$(run_psql "SELECT file_path FROM documents WHERE id = '$doc_id';" | tr -d ' ')

    echo -e "Document: ${GREEN}$(echo $doc_info | head -1)${NC}"
    echo ""

    confirm_action "You are about to delete document $doc_id and all related data"

    echo ""
    echo -e "${BLUE}1/5 Deleting Qdrant vectors...${NC}"
    # Delete vectors from Qdrant
    if [[ -n "$kb_id" ]]; then
        curl -s -X POST "http://$QDRANT_HOST:$QDRANT_PORT/collections/kb_$kb_id/points/delete" \
            -H "Content-Type: application/json" \
            -d "{\"filter\": {\"must\": [{\"key\": \"document_id\", \"match\": {\"value\": \"$doc_id\"}}]}}" > /dev/null 2>&1 || echo "  (Collection may not exist)"
        echo -e "  ${GREEN}Done${NC}"
    fi

    echo -e "${BLUE}2/5 Deleting MinIO files...${NC}"
    # Delete from MinIO
    if [[ -n "$file_path" && "$file_path" != "null" ]]; then
        docker exec "$MINIO_CONTAINER" mc rm --force "myminio/$MINIO_BUCKET/$file_path" 2>/dev/null || echo "  (File may not exist)"
        # Also try to delete parsed content
        docker exec "$MINIO_CONTAINER" mc rm --force "myminio/$MINIO_BUCKET/parsed/${doc_id}.json" 2>/dev/null || true
        echo -e "  ${GREEN}Done${NC}"
    fi

    echo -e "${BLUE}3/5 Deleting observability data...${NC}"
    run_psql "DELETE FROM observability.spans WHERE trace_id IN (SELECT id FROM observability.traces WHERE document_id = '$doc_id');" > /dev/null 2>&1 || true
    run_psql "DELETE FROM observability.traces WHERE document_id = '$doc_id';" > /dev/null 2>&1 || true
    run_psql "DELETE FROM observability.document_events WHERE document_id = '$doc_id';" > /dev/null 2>&1 || true
    echo -e "  ${GREEN}Done${NC}"

    echo -e "${BLUE}4/5 Deleting related records...${NC}"
    run_psql "DELETE FROM drafts WHERE document_id = '$doc_id';" > /dev/null 2>&1 || true
    run_psql "DELETE FROM audit.events WHERE entity_id = '$doc_id' AND entity_type = 'document';" > /dev/null 2>&1 || true
    echo -e "  ${GREEN}Done${NC}"

    echo -e "${BLUE}5/5 Deleting document record...${NC}"
    run_psql "DELETE FROM documents WHERE id = '$doc_id';" > /dev/null 2>&1 || true
    echo -e "  ${GREEN}Done${NC}"

    echo -e "${BLUE}6/6 Clearing Redis cache...${NC}"
    docker exec "$REDIS_CONTAINER" redis-cli KEYS "*$doc_id*" 2>/dev/null | xargs -r docker exec -i "$REDIS_CONTAINER" redis-cli DEL 2>/dev/null || true
    echo -e "  ${GREEN}Done${NC}"

    echo ""
    echo -e "${GREEN}=== Document $doc_id successfully pruned ===${NC}"
}

prune_all_documents() {
    # Setup MinIO alias
    setup_minio

    echo -e "${BLUE}=== Pruning ALL documents ===${NC}"

    # Get document count
    local doc_count=$(run_psql "SELECT COUNT(*) FROM documents;" | tr -d ' ')
    local kb_ids=$(run_psql "SELECT DISTINCT kb_id FROM documents;" | tr -d ' ')

    echo "Found $doc_count documents to delete"
    echo ""

    confirm_action "You are about to delete ALL $doc_count documents and related data"

    echo ""
    echo -e "${BLUE}1/6 Deleting all Qdrant collections...${NC}"
    # Get all KB collections and delete vectors
    for kb_id in $kb_ids; do
        if [[ -n "$kb_id" && "$kb_id" != "" ]]; then
            curl -s -X DELETE "http://$QDRANT_HOST:$QDRANT_PORT/collections/kb_$kb_id" > /dev/null 2>&1 || true
        fi
    done
    echo -e "  ${GREEN}Done${NC}"

    echo -e "${BLUE}2/6 Deleting all MinIO document files...${NC}"
    docker exec "$MINIO_CONTAINER" mc rm --recursive --force "myminio/$MINIO_BUCKET/" 2>/dev/null || echo "  (Bucket may be empty)"
    echo -e "  ${GREEN}Done${NC}"

    echo -e "${BLUE}3/6 Deleting all observability data...${NC}"
    run_psql "TRUNCATE TABLE observability.spans CASCADE;" > /dev/null 2>&1 || true
    run_psql "TRUNCATE TABLE observability.traces CASCADE;" > /dev/null 2>&1 || true
    run_psql "TRUNCATE TABLE observability.document_events CASCADE;" > /dev/null 2>&1 || true
    run_psql "TRUNCATE TABLE observability.chat_messages CASCADE;" > /dev/null 2>&1 || true
    run_psql "TRUNCATE TABLE observability.metrics_aggregates CASCADE;" > /dev/null 2>&1 || true
    echo -e "  ${GREEN}Done${NC}"

    echo -e "${BLUE}4/6 Deleting all related records...${NC}"
    run_psql "TRUNCATE TABLE drafts CASCADE;" > /dev/null 2>&1 || true
    run_psql "DELETE FROM audit.events WHERE entity_type = 'document';" > /dev/null 2>&1 || true
    run_psql "TRUNCATE TABLE public.outbox CASCADE;" > /dev/null 2>&1 || true
    echo -e "  ${GREEN}Done${NC}"

    echo -e "${BLUE}5/6 Deleting all document records...${NC}"
    run_psql "TRUNCATE TABLE documents CASCADE;" > /dev/null 2>&1 || true
    echo -e "  ${GREEN}Done${NC}"

    echo -e "${BLUE}6/6 Flushing Redis cache...${NC}"
    docker exec "$REDIS_CONTAINER" redis-cli FLUSHALL > /dev/null 2>&1 || true
    echo -e "  ${GREEN}Done${NC}"

    echo ""
    echo -e "${GREEN}=== All documents successfully pruned ===${NC}"
}

# Main
case "$1" in
    --help|-h)
        show_help
        ;;
    --all)
        prune_all_documents
        ;;
    "")
        show_help
        exit 1
        ;;
    *)
        # Validate UUID format
        if [[ ! "$1" =~ ^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$ ]]; then
            echo -e "${RED}Invalid document ID format. Expected UUID.${NC}"
            exit 1
        fi
        prune_single_document "$1"
        ;;
esac
