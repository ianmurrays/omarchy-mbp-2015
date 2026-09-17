# Intel iGPU runtime suspend

**Status:** Nothing to apply on Omarchy. Verified 2026-09-18.

The Intel Iris Pro P5200 (`0000:00:02.0`, `card1`) drives no display. On Fedora it never
entered runtime suspend, and 3 separate holders had to be removed. On Omarchy 2 of those
3 holders do not exist, and the third is already in the kernel arguments.

| Holder on Fedora | State on Omarchy |
|---|---|
| Mutter and `gnome-shell` open `/dev/dri/card1`, because udev tags the iGPU `master-of-seat` | No Mutter. aquamarine opens only `/dev/dri/card0`, the Radeon. The udev tag is still there and does no harm. |
| GTK4 renders on the iGPU through the Intel HASVK Vulkan driver, because RADV refuses the `radeon` card | Not seen. `GSK_RENDERER` is unset and `i915` stays suspended. |
| `drm_kms_helper.poll=Y` probes 4 phantom connectors about every 22 s | `drm_kms_helper.poll=0` is in [`files/etc/limine-entry-tool.d/macbookpro11-5.conf`](../files/etc/limine-entry-tool.d/macbookpro11-5.conf) and in `/proc/cmdline`. |

**Verify:**

```
cat /sys/bus/pci/devices/0000:00:02.0/power/runtime_status    # suspended
grep -o drm_kms_helper.poll=0 /proc/cmdline
```

On 2026-09-18 the first command reads `suspended` although
`udevadm info /sys/class/drm/card1` still shows `TAGS=:master-of-seat:`, which is the
evidence that the udev rule is not necessary under Hyprland.

> **Caution:** Do not read `/sys/class/drm/card*-*/status` to find if polling is off. A
> read of that file starts a connector probe. Use `udevadm monitor` or look at the
> screen.

**If `i915` goes back to `active`:**

1. Find the holder: `sudo fuser -v /dev/dri/card1 /dev/dri/renderD129`.
2. A GTK4 app on the iGPU: copy
   [`files/home/.config/environment.d/90-gsk-renderer.conf`](../files/home/.config/environment.d/90-gsk-renderer.conf)
   to `~/.config/environment.d/` and log in again. It sets `GSK_RENDERER=gl`. The file is
   tracked but not installed.
3. A compositor that opens `card1`: the Fedora udev rule that moves the iGPU off seat0 is
   archived at
   [`docs/fedora/files/etc/udev/rules.d/99-hide-i915-from-seat.rules`](fedora/files/etc/udev/rules.d/99-hide-i915-from-seat.rules).
4. Kernel arguments go in the Limine drop-in, never `grubby`. See
   [gpu-kernel-args.md](gpu-kernel-args.md).

**Notes:**

- All external ports connect to the Radeon. All `card1` connectors stay `disconnected`.
- With `poll=0`, a DisplayPort monitor still works. The Radeon uses HPD interrupts.
  HDMI is not tested.
- `runtime_status=suspended` does not mean that the device is off.
  `/sys/bus/pci/devices/0000:00:02.0/power_state` still shows `D0`. `i915` only gates
  internal power wells.
- The power decrease is not measured. A controlled idle comparison on battery against
  the 24.86 W baseline in [power.md](power.md) is not done.
- The Fedora diagnosis, the measured before-and-after table and the GNOME "Launch Using
  Discrete Graphics Card" note are in
  [fedora/igpu-runtime-suspend.md](fedora/igpu-runtime-suspend.md).
