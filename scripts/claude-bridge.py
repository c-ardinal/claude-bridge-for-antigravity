#!/usr/bin/env python3
"""
claude-bridge.py - Cross-platform Claude Code <-> Antigravity plugin bridge.

A single script that handles both plugin synchronization and script execution.

Requirements: Python 3.6+, no external dependencies.

Usage:
  python claude-bridge.py sync              Sync plugins from Claude marketplace
  python claude-bridge.py run               Execute a plugin script with env bridging
  python claude-bridge.py list              List all bridged plugins
  python claude-bridge.py info <plugin>     Show details of a specific plugin
  python claude-bridge.py translate-readme  Translate README.md to README_en.md (Option 2)

Examples:
  python claude-bridge.py sync
  python claude-bridge.py list
  python claude-bridge.py info security-guidance
  python claude-bridge.py run --plugin security-guidance --script hooks-handlers/validate.sh
  python claude-bridge.py run --plugin hookify --script scripts/check.sh -- --verbose
"""

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Files/directories that indicate a directory is a meaningful Claude Code plugin.
PLUGIN_INDICATORS = (
    "plugin.json",
    "skills",
    "hooks",
    "agents",
    "commands",
    "README.md",
)

# Directories that should never be treated as plugins.
EXCLUDE_NAMES = frozenset({
    ".git",
    ".github",
    ".claude",
    ".claude-plugin",
    "node_modules",
    "__pycache__",
    ".venv",
    "tests",
    "test",
    "docs",
    "doc",
    "src",
    "dist",
    "build",
})


def get_claude_marketplace() -> Path:
    return Path.home() / ".claude" / "plugins" / "marketplaces"


def get_bridge_plugins_dir() -> Path:
    return Path.home() / ".gemini" / "antigravity" / "skills" / "claude-bridge" / "plugins"


def get_global_workflows_dir() -> Path:
    return Path.home() / ".gemini" / "antigravity" / "global_workflows"


def is_plugin_dir(path: Path) -> bool:
    """Check if a directory looks like a Claude Code plugin."""
    if path.name.startswith(".") or path.name in EXCLUDE_NAMES:
        return False
    return any((path / indicator).exists() for indicator in PLUGIN_INDICATORS)


def create_link(source: Path, dest: Path, is_windows: bool) -> bool:
    """Create a directory link. Junction on Windows, Symlink on Unix."""
    try:
        if is_windows:
            subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(dest), str(source)],
                check=True, capture_output=True,
            )
        else:
            os.symlink(source, dest)
        return True
    except Exception as e:
        print(f"    [!] Failed to link directory: {e}")
        return False


def create_file_link(source: Path, dest: Path, is_windows: bool) -> bool:
    """Create a file link. Hard link on Windows (/H), Symbolic link on Unix."""
    try:
        if is_windows:
            subprocess.run(
                ["cmd", "/c", "mklink", "/H", str(dest), str(source)],
                check=True, capture_output=True,
            )
        else:
            os.symlink(source, dest)
        return True
    except Exception as e:
        print(f"    [!] Failed to link file: {e}")
        return False


def remove_link(path: Path, is_windows: bool) -> bool:
    """Remove a link safely."""
    try:
        if is_windows:
            if path.is_dir():
                os.rmdir(path)
            else:
                os.remove(path)
        else:
            if path.is_symlink() or path.is_file():
                path.unlink()
            else:
                os.rmdir(path)
        return True
    except Exception as e:
        print(f"    [!] Failed to remove: {e}")
        return False


def resolve_plugin(bridge_plugins: Path, name: str) -> Path:
    """Resolve a (possibly partial) plugin name to its directory."""
    exact = bridge_plugins / name
    if exact.exists():
        return exact.resolve()

    candidates = [p for p in bridge_plugins.iterdir() if name in p.name]
    if len(candidates) == 1:
        return candidates[0].resolve()
    elif len(candidates) > 1:
        print(f"[!] Ambiguous plugin name '{name}'. Matches:", file=sys.stderr)
        for c in candidates:
            print(f"    - {c.name}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"[!] Plugin '{name}' not found.", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_sync(_args):
    """Sync plugins and workflows from the Claude marketplace."""
    marketplace = get_claude_marketplace()
    bridge_plugins = get_bridge_plugins_dir()
    global_workflows = get_global_workflows_dir()
    is_windows = platform.system() == "Windows"

    print("[*] Claude-Antigravity Bridge Sync")
    print(f"    Platform : {platform.system()}")
    print(f"    Source   : {marketplace}")
    print(f"    Plugins  : {bridge_plugins}")
    print(f"    Workflows: {global_workflows}")
    print()

    if not marketplace.exists():
        print("[!] Claude Marketplace not found. Skipping.")
        return

    bridge_plugins.mkdir(parents=True, exist_ok=True)
    global_workflows.mkdir(parents=True, exist_ok=True)

    valid_plugin_names: list = []
    valid_workflow_names: list = []
    
    plugins_linked = 0
    plugins_skipped = 0
    workflows_linked = 0
    workflows_skipped = 0

    for mp_dir in sorted(marketplace.iterdir()):
        if not mp_dir.is_dir() or mp_dir.name.startswith("."):
            continue

        mp_name = mp_dir.name
        print(f"[*] Marketplace: {mp_name}")

        plugin_base = mp_dir / "plugins"
        if not plugin_base.is_dir():
            plugin_base = mp_dir

        for plugin_dir in sorted(plugin_base.iterdir()):
            if not plugin_dir.is_dir():
                continue
            if not is_plugin_dir(plugin_dir):
                continue

            bridge_name = f"{mp_name}__{plugin_dir.name}"
            dest = bridge_plugins / bridge_name
            valid_plugin_names.append(bridge_name)

            if dest.exists() or (hasattr(dest, "is_symlink") and dest.is_symlink()):
                plugins_skipped += 1
            else:
                print(f"    [+] Link Plugin: {plugin_dir.name}")
                if create_link(plugin_dir, dest, is_windows):
                    plugins_linked += 1

            # --- Sync Workflows (Commands) ---
            commands_dir = plugin_dir / "commands"
            if commands_dir.exists() and commands_dir.is_dir():
                for cmd_file in commands_dir.glob("*.md"):
                    wf_name = f"cb__{mp_name}__{plugin_dir.name}__{cmd_file.name}"
                    wf_dest = global_workflows / wf_name
                    valid_workflow_names.append(wf_name)

                    if wf_dest.exists() or (hasattr(wf_dest, "is_symlink") and wf_dest.is_symlink()):
                        workflows_skipped += 1
                    else:
                        print(f"    [+] Link Workflow: {cmd_file.name} -> {wf_name}")
                        if create_file_link(cmd_file, wf_dest, is_windows):
                            workflows_linked += 1

    # Cleanup obsolete plugins
    plugins_removed = 0
    for existing in sorted(bridge_plugins.iterdir()):
        if existing.name not in valid_plugin_names:
            print(f"    [-] Remove Plugin: {existing.name}")
            if remove_link(existing, is_windows):
                plugins_removed += 1

    # Cleanup obsolete workflows
    workflows_removed = 0
    for existing in sorted(global_workflows.iterdir()):
        if existing.name.startswith("cb__") and existing.name not in valid_workflow_names:
            print(f"    [-] Remove Workflow: {existing.name}")
            if remove_link(existing, is_windows):
                workflows_removed += 1

    print()
    print(f"[+] Done.")
    print(f"    Plugins  : {len(valid_plugin_names)} bridged ({plugins_linked} new, {plugins_skipped} existing, {plugins_removed} removed)")
    print(f"    Workflows: {len(valid_workflow_names)} bridged ({workflows_linked} new, {workflows_skipped} existing, {workflows_removed} removed)")


def cmd_list(_args):
    """List all bridged plugins."""
    bridge_plugins = get_bridge_plugins_dir()

    if not bridge_plugins.exists():
        print("[!] No plugins bridged yet. Run 'sync' first.")
        return

    plugins = sorted(p for p in bridge_plugins.iterdir() if p.is_dir())
    if not plugins:
        print("[!] No plugins found.")
        return

    print(f"[*] {len(plugins)} bridged plugins:\n")
    for p in plugins:
        # Show what resources are available
        resources = []
        if (p / "skills").exists():
            resources.append("skills")
        if (p / "hooks").exists():
            resources.append("hooks")
        if (p / "agents").exists():
            resources.append("agents")
        if (p / "commands").exists():
            resources.append("commands")
        if (p / "README.md").exists():
            resources.append("readme")

        tag = ", ".join(resources) if resources else "minimal"
        print(f"  {p.name}  [{tag}]")


def cmd_info(args):
    """Show details of a specific plugin."""
    bridge_plugins = get_bridge_plugins_dir()
    plugin_root = resolve_plugin(bridge_plugins, args.plugin)

    print(f"[*] Plugin: {plugin_root.name}")
    print(f"    Path  : {plugin_root}")
    print()

    # Show structure
    for item in sorted(plugin_root.iterdir()):
        if item.is_dir():
            children = list(item.iterdir())
            print(f"  📁 {item.name}/  ({len(children)} items)")
            for child in sorted(children)[:10]:
                prefix = "📁" if child.is_dir() else "📄"
                print(f"      {prefix} {child.name}")
            if len(children) > 10:
                print(f"      ... and {len(children) - 10} more")
        else:
            size = item.stat().st_size
            print(f"  📄 {item.name}  ({size:,} bytes)")

    # Show hooks summary if available
    hooks_json = plugin_root / "hooks" / "hooks.json"
    if hooks_json.exists():
        print()
        print("  [Hooks]")
        try:
            data = json.loads(hooks_json.read_text(encoding="utf-8"))
            hooks = data.get("hooks", data)
            for event, matchers in hooks.items():
                if event == "description":
                    continue
                print(f"    {event}:")
                if isinstance(matchers, list):
                    for m in matchers:
                        matcher = m.get("matcher", "*")
                        hook_list = m.get("hooks", [])
                        types = [h.get("type", "?") for h in hook_list]
                        print(f"      matcher={matcher}  types={types}")
        except Exception:
            print("    (parse error)")


def cmd_run(args):
    """Execute a plugin script with bridged environment variables."""
    bridge_plugins = get_bridge_plugins_dir()
    plugin_root = resolve_plugin(bridge_plugins, args.plugin)
    script_path = plugin_root / args.script
    project_dir = Path(args.project_dir).resolve() if args.project_dir else Path.cwd()

    if not script_path.exists():
        print(f"[!] Script not found: {script_path}", file=sys.stderr)
        sys.exit(1)

    # Build environment
    env = os.environ.copy()
    env["CLAUDE_PLUGIN_ROOT"] = str(plugin_root)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)

    # Determine executor
    script_ext = script_path.suffix.lower()
    is_windows = platform.system() == "Windows"

    if script_ext in (".sh", ""):
        if is_windows:
            git_bash = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"
            shell = str(git_bash) if git_bash.exists() else "bash"
            cmd = [shell, str(script_path)] + args.extra_args
        else:
            cmd = ["bash", str(script_path)] + args.extra_args
    elif script_ext == ".py":
        cmd = [sys.executable, str(script_path)] + args.extra_args
    elif script_ext == ".ps1":
        cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(script_path)] + args.extra_args
    else:
        cmd = [str(script_path)] + args.extra_args

    print(f"[*] Plugin  : {plugin_root.name}")
    print(f"[*] Script  : {args.script}")
    print(f"[*] Project : {project_dir}")
    print()

    stdin_data = args.stdin_data.encode() if args.stdin_data else None
    result = subprocess.run(cmd, env=env, cwd=str(project_dir), input=stdin_data)
    sys.exit(result.returncode)


def cmd_translate_readme(_args):
    """Translate README.md to README_en.md (Bridge to AI)."""
    # This command normally calls an LLM API.
    # In this bridge context, it serves as the orchestration point for Option 2.
    readme_path = Path(__file__).parent.parent / "README.md"
    target_path = Path(__file__).parent.parent / "README_en.md"

    if not readme_path.exists():
        print(f"[!] README.md not found at {readme_path}")
        sys.exit(1)

    print("[*] Option 2: Automated Translation (Simulation/Orchestration)")
    print(f"    Source: {readme_path}")
    print(f"    Target: {target_path}")
    print()

    # In a real CI environment, we would do:
    # api_key = os.environ.get("ANTHROPIC_API_KEY")
    # if api_key:
    #     translate_via_api(readme_path, target_path, api_key)

    print("[+] Prepared translation context.")
    print("[!] Requesting Antigravity Agent to perform the high-fidelity translation...")
    # The agent (Antigravity) sees this output and takes over the heavy lifting.


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="claude-bridge",
        description="Claude Code <-> Antigravity plugin bridge.",
    )
    sub = parser.add_subparsers(dest="command")

    # sync
    sub.add_parser("sync", help="Sync plugins from Claude marketplace")

    # list
    sub.add_parser("list", help="List all bridged plugins")
    
    # translate-readme
    sub.add_parser("translate-readme", help="Translate README.md to README_en.md")

    # info
    p_info = sub.add_parser("info", help="Show details of a specific plugin")
    p_info.add_argument("plugin", help="Plugin name (full or partial match)")

    # run
    p_run = sub.add_parser("run", help="Execute a plugin script with env bridging")
    p_run.add_argument("--plugin", required=True, help="Plugin name (full or partial)")
    p_run.add_argument("--script", required=True, help="Relative path to script in the plugin")
    p_run.add_argument("--project-dir", default=None, help="Override project directory")
    p_run.add_argument("--stdin-data", default=None, help="JSON to pipe to script stdin")
    p_run.add_argument("extra_args", nargs="*", help="Extra arguments for the script")

    args = parser.parse_args()

    commands = {
        "sync": cmd_sync,
        "list": cmd_list,
        "info": cmd_info,
        "run": cmd_run,
        "translate-readme": cmd_translate_readme,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
