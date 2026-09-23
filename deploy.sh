#!/bin/bash
# nekon.ai — Azure Infrastructure Deployment Script Wrapper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/deploy_azure.sh" "$@"
