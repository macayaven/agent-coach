#!/usr/bin/env bash
# Tests for .github/scripts/run-refresh-agent.sh, with a fake `claude` and a fake
# `curl` so nothing real is called. They check how credentials are handled.
set -uo pipefail

script="$(cd "$(dirname "$0")/.." && pwd)/.github/scripts/run-refresh-agent.sh"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail=0
check() { if eval "$2"; then echo "ok: $1"; else echo "FAIL: $1"; fail=1; fi; }

mkdir -p "$tmp/bin"
cat > "$tmp/bin/claude" <<'FAKE'
#!/usr/bin/env bash
env > "$FAKE_LOG/env"
printf '%s\n' "$@" > "$FAKE_LOG/args"
cat "${ANTHROPIC_IDENTITY_TOKEN_FILE:-/dev/null}" > "$FAKE_LOG/token" 2>/dev/null
echo "${FAKE_RESULT:-{\"type\":\"result\",\"is_error\":false,\"num_turns\":3,\"total_cost_usd\":0.42}}"
FAKE
cat > "$tmp/bin/curl" <<'FAKE'
#!/usr/bin/env bash
echo "$*" >> "$FAKE_LOG/curl"
echo '{"value":"fake.identity.token"}'
FAKE
chmod +x "$tmp/bin/claude" "$tmp/bin/curl"

run() { # run <name> [VAR=value ...]
  export FAKE_LOG="$tmp/$1"; shift
  rm -rf "$FAKE_LOG" "$tmp/runner"; mkdir -p "$FAKE_LOG" "$tmp/runner"
  env -i PATH="$tmp/bin:$PATH" HOME="$tmp" RUNNER_TEMP="$tmp/runner" FAKE_LOG="$FAKE_LOG" "$@" \
    bash "$script" > "$FAKE_LOG/stdout" 2> "$FAKE_LOG/stderr"
}

# Keyless sign-in
run keyless ANTHROPIC_FEDERATION_RULE_ID=fdrl_x ANTHROPIC_ORGANIZATION_ID=org-x ANTHROPIC_API_KEY=sk-stale \
  ANTHROPIC_WORKSPACE_ID= ACTIONS_ID_TOKEN_REQUEST_TOKEN=req-token ACTIONS_ID_TOKEN_REQUEST_URL='https://gh.example/token?x=1'
check "keyless: exits 0" "[ $? -eq 0 ]"
L="$tmp/keyless"
check "keyless: the agent gets the identity token file" "[ \"\$(cat $L/token)\" = fake.identity.token ]"
check "keyless: token requested for the Claude API audience" "grep -q 'audience=https://api.anthropic.com' $L/curl"
check "keyless: a stored key is not passed on" "! grep -q '^ANTHROPIC_API_KEY=' $L/env"
check "keyless: empty variables are dropped" "! grep -q '^ANTHROPIC_WORKSPACE_ID=' $L/env"
check "keyless: the agent can't request identity tokens" "! grep -q '^ACTIONS_ID_TOKEN_REQUEST' $L/env"
check "keyless: sign-in files are removed afterwards" "[ ! -e $tmp/runner/claude-workload-identity ]"
check "reports turns and cost" "grep -q '3 turns, \$0.42' $L/stdout"
check "agent has no shell and can't read the temp folder" "grep -q 'Bash,WebSearch,Read(//proc/\*\*),Read(/$tmp/runner/\*\*)' $L/args"
check "agent may fetch only listed sites" "grep -q 'WebFetch(domain:code.claude.com)' $L/args && ! grep -q 'WebFetch,' $L/args"
check "strict permission mode" "grep -qx 'default' $L/args"

# API key
run key ANTHROPIC_API_KEY=sk-real ANTHROPIC_FEDERATION_RULE_ID= REFRESH_MODEL=some-model
check "key: exits 0" "[ $? -eq 0 ]"
check "key: the key is passed on" "grep -q '^ANTHROPIC_API_KEY=sk-real' $tmp/key/env"
check "key: no identity token is requested" "[ ! -e $tmp/key/curl ]"
check "optional model is passed" "grep -qx 'some-model' $tmp/key/args"

# Failures
run failed ANTHROPIC_API_KEY=sk-real FAKE_RESULT='{"type":"result","is_error":true,"result":"Credit balance is too low"}'
check "a failed result fails the step" "[ $? -ne 0 ]"
check "the result is kept for the reason step" "grep -q 'Credit balance' $tmp/runner/claude-execution-output.json"
run nosignin
check "no sign-in configured: fails with a message" "[ $? -ne 0 ] && grep -q 'No sign-in' $tmp/nosignin/stderr"

exit $fail
