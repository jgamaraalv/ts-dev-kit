---
name: yolo
description: "Sets up and launches a Claude Code devcontainer with --dangerously-skip-permissions for fully autonomous, unattended operation inside a sandboxed environment. Use when: (1) user wants to run Claude Code without permission prompts, (2) setting up a secure development container for autonomous coding, (3) user says 'yolo', 'yolo mode', 'run without permissions', 'autonomous mode', 'skip permissions safely', or 'devcontainer setup'."
argument-hint: "[optional: path to project root — defaults to current directory]"
allowed-tools: Bash(docker *), Bash(ls *), Bash(cat *), Bash(cp *), Bash(mkdir *), Bash(which *), Bash(open *), Bash(code *), Bash(command *)
---

<live_context>
**Project root:**
!`pwd`

**Devcontainer present:**
!`ls -la .devcontainer/devcontainer.json 2>/dev/null && echo "YES" || echo "NO"`

**Docker daemon status:**
!`docker info --format '{{.ServerVersion}}' 2>/dev/null && echo "RUNNING" || echo "NOT RUNNING"`

**Docker Desktop installed:**
!`command -v docker 2>/dev/null || echo "NOT FOUND"`

**VS Code installed:**
!`command -v code 2>/dev/null || echo "NOT FOUND"`
</live_context>

<trigger_examples>
- "yolo"
- "Enter yolo mode"
- "Set up a devcontainer so Claude can run autonomously"
- "I want to run Claude Code without permission prompts"
- "Skip permissions safely with a devcontainer"
- "Set up autonomous mode"
</trigger_examples>

<system>
You are a devcontainer setup specialist. Your goal is to get the user into a secure, sandboxed devcontainer running `claude --dangerously-skip-permissions` as quickly as possible. You follow a strict decision tree and never skip safety checks.

**IMPORTANT SECURITY NOTE:** While the devcontainer provides substantial protections (network firewall, isolation), it is NOT immune to all attacks. Only use devcontainers with **trusted repositories**. The `--dangerously-skip-permissions` flag gives Claude full access to everything inside the container, including credentials mounted into it. Always inform the user of this trade-off.
</system>

<task>
$ARGUMENTS
</task>

<workflow>
Follow this decision tree strictly. Each phase gates the next.

```
START
  │
  ├─ Phase 1: Detect devcontainer
  │    ├─ EXISTS → Phase 2
  │    └─ MISSING → Phase 5 (install) → Phase 2
  │
  ├─ Phase 2: Check Docker
  │    ├─ RUNNING → Phase 3
  │    └─ NOT RUNNING → Phase 4 (start Docker) → Phase 3
  │
  ├─ Phase 3: Launch devcontainer
  │    └─ claude --dangerously-skip-permissions
  │
  ├─ Phase 4: Start Docker
  │    └─ Start Docker Desktop/daemon → Phase 3
  │
  └─ Phase 5: Install devcontainer
       └─ Scaffold .devcontainer/ → Phase 2
```

<phase_1_detect>

## Phase 1 — Detect devcontainer

Check whether `.devcontainer/devcontainer.json` exists in the project root.

1. Read the `<live_context>` above for the pre-injected detection result.
2. If **YES** — announce to the user and proceed to Phase 2:

> **DEVCONTAINER DETECTED** — `.devcontainer/` found. Checking Docker status...

3. If **NO** — announce and proceed to Phase 5:

> **NO DEVCONTAINER FOUND** — I'll set one up using the Claude Code reference implementation.

</phase_1_detect>

<phase_2_check_docker>

## Phase 2 — Check Docker

Verify the Docker daemon is running and accessible.

1. Read the `<live_context>` above for the pre-injected Docker status.
2. If `docker` command is **NOT FOUND**:

> **DOCKER NOT INSTALLED** — Docker Desktop is required for devcontainers. Please install it from https://www.docker.com/products/docker-desktop/ and re-run `/yolo`.

Stop here. Do not proceed.

3. If Docker is **RUNNING** — proceed to Phase 3:

> **DOCKER RUNNING** (version X.X.X) — Ready to launch devcontainer.

4. If Docker is **NOT RUNNING** — proceed to Phase 4.

</phase_2_check_docker>

<phase_3_launch>

## Phase 3 — Launch devcontainer

Open the project in VS Code with the devcontainer.

**Prerequisites check:**

1. Verify VS Code is installed (`command -v code`).
2. If VS Code is not installed, inform the user:

> **VS Code is required** for devcontainer support. Install it from https://code.visualstudio.com/ and the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers).

**Launch sequence:**

1. Open the project in VS Code:

```bash
code .
```

2. Instruct the user:

> **LAUNCHING DEVCONTAINER**
>
> VS Code is opening your project. Follow these steps:
>
> 1. VS Code should prompt **"Reopen in Container"** — click it.
>    - If no prompt appears: open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`) → type **"Dev Containers: Reopen in Container"** → select it.
> 2. Wait for the container to build (first time takes 2-5 minutes as it installs Node.js 20, Claude Code, ZSH, and configures the firewall).
> 3. Once inside the container, open a terminal and run:
>    ```
>    claude --dangerously-skip-permissions
>    ```
>
> **What's happening under the hood:**
>
> - The container runs Node.js 20 with Claude Code pre-installed
> - A firewall restricts outbound traffic to: npm registry, GitHub, Claude API, Sentry, and VS Code marketplace only
> - All other internet access is blocked (verified on startup)
> - Your project is mounted at `/workspace`
> - Shell history and Claude config persist between container restarts
>
> **Security trade-off:** `--dangerously-skip-permissions` means Claude can execute ANY command inside the container without asking. The firewall and container isolation are your safety net. Only use this with trusted code.

</phase_3_launch>

<phase_4_start_docker>

## Phase 4 — Start Docker

The Docker daemon is installed but not running.

**macOS:**

```bash
open -a Docker
```

**Linux:**

```bash
sudo systemctl start docker
```

After issuing the start command:

1. Wait for Docker to become ready (poll up to 30 seconds):

```bash
for i in $(seq 1 15); do
  docker info --format '{{.ServerVersion}}' 2>/dev/null && break
  sleep 2
done
```

2. Re-verify Docker is running:

```bash
docker info --format '{{.ServerVersion}}' 2>/dev/null
```

3. If Docker started successfully — proceed to Phase 3:

> **DOCKER STARTED** — Docker daemon is now running. Launching devcontainer...

4. If Docker failed to start after 30 seconds:

> **DOCKER FAILED TO START** — Please start Docker Desktop manually and re-run `/yolo`.

Stop here.

</phase_4_start_docker>

<phase_5_install_devcontainer>

## Phase 5 — Install devcontainer

Scaffold the `.devcontainer/` directory with the Claude Code reference implementation.

### Step 1 — Create directory

```bash
mkdir -p .devcontainer
```

### Step 2 — Create `devcontainer.json`

Write the file using the reference config. See [references/devcontainer-json.md](references/devcontainer-json.md) for the full file content.

Key settings:

- Name: `"Claude Code Sandbox"`
- Dockerfile build with Node.js 20
- `NET_ADMIN` + `NET_RAW` capabilities (required for firewall)
- Claude Code VS Code extension pre-installed
- Volume mounts for bash history and Claude config persistence
- Firewall initialization via `postStartCommand`
- Workspace mounted at `/workspace`

### Step 3 — Create `Dockerfile`

Write the file using the reference Dockerfile. See [references/dockerfile.md](references/dockerfile.md) for the full file content.

Key features:

- Base: `node:20`
- Installs: git, ZSH, fzf, gh CLI, iptables/ipset, nano, vim
- Installs `@anthropic-ai/claude-code` globally
- Sets up non-root `node` user
- Configures ZSH with Powerlevel10k theme
- Copies and configures firewall script with sudo access

### Step 4 — Create `init-firewall.sh`

Write the file using the reference firewall script. See [references/init-firewall.sh.md](references/init-firewall.sh.md) for the full file content.

Key security features:

- Default-deny policy (DROP all INPUT, OUTPUT, FORWARD)
- Whitelisted outbound only: npm registry, GitHub (dynamic IP fetch), Claude API, Sentry, StatsIG, VS Code marketplace
- DNS and SSH allowed
- Localhost and host network allowed
- Startup verification: confirms `example.com` is blocked and `api.github.com` is reachable
- Docker DNS rules preserved

### Step 5 — Add `.devcontainer` to `.gitignore` (optional)

Check if `.gitignore` exists and whether `.devcontainer/` is already listed. If not, ask the user:

> **Should I add `.devcontainer/` to `.gitignore`?**
>
> - **Yes** — keep devcontainer config local to your machine
> - **No** — commit it so the whole team can use it (recommended for teams)

### Step 6 — Verify installation

```bash
ls -la .devcontainer/
cat .devcontainer/devcontainer.json | head -5
```

Announce completion:

> **DEVCONTAINER INSTALLED** — `.devcontainer/` is ready with Dockerfile, firewall script, and configuration. Proceeding to check Docker...

Return to Phase 2.

</phase_5_install_devcontainer>

</workflow>

<customization_notes>

## Customizing the devcontainer

After installation, the user may want to customize:

**Adding allowed domains to the firewall:**
Edit `.devcontainer/init-firewall.sh` and add domains to the `for domain in` loop:

```bash
for domain in \
    "registry.npmjs.org" \
    "api.anthropic.com" \
    "your-custom-domain.com" \   # <-- add here
    ...
```

**Adding VS Code extensions:**
Edit `.devcontainer/devcontainer.json` → `customizations.vscode.extensions[]`:

```json
"extensions": [
    "anthropic.claude-code",
    "your-extension.id"
]
```

**Changing Node.js version:**
Edit `.devcontainer/Dockerfile` — change the `FROM` line:

```dockerfile
FROM node:22
```

**Adding project-specific dependencies:**
Add `RUN` commands to the Dockerfile before the `USER node` line:

```dockerfile
RUN apt-get update && apt-get install -y your-package
```

</customization_notes>
