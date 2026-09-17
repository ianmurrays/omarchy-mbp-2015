# Apps and tools

> **ARCHIVED — Fedora.** `dnf`, COPR, SELinux labels, `.deb` extraction and Ptyxis. Omarchy
> provides mise and Docker itself. The parts that still apply were moved to
> [../apps.md](../apps.md); the 1Password autostart trap and the `pkill -f` trap below are
> still true.

Electron apps on this machine need `--disable-gpu-compositing`. See
[electron-glitch.md](../electron-glitch.md).

## Orca ADE (AppImage)

**Status:** Applied 2026-09-11 (install) and 2026-09-14 (autostart). Sources: sessions
`18d61c42`, `6a374f59`.

1. Move the AppImage and make it executable:
   ```
   mkdir -p ~/Applications
   mv ~/Downloads/orca-linux.AppImage ~/Applications/orca-ide.AppImage
   chmod +x ~/Applications/orca-ide.AppImage
   ```
2. Copy the icons from the AppImage:
   ```
   ~/Applications/orca-ide.AppImage --appimage-mount    # in a 2nd terminal; prints the mount point, stays open until Ctrl+C
   for sz in 16x16 24x24 32x32 48x48 64x64 128x128 256x256 512x512; do
     install -Dm644 "$MP/usr/share/icons/hicolor/$sz/apps/orca-ide.png" ~/.local/share/icons/hicolor/$sz/apps/orca-ide.png
   done
   gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
   ```
   `$MP` is the mount point from the first command.
3. Copy [`orca-ide.desktop`](files/home/.local/share/applications/orca-ide.desktop) to
   `~/.local/share/applications/`.
4. To start Orca at login, copy the
   [autostart entry](files/home/.config/autostart/orca-ide.desktop) to
   `~/.config/autostart/`.
5. Validate and update the database:
   ```
   desktop-file-validate ~/.local/share/applications/orca-ide.desktop ~/.config/autostart/orca-ide.desktop
   update-desktop-database ~/.local/share/applications
   ```

**Notes:**

- Fedora 44 has no `libfuse.so.2`. This AppImage has a static runtime, so `fuse-libs` is
  not necessary.
- The AppImage updates itself. `X-AppImage-Version=1.4.200` in the desktop entry can be
  old. Orca also makes `~/.local/bin/orca-ide`.
- `/usr/bin/orca` and `orca.desktop` are the GNOME screen reader, not Orca ADE.
- The autostart entry starts Orca at login, not at boot. Start at boot needs a systemd
  user service for `orca serve` and `loginctl enable-linger`. Not done.
- `spawn codex ENOENT` in the Orca log is harmless. The `codex` CLI is not installed.

> **Caution:** Do not use `pkill -f orca-ide`. The pattern also matches the shell that
> runs the command. Use `pkill -x orca-ide`.

## Claude Desktop (.deb)

**Status:** Applied 2026-09-14, version 44.2.0. Source: session `2ee64b83`.

Anthropic gives Claude Desktop for Linux only as a `.deb`. `claude.com/download` has no
`.rpm` link. The `.deb` payload uses standard paths. Its `postinst` script only adds an
apt repo and an AppArmor profile, which do not apply to Fedora. All 12 runtime
dependencies were already installed. `alien` is not necessary.

1. Extract the archive:
   ```
   ar x ~/Downloads/claude-desktop_amd64.deb
   ```
2. Extract the payload to `/`. The `-p` option keeps mode 4755 on `chrome-sandbox`:
   ```
   sudo tar -xpf data.tar.xz -C / --exclude='./usr/share/doc/*'
   ```
3. Set the SELinux labels:
   ```
   sudo restorecon -RF /usr/lib/claude-desktop /usr/bin/claude-desktop /usr/share/applications/com.anthropic.Claude.desktop
   ```
4. Update the caches:
   ```
   sudo gtk-update-icon-cache -f /usr/share/icons/hicolor
   sudo update-desktop-database /usr/share/applications
   ```
5. Copy [`com.anthropic.Claude.desktop`](files/home/.local/share/applications/com.anthropic.Claude.desktop)
   to `~/.local/share/applications/`. Then run
   `update-desktop-database ~/.local/share/applications`.

**Verify:** `cat /usr/lib/claude-desktop/version`.

**Notes:**

- Updates are manual. For a new version, download the `.deb` and do the steps again.
- `dpkg-deb` is not installed. `ar` and `tar` are sufficient.
- The `.deb` control file says `Version: 1.52386.6`. The app version file says `44.2.0`.
- `rpm -q claude-desktop` shows "not installed". This is correct for this install
  method.
- If the app still flickers, try `--ozone-platform=x11`.

**Uninstall:**

```
sudo rm -rf /usr/lib/claude-desktop /usr/bin/claude-desktop /usr/share/applications/com.anthropic.Claude.desktop /usr/share/icons/hicolor/*/apps/claude-desktop.png
rm ~/.local/share/applications/com.anthropic.Claude.desktop
```

## A GUI password prompt from an agent session

An agent session (Claude Code, Orca) has no terminal. `sudo` fails with `a terminal is
required to read the password`. `pkexec` shows the GNOME polkit password dialog:

```
pkexec /usr/bin/bash /path/to/script.sh
```

Give `pkexec` absolute paths.

## Zellij copy under Ptyxis

**Status:** Applied 2026-09-11. Source: session `8caf6b06`.

**Symptom:** A zellij selection shows "Copied to clipboard", but the clipboard does not
change.

**Cause:** When `copy_command` is not set, zellij copies with the OSC 52 escape
sequence. Ptyxis (VTE) does not implement OSC 52 clipboard writes and ignores the
sequence. Zellij does not know this, so it reports success.

**Fix:** In `~/.config/zellij/config.kdl`, set `copy_command`. The stock file has it
commented out. On this machine, line 369 changed from `// copy_command "pbcopy"` to:

```kdl
copy_command "wl-copy"
```

Then stop the session and start a new one: `zellij kill-session <name>`. Zellij cannot
load its config again in a running session.

**Notes:**

- The zellij server must have `WAYLAND_DISPLAY` and `XDG_RUNTIME_DIR`. A server that
  starts from a terminal has them. A server that starts from a systemd unit possibly
  does not.
- `copy_clipboard "primary"` has no effect when `copy_command` is set. Use
  `copy_command "wl-copy --primary"`.
- Without a config change: hold **Shift** while you drag. Ptyxis then does the
  selection, and the copy works.

## Node via mise

**Status:** Applied 2026-09-11. Source: session `8ff274ca`.

mise installs Node at user level, with no sudo, and can pin versions per project. No
`nodejs` dnf package is installed.

1. Install mise to `~/.local/bin/mise`:
   ```
   curl -fsSL https://mise.run | sh
   ```
2. Copy [`mise.sh`](files/home/.bashrc.d/mise.sh) to `~/.bashrc.d/`. The stock Fedora
   `~/.bashrc` reads each file in `~/.bashrc.d/`.
3. Set the global Node version. This writes
   [`~/.config/mise/config.toml`](files/home/.config/mise/config.toml):
   ```
   mise use -g node@24
   ```
4. Start a new shell: `exec bash`.

**Verify:** `which node npx` shows paths in `~/.local/share/mise/shims/`.

**Notes:**

- Change the global version with `mise use -g node@22`. Set a project version with
  `mise use node@<ver>` in the project.
- `npm i -g <pkg>` installs into the current Node version. A version change loses it.
  For tools that must stay, use `mise use -g npm:<pkg>`.
- On 2026-09-14, a `ruby -v` in an unrelated project made mise install Ruby 4.0.1 (about
  99 MB) in `~/.local/share/mise/installs/ruby/4.0.1`. Nothing uses it.

## Docker CE

**Status:** Applied 2026-09-14. Source: session `a5175ca7`.

Podman was installed, but with no compose provider. Docker CE has the compose plugin and
SELinux labels are off by default, so Docker CE was selected over Fedora `moby-engine`.

1. Add the repo. This writes [`docker-ce.repo`](files/etc/yum.repos.d/docker-ce.repo):
   ```
   sudo dnf config-manager addrepo --from-repofile=https://download.docker.com/linux/fedora/docker-ce.repo
   ```
2. Install the packages:
   ```
   sudo dnf install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   ```
3. Enable the service:
   ```
   sudo systemctl enable --now docker
   ```
4. Add your user to the `docker` group:
   ```
   sudo usermod -aG docker $USER
   ```
5. **Reboot.** A logout is not sufficient (see the caution).

> **Caution:** `user@1000.service` starts at boot and keeps the old group list after a
> logout. Orca and Claude Code run under it. Only a reboot gives them the `docker` group.
> Before the reboot, use `sg docker -c '<command>'`.

**Verify:** `id -nG` includes `docker`. `docker info` works without `sudo`.

No `/etc/docker/daemon.json` exists.

## ccstatusline (Claude Code status line)

**Status:** Applied 2026-09-14. Source: session `fde44e28`.

**Symptom:** The Claude Code status line was empty.

**Cause:** `statusLine.command` in `~/.claude/settings.json` was
`bunx -y ccstatusline@latest`, but bun is not installed. bun is still not installed.

**Fix:**

1. Install ccstatusline into the mise Node:
   ```
   npm i -g ccstatusline@latest
   ```
2. In `~/.claude/settings.json`, set `statusLine.command` to
   `~/.local/share/mise/shims/ccstatusline`, with the home directory written out in full.

**Notes:**

- Use the mise shim, not the binary. Without mise activation, `node` is not in `PATH`,
  and the binary fails.
- A change of the global Node version loses the install. Run `npm i -g ccstatusline`
  again.
- The widget config is [`~/.config/ccstatusline/settings.json`](../../files/home/.config/ccstatusline/settings.json).
  Line 1: model, output style, context, thinking effort, session usage, reset timer,
  weekly usage. Line 2: git branch, worktree, directory, version.

## ~/.claude iTerm hook on Linux

**Status:** Applied 2026-09-14, in the private dotfiles repository that holds `~/.claude`.
Source: session
`9adb53df`.

**Symptom:** Claude Code hooks gave warnings on Fedora.

**Cause:** `~/.claude/settings.json` comes from the Mac. 10 hooks called
`/Users/<user>/.config/iterm2/cc-status`, a macOS path that does not exist on Linux.

**Fix:** Each of the 10 hook commands is now:

```
if [ -x "${HOME-}/.config/iterm2/cc-status" ]; then "${HOME-}/.config/iterm2/cc-status"; else cat >/dev/null 2>&1 || :; fi
```

The fix is in the private dotfiles repository, not in this repository.

## Packages that the user installed

- `zellij` (2026-09-11)
- `htop` (2026-09-14): `sudo dnf install htop`
- `vim-enhanced` (2026-09-14)
