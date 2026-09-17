# Apps and tools

What Omarchy already provides, and the few app-level things still worth recording. The
Fedora-era app notes are archived in [fedora/apps.md](fedora/apps.md).

## Provided by Omarchy

Installed on 2026-09-17 without any work: `mise-bin` (2026.9.9), `docker` (29.7.2),
`foot` (1.28.0), `chromium` (152.0.7977.82), `obsidian`, `electron43`,
`power-profiles-daemon` (0.30), `polkit`, Hyprland (0.56.2) and the quickshell-based
Omarchy shell. Do not port the Fedora instructions for mise or Docker.

Installed after the first boot: `htop` (3.5.3), `tailscale` (1.102.3, `tailscaled`
enabled), `slack-desktop` (4.52.155) and `1password` (8.12.36). State on 2026-09-18.

Installed on Fedora and still absent here: `zellij`, `tlp`, `alacritty`, and `gh` from a
package (`gh` is present through mise instead). `openssh` is installed and `sshd` is
disabled.

## A GUI password prompt from an agent session

An agent session (Claude Code) has no terminal, so `sudo` fails with `a terminal is
required to read the password`. `pkexec` shows the polkit dialog instead:

```
pkexec /usr/bin/bash /path/to/script.sh
```

Give `pkexec` absolute paths. `polkitd` runs on Omarchy, so this works.

This came up on 2026-09-17: the IOMMU fix needed `/boot` and `/etc`, and the agent could
neither read nor write them. The workaround used was to write the script to disk and have
the user run it with `sudo` from the terminal.

> **Caution:** Do not use `pkill -f <path>` in a script. The pattern also matches the
> shell running the script, which kills it mid-run. Use `pkill -x <name>`. This is
> recorded in the Fedora notes and was still hit again on Omarchy.

## Claude Code status line (ccstatusline)

**Status:** In use on 2026-09-18. `~/.claude/settings.json` holds a `statusLine` block
with `"command": "npx -y ccstatusline@latest"`, and `~/.config/ccstatusline/settings.json`
exists again.

The widget configuration from the Fedora install is kept at
[`files/home/.config/ccstatusline/settings.json`](../files/home/.config/ccstatusline/settings.json).
Line 1: model, output style, context, thinking effort, session usage, reset timer, weekly
usage. Line 2: git branch, worktree, directory, version.

To set it up on a new machine, `npx -y ccstatusline@latest` needs no install and is what
this machine uses. A global install is the other option:

```
npm i -g ccstatusline@latest
```

Then point `statusLine.command` in `~/.claude/settings.json` at the **mise shim**, not the
binary: `~/.local/share/mise/shims/ccstatusline`. Without mise activation `node` is not on
`PATH` and the binary fails. A change of the global Node version loses the install.

## `~/.claude` iTerm hook on Linux

`~/.claude/settings.json` comes from a Mac, where 10 hooks call
`~/.config/iterm2/cc-status`. That path does not exist on Linux and each hook warns. The
guard is:

```
if [ -x "${HOME-}/.config/iterm2/cc-status" ]; then "${HOME-}/.config/iterm2/cc-status"; else cat >/dev/null 2>&1 || :; fi
```

The fix lives in the private dotfiles repository that holds `~/.claude`, not in this one,
so it carried across the reinstall with that repository.
