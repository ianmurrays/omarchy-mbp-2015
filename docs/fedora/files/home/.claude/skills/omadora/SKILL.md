---
name: omadora
description: >
  Required for changes to this Fedora 44 GNOME MacBook Pro (MacBookPro11,5) and for the
  omadora repo at ~/src/omadora. Use when the user wants to change a keyboard shortcut,
  the Omadora menu (Super+Space), the Super+K list, crash capture, the agent hotkey, a
  GNOME setting, a system config file, or to record a fix. Triggers: shortcut, keybinding,
  hotkey, menu, Vicinae, gsettings, dconf, Omarchy, omadora, "record this fix".
---

# Omadora

The repo `~/src/omadora` records each change to this machine: the fixes for the hardware,
and a port of Omarchy features to GNOME. Read `~/src/omadora/README.md` first. It has the
index of the docs and the open items.

Use plan mode for a change to the system. Show the plan to the user before you change it.

## Repo layout

- `docs/<topic>.md`: one doc for each topic. Each change has **Status** (with a date),
  **Source**, the symptom, the cause, the fix steps, what did not work, and the revert steps.
- `files/`: the real config files. The path in `files/` is the install path.
  `files/etc/...` goes to `/etc/...` and `files/home/...` goes to `~/...`.
- `dconf/omadora.ini`: the GNOME shortcut settings. dconf settings have no file path.
- `README.md`: the index table, the open items, and the install order.

Most files in `files/` are copies. These files are symbolic links to the repo, so a change
in the repo is live:

- `~/.local/bin/omadora-*`
- `~/.claude/skills/omadora` and `~/.claude/skills/diagnose-crash`
- `~/.bashrc.d/agents.sh`

`~/.config/systemd/user/omadora-crash-watch.service` is a copy.

## The Omarchy features

See `docs/omarchy-features.md`.

| Part | File |
|---|---|
| Menu (Super+Space, Super+Escape) | `files/home/.local/bin/omadora-menu` |
| Keybinding list (Super+K) | `files/home/.local/bin/omadora-menu-keybindings` |
| Agent in a new terminal (Super+Shift+Ctrl+A) | `files/home/.local/bin/omadora-agent` |
| Crash capture | `files/home/.local/bin/omadora-crash-watch` and its user service |
| Shortcuts | `dconf/omadora.ini` |

Vicinae is the launcher. `vicinae dmenu` shows each menu list.

### Add or change a shortcut

1. Save the current settings:
   ```
   dconf dump / > "$(mktemp --suffix=.ini)"
   ```
2. Find a free key. Search the output of `omadora-menu-keybindings --print`.
3. Edit `dconf/omadora.ini`. A new custom shortcut needs a section
   `[org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/omadora-<slug>]`
   with `binding`, `command`, and `name`. Add its path to `custom-keybindings`.
4. Load the file:
   ```
   dconf load / < ~/src/omadora/dconf/omadora.ini
   ```
5. Make sure that the key shows in `omadora-menu-keybindings --print`.
6. Update the key table in `docs/omarchy-features.md`.

A shortcut command has no shell. For pipes, variables, or `~`, put the command in
`omadora-menu` as a route.

### Add a menu entry

1. Edit the `show_*` function in `omadora-menu`. Add the label to the `menu` call and a
   branch to the `case`.
2. Run `bash -n ~/src/omadora/files/home/.local/bin/omadora-menu`.
3. Update the menu tree in `docs/omarchy-features.md`.

No install step is necessary. `~/.local/bin/omadora-menu` is a symbolic link.

## Record a change

1. Add the change to the related doc, or make a new doc in `docs/`.
2. Add or update the row in the `README.md` index. Add an open item for each part that
   you did not verify.
3. Write docs, code comments, and commit messages in Simplified Technical English (the
   `/ste` skill).

## Safety

- Before you change kernel arguments, the GPU, suspend, or power settings, read
  `docs/gpu-kernel-args.md` and `docs/power.md`. A wrong kernel argument stops the
  display after resume.
- Do not try to switch the GPU mux at runtime. See `docs/gpu-kernel-args.md`.
- The Tailscale dnf repo has a GPG key error. Add `--disablerepo=tailscale-stable` to
  non-interactive `dnf` commands.
- `sudo` needs a password. Give the user the command with the `!` prefix.
