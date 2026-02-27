# init-firewall.sh — Reference

Write this file to `.devcontainer/init-firewall.sh`:

```bash
#!/bin/bash
set -uo pipefail  # Strict vars and pipelines, but handle errors manually
IFS=$'\n\t'

LOG="/tmp/firewall-init.log"
exec > >(tee -a "$LOG") 2>&1
echo "=== Firewall init started at $(date -u) ==="

# --- Diagnostics -----------------------------------------------------------
echo "--- Pre-flight checks ---"
HAVE_IPTABLES=false
HAVE_IPSET=false

if iptables -L -n >/dev/null 2>&1; then
    HAVE_IPTABLES=true
    echo "[OK] iptables is functional"
else
    echo "[FAIL] iptables is NOT functional — firewall cannot be configured"
    echo "Hint: ensure --cap-add=NET_ADMIN is set in devcontainer.json runArgs"
    exit 1
fi

if ipset list >/dev/null 2>&1 || ipset create _test hash:net 2>/dev/null; then
    ipset destroy _test 2>/dev/null || true
    HAVE_IPSET=true
    echo "[OK] ipset is functional"
else
    echo "[WARN] ipset is NOT functional — falling back to iptables-only rules"
fi

if command -v dig >/dev/null 2>&1; then
    echo "[OK] dig is available"
else
    echo "[WARN] dig not found — DNS resolution will use getent"
fi

if command -v aggregate >/dev/null 2>&1; then
    echo "[OK] aggregate is available"
else
    echo "[WARN] aggregate not found — GitHub CIDRs will be added individually"
fi

# --- Helper: resolve domain to IPs ----------------------------------------
resolve_domain() {
    local domain="$1"
    local ips=""
    if command -v dig >/dev/null 2>&1; then
        ips=$(dig +noall +answer +short A "$domain" 2>/dev/null | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | sort -u)
    fi
    if [ -z "$ips" ] && command -v getent >/dev/null 2>&1; then
        ips=$(getent ahostsv4 "$domain" 2>/dev/null | awk '{print $1}' | sort -u | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$')
    fi
    echo "$ips"
}

# --- 1. Preserve Docker DNS -----------------------------------------------
echo "--- Preserving Docker DNS rules ---"
DOCKER_DNS_RULES=$(iptables-save -t nat 2>/dev/null | grep "127\.0\.0\.11" || true)

# --- 2. Flush existing rules -----------------------------------------------
echo "--- Flushing existing rules ---"
iptables -F  || true
iptables -X  || true
iptables -t nat -F    || true
iptables -t nat -X    || true
iptables -t mangle -F || true
iptables -t mangle -X || true
if [ "$HAVE_IPSET" = true ]; then
    ipset destroy allowed-domains 2>/dev/null || true
fi

# --- 3. Restore Docker DNS -------------------------------------------------
if [ -n "$DOCKER_DNS_RULES" ]; then
    echo "Restoring Docker DNS rules..."
    iptables -t nat -N DOCKER_OUTPUT 2>/dev/null || true
    iptables -t nat -N DOCKER_POSTROUTING 2>/dev/null || true
    echo "$DOCKER_DNS_RULES" | while read -r rule; do
        iptables -t nat $rule 2>/dev/null || true
    done
else
    echo "No Docker DNS rules to restore"
fi

# --- 4. Base rules (DNS, SSH, localhost) ------------------------------------
echo "--- Setting base rules ---"
# Outbound DNS
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
# Inbound DNS responses
iptables -A INPUT -p udp --sport 53 -j ACCEPT
iptables -A INPUT -p tcp --sport 53 -j ACCEPT
# Outbound SSH
iptables -A OUTPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --sport 22 -m state --state ESTABLISHED -j ACCEPT
# Localhost
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# --- 5. Host network -------------------------------------------------------
HOST_IP=$(ip route 2>/dev/null | grep default | head -1 | awk '{print $3}')
if [ -n "$HOST_IP" ]; then
    HOST_NETWORK=$(echo "$HOST_IP" | sed "s/\.[0-9]*$/.0\/16/")
    echo "Host network: $HOST_NETWORK (via $HOST_IP)"
    iptables -A INPUT -s "$HOST_NETWORK" -j ACCEPT
    iptables -A OUTPUT -d "$HOST_NETWORK" -j ACCEPT
else
    echo "[WARN] Could not detect host IP — allowing RFC1918 ranges for Docker connectivity"
    iptables -A INPUT -s 172.16.0.0/12 -j ACCEPT
    iptables -A OUTPUT -d 172.16.0.0/12 -j ACCEPT
    iptables -A INPUT -s 192.168.0.0/16 -j ACCEPT
    iptables -A OUTPUT -d 192.168.0.0/16 -j ACCEPT
    iptables -A INPUT -s 10.0.0.0/8 -j ACCEPT
    iptables -A OUTPUT -d 10.0.0.0/8 -j ACCEPT
fi

# --- 6. Allowed domains ----------------------------------------------------
ALLOWED_DOMAINS=(
    "registry.npmjs.org"
    "api.anthropic.com"
    "sentry.io"
    "statsig.anthropic.com"
    "statsig.com"
    "marketplace.visualstudio.com"
    "vscode.blob.core.windows.net"
    "update.code.visualstudio.com"
)

if [ "$HAVE_IPSET" = true ]; then
    # ---- ipset mode (preferred) ----
    echo "--- Building ipset allowlist ---"
    ipset create allowed-domains hash:net

    # GitHub dynamic IPs
    echo "Fetching GitHub IP ranges..."
    gh_ranges=$(curl -sf --connect-timeout 10 https://api.github.com/meta 2>/dev/null || true)
    if [ -n "$gh_ranges" ] && echo "$gh_ranges" | jq -e '.web and .api and .git' >/dev/null 2>&1; then
        if command -v aggregate >/dev/null 2>&1; then
            while read -r cidr; do
                [[ "$cidr" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+$ ]] && ipset add allowed-domains "$cidr" 2>/dev/null || true
            done < <(echo "$gh_ranges" | jq -r '(.web + .api + .git)[]' | aggregate -q 2>/dev/null)
        else
            while read -r cidr; do
                [[ "$cidr" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+$ ]] && ipset add allowed-domains "$cidr" 2>/dev/null || true
            done < <(echo "$gh_ranges" | jq -r '(.web + .api + .git)[]')
        fi
        echo "[OK] GitHub IP ranges added"
    else
        echo "[WARN] Could not fetch GitHub IPs — resolving github.com directly"
        for gh_domain in "github.com" "api.github.com" "raw.githubusercontent.com" "objects.githubusercontent.com"; do
            ips=$(resolve_domain "$gh_domain")
            while read -r ip; do
                [ -n "$ip" ] && ipset add allowed-domains "$ip" 2>/dev/null || true
            done <<< "$ips"
        done
    fi

    # Other allowed domains
    for domain in "${ALLOWED_DOMAINS[@]}"; do
        echo "Resolving $domain..."
        ips=$(resolve_domain "$domain")
        if [ -z "$ips" ]; then
            echo "[WARN] Failed to resolve $domain — skipping"
            continue
        fi
        while read -r ip; do
            [ -n "$ip" ] && ipset add allowed-domains "$ip" 2>/dev/null || true
        done <<< "$ips"
    done

    # Apply ipset match rule
    iptables -A OUTPUT -m set --match-set allowed-domains dst -j ACCEPT

else
    # ---- iptables-only mode (fallback) ----
    echo "--- Building iptables allowlist (no ipset) ---"

    # GitHub IPs
    echo "Fetching GitHub IP ranges..."
    gh_ranges=$(curl -sf --connect-timeout 10 https://api.github.com/meta 2>/dev/null || true)
    if [ -n "$gh_ranges" ] && echo "$gh_ranges" | jq -e '.web and .api and .git' >/dev/null 2>&1; then
        while read -r cidr; do
            [[ "$cidr" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/[0-9]+$ ]] && \
                iptables -A OUTPUT -d "$cidr" -j ACCEPT 2>/dev/null || true
        done < <(echo "$gh_ranges" | jq -r '(.web + .api + .git)[]')
        echo "[OK] GitHub IP ranges added via iptables"
    else
        echo "[WARN] Could not fetch GitHub IPs — resolving github.com directly"
        for gh_domain in "github.com" "api.github.com" "raw.githubusercontent.com" "objects.githubusercontent.com"; do
            ips=$(resolve_domain "$gh_domain")
            while read -r ip; do
                [ -n "$ip" ] && iptables -A OUTPUT -d "$ip" -j ACCEPT 2>/dev/null || true
            done <<< "$ips"
        done
    fi

    # Other allowed domains
    for domain in "${ALLOWED_DOMAINS[@]}"; do
        echo "Resolving $domain..."
        ips=$(resolve_domain "$domain")
        if [ -z "$ips" ]; then
            echo "[WARN] Failed to resolve $domain — skipping"
            continue
        fi
        while read -r ip; do
            [ -n "$ip" ] && iptables -A OUTPUT -d "$ip" -j ACCEPT 2>/dev/null || true
        done <<< "$ips"
    done
fi

# --- 7. Default-deny policies ----------------------------------------------
echo "--- Applying default-deny policies ---"
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT DROP

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Reject everything else with immediate feedback
iptables -A OUTPUT -j REJECT --reject-with icmp-admin-prohibited

# --- 8. Verification -------------------------------------------------------
echo "--- Verifying firewall ---"
VERIFIED=true

if curl --connect-timeout 5 https://example.com >/dev/null 2>&1; then
    echo "[FAIL] Firewall verification failed — reached https://example.com (should be blocked)"
    VERIFIED=false
else
    echo "[OK] https://example.com is blocked as expected"
fi

if curl --connect-timeout 5 https://api.github.com/zen >/dev/null 2>&1; then
    echo "[OK] https://api.github.com is reachable as expected"
else
    echo "[WARN] https://api.github.com is not reachable — GitHub IPs may have changed"
    echo "       Claude Code will still work, but git operations may fail"
fi

if [ "$VERIFIED" = false ]; then
    echo "=== FIREWALL VERIFICATION FAILED ==="
    exit 1
fi

echo "=== Firewall configured successfully ==="
echo "Mode: $([ "$HAVE_IPSET" = true ] && echo 'ipset' || echo 'iptables-only')"
echo "Log: $LOG"
```

## Key improvements over the original

| Issue | Original behavior | Improved behavior |
|-------|-------------------|-------------------|
| Duplicate IPs from DNS | `ipset add` fatal error (exit 1) | Deduplicates via `sort -u` + `ipset add ... \|\| true` |
| `ipset` not available | Fatal crash | Falls back to iptables-only rules |
| `aggregate` not available | Fatal crash | Adds CIDRs individually without aggregation |
| `dig` not available | Fatal crash | Falls back to `getent ahostsv4` |
| GitHub API unreachable | Fatal crash | Resolves github.com/api.github.com directly |
| Domain resolution fails | Fatal crash | Skips domain with warning, continues |
| Host IP detection fails | Fatal crash | Allows all RFC1918 ranges as fallback |
| Docker DNS restore fails | Silent + potential crash | Handles per-rule with `|| true` |
| No diagnostic output | Blind exit code 1 | Full log at `/tmp/firewall-init.log` |
| GitHub unreachable after setup | Fatal crash | Warning only (Claude API is the critical path) |

## Firewall rules summary

| Rule | Direction | Purpose |
|------|-----------|---------|
| DNS (UDP/TCP 53) | Outbound | Domain name resolution |
| SSH (TCP 22) | Outbound | Git over SSH |
| Localhost | Both | Container-internal communication |
| Host network | Both | Docker host ↔ container communication |
| GitHub IPs | Outbound | Git operations, GitHub API (dynamically fetched or resolved) |
| npm registry | Outbound | Package installation |
| api.anthropic.com | Outbound | Claude API calls |
| sentry.io | Outbound | Error reporting |
| statsig.anthropic.com | Outbound | Feature flags |
| VS Code marketplace | Outbound | Extension downloads |
| **Everything else** | **BLOCKED** | Default-deny with REJECT |

## Verification on startup

The script verifies the firewall by:
1. Confirming `https://example.com` is **blocked** (must fail — otherwise exit 1)
2. Confirming `https://api.github.com` is **reachable** (warning only if it fails)

All output is logged to `/tmp/firewall-init.log` for debugging.
