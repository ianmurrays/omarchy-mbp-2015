# Chromium and Electron glitch

**Status:** Fixed on Omarchy 2026-09-17, the user confirmed. Sources: Fedora sessions
`8fbd21c4` (2026-09-07), `bca8a489` and `18d61c42` (2026-09-11), `2ee64b83` (2026-09-14);
Omarchy session `317384bf` (2026-09-17).

**Symptom:** Chromium flickers, shows corrupted or old pixels, and stutters on scroll, all
at the same time. Video playback is correct. Firefox is correct.

> **Not the same bug as [iommu-dma-faults.md](iommu-dma-faults.md).** That one blanks the
> whole desktop and was diagnosed on the first Omarchy boot. This one was diagnosed on
> Fedora with VT-d off, affects only Chromium-based apps, and survives the IOMMU fix. If
> the bar and wallpaper are also blank, fix the IOMMU first.

**Cause:** `radeon` is a legacy driver with no atomic modesetting. Hyprland logs
`failed to set DRM_CLIENT_CAP_ATOMIC, falling back to legacy` and
`drmProps.supportsAddFb2Modifiers: false`, the same condition GNOME logged as
`using non-atomic mode setting`. The problem is in the buffer handoff from Chromium to
the compositor for scanout, not in the rendering.
[gpu-kernel-args.md](gpu-kernel-args.md) explains why the panel uses `radeon`.

**Fix:** `--disable-gpu-compositing`. Rasterization, canvas and video decode stay on the
GPU. Only the final composite moves to the CPU, which costs CPU time at 2880x1800.

## Where the flag goes on Omarchy

Arch launchers read a `flags.conf` file, so most apps need no desktop-entry edit. Which
file depends on the app:

| App | Reads | This repo |
|---|---|---|
| Chromium | `/etc/chromium-flags.conf`, then `~/.config/chromium-flags.conf` | [`files/etc/chromium-flags.conf`](../files/etc/chromium-flags.conf) |
| Obsidian, any Arch `electron*` app | `~/.config/electron<N>-flags.conf`, else `~/.config/electron-flags.conf` | [`files/home/.config/electron-flags.conf`](../files/home/.config/electron-flags.conf) |
| Chrome | `~/.config/chrome-flags.conf` only, no `/etc` fallback | not tracked, see below |
| Brave, Edge (if installed) | `~/.config/<name>-flags.conf` | not installed |
| Slack | nothing | [`files/home/.local/share/applications/slack.desktop`](../files/home/.local/share/applications/slack.desktop) |
| 1Password | nothing | [`files/home/.local/share/applications/1password.desktop`](../files/home/.local/share/applications/1password.desktop) |
| Claude Desktop | nothing | not installed |
| Discord | n/a here: an `omarchy-launch-webapp` Chromium web app | [`files/etc/chromium-flags.conf`](../files/etc/chromium-flags.conf) |

> **Caution:** Do not put the flag in `~/.config/chromium-flags.conf`. Omarchy owns that
> file and its migrations overwrite it:
> `cp -f "$OMARCHY_PATH/config/chromium-flags.conf" ~/.config/<browser>-flags.conf`.
> `/etc/chromium-flags.conf` is read first and Omarchy never touches it.

Install:

```
sudo install -m 0644 files/etc/chromium-flags.conf /etc/chromium-flags.conf
install -m 0644 files/home/.config/electron-flags.conf ~/.config/electron-flags.conf
```

Then quit the app fully and start it again.

**Verify:**

```
chromium --help | sed -n '/Currently detected flags/,$p'
ps -o args= -C chromium | head -1
```

The `electron43` wrapper uses `elif`: if `~/.config/electron43-flags.conf` exists, the
generic `electron-flags.conf` is **ignored**. Keep only the generic file unless you need
a per-version difference.

## Google Chrome

**Status:** Fixed 2026-09-18, `google-chrome` 153.0.8010.47-1 from the AUR.

`/usr/bin/google-chrome-stable` is a 10-line wrapper that reads **only**
`$XDG_CONFIG_HOME/chrome-flags.conf`. There is no `/etc/chrome-flags.conf` fallback the
way there is for Chromium, so unlike Chromium the flag has to live in `~/.config`:

```
--disable-gpu-compositing
```

The wrapper strips `#` comments, so the usual comment header is safe there.

**Not `--use-gl=desktop`.** The Fedora-era entry in
[`docs/fedora/`](fedora/files/home/.local/share/applications/google-chrome.desktop) put
that flag on all three `Exec` lines. It is removed from Chrome and Chromium on Arch and
kills the GPU process; see the section below.

**Is `~/.config/chrome-flags.conf` safe from Omarchy?** Checked on 2026-09-18 against
Omarchy's whole migration set. Three migrations touch `chrome-flags.conf` and all three
are **additive** — `sed -i` on the existing `--load-extension=` line, or an append:

| Migration | Does |
|---|---|
| `1780517689` | appends the yt-dlp extension |
| `1784508556` | appends `--password-store=gnome-libsecret` |
| `1785543725` | appends the WhatsApp Slim extension |

The `cp -f "$OMARCHY_PATH/config/chromium-flags.conf"` pattern the caution above warns
about appears exactly once, in `1784510887`, and it seeds
`~/.config/brave-origin-flags.conf` for a browser being swapped in. Nothing in the
current Omarchy overwrites `chrome-flags.conf`. If a future migration ever seeds it that
way, the flag is lost silently and has to go back.

The file is therefore **not tracked in this repo**: it is Omarchy-owned and its
`--load-extension=` line drifts with every migration, so a tracked copy would go stale
and invite a bad restore. Re-add the flag by hand.

**Verified:**

```
for p in $(pgrep -x chrome); do tr '\0' ' ' < /proc/$p/cmdline; echo; done
```

Every **renderer** shows `--disable-gpu-compositing`, and `chrome.err` has no
`ERROR:ui/gl/init/gl_factory.cc` line and no `Exiting GPU process`, so the switch was
accepted rather than merely passed. The GPU process stays alive and does not carry the
switch; that is expected, not a failure.

One unrelated error does show on this machine:
`ERROR:media/gpu/vaapi/vaapi_wrapper.cc] vaInitialize failed: resource allocation
failed`, i.e. no VA-API hardware video decode in Chrome. It comes from the GPU process's
VA-API probe, which `--disable-gpu-compositing` does not touch. Chrome was never run
before the flag was added, so it was not confirmed against a clean baseline, and it was
not investigated.

## Apps that bundle their own Electron

1Password, Slack and Claude Desktop ignore every `flags.conf`. They need a user copy of
the desktop entry, which also overrides the packaged one and survives package updates:

1. `cp /usr/share/applications/<app>.desktop ~/.local/share/applications/`
2. Add the flag to **every** `Exec` line.
3. `update-desktop-database ~/.local/share/applications`
4. Quit the app fully and start it again from the launcher.

**Slack** was installed this way on 2026-09-17, from the AUR
(`omarchy pkg aur add slack-desktop`, 4.52.155). Its flagged entry is tracked at
[`files/home/.local/share/applications/slack.desktop`](../files/home/.local/share/applications/slack.desktop);
keep the packaged `--gtk-version=3` and `-s %U` when you refresh it from
`/usr/share/applications/slack.desktop`. `/usr/bin/slack` is a symlink straight to the
Electron binary, so `Exec` flags reach Electron with no wrapper in between.

**1Password** was installed on 2026-09-17 by `omarchy-install-service-1password`
(8.12.36-2 from `extra`). Its flagged entry is tracked at
[`files/home/.local/share/applications/1password.desktop`](../files/home/.local/share/applications/1password.desktop);
keep the packaged `--force-device-scale-factor=1` and `%U` when you refresh it from
`/usr/share/applications/1password.desktop`.

Verified on 2026-09-18 by launching the entry and checking every child process:

```
for p in $(pgrep -x 1password); do tr '\0' ' ' < /proc/$p/cmdline; echo; done
```

The **renderer** must show `--disable-gpu-compositing`, not just the browser process.
Chromium forwards the switch to renderers only once it is in effect, so that is the
cheap proof it was *accepted*; the browser process alone only proves it was *passed*.
The GPU process never carries it and is still expected to be running.

Claude Desktop is not installed on Omarchy. Discord is an `omarchy-launch-webapp`
Chromium web app here, not bundled Electron, so `/etc/chromium-flags.conf` already
covers it. The Fedora-era copies are in
[`docs/fedora/`](fedora/files/home/.local/share/applications/).

### The 1Password instance started at login

**Status:** The flag was accepted on 2026-09-18. The user has not yet judged the flicker.

The desktop entry above covers a launch from the launcher. It does not cover the login
instance, and that instance is the one you get all day: 1Password is single-instance, so
while it runs, the launcher entry only activates it. The command line the login instance
started with is the command line for the whole session, and the launcher entry's flags,
`--force-device-scale-factor=1` included, do nothing.

1Password rewrites its own autostart entry on every start, so the flag cannot live there.
Confirmed on 2026-09-18: 1Password put
`~/.config/autostart/com.onepassword.OnePassword.desktop` back to
`Exec=/opt/1Password/1password --silent` on its next start.

Omarchy runs Hyprland under uwsm, so XDG autostart entries become user units through
`systemd-xdg-autostart-generator`. The generator makes the user service
`app-com.onepassword.OnePassword@autostart.service` from the entry, and a systemd drop-in
overrides the generated command. 1Password does not
control the drop-in, so the flag persists. Keep "Start at login" on in the app.

[`files/home/.config/systemd/user/app-com.onepassword.OnePassword@autostart.service.d/gpu.conf`](../files/home/.config/systemd/user/app-com.onepassword.OnePassword@autostart.service.d/gpu.conf):

```
[Service]
ExecStart=
ExecStart=/opt/1Password/1password --silent --disable-gpu-compositing
```

The empty `ExecStart=` is necessary. It clears the generated command before the second
line sets the new one.

Install:

```
install -Dm0644 'files/home/.config/systemd/user/app-com.onepassword.OnePassword@autostart.service.d/gpu.conf' \
  ~/.config/systemd/user/'app-com.onepassword.OnePassword@autostart.service.d'/gpu.conf
systemctl --user daemon-reload
systemctl --user restart app-com.onepassword.OnePassword@autostart.service
```

**Verified** on 2026-09-18:

```
systemctl --user show app-com.onepassword.OnePassword@autostart.service -p ExecStart -p DropInPaths
```

`DropInPaths` lists `gpu.conf` and `argv[]` shows the flag. Then open the 1Password window
and run the renderer check above. `--silent` starts 1Password without a window, and
Chromium makes no renderer until a window opens, so the renderer check shows nothing until
you open the window.

> **Caution:** the drop-in holds the full command. If a 1Password update changes the
> `Exec` line in its autostart entry, the drop-in hides that change and gives no message.

On Fedora the same problem was solved with a renamed autostart file and "Start at login"
off. See [`docs/fedora/apps.md`](fedora/apps.md) and the archived
[`1password-gpu.desktop`](fedora/files/home/.config/autostart/1password-gpu.desktop).
Omarchy uses the systemd drop-in above instead, which keeps "Start at login" on.

## `--use-gl=desktop` does not work on Arch

**Status:** Tested and rejected 2026-09-17.

Until 2026-09-17 this repo recommended `--use-gl=desktop`, from
[omacom/omarchy discussion 4694](https://github.com/omacom/omarchy/discussions/4694) and
verified against Google Chrome 153 on Fedora. **It is removed from Chromium 152 on Arch**
and does not fail gracefully. Every launch kills the GPU process:

```
ERROR:ui/gl/init/gl_factory.cc:110] Requested GL implementation (gl=none,angle=none) not found
  in allowed implementations: [(gl=egl-angle,angle=opengl),(gl=egl-angle,angle=opengles),(gl=egl-angle,angle=vulkan)]
ERROR:components/viz/service/main/viz_main_impl.cc:190] Exiting GPU process due to errors during initialization
```

ANGLE is now mandatory. The only choices are `--use-angle=gl`, `gles` or `vulkan`.

The old verification step in this repo was `ps` showing the flag, which only proves the
flag was **passed**, not **accepted**. If you reinstall Google Chrome, check its stderr
before trusting the flag there.

**Tried, did not work:**

- `--use-gl=desktop` (Chromium 152, Arch): GPU process exits on every launch, see above.
- `--use-gl=angle --use-angle=gl` (Chrome, Fedora): still glitched.
- `DRI_PRIME=pci-0000_00_02_0` (render on the Intel iGPU, Fedora): still glitched. The
  problem is thus not a `radeonsi` render bug.
- `DRI_PRIME` and ANGLE together (Fedora): still glitched.
- `intel_iommu=igfx_off`: irrelevant. It exempts the iGPU at `00:02.0`; nothing here
  faults on the iGPU. See [iommu-dma-faults.md](iommu-dma-faults.md).

**Not tested against the glitch:** `--use-angle=gl`, `gles` and `vulkan` were each
confirmed on 2026-09-17 to initialise without killing the GPU process, but none was
judged against the flicker. `--use-angle=gl` is the cheapest option if you want to retry,
though its Fedora equivalent did not help.

**Alternatives if the flicker returns:**

```
--ozone-platform=x11        # Fedora: no glitch, lower frame rate
--use-angle=gl              # cheaper than CPU compositing, previously ineffective
```

Both go in the same 2 files.

**Notes:**

- Flicker and stale pixels are temporal. A screenshot does not show them, so this fix
  cannot be verified by measurement the way the IOMMU fix was. The user is the
  instrument.
- A panel on the Intel iGPU would fix this natively, because `i915` has atomic KMS. The
  mux switch failed. See [gpu-kernel-args.md](gpu-kernel-args.md).
- Vicinae and other Qt Quick apps can show the same class of problem. The Qt escape hatch
  is `QT_QUICK_BACKEND=software`.

**Revert:** `sudo rm /etc/chromium-flags.conf`, `rm ~/.config/electron-flags.conf`,
`rm ~/.local/share/applications/{slack,1password}.desktop` and
`rm -r ~/.config/systemd/user/'app-com.onepassword.OnePassword@autostart.service.d'`, then
`systemctl --user daemon-reload`.
