# Archive: Intel iGPU runtime suspend on Fedora

**Status:** Applied on Fedora 2026-09-14. The user confirmed the display hotplug. Source:
session `72707d5e`.

Two of the 3 causes below are GNOME causes, and the fix used `grubby`. Omarchy has
neither. The Omarchy state is in
[../igpu-runtime-suspend.md](../igpu-runtime-suspend.md).

**Symptom:** The Intel Iris Pro P5200 (`0000:00:02.0`, `card1`) drives no display, but
`/sys/bus/pci/devices/0000:00:02.0/power/runtime_status` always shows `active`.

**Cause:** 3 independent holders keep `i915` awake:

1. udev tags the iGPU `master-of-seat` on seat0. Mutter then opens it
   (`Created gbm renderer for '/dev/dri/card1'`), and `gnome-shell` and Xwayland hold
   `/dev/dri/card1`.
2. GTK4 4.22 uses the Vulkan renderer by default. RADV refuses the Radeon, because it
   uses `radeon` and not `amdgpu` (`VK_ERROR_INCOMPATIBLE_DRIVER`). GTK4 then uses the
   Intel HASVK driver, which Mesa marks as incomplete. GTK4 apps (Ptyxis,
   gnome-characters, Orca) render on the iGPU and hold `/dev/dri/renderD129`.
3. `drm_kms_helper.poll=Y` wakes `i915` about every 22 s to probe its 4 connectors,
   which connect to nothing.

**Fix:**

1. Copy [`99-hide-i915-from-seat.rules`](files/etc/udev/rules.d/99-hide-i915-from-seat.rules)
   to `/etc/udev/rules.d/` with mode 0644.
2. Copy [`files/home/.config/environment.d/90-gsk-renderer.conf`](../../files/home/.config/environment.d/90-gsk-renderer.conf)
   to `~/.config/environment.d/`. It sets `GSK_RENDERER=gl`.
3. Add the kernel argument:
   ```
   sudo grubby --update-kernel=ALL --args="drm_kms_helper.poll=0"
   ```
   `drm_kms_helper` is built into the kernel. A `modprobe.d` file has no effect.
4. Reboot.

**Result:**

| State | `i915` suspended |
|---|---|
| Before | about 0% |
| Steps 1 and 2 | about 40% |
| Steps 1, 2 and 3 | 99% (30 of 30 samples) |

**Notes:**

- All external ports connect to the Radeon. A DisplayPort hotplug test showed
  `card0-DP-1` connect and disconnect. All `card1` connectors stayed `disconnected`.
- With `poll=0`, a DisplayPort monitor still works. The Radeon uses HPD interrupts:
  `udevadm monitor` showed `ACTION=change HOTPLUG=1 CONNECTOR=62 DEVNAME=/dev/dri/card0`.
- HDMI is not tested. If HDMI hotplug fails, remove `drm_kms_helper.poll=0` first, then
  the udev rule.
- `runtime_status=suspended` does not mean that the device is off.
  `/sys/bus/pci/devices/0000:00:02.0/power_state` still shows `D0`. `i915` only gates
  internal power wells.
- GTK4 apps still log Vulkan probe warnings at start. These warnings are harmless,
  because no process holds `renderD129`.

**Revert:**

```
sudo rm /etc/udev/rules.d/99-hide-i915-from-seat.rules
rm ~/.config/environment.d/90-gsk-renderer.conf
sudo grubby --update-kernel=ALL --remove-args="drm_kms_helper.poll=0"
```

Then reboot.

## "Launch Using Discrete Graphics Card" is inverted

**Status:** Information only. No change. GNOME only.

The GNOME app launcher context menu item "Launch Using Discrete Graphics Card" starts
the app on the **Intel iGPU**, not on the Radeon. The item sets
`DRI_PRIME=pci-0000_00_02_0` and `VK_LOADER_DRIVERS_SELECT=*intel*`. The GL renderer
changes from `radeonsi, verde` to `Mesa Intel(R) Iris(R) Pro Graphics P5200`.

**Why:** `switcheroo-control` marks the Radeon `Default: true`, because it is
`boot_vga=1` and owns the panel. Thus "the other GPU" is the Intel iGPU. Neither GPU has
`Discrete: true`. GNOME Shell (`_updateGpuItem()`) selects the label only from
`PrefersNonDefaultGPU=true` in the desktop file. No desktop file on that system set it,
so every app showed "Discrete".

The item gave reverse PRIME: the render was on Intel, and the Radeon showed the frames.
It is slower for 3D and does not decrease power, because the Radeon drives the panel at
all times. The underlying fact still holds on Omarchy: `DRI_PRIME=pci-0000_00_02_0`
renders on the Intel iGPU, and the Radeon still scans out.
