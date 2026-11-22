#!/usr/bin/env bash
# Copy the agent's refreshed reference files into the checkout, but only if they
# are what we expect: a modest number of small Markdown files and nothing else.
# Usage: accept-refresh.sh <downloaded-artifact-dir> <references-dir>
set -euo pipefail

src="$1/references"
dest="$2"

[ -d "$src" ] || { echo "No references/ folder in the artifact." >&2; exit 1; }
[ -f "$src/index.md" ] || { echo "The artifact has no index.md." >&2; exit 1; }

unexpected=$(find "$src" -mindepth 1 ! -type d ! \( -type f -name '*.md' \) -print)
if [ -n "$unexpected" ]; then
  echo "Refusing: the refresh produced something other than Markdown files:" >&2
  echo "$unexpected" >&2
  exit 1
fi

outside=$(find "$src" -mindepth 1 -type d ! -path "$src/techniques" -print)
if [ -n "$outside" ]; then
  echo "Refusing: unexpected folders:" >&2
  echo "$outside" >&2
  exit 1
fi

count=$(find "$src" -type f | wc -l)
[ "$count" -le 60 ] || { echo "Refusing: $count files is more than expected." >&2; exit 1; }

large=$(find "$src" -type f -size +64k -print)
if [ -n "$large" ]; then
  echo "Refusing: files over 64 KB:" >&2
  echo "$large" >&2
  exit 1
fi

rm -rf "$dest"
mkdir -p "$dest"
cp -R "$src/." "$dest/"
echo "Accepted $count reference files."
