#!/bin/bash

set -euo pipefail

repo=virtee/tdx-measure

auth_args=()
if [ -n "${GITHUB_TOKEN:-}" ]; then
    auth_args=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
fi

latest_release=$(curl -fsSL "${auth_args[@]}" \
    -H "Accept: application/vnd.github+json" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/${repo}/releases/latest" \
    | grep -o '"tag_name": "[^"]*"' | cut -d'"' -f4 || true)

if [ -z "${latest_release}" ]; then
    echo "Failed to resolve latest release tag for ${repo}" >&2
    exit 1
fi

echo "Fetching tdx-measure ${latest_release}"
curl -fsSL "${auth_args[@]}" \
    "https://github.com/${repo}/releases/download/${latest_release}/tdx-measure" \
    -o tdx-measure

# Sanity-check that we got a real ELF binary, not an HTML error page
if ! head -c 4 tdx-measure | grep -q $'\x7fELF'; then
    echo "Downloaded tdx-measure is not an ELF binary:" >&2
    file tdx-measure || true
    head -c 200 tdx-measure >&2 || true
    exit 1
fi

chmod +x tdx-measure
