# IOMMU blocks the Radeon (blank desktop)

**Status:** Applied and verified 2026-09-17, the first night on Omarchy. Source: session
`317384bf`.

**Symptom:** The GUI starts, but almost nothing is drawn.

- The wallpaper and the top bar never appear. They stay blank.
- Terminal text is invisible until you select it with the mouse. The selection makes it
  appear.
- Chromium and the Claude Code TUI flicker and show stale pixels.
- A `grim` screenshot shows the same damage, and 2 screenshots taken 1 s apart are
  byte-identical even while the screen animates.

The screen looks white, which is misleading. The pixels are not white. They are
`rgba(0,0,0,0)`, untouched memory that a PNG viewer composites onto a white page.

**Cause:** The Intel IOMMU (VT-d) rejects the DMA transfers of the discrete Radeon:

```
DMAR: [DMA Read  NO_PASID] Request device [0000:01:00.0] fault addr 0x68c00000 [fault reason 0x0c] non-zero reserved fields in PTE
DMAR: [DMA Write NO_PASID] Request device [0000:01:00.0] fault addr 0x68c01000 [fault reason 0x0c] non-zero reserved fields in PTE
dmar_fault: 13380 callbacks suppressed
```

`0000:01:00.0` is the Radeon R9 M370X, the GPU that drives the panel. The GPU cannot
reliably read or write its own buffers, so most of each frame is never composited.

The transfer fails, not the drawing. This is why the symptom depends on repainting:

| What | Repaints | Result |
|---|---|---|
| Wallpaper, bar (quickshell) | Once, then never | Blank forever |
| Terminal body | Only on damage | Invisible until selected |
| Claude Code input box, spinner | Continuously | Correct |

**Why this is new on Omarchy:** Fedora 44 booted with VT-d off, so no device was ever
remapped. Arch enables it. Compare:

```
ls -A /sys/class/iommu        # Fedora: empty.  Omarchy before the fix: dmar0 dmar1
```

The hardware did not change. The kernel default did.

**Fix:** Turn off DMA remapping with a kernel argument. Omarchy reads each file in
`/etc/limine-entry-tool.d/`, so this goes in the same drop-in as the other MacBook
arguments, [`macbookpro11-5.conf`](../files/etc/limine-entry-tool.d/macbookpro11-5.conf).
The tracked copy of that file already carries the line, so a fresh install needs only
step 1 of the [README](../README.md). Use the commands below only on a machine whose
drop-in does not have it yet:

```
sudo tee -a /etc/limine-entry-tool.d/macbookpro11-5.conf <<'EOF'
KERNEL_CMDLINE[default]+=" intel_iommu=off"
EOF
sudo limine-update
```

Then reboot. See [gpu-kernel-args.md](gpu-kernel-args.md) for how the drop-in reaches
the boot entry.

**Verify:**

```
grep -o intel_iommu=off /proc/cmdline                        # intel_iommu=off
ls -A /sys/class/iommu                                        # empty
journalctl -k -b 0 | grep -c 'DMA.*fault addr'                # 0
```

Measured before and after on this machine:

| | Before | After |
|---|---|---|
| Opaque pixels in a `grim` capture | 8.98% | 100% |
| `DMA ... fault addr` lines in 1 boot | tens of thousands | 0 |
| DMAR units / IOMMU groups | 2 / 13+ | 0 / 0 |

To measure the coverage yourself:

```
grim /tmp/shot.png && magick /tmp/shot.png -alpha extract -format '%[fx:mean*100]' info:
```

**`intel_iommu=igfx_off` is the wrong flag.** A user with the same model reports it in
[omacom/omarchy discussion 4694](https://github.com/omacom/omarchy/discussions/4694), and
an earlier version of this repo recorded it as "not applicable". Both miss the point:
`igfx_off` exempts the **integrated** GPU at `00:02.0` from remapping. The device that
faults here is the **discrete** Radeon at `01:00.0`. The flag cannot help, whether or not
VT-d is on.

**Alternative, not tried:** `iommu=pt` gives devices an identity-mapped DMA domain
instead of turning VT-d off. It should clear the same faults and it keeps interrupt
remapping, which `intel_iommu=off` also disables. `intel_iommu=off` was chosen because
the Apple DMAR table on this machine is already visibly quirky (`DMAR-IR: x2apic is
disabled because BIOS sets x2apic opt out bit`) and 1 reboot had to be enough. If you
want interrupt remapping back, swap the argument and re-run the verification above.

**What `intel_iommu=off` costs:** no DMA protection against a malicious Thunderbolt or
PCIe device, and no interrupt remapping. There is no virtualisation use on this machine.
`libata.force=noncq` and the other arguments are unaffected.

**Notes:**

- The faults are intermittent, not total. That is why the screen flickers instead of
  freezing.
- `grim` is unreliable while this bug is active. Screencopy is itself a GPU DMA transfer,
  so the diagnostic tool is corrupted by the fault it is diagnosing. Two captures came
  back identical while the screen was animating.
- "Text invisible until selected" is a far better search term for this than "screen is
  white".
- This is not the same bug as [electron-glitch.md](electron-glitch.md). That one was
  diagnosed on Fedora with VT-d off and survives this fix.

**Revert:** remove the `intel_iommu=off` line from the drop-in, run `sudo limine-update`,
reboot. The desktop goes blank again.
