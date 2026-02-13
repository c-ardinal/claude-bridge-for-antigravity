---
name: claude-bridge
description: This skill allows Antigravity to utilize plugins and skills from Claude Code. It bridges the gap between Claude's environment (marketplaces, hooks, scripts) and Antigravity's workflow.
version: 2.0.0
---

# Claude Code Bridge for Antigravity

## Overview

This skill makes Claude Code plugin resources accessible from the Antigravity environment.
Claude Code plugins contain valuable **knowledge, instructions, and scripts** that can be
leveraged by Antigravity as reference material and executable utilities.

## Compatibility Matrix

| Resource Type       | Location in Plugin            | Antigravity Support   | Notes                                                                                                              |
| ------------------- | ----------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Skills (`SKILL.md`) | `skills/*/SKILL.md`           | ✅ Directly usable    | Markdown instructions. Read and follow as-is.                                                                      |
| Shell Scripts       | `scripts/`, `hooks-handlers/` | ✅ Executable         | Run via `claude-bridge.py run` wrapper for env var bridging.                                                       |
| Reference Docs      | `README.md`, `references/`    | ✅ Readable           | Knowledge and patterns to consult.                                                                                 |
| Commands (`*.md`)   | `commands/*.md`               | ✅ Usable (Workflows) | Linked to `global_workflows/` with `cb__` prefix. Run via `/` slash command.                                       |
| Hook Definitions    | `hooks/hooks.json`            | 📖 Reference only     | Describes validation logic. **Cannot auto-fire** in Antigravity. Manually invoke the underlying scripts if needed. |
| Agents              | `agents/*.md`                 | 📖 Reference only     | Subagent definitions for Claude Code. Read for logic/prompts, but Antigravity has no equivalent subagent launcher. |
| MCP Configs         | `.mcp.json`                   | ⚠️ Partial            | MCP server definitions may be reusable if Antigravity has the same MCP server configured.                          |

## Usage

### Reading a Plugin's Skill

```
1. Navigate to: [SKILLS_DIR]/claude-bridge/plugins/<marketplace>_<plugin>/skills/<skill-name>/SKILL.md
2. Read the SKILL.md with view_file.
3. Follow the instructions as if they were Antigravity skill instructions.
```

### Executing a Plugin Script

Use the provided wrapper to ensure Claude-compatible environment variables are set:

```bash
# Cross-platform
python [SKILLS_DIR]/claude-bridge/scripts/claude-bridge.py run \
  --plugin security-guidance \
  --script hooks-handlers/session-start.sh
```

The wrapper automatically sets:

- `CLAUDE_PLUGIN_ROOT` → The plugin's actual directory path.
- `CLAUDE_PROJECT_DIR` → The current working directory (your project root).

### Consulting Hook Logic

Hooks define **when** and **how** validations run in Claude Code. While Antigravity cannot
auto-fire these hooks, you can still benefit from them:

1. Read `hooks/hooks.json` to understand what validations the plugin performs.
2. For `"type": "command"` hooks, execute the referenced script manually via the wrapper.
3. For `"type": "prompt"` hooks, read the prompt text and apply the same reasoning inline.

## CLI Commands

All operations are handled by a single cross-platform script (Python 3.6+, no dependencies):

```bash
python [SKILLS_DIR]/claude-bridge/scripts/claude-bridge.py sync     # Sync plugins
python [SKILLS_DIR]/claude-bridge/scripts/claude-bridge.py list     # List bridged plugins
python [SKILLS_DIR]/claude-bridge/scripts/claude-bridge.py info <plugin>  # Plugin details
python [SKILLS_DIR]/claude-bridge/scripts/claude-bridge.py run ...  # Run a plugin script
```

### `sync`

- Discovers all valid plugins in `~/.claude/plugins/marketplaces/`.
- Creates filesystem links (Junctions on Windows, Symlinks on Unix) for plugins.
- Syncs `commands/*.md` files to Antigravity's `global_workflows/` directory.
- Naming convention for workflows: `cb__[marketplace]__[plugin]__[filename].md`.
- Removes obsolete links for uninstalled plugins and their workflows.
- Plugin file contents are **always live** — changes in the Claude marketplace are
  reflected immediately. Only re-run `sync` when plugins are added or removed.

### `list`

- Shows all bridged plugins with their available resource types.

### `info <plugin>`

- Displays the directory structure and hook summary of a specific plugin.
- Supports partial name matching (e.g., `security-guidance` instead of the full bridge name).

### `run --plugin <name> --script <path>`

- Executes a plugin script with bridged environment variables.
- Auto-detects script type (`.sh`, `.py`, `.ps1`) and selects the appropriate interpreter.
- Optional: `--project-dir`, `--stdin-data` for hook input simulation.

## Directory Structure

```
claude-bridge/
├── SKILL.md                   # This file
├── scripts/
│   └── claude-bridge.py       # Unified CLI tool (sync, list, info, run)
└── plugins/                   # Auto-populated by `claude-bridge.py sync`
    ├── <marketplace>__<plugin>/  (Junction/Symlink to source)
    └── ...

[HOME]/.gemini/antigravity/global_workflows/
├── cb__<marketplace>__<plugin>__<command>.md  (Hardlink/Symlink)
└── ...
```
