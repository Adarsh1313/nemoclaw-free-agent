# nemoclaw-free-agent

# nemoclaw-free-agent

# 🦞 NemoClaw — Sandboxed AI Agent on GitHub Codespaces

**NemoClaw** is NVIDIA's secure runtime for deploying OpenClaw autonomous agents inside a policy-governed sandbox. This repository documents how to run a persistent, fully autonomous AI agent using GitHub Codespaces as the host environment — with zero GPU spend, no VPS provisioning, and no local system risk.

The agent is backed by NVIDIA's Nemotron 3 Super 120B model served through the NVIDIA Inference API, routed entirely through the OpenShell security gateway.

> **Status:** NemoClaw is in early preview as of March 2026. APIs, CLI interfaces, and sandbox behavior are subject to breaking changes. Not recommended for production workloads.

---

## Table of Contents

- [Architecture](#architecture)
- [NemoClaw vs OpenClaw](#nemoclaw-vs-openclaw)
- [Use Cases](#use-cases)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Configuration](#configuration)
- [Security Model](#security-model)
- [Known Issues](#known-issues)
- [References](#references)
- [License](#license)

---

## Architecture

```
GitHub Codespaces (Ubuntu Host)
└── NemoClaw CLI
    └── K3s (local Kubernetes runtime)
        └── OpenShell Gateway (policy engine + inference interceptor)
            └── OpenClaw Agent Container
                ├── Task executor / memory loop
                └── Inference calls → NVIDIA API (Nemotron 3 Super 120B)
```

NemoClaw deploys OpenClaw inside a K3s-managed container. All outbound calls — including inference requests — are intercepted by the OpenShell gateway before leaving the sandbox. Policies governing network egress, filesystem scope, and syscall access are declared at sandbox creation time and enforced at the kernel level.

GitHub Codespaces functions as the persistent host server. The Codespace remains active as long as it is not stopped, giving the agent a stable execution environment without provisioning or maintaining external infrastructure.

---

## NemoClaw vs OpenClaw

| | OpenClaw | NemoClaw |
|---|---|---|
| Role | Autonomous agent runtime | Secure sandbox wrapping OpenClaw |
| Security boundary | Application-layer only | Kernel-level via OpenShell |
| Network control | Unrestricted | Declarative egress policies, hot-reloadable |
| Filesystem scope | Host filesystem | Isolated to `/sandbox` and `/tmp` |
| Inference routing | Direct to provider | Intercepted and rerouted through OpenShell gateway |
| Syscall enforcement | None | Blocks privilege escalation and dangerous calls |
| Target context | Local development, personal use | Shared environments, multi-tenant pipelines |

NemoClaw is not a different agent — it is OpenClaw with OpenShell's governance layer applied. Every file read, network request, and model call is mediated by the gateway.

---

## Use Cases

**Autonomous development assistant** — Run long-horizon tasks (refactoring, test generation, build bisection) against a codebase without risk to the host environment.

**Scheduled data pipeline execution** — Operate repeating API-call / transform / write workflows with egress locked to whitelisted endpoints only.

**Secure code review and audit** — Audit untrusted third-party code inside the sandbox; the code under review has no visibility into the host or other services.

**Prototype SaaS automation backend** — Persistent Codespace + continuous agent = a functional prototype layer for background task execution before committing to paid infrastructure.

**Research and evaluation of 120B-class models** — Direct access to Nemotron 3 Super 120B for benchmarking reasoning, tool use, or long-context performance without on-prem GPU capacity.

---

## Prerequisites

- GitHub account with Codespaces access
- NVIDIA API key — obtain at [build.nvidia.com](https://build.nvidia.com/)
- Codespaces machine type: **4-core / 16 GB RAM minimum** (see [Known Issues](#known-issues))
- The default Codespaces environment ships with Node.js and Docker pre-installed; no additional system dependencies are required

---

## Setup

### 1. Open a Codespace

From this repository on GitHub, navigate to **Code → Codespaces → New codespace**. Select the **4-core / 16 GB** machine type.

### 2. Run the installer

```bash
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash
```

This installs the `nemoclaw` CLI, starts the local K3s runtime, and brings up the OpenShell gateway.

### 3. Run onboarding

```bash
nemoclaw onboard
```

When prompted:

1. Select **NVIDIA Endpoints** as the inference provider
2. Enter your NVIDIA API key
3. Select model: `nvidia/nemotron-3-super-120b-a12b`
4. Name your sandbox (e.g., `dev-agent`)

Onboarding validates the provider configuration, pulls the sandbox image (~2.4 GB), and initializes the OpenClaw container.

### 4. Connect and start the agent

```bash
nemoclaw dev-agent connect
```

Inside the sandbox shell:

```bash
sandbox@dev-agent:~$ openclaw start
```

This launches the OpenClaw terminal UI (TUI). The agent is now running with persistent memory and execution context.

### Agent management (from host)

```bash
nemoclaw dev-agent status          # Health and resource usage
nemoclaw dev-agent logs --follow   # Stream live logs
nemoclaw dev-agent stop            # Graceful shutdown
nemoclaw dev-agent restart         # Restart without losing sandbox state
```

---

## Configuration

Sandbox behavior is declared at creation time via a policy manifest. The following covers the fields relevant to a Codespaces deployment:

```yaml
# nemoclaw-policy.yaml
sandbox:
  name: dev-agent
  filesystem:
    allowed_paths:
      - /sandbox
      - /tmp
  network:
    egress:
      - host: api.nvidia.com
        port: 443
      - host: build.nvidia.com
        port: 443
  inference:
    provider: nvidia
    model: nvidia/nemotron-3-super-120b-a12b
```

Network and inference policies can be reloaded at runtime without restarting the sandbox:

```bash
nemoclaw dev-agent reload-policy --file nemoclaw-policy.yaml
```

Filesystem and syscall policies are immutable after sandbox creation.

---

## Security Model

| Control plane | Behavior |
|---|---|
| Network egress | Outbound blocked by default; only manifest-declared hosts/ports are reachable |
| Filesystem isolation | Agent scoped to `/sandbox` and `/tmp`; host paths and env vars are not visible |
| Syscall filtering | seccomp profile blocks `ptrace`, `mount`, `setuid`, and related escalation calls |
| Inference interception | All model API calls pass through the OpenShell gateway before reaching the provider |

Network and inference policies are hot-reloadable. Filesystem and syscall policies are immutable after sandbox creation.

---

## Known Issues

**Sandbox image push failure on 2-core / 8 GB instances** — The ~2.4 GB image push to the local K3s registry silently fails mid-transfer on underpowered instances. The installer may falsely report success; the sandbox surfaces as `status: NotFound` on connect. Use a 4-core / 16 GB machine type. Tracked at [#150](https://github.com/NVIDIA/NemoClaw/issues/150).

**Codespace idle timeout** — Codespaces stops after 30 minutes of inactivity, suspending the sandbox and any in-flight tasks. Extend the timeout (max 4 hours) in your [Codespaces settings](https://github.com/settings/codespaces), or disable it on paid plans.

**Early preview instability** — CLI, policy schema, and sandbox behavior are not stable; breaking changes ship without deprecation windows. Pin to a specific installer version if reproducibility matters.

---

## API Credits

NVIDIA provides free credits on sign-up at [build.nvidia.com](https://build.nvidia.com/) — sufficient to evaluate and run the agent at moderate usage without a payment method. Credits are consumed per inference token against the Nemotron model; a typical interactive session costs a fraction of a cent, but long autonomous runs with high output volumes will deplete credits faster. Monitor usage in the NVIDIA API dashboard and set a spending limit before running unattended workloads.

---



| Resource | URL |
|---|---|
| NVIDIA NemoClaw repository | [github.com/NVIDIA/NemoClaw](https://github.com/NVIDIA/NemoClaw) |
| NVIDIA Inference API | [build.nvidia.com](https://build.nvidia.com/) |
| OpenShell technical overview | [developer.nvidia.com/blog/...](https://developer.nvidia.com/blog/run-autonomous-self-evolving-agents-more-safely-with-nvidia-openshell/) |
| GitHub Codespaces documentation | [docs.github.com/en/codespaces](https://docs.github.com/en/codespaces) |
| Community sandbox presets | [github.com/VoltAgent/awesome-nemoclaw](https://github.com/VoltAgent/awesome-nemoclaw) |

---

## Acknowledgements
Setup guide based on [I ran Nvidia's NemoClaw for FREE without GPU (Secret Way)](https://www.youtube.com/watch?v=pIUSlcd6F1o&t=30s) by [Sameer Vish](https://www.youtube.com/@SameerVish).


## License

This project builds on [NVIDIA NemoClaw](https://github.com/NVIDIA/NemoClaw), distributed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0).
