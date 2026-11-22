#!/usr/bin/env bash
# Run the refresh agent with the Claude Code CLI directly (`claude -p`).
#
# Why not the Claude Code GitHub Action: usage through that action is billed as
# Claude Code usage, which a Claude plan's monthly API credits don't cover.
# `claude -p` that you run yourself is billed as Agent SDK usage, which they do.
#
# Sign-in: keyless when ANTHROPIC_FEDERATION_RULE_ID and ANTHROPIC_ORGANIZATION_ID
# are set (the Claude API checks this workflow's GitHub identity), otherwise the
# ANTHROPIC_API_KEY secret.
set -euo pipefail
umask 077

out="$RUNNER_TEMP/claude-execution-output.json"
prompt="Follow skills/agent-coach/references/REFRESH.md exactly. Today's date is $(date -u +%F)."

# The agent may read and edit files and fetch from the source sites. Nothing else.
sources="code.claude.com www.anthropic.com anthropic.com learn.chatgpt.com developers.openai.com
  openai.com antigravity.google developers.googleblog.com cursor.com docs.github.com github.blog
  raw.githubusercontent.com agents.md agentskills.io simonwillison.net"
allowed="Read,Glob,Grep,Edit,Write"
for domain in $sources; do allowed="$allowed,WebFetch(domain:$domain)"; done
# No shell, no web search, and no reading of process memory or the runner's temp
# folder, which is where the sign-in token is kept.
denied="Bash,WebSearch,Read(//proc/**),Read(/$RUNNER_TEMP/**)"

# An empty credential variable can shadow a real one, so drop the empty ones.
for name in ANTHROPIC_API_KEY ANTHROPIC_FEDERATION_RULE_ID ANTHROPIC_ORGANIZATION_ID \
            ANTHROPIC_SERVICE_ACCOUNT_ID ANTHROPIC_WORKSPACE_ID REFRESH_MODEL; do
  [ -n "${!name:-}" ] || unset "$name"
done

if [ -n "${ANTHROPIC_FEDERATION_RULE_ID:-}" ] && [ -n "${ANTHROPIC_ORGANIZATION_ID:-}" ]; then
  unset ANTHROPIC_API_KEY # a stored key would override keyless sign-in
  token_dir="$RUNNER_TEMP/claude-workload-identity"
  mkdir -p "$token_dir/config/configs"
  export ANTHROPIC_IDENTITY_TOKEN_FILE="$token_dir/identity-token"
  # A minimal profile makes the CLI cache its sign-in instead of repeating it.
  echo '{"version":"1.0","authentication":{"type":"oidc_federation"}}' > "$token_dir/config/configs/default.json"
  export ANTHROPIC_CONFIG_DIR="$token_dir/config" ANTHROPIC_PROFILE=default

  fetch_identity_token() {
    curl -fsS --retry 3 -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
      "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=https://api.anthropic.com" |
      python3 -c 'import json, sys; sys.stdout.write(json.load(sys.stdin)["value"])' \
        > "$ANTHROPIC_IDENTITY_TOKEN_FILE.tmp"
    mv "$ANTHROPIC_IDENTITY_TOKEN_FILE.tmp" "$ANTHROPIC_IDENTITY_TOKEN_FILE"
  }
  fetch_identity_token
  # GitHub's token lasts five minutes and works once, and the CLI re-reads the
  # file each time it renews its sign-in. Keep a fresh one there.
  (while sleep "${REFRESH_TOKEN_EVERY:-240}"; do fetch_identity_token || true; done) > /dev/null 2>&1 &
  refresher=$!
  cleanup() {
    pkill -P "$refresher" 2> /dev/null || true
    kill "$refresher" 2> /dev/null || true
    rm -rf "$token_dir"
  }
  trap cleanup EXIT
elif [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "No sign-in is configured. See the setup notes at the top of the workflow." >&2
  exit 1
fi

status=0
# The agent has no use for the means to request identity tokens, so withhold it.
env -u ACTIONS_ID_TOKEN_REQUEST_TOKEN -u ACTIONS_ID_TOKEN_REQUEST_URL \
  claude -p "$prompt" \
  --permission-mode default \
  --max-turns 120 \
  ${REFRESH_MODEL:+--model "$REFRESH_MODEL"} \
  --allowedTools "$allowed" \
  --disallowedTools "$denied" \
  --output-format json > "$out" || status=$?

# The CLI can exit 0 after a failed run, so read the result as well.
python3 - "$out" <<'PY' || status=1
import json, sys
try:
    result = json.load(open(sys.argv[1]))
except (OSError, ValueError):
    sys.exit(1)
print(f"Agent finished: {result.get('num_turns', '?')} turns, ${result.get('total_cost_usd', 0):.2f}")
sys.exit(1 if result.get("is_error") else 0)
PY
exit "$status"
