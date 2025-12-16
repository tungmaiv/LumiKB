#!/bin/bash
# Data Consistency Check Script
# Finds orphan items across PostgreSQL, Qdrant, and MinIO
#
# Usage:
#   ./check-consistency.sh           # Run all checks
#   ./check-consistency.sh --fix     # Run checks and offer to fix orphans

# Note: not using set -e as we need to handle empty results gracefully

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
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

FIX_MODE=false
ISSUES_FOUND=0

if [[ "$1" == "--fix" ]]; then
    FIX_MODE=true
fi

run_psql() {
    docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "$1" 2>/dev/null
}

run_psql_count() {
    docker exec "$POSTGRES_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c "$1" 2>/dev/null | tr -d ' '
}

# Configure MinIO mc alias
setup_minio_alias() {
    docker exec "$MINIO_CONTAINER" mc alias set myminio http://localhost:9000 "$MINIO_ACCESS_KEY" "$MINIO_SECRET_KEY" >/dev/null 2>&1 || true
}

# List files in MinIO bucket
list_minio_files() {
    docker exec "$MINIO_CONTAINER" mc ls "myminio/$MINIO_BUCKET/" --recursive 2>/dev/null | awk '{print $NF}' || true
}

# Check if file exists in MinIO
check_minio_file() {
    local file_path="$1"
    docker exec "$MINIO_CONTAINER" mc stat "myminio/$MINIO_BUCKET/$file_path" >/dev/null 2>&1
}

# Delete file from MinIO
delete_minio_file() {
    local file_path="$1"
    docker exec "$MINIO_CONTAINER" mc rm "myminio/$MINIO_BUCKET/$file_path" >/dev/null 2>&1
}

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              LumiKB Data Consistency Check                       ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Setup MinIO alias
setup_minio_alias

# =============================================================================
# 1. Check for orphan Qdrant vectors (vectors without documents)
# =============================================================================
echo -e "${CYAN}[1/8] Checking for orphan Qdrant vectors...${NC}"

# Get all KB collections from Qdrant
collections=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections" | grep -oP '"name":"kb_[^"]+' | cut -d'"' -f4 || true)

orphan_vectors=0
for collection in $collections; do
    kb_id="${collection#kb_}"

    # Check if KB exists
    kb_exists=$(run_psql_count "SELECT COUNT(*) FROM knowledge_bases WHERE id = '$kb_id';")

    if [[ "$kb_exists" == "0" ]]; then
        echo -e "  ${YELLOW}Orphan collection: $collection (KB not in database)${NC}"
        ((orphan_vectors++)) || true
        ((ISSUES_FOUND++)) || true

        if [[ "$FIX_MODE" == true ]]; then
            echo -e "    ${BLUE}Deleting orphan collection...${NC}"
            curl -s -X DELETE "http://$QDRANT_HOST:$QDRANT_PORT/collections/$collection" > /dev/null
            echo -e "    ${GREEN}Deleted${NC}"
        fi
    else
        # Check for vectors pointing to non-existent documents
        # Get sample document IDs from collection
        sample=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections/$collection/points/scroll" \
            -H "Content-Type: application/json" \
            -d '{"limit": 100, "with_payload": true}' 2>/dev/null || echo "{}")

        doc_ids=$(echo "$sample" | grep -oP '"document_id":"[^"]+' | cut -d'"' -f4 | sort -u || true)

        for doc_id in $doc_ids; do
            if [[ -n "$doc_id" ]]; then
                doc_exists=$(run_psql_count "SELECT COUNT(*) FROM documents WHERE id = '$doc_id';")
                if [[ "$doc_exists" == "0" ]]; then
                    echo -e "  ${YELLOW}Orphan vectors: document $doc_id in $collection${NC}"
                    ((orphan_vectors++)) || true
                    ((ISSUES_FOUND++)) || true

                    if [[ "$FIX_MODE" == true ]]; then
                        echo -e "    ${BLUE}Deleting orphan vectors...${NC}"
                        curl -s -X POST "http://$QDRANT_HOST:$QDRANT_PORT/collections/$collection/points/delete" \
                            -H "Content-Type: application/json" \
                            -d "{\"filter\": {\"must\": [{\"key\": \"document_id\", \"match\": {\"value\": \"$doc_id\"}}]}}" > /dev/null
                        echo -e "    ${GREEN}Deleted${NC}"
                    fi
                fi
            fi
        done
    fi
done

if [[ $orphan_vectors -eq 0 ]]; then
    echo -e "  ${GREEN}No orphan vectors found${NC}"
fi

# =============================================================================
# 2. Check for orphan MinIO files (files without documents)
# =============================================================================
echo ""
echo -e "${CYAN}[2/8] Checking for orphan MinIO files...${NC}"

# List files in MinIO and check against database
minio_files=$(list_minio_files)
orphan_files=0

for file_path in $minio_files; do
    if [[ -n "$file_path" ]]; then
        # Check if file is referenced by any document
        file_exists=$(run_psql_count "SELECT COUNT(*) FROM documents WHERE file_path = '$file_path';")

        if [[ "$file_exists" == "0" ]]; then
            # Skip parsed content files (different pattern)
            if [[ ! "$file_path" =~ ^parsed/ ]]; then
                echo -e "  ${YELLOW}Orphan file: $file_path${NC}"
                ((orphan_files++)) || true
                ((ISSUES_FOUND++)) || true

                if [[ "$FIX_MODE" == true ]]; then
                    echo -e "    ${BLUE}Deleting orphan file...${NC}"
                    delete_minio_file "$file_path"
                    echo -e "    ${GREEN}Deleted${NC}"
                fi
            fi
        fi
    fi
done

if [[ $orphan_files -eq 0 ]]; then
    echo -e "  ${GREEN}No orphan files found${NC}"
fi

# =============================================================================
# 3. Check for documents without files in MinIO
# =============================================================================
echo ""
echo -e "${CYAN}[3/8] Checking for documents missing files in MinIO...${NC}"

missing_files=$(run_psql "SELECT id, file_path FROM documents WHERE file_path IS NOT NULL AND status != 'pending';")
docs_missing_files=0

while IFS='|' read -r doc_id file_path; do
    doc_id=$(echo "$doc_id" | tr -d ' ')
    file_path=$(echo "$file_path" | tr -d ' ')

    if [[ -n "$doc_id" && -n "$file_path" ]]; then
        # Check if file exists in MinIO
        if ! check_minio_file "$file_path"; then
            echo -e "  ${YELLOW}Document $doc_id missing file: $file_path${NC}"
            ((docs_missing_files++)) || true
            ((ISSUES_FOUND++)) || true
        fi
    fi
done <<< "$missing_files"

if [[ $docs_missing_files -eq 0 ]]; then
    echo -e "  ${GREEN}All documents have their files${NC}"
fi

# =============================================================================
# 4. Check for documents without vectors (completed status)
# =============================================================================
echo ""
echo -e "${CYAN}[4/8] Checking for completed documents missing vectors...${NC}"

completed_docs=$(run_psql "SELECT id, kb_id, chunk_count FROM documents WHERE status = 'completed' AND chunk_count > 0;")
docs_missing_vectors=0

while IFS='|' read -r doc_id kb_id chunk_count; do
    doc_id=$(echo "$doc_id" | tr -d ' ')
    kb_id=$(echo "$kb_id" | tr -d ' ')
    chunk_count=$(echo "$chunk_count" | tr -d ' ')

    if [[ -n "$doc_id" && -n "$kb_id" ]]; then
        # Count vectors in Qdrant for this document
        vector_count=$(curl -s -X POST "http://$QDRANT_HOST:$QDRANT_PORT/collections/kb_$kb_id/points/count" \
            -H "Content-Type: application/json" \
            -d "{\"filter\": {\"must\": [{\"key\": \"document_id\", \"match\": {\"value\": \"$doc_id\"}}]}}" 2>/dev/null \
            | grep -oP '"count":\d+' | cut -d':' -f2 || echo "0")

        if [[ "$vector_count" == "0" || -z "$vector_count" ]]; then
            echo -e "  ${YELLOW}Document $doc_id has no vectors (expected $chunk_count chunks)${NC}"
            ((docs_missing_vectors++)) || true
            ((ISSUES_FOUND++)) || true
        elif [[ "$vector_count" != "$chunk_count" ]]; then
            echo -e "  ${YELLOW}Document $doc_id: vector count mismatch (DB: $chunk_count, Qdrant: $vector_count)${NC}"
            ((ISSUES_FOUND++)) || true
        fi
    fi
done <<< "$completed_docs"

if [[ $docs_missing_vectors -eq 0 ]]; then
    echo -e "  ${GREEN}All completed documents have vectors${NC}"
fi

# =============================================================================
# 5. Check for orphan traces (traces without documents)
# =============================================================================
echo ""
echo -e "${CYAN}[5/8] Checking for orphan traces...${NC}"

orphan_traces=$(run_psql_count "
    SELECT COUNT(*) FROM observability.traces t
    WHERE t.document_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM documents d WHERE d.id = t.document_id);
")

if [[ "$orphan_traces" != "0" && -n "$orphan_traces" ]]; then
    echo -e "  ${YELLOW}Found $orphan_traces orphan traces${NC}"
    ((ISSUES_FOUND++)) || true

    if [[ "$FIX_MODE" == true ]]; then
        echo -e "    ${BLUE}Deleting orphan traces and spans...${NC}"
        run_psql "DELETE FROM observability.spans WHERE trace_id IN (SELECT id FROM observability.traces WHERE document_id IS NOT NULL AND document_id NOT IN (SELECT id FROM documents));" > /dev/null
        run_psql "DELETE FROM observability.traces WHERE document_id IS NOT NULL AND document_id NOT IN (SELECT id FROM documents);" > /dev/null
        echo -e "    ${GREEN}Deleted${NC}"
    fi
else
    echo -e "  ${GREEN}No orphan traces found${NC}"
fi

# =============================================================================
# 6. Check for orphan spans (spans without traces)
# =============================================================================
echo ""
echo -e "${CYAN}[6/8] Checking for orphan spans...${NC}"

orphan_spans=$(run_psql_count "
    SELECT COUNT(*) FROM observability.spans s
    WHERE NOT EXISTS (SELECT 1 FROM observability.traces t WHERE t.id = s.trace_id);
")

if [[ "$orphan_spans" != "0" && -n "$orphan_spans" ]]; then
    echo -e "  ${YELLOW}Found $orphan_spans orphan spans${NC}"
    ((ISSUES_FOUND++)) || true

    if [[ "$FIX_MODE" == true ]]; then
        echo -e "    ${BLUE}Deleting orphan spans...${NC}"
        run_psql "DELETE FROM observability.spans WHERE trace_id NOT IN (SELECT id FROM observability.traces);" > /dev/null
        echo -e "    ${GREEN}Deleted${NC}"
    fi
else
    echo -e "  ${GREEN}No orphan spans found${NC}"
fi

# =============================================================================
# 7. Check for orphan drafts (drafts without documents)
# =============================================================================
echo ""
echo -e "${CYAN}[7/8] Checking for orphan drafts...${NC}"

orphan_drafts=$(run_psql_count "
    SELECT COUNT(*) FROM drafts dr
    WHERE dr.document_id IS NOT NULL
    AND NOT EXISTS (SELECT 1 FROM documents d WHERE d.id = dr.document_id);
")

if [[ "$orphan_drafts" != "0" && -n "$orphan_drafts" ]]; then
    echo -e "  ${YELLOW}Found $orphan_drafts orphan drafts${NC}"
    ((ISSUES_FOUND++)) || true

    if [[ "$FIX_MODE" == true ]]; then
        echo -e "    ${BLUE}Deleting orphan drafts...${NC}"
        run_psql "DELETE FROM drafts WHERE document_id IS NOT NULL AND document_id NOT IN (SELECT id FROM documents);" > /dev/null
        echo -e "    ${GREEN}Deleted${NC}"
    fi
else
    echo -e "  ${GREEN}No orphan drafts found${NC}"
fi

# =============================================================================
# 8. Check for KB permission inconsistencies
# =============================================================================
echo ""
echo -e "${CYAN}[8/8] Checking for orphan KB permissions...${NC}"

orphan_kb_perms=$(run_psql_count "
    SELECT COUNT(*) FROM kb_permissions kp
    WHERE NOT EXISTS (SELECT 1 FROM knowledge_bases kb WHERE kb.id = kp.kb_id);
")

if [[ "$orphan_kb_perms" != "0" && -n "$orphan_kb_perms" ]]; then
    echo -e "  ${YELLOW}Found $orphan_kb_perms orphan KB permissions${NC}"
    ((ISSUES_FOUND++)) || true

    if [[ "$FIX_MODE" == true ]]; then
        echo -e "    ${BLUE}Deleting orphan KB permissions...${NC}"
        run_psql "DELETE FROM kb_permissions WHERE kb_id NOT IN (SELECT id FROM knowledge_bases);" > /dev/null
        echo -e "    ${GREEN}Deleted${NC}"
    fi
else
    echo -e "  ${GREEN}No orphan KB permissions found${NC}"
fi

# =============================================================================
# Summary
# =============================================================================
echo ""
echo -e "${BLUE}══════════════════════════════════════════════════════════════════${NC}"

if [[ $ISSUES_FOUND -eq 0 ]]; then
    echo -e "${GREEN}All consistency checks passed! No orphan items found.${NC}"
else
    echo -e "${YELLOW}Found $ISSUES_FOUND potential issues.${NC}"
    if [[ "$FIX_MODE" == false ]]; then
        echo -e "Run with ${CYAN}--fix${NC} flag to automatically clean up orphan items."
    else
        echo -e "${GREEN}Cleanup completed.${NC}"
    fi
fi

echo ""

# Statistics
echo -e "${BLUE}=== Current Statistics ===${NC}"
doc_count=$(run_psql_count "SELECT COUNT(*) FROM documents;")
kb_count=$(run_psql_count "SELECT COUNT(*) FROM knowledge_bases;")
trace_count=$(run_psql_count "SELECT COUNT(*) FROM observability.traces;")
span_count=$(run_psql_count "SELECT COUNT(*) FROM observability.spans;")

echo "Documents:       $doc_count"
echo "Knowledge Bases: $kb_count"
echo "Traces:          $trace_count"
echo "Spans:           $span_count"
echo ""

# Qdrant stats
echo -e "${BLUE}=== Qdrant Collections ===${NC}"
curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections" 2>/dev/null | \
    grep -oP '"name":"[^"]+' | cut -d'"' -f4 | while read col; do
        points=$(curl -s "http://$QDRANT_HOST:$QDRANT_PORT/collections/$col" 2>/dev/null | grep -oP '"points_count":\d+' | cut -d':' -f2 || echo "0")
        echo "  $col: $points points"
    done || echo "  (No collections)"

echo ""
