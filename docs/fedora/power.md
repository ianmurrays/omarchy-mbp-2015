# Archive: power on Fedora

The procedures on this page ran on Fedora 44 with GNOME. They do not run on Omarchy: the
package manager, the power profile daemon and the idle settings are all different. The
Omarchy versions are in [../power.md](../power.md), which also keeps the measured numbers
and the battery facts, because the hardware did not change.

## TLP replaces tuned

**Status:** Applied on Fedora 2026-09-07. Source: session `8fbd21c4`.

**Symptom:** About 29 W at idle. SATA link power at `max_performance`. Radeon DPM at
`balanced`.

**Fix:**

1. Remove tuned first:
   ```
   sudo dnf remove -y tuned tuned-ppd
   ```
2. Install TLP:
   ```
   sudo dnf install -y tlp powertop
   ```
   On Fedora this also installs `tlp-pd`, `hdparm` and `xset`.
3. Copy [`files/etc/tlp.d/01-macbookpro11-5.conf`](../../files/etc/tlp.d/01-macbookpro11-5.conf)
   to `/etc/tlp.d/`.
4. Enable TLP:
   ```
   sudo systemctl enable --now tlp
   sudo tlp start
   ```

> **Caution:** Do not use `dnf install --allowerasing tlp`. The solver then selects the
> older `tlp-1.9.0`, which does not declare the conflict with tuned, and the
> transaction fails on file conflicts.

> **Caution:** A `dnf` transaction that runs while an offline update is pending cancels
> that update. After the install, run `sudo dnf upgrade` again.

**Verify:** `tlp-stat -s` shows TLP enabled. `rpm -q tuned` shows "not installed".

**Traps:**

- TLP 1.10 has 3 profiles: performance, balanced and save. GNOME "Power Saver" selects
  `SAV`. The `_ON_SAV` defaults override the `_ON_BAT` values. A value set only with
  `_ON_BAT` has no effect in Power Saver. The conf file sets the `_ON_SAV` values.
- `tlp-pd` provides `net.hadess.PowerProfiles`, so the GNOME power profile menu stays
  available after the removal of `tuned-ppd`.
- `CPU_SCALING_GOVERNOR` is `schedutil`. The CPU driver is `intel_cpufreq` in passive
  mode, and in that mode `powersave` holds the CPU at its minimum frequency.

**Open on Fedora:** `tlp-pd.service` was disabled. TLP logged "You can't switch TLP
profiles by mouse click because tlp-pd.service is not enabled". The effect on the GNOME
menu was not verified.

**Revert:**
```
sudo dnf remove tlp && sudo dnf install tuned tuned-ppd && sudo systemctl enable --now tuned tuned-ppd
```

## No idle suspend

**Status:** Applied on Fedora 2026-09-11. Source: session `3a667dc5`.

**Goal:** The machine stays awake and reachable. The screen still blanks and locks.

**Fix:**

```
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'
```

These keys stay at their default values: `org.gnome.desktop.session idle-delay` 300,
`org.gnome.desktop.screensaver lock-enabled` true, `lock-delay` 0.

**Verify:** `gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type`
shows `'nothing'`.

**Notes:**

- On battery, the machine uses the full idle power until the battery is empty. This is
  intentional. It is not a power regression.
- logind `IdleAction` was `ignore`. `HandleLidSwitch` was `suspend`, so a closed lid
  still suspends.
- Proposed, not applied: `/etc/systemd/logind.conf.d/10-no-lid-suspend.conf` with
  `[Login]`, `HandleLidSwitch=ignore` and `HandleLidSwitchExternalPower=ignore`.

**Revert:** `gsettings reset` on the 2 keys. The Fedora default is `'suspend'` after
900 s.

**Why this is not needed on Omarchy:** there is no `org.gnome.settings-daemon` schema,
and logind already has `IdleAction=ignore`. See [../power.md](../power.md).
