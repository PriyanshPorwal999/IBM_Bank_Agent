#!/bin/bash

# Sync Better Branch to Upstream RD Branch
# Usage: ./sync-to-upstream.sh

set -e

echo "🔄 Syncing 'better' branch to upstream 'RD' branch..."

# Ensure we're on the better branch
echo "📋 Checking current branch..."
git checkout better

# Fetch latest from upstream
echo "⬇️ Fetching latest from upstream..."
git fetch upstream

# Check if upstream RD branch exists
if git show-ref --verify --quiet refs/remotes/upstream/RD; then
    echo "📍 Upstream RD branch exists, updating..."
else
    echo "🆕 Creating new RD branch in upstream..."
fi

# Push better branch to upstream RD
echo "⬆️ Pushing to upstream RD branch..."
git push upstream better:RD

echo "✅ Successfully synced 'better' branch to 'upstream/RD'"
echo ""
echo "🔗 Check the upstream repository:"
echo "   https://github.com/PriyanshPorwal999/IBM_Bank_Agent/tree/RD"
