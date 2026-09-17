# Archive: the Fedora install

This machine ran Fedora 44 with GNOME on Wayland from 2026-09-07 to 2026-09-17, then was
reinstalled with Omarchy. See [omarchy-install.md](../omarchy-install.md).

Everything in this directory describes that Fedora install. None of it is applied on
Omarchy, and most of it cannot be. It is kept because the diagnoses are real work and the
hardware has not changed: if a problem comes back, the reasoning here is still the
fastest route to it.

| File | Why it is archived |
|---|---|
| [omarchy-features.md](omarchy-features.md) | Its entire purpose was to port Omarchy's menus, shortcuts, agent hotkey and crash capture **onto** GNOME, using Vicinae in place of the Omarchy shell. The machine now runs Omarchy, so all of it is replaced by the real thing. |
| [power.md](power.md) | `dnf`, the tuned/TLP swap and the GNOME `gsettings` keys for idle suspend. Arch splits TLP into `tlp` and `tlp-pd`, and Omarchy has no idle suspend to turn off. The measured numbers and the battery facts stayed in [../power.md](../power.md). |
| [igpu-runtime-suspend.md](igpu-runtime-suspend.md) | 2 of the 3 holders that kept `i915` awake were Mutter and `gnome-shell`, and the fix used `grubby`. Under Hyprland the iGPU already sleeps; see [../igpu-runtime-suspend.md](../igpu-runtime-suspend.md). |
| `files/etc/udev/rules.d/99-hide-i915-from-seat.rules` | Moves the iGPU off seat0 so Mutter skips it. There is no Mutter on Omarchy, and `i915` reaches `suspended` with the `master-of-seat` tag still in place. |
| [boot-splash.md](boot-splash.md) | Fedora Plymouth via `grubby` and `/etc/default/grub`. Omarchy sets `quiet splash` in `/etc/limine-entry-tool.d/omarchy-defaults.conf` and ships its own theme. |
| [apps.md](apps.md) | Mostly `dnf`, COPR, SELinux labels, `.deb` extraction and Ptyxis. Omarchy provides mise and Docker itself. The still-useful parts were moved to [../apps.md](../apps.md). |
| `dconf/omadora.ini` | GNOME keyboard shortcuts. Hyprland has its own. |
| `files/home/.local/bin/omadora-*` | The GNOME menu, keybinding list, agent launcher and crash watcher. Omarchy has `omarchy-menu` and `omarchy-crash-watch`. |
| `files/home/.claude/skills/` | Ports of the Omarchy `diagnose-crash` and Omarchy skills onto Fedora. Omarchy ships both. |
| `files/home/.config/autostart/` | GNOME autostart entries for Orca and 1Password. Hyprland uses `exec-once` and uwsm. |
| `files/home/.local/share/applications/` | Desktop entries carrying `--disable-gpu-compositing` for Chrome, Claude Desktop, 1Password and Orca. None of those apps is installed on Omarchy, but the **recipe** still applies to any app that bundles its own Electron. See [../electron-glitch.md](../electron-glitch.md). |
| `files/etc/yum.repos.d/` | Fedora Docker CE repo. |
| `files/home/.config/mise/config.toml` | The Fedora-era mise tool list (`node = "24"`). The live file on Omarchy has different tools and versions, and no doc in this repo depends on it. |
| `files/home/.bashrc.d/` | Fedora reads `~/.bashrc.d/`; Omarchy manages its own shell config. |

## Things in here that are still true

- **The 1Password autostart trap.** 1Password rewrites its own autostart entry on every
  start, so a flag added to it never survives. The Fedora workaround (turn off "Start at
  login", use an autostart file under a different name) is in [apps.md](apps.md) and
  [`1password-gpu.desktop`](files/home/.config/autostart/1password-gpu.desktop). Omarchy
  runs Hyprland under uwsm, so autostart entries become systemd user units and a drop-in
  overrides the generated command instead; see [../electron-glitch.md](../electron-glitch.md).
- **`pkexec` for a GUI password prompt** from an agent session with no terminal. Still
  the right answer on Omarchy; `polkitd` is running.
- **The `pkill -f` trap.** `pkill -f <path>` also matches the shell running the script.
  Use `pkill -x`. This was hit again on 2026-09-17, on Omarchy, in the session that wrote
  this file.
- **The Claude Desktop `.deb` layout.** Anthropic ships Linux only as a `.deb`; the
  payload uses standard paths and `ar` plus `tar` is enough.
