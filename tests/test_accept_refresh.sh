#!/usr/bin/env bash
# Tests for .github/scripts/accept-refresh.sh: it must accept a normal refresh and
# refuse anything that isn't a small Markdown file under references/.
set -uo pipefail

script="$(cd "$(dirname "$0")/.." && pwd)/.github/scripts/accept-refresh.sh"
real="$(cd "$(dirname "$0")/.." && pwd)/skills/agent-coach/references"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail=0

fresh() {  # a clean copy of the real references, as the agent job would upload it
  rm -rf "$tmp/art" "$tmp/dest"
  mkdir -p "$tmp/art"
  cp -R "$real" "$tmp/art/references"
}

expect() {  # expect <accept|refuse> <description>
  if bash "$script" "$tmp/art" "$tmp/dest" >/dev/null 2>&1; then got=accept; else got=refuse; fi
  if [ "$got" = "$1" ]; then echo "ok: $2"; else echo "FAIL: $2 (expected $1, got $got)"; fail=1; fi
}

fresh; expect accept "a normal refresh"
[ -f "$tmp/dest/index.md" ] && [ -f "$tmp/dest/techniques/03-verification.md" ] || { echo "FAIL: files were not copied"; fail=1; }

fresh; rm "$tmp/art/references/techniques/17-evals.md"; mkdir -p "$tmp/dest/techniques"; touch "$tmp/dest/techniques/17-evals.md"
expect accept "a retired technique"
[ ! -e "$tmp/dest/techniques/17-evals.md" ] || { echo "FAIL: retired file was left behind"; fail=1; }

fresh; echo 'import os' > "$tmp/art/references/evil.py";            expect refuse "a script among the files"
fresh; ln -s /etc/passwd "$tmp/art/references/link.md";             expect refuse "a symlink"
fresh; mkdir "$tmp/art/references/extra"; echo x > "$tmp/art/references/extra/a.md"; expect refuse "an unexpected folder"
fresh; head -c 70000 /dev/zero | tr '\0' 'a' > "$tmp/art/references/big.md"; expect refuse "an oversized file"
fresh; rm "$tmp/art/references/index.md";                           expect refuse "a missing index"
fresh; rm -rf "$tmp/art/references";                                expect refuse "a missing references folder"

exit $fail
