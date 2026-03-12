#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# push_to_github.sh
#
# Initialises a local git repo and pushes to a new GitHub repository.
#
# Usage:
#   chmod +x push_to_github.sh
#   GITHUB_TOKEN=ghp_xxx GITHUB_USER=yourname ./push_to_github.sh
#
# Or with a custom repo name:
#   GITHUB_TOKEN=ghp_xxx GITHUB_USER=yourname REPO_NAME=my-tracker ./push_to_github.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

GITHUB_USER="${GITHUB_USER:?Set GITHUB_USER to your GitHub username}"
GITHUB_TOKEN="${GITHUB_TOKEN:?Set GITHUB_TOKEN to your Personal Access Token}"
REPO_NAME="${REPO_NAME:-vehicle-maintenance}"
DESCRIPTION="Self-hosted vehicle maintenance tracker built with Flask and SQLite"

echo "▶  Initialising git repository..."
git init
git add .
git commit -m "Initial commit: Vehicle Maintenance Tracker

- Flask + SQLite web app for tracking vehicle service history
- Multi-vehicle support (cars, motorcycles, ATVs, boats)
- Receipt upload (PDF, images)
- 17 default service types + custom types
- Cost reports and overdue-mileage alerts
- 35 unit and integration tests
- GitHub Actions CI"

echo "▶  Creating GitHub repository '$REPO_NAME'..."
curl -s -X POST \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/user/repos \
  -d "{\"name\": \"${REPO_NAME}\", \"description\": \"${DESCRIPTION}\", \"private\": false}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('  Repo URL:', d.get('html_url', d.get('message','error')))"

echo "▶  Pushing to GitHub..."
git remote add origin "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${GITHUB_USER}/${REPO_NAME}.git"
git branch -M main
git push -u origin main

echo ""
echo "✅  Done! Your repository is live at:"
echo "    https://github.com/${GITHUB_USER}/${REPO_NAME}"
