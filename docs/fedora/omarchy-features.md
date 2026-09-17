# Omarchy features on GNOME

> **OBSOLETE — archived.** This doc ports Omarchy's menus, shortcuts, agent hotkey and
> crash capture *onto* Fedora GNOME, using Vicinae in place of the Omarchy shell. The
> machine now runs Omarchy itself, so every item here is replaced by the real feature.
> Kept for the reasoning only. See [../fedora/README.md](README.md).

**Status:** Applied 2026-09-17. Vicinae 0.28.2 and extension 1.7.2. The extension is
active after the next login. The crash notification action opens Claude Code (verified). The keys and the menus are not yet verified with a keyboard.
Source: session `eb735b17`.

[Omarchy](https://omarchy.org/manual/) is Arch Linux with Hyprland. This doc ports its
keyboard menus, its shortcuts, and its agent features to Fedora GNOME.

Omarchy 4 (`basecamp/omarchy`, branch `quattro`) shows all menus with a Quickshell shell.
The shell uses the `wlr-layer-shell` protocol. Mutter (the GNOME compositor) does not have
this protocol, thus the shell does not show on GNOME. Walker (the Omarchy 3 launcher) shows
only as a normal window on GNOME. Rofi 2.0 does not start on GNOME Wayland.

[Vicinae](https://docs.vicinae.com/) is the replacement. It has an app launcher, clipboard
history, an emoji picker, a calculator, and a dmenu mode. Its GNOME extension makes a
floating window that closes when it loses focus. The menu scripts are a port of the
Omarchy 3.8.4 `bin/omarchy-menu` bash script, with `vicinae dmenu` in place of
`walker --dmenu`.

Hyprland was not installed. A Hyprland session (for example
[Omedora](https://github.com/AndrewGaspar/omedora)) is not tested on this Radeon GPU, and
the GNOME fixes in this repo do not apply to it.

## Keys

The custom shortcuts are in [`dconf/omadora.ini`](dconf/omadora.ini). Super+K shows
all shortcuts that are set.

| Key | Action |
|---|---|
| Super+Space | Omadora menu |
| Super+Alt+Space | Apps (Vicinae) |
| Super+Escape | System menu |
| Super+K | Keybinding list |
| Super+Ctrl+E | Emoji picker (Vicinae) |
| Super+Ctrl+V | Clipboard history (Vicinae) |
| Super+Ctrl+Q | Calculator |
| Super+Ctrl+T | Activity (`btop`) |
| Super+Ctrl+C | GNOME screenshot and screen recording UI |
| Super+Ctrl+A / B / W / D / P | Sound / Bluetooth / Wi-Fi / Display / Power settings |
| Super+Ctrl+N | Toggle nightlight |
| Super+Ctrl+I | Toggle stay awake (no screen blank and no lock on idle) |
| Super+Ctrl+R | Set a reminder |
| Super+Ctrl+Alt+R | Show the reminders |
| Super+Ctrl+Shift+R | Clear the reminders |
| Super+Ctrl+Alt+T | Show the time |
| Super+Ctrl+Alt+B | Show the battery level |
| Super+Return | Terminal (Ptyxis) |
| Super+Shift+Return | Browser (Chrome) |
| Super+Shift+F | File manager |
| Super+Shift+/ | Password manager (1Password) |
| Super+Shift+Ctrl+A | Claude Code in a new terminal |
| Super+W, Super+Q | Close the window |
| Super+F | Full screen |
| Super+1..4 | Go to workspace 1..4 |
| Super+Shift+1..4 | Move the window to workspace 1..4 |

Changes to GNOME defaults:

- `<Super>space` no longer changes the keyboard layout. The top bar changes the layout.
- `<Super>1..4` no longer open the dock favorites. `<Super>5..9` still do.
- `<Super>Escape` no longer restores the shortcuts that an app blocks (for example a VM or
  a remote desktop).
- The number of workspaces is fixed at 4.

## Menu

[`omadora-menu`](files/home/.local/bin/omadora-menu):

```
Apps       Vicinae
Learn      Keybindings, Omarchy, GNOME, Fedora, Bash, Omadora (manuals)
Trigger    Agent, Emoji, Clipboard
           Reminder > Set, Show all, Clear all
           Toggle   > Stay Awake, Notifications, Nightlight, Dark Mode, Crash Capture
Setup      Keyboard, Display, Sound, Wi-Fi, Bluetooth, Power (GNOME Settings)
Update     System (dnf), Flatpak, Firmware (fwupd), Restart Wi-Fi (brcmfmac)
System     Lock, Suspend, Logout, Restart, Shutdown
```

`omadora-menu` also takes a route: `system`, `toggle NAME`, `reminder [show|clear]`,
`notice time|battery`. The shortcuts use these routes.

A reminder is a transient systemd user timer, `omadora-reminder-<time>.timer`. The unit
description holds the text.

## Keybinding list (Super+K)

[`omadora-menu-keybindings`](files/home/.local/bin/omadora-menu-keybindings) reads the
live GNOME settings with `Gio`. The custom shortcuts come first. Then come all keys of
`org.gnome.desktop.wm.keybindings`, `org.gnome.shell.keybindings`,
`org.gnome.mutter.keybindings`, `org.gnome.mutter.wayland.keybindings`, and
`org.gnome.settings-daemon.plugins.media-keys`. The list is for reading only.

- `omadora-menu-keybindings --print` writes the list to stdout.
- `omadora-menu-keybindings --check` runs the self-check of the key format.

## Agent

- Super+Shift+Ctrl+A runs [`omadora-agent`](files/home/.local/bin/omadora-agent). It
  opens Claude Code in a new Ptyxis window in `~/src`. Omarchy starts agents from
  `~/Work`, because agents do not keep the trust setting for the home directory.
- [`agents.sh`](files/home/.bashrc.d/agents.sh) adds the aliases `a` and `cx`. Both run
  `claude --permission-mode auto`, the same mode as Omarchy.
- The [`omadora` skill](files/home/.claude/skills/omadora/SKILL.md) tells an agent about
  this repo, and how to change a shortcut or a menu entry. It is the equivalent of the
  Omarchy skill.

## Crash capture

[`omadora-crash-watch`](files/home/.local/bin/omadora-crash-watch) reads the user
journal for `systemd-coredump` messages (`MESSAGE_ID=fc2e22bc6ee647b6b90729ab34a250b1`).
For each crash, it shows a critical notification with a "Diagnose with Claude" action. The
action runs `omadora-agent` with a prompt for the
[`diagnose-crash` skill](files/home/.claude/skills/diagnose-crash/SKILL.md). A program
that crashes again in 60 seconds gets no new notification.

The user service
[`omadora-crash-watch.service`](files/home/.config/systemd/user/omadora-crash-watch.service)
starts the script with the graphical session.

The `diagnose-crash` skill is a port of the Omarchy skill. It uses `coredumpctl`, the
Fedora debuginfod server, `rpm`, `dnf history`, and `abrt`.

## Install

1. Install Vicinae and btop:
   ```
   sudo dnf copr enable quadratech188/vicinae
   sudo dnf install --disablerepo=tailscale-stable vicinae btop
   systemctl --user enable --now vicinae
   ```
2. Install the Vicinae GNOME extension:
   ```
   gh release download -R dagimg-dot/vicinae-gnome-extension -p '*.zip'
   gnome-extensions install --force vicinae@dagimg-dot.shell-extension-v*.zip
   ```
3. Enable the extension. The running GNOME Shell does not know the new extension, so
   `gnome-extensions enable` fails. Add the UUID to the list instead:
   ```
   gsettings get org.gnome.shell enabled-extensions
   gsettings set org.gnome.shell enabled-extensions "[<current list>, 'vicinae@dagimg-dot']"
   ```
4. Block 1Password from the clipboard history. The extension compares the names with a
   substring match that ignores case. The 2 names cover `1Password` and
   `com.onepassword.OnePassword`:
   ```
   gsettings --schemadir ~/.local/share/gnome-shell/extensions/vicinae@dagimg-dot/schemas \
     set org.gnome.shell.extensions.vicinae blocked-applications "['1Password', 'onepassword']"
   ```
5. Log out and log in. GNOME on Wayland loads a new extension only at login.
6. Make the symbolic links:
   ```
   ln -sfn ~/src/omadora/files/home/.local/bin/omadora-* ~/.local/bin/
   ln -sfn ~/src/omadora/files/home/.claude/skills/omadora ~/.claude/skills/omadora
   ln -sfn ~/src/omadora/files/home/.claude/skills/diagnose-crash ~/.claude/skills/diagnose-crash
   ln -sfn ~/src/omadora/files/home/.bashrc.d/agents.sh ~/.bashrc.d/agents.sh
   ```
7. Install and start the crash watcher:
   ```
   cp ~/src/omadora/files/home/.config/systemd/user/omadora-crash-watch.service ~/.config/systemd/user/
   systemctl --user daemon-reload
   systemctl --user enable --now omadora-crash-watch
   ```
8. Save the current dconf settings, then load the shortcuts:
   ```
   dconf dump / > ~/dconf-before-omadora.ini
   dconf reset -f /org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/custom0/
   dconf load / < ~/src/omadora/dconf/omadora.ini
   ```
   `custom0` was an old test shortcut (`notify-send "test"`) with no key.

## Verify

1. Run `omadora-menu-keybindings --check`. The output is `ok`.
2. Run `omadora-menu-keybindings --print | head -1`. The line starts with `Super + Space`
   and ends with `→ Omadora menu`.
3. Push Super+Space. The menu opens. Push Escape. The menu closes and nothing runs.
4. Run `omadora-menu toggle nightlight` 2 times. The setting has its first value again.
5. Set a reminder for 1 minute. Run `omadora-menu reminder show` before it starts.
6. Start a crash:
   ```
   bash -c 'kill -SEGV $$'
   ```
   A notification "bash crashed (SIGSEGV)" shows. Click "Diagnose with Claude". Claude
   Code opens in `~/src`.
7. Push Super+2, then Super+Shift+1.

## Not ported

| Omarchy feature | Reason |
|---|---|
| Style: themes, backgrounds, fonts, Plymouth | Needs the Omarchy shell and Hyprland |
| Install and Remove menus | pacman and AUR |
| Share (LocalSend) | LocalSend is not installed |
| Capture scripts, color picker, OCR, QR | grim, slurp, and hyprpicker need wlroots. Super+Ctrl+C opens the GNOME UI. |
| Hyprland toggles: gaps, layouts, groups, scratchpad, Super+Arrow focus | No GNOME equivalent |
| Super+C / V / X universal clipboard | GNOME cannot remap keys for each window |
| Notification keys (Super+Comma) | GNOME has no command to close a notification |
| CapsLock emoji compose | Caps Lock is Ctrl on this machine |
| Agents usage panel | No bar. ccstatusline shows the usage in Claude Code. |
| mise agent stubs, agent picker, `tdl` tmux layouts | Only Claude Code is in use. Zellij is in use, not tmux. |
| Crash mute list | Toggle > Crash Capture turns off all notifications |

## Notes

- On 0.28.2, `vicinae dmenu --help` lists all options that the scripts use.
  `vicinae cmd ls --json` lists `core:search-emojis` and `clipboard:history`. A
  closed dmenu exits with 1.
- A `vicinae vicinae://close` command stopped and did not exit after a closed dmenu.
  The scripts do not use it.
- Vicinae uses Qt Quick. If it shows incorrectly on the Radeon GPU, add
  `Environment=QT_QUICK_BACKEND=software` in a drop-in for `vicinae.service`. See
  [electron-glitch.md](../electron-glitch.md) for the same type of problem.
- The custom shortcut paths have names (`omadora-menu/`), not numbers (`custom0/`).
  GNOME Settings shows them. GNOME Settings uses the next free `customN/` path for a
  shortcut that you add there.
- ABRT is active. It can show its own crash notification next to the Omadora notification.
- A GNOME shortcut command has no shell. A command that needs pipes, variables, or `~` is
  a route in `omadora-menu`.

## Revert

1. Reset the shortcuts. `dconf load` of the backup does not remove the new keys. The first
   command also resets all other changes to the media keys:
   ```
   dconf reset -f /org/gnome/settings-daemon/plugins/media-keys/
   for k in close toggle-fullscreen switch-input-source switch-input-source-backward \
            switch-to-workspace-{1..4} move-to-workspace-{1..4}; do
     gsettings reset org.gnome.desktop.wm.keybindings $k
   done
   for k in show-screenshot-ui switch-to-application-{1..4}; do
     gsettings reset org.gnome.shell.keybindings $k
   done
   gsettings reset org.gnome.mutter.wayland.keybindings restore-shortcuts
   gsettings reset org.gnome.mutter dynamic-workspaces
   gsettings reset org.gnome.desktop.wm.preferences num-workspaces
   ```
2. Stop the services and remove the files:
   ```
   systemctl --user disable --now omadora-crash-watch vicinae
   rm ~/.config/systemd/user/omadora-crash-watch.service ~/.local/bin/omadora-*
   rm ~/.claude/skills/omadora ~/.claude/skills/diagnose-crash ~/.bashrc.d/agents.sh
   ```
3. Remove Vicinae:
   ```
   gnome-extensions uninstall vicinae@dagimg-dot
   sudo dnf remove vicinae
   sudo dnf copr remove quadratech188/vicinae
   ```
