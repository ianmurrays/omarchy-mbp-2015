# Power

> **Omarchy status, 2026-09-18: TLP is not applied.** `tlp` is not installed.
> `power-profiles-daemon` 0.30-1 is installed, enabled and active, and it is what the
> Omarchy power menu talks to. Idle suspend is already off; see below. The Fedora
> procedures that this page replaced are archived in [fedora/power.md](fedora/power.md).

## Measured idle budget

Measured 2026-09-07 on battery, after TLP, load 0.16, backlight at full: **24.86 W**.
The measurement is from the Fedora install. The hardware did not change, so the numbers
still describe this machine, but they were not taken again on Omarchy.

| Part | Power |
|---|---|
| CPU package (RAPL) | 4.19 W |
| DRAM (RAPL) | 1.31 W |
| Backlight, full range | about 2 W |
| Other (Radeon, PCH, Wi-Fi, Thunderbolt, SSD, VRM) | about 16 W, not measured |

Before TLP, idle power was about 29 W. Before the radeon fix, it was 36.4 W. The idle
Radeon is the most probable large part of the 16 W. The Radeon cannot turn off, because
it drives the panel.

RAPL `energy_uj` is readable only by root.

## TLP instead of power-profiles-daemon

**Status:** Not applied on Omarchy. Applied on Fedora 2026-09-07, where it gave the
24.86 W above. Source: session `8fbd21c4`.

**Symptom:** About 29 W at idle. SATA link power at `max_performance`. Radeon DPM at
`balanced`.

**Trade-off:** Arch has `tlp` and `tlp-pd` as 2 packages. `tlp-pd` 1.10.2-1 has
`Provides: power-profiles-daemon` and `Conflicts With: power-profiles-daemon`, so it
replaces the daemon and keeps the same `net.hadess.PowerProfiles` interface. Install both
packages, or the Omarchy power menu loses its backend. The menu was not tested against
`tlp-pd` on this machine.

**Fix:**

1. Install TLP, its power profile daemon, and powertop. Pacman asks to remove
   `power-profiles-daemon` in the same transaction, because `tlp-pd` conflicts with it:
   ```
   sudo pacman -S tlp tlp-pd powertop
   ```
2. Copy [`files/etc/tlp.d/01-macbookpro11-5.conf`](../files/etc/tlp.d/01-macbookpro11-5.conf)
   to `/etc/tlp.d/`:
   ```
   sudo install -m 0644 files/etc/tlp.d/01-macbookpro11-5.conf /etc/tlp.d/
   ```
3. Enable TLP and its profile daemon:
   ```
   sudo systemctl enable --now tlp tlp-pd
   ```

**Verify:** `tlp-stat -s` shows TLP enabled. Then check that the power menu still has a
backend: `powerprofilesctl get` must still answer. Not tested against `tlp-pd` on this
machine.

**Traps:**

- TLP 1.10 has 3 profiles: performance, balanced and save. A power menu that selects
  "Power Saver" selects `SAV`. The `_ON_SAV` defaults override the `_ON_BAT` values. A
  value set only with `_ON_BAT` has no effect in that profile. The conf file sets the
  `_ON_SAV` values.
- `CPU_SCALING_GOVERNOR` is `schedutil`. The CPU driver is `intel_cpufreq` in passive
  mode, and in that mode `powersave` holds the CPU at its minimum frequency.
- Enable `tlp-pd.service`. Without it, TLP logs "You can't switch TLP profiles by mouse
  click because tlp-pd.service is not enabled".

**Tried, did not work** (on Fedora, same hardware):

- SATA ALPM. The Apple/Samsung `S4LN058A01` AHCI controller reports no `salp` or `sadm`
  flag, so `link_power_management_policy` stays `max_performance`. The lines are
  commented out in the conf file.
- `RADEON_DPM_PERF_LEVEL=low`. It holds the GPU at 300 MHz and gave no measurable power
  decrease. The conf file uses `auto`.

**Revert:**
```
sudo pacman -Rns tlp tlp-pd && sudo pacman -S power-profiles-daemon && sudo systemctl enable --now power-profiles-daemon
```

## No idle suspend

**Status:** Already true on Omarchy. No change is necessary. Verified 2026-09-18.

**Goal:** The machine stays awake and reachable. The screen still blanks and locks.

Omarchy does not suspend on idle. logind `IdleAction` is `ignore`, and the Omarchy shell
controls only the screensaver and the lock screen.

**Verify:**

The answer must be `s "ignore"`:

```
busctl get-property org.freedesktop.login1 /org/freedesktop/login1 org.freedesktop.login1.Manager IdleAction
```

**The knobs:**

- `~/.config/omarchy/shell.json`, key `idle`: `screensaver` 150 and `lock` 300, in
  seconds since the idle time started. The shell reads the file again on each save.
- `omarchy toggle idle stay-awake` stops the screensaver and the lock screen until you
  set `allow-idle` again. It writes `~/.local/state/omarchy/indicators/stay-awake`.
- A closed lid still suspends: logind `HandleLidSwitch` is `suspend`. To stop that, make
  `/etc/systemd/logind.conf.d/10-no-lid-suspend.conf` with `[Login]`,
  `HandleLidSwitch=ignore` and `HandleLidSwitchExternalPower=ignore`. This is proposed,
  not applied.

**Note:** On battery, the machine uses the full idle power until the battery is empty.
This is intentional. It is not a power regression.

## Battery charge limit (80%)

**Status:** Not possible on this hardware. Source: session `72707d5e` (2026-09-14).

- `BAT0` has no `charge_control_start_threshold`, `charge_control_end_threshold` or
  `charge_behaviour`. `tlp-stat -b` shows "(not available)".
- `applesmc` cannot write the Apple charge limit SMC key (`BCLM`).
- Battery health on 2026-09-14: 8246/8600 mAh (96%), 54 cycles.
