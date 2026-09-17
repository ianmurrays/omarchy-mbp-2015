# GPU and kernel arguments

The internal panel of the MacBookPro11,5 connects to the AMD Radeon R9 M370X
(`01:00.0`, `1002:6821`, Southern Islands "Verde"). It does not connect to the Intel
Iris Pro P5200. `i915` logs `failed to retrieve link info, disabling eDP` at init. All
external ports (1 HDMI, 2 Thunderbolt/DP) also connect to the Radeon. Thus the Radeon
must have a working KMS driver, or the display fails.

## How kernel arguments reach the boot entry on Omarchy

Omarchy boots with Limine, not GRUB. There is no `grubby`. `limine-entry-tool` builds
the `cmdline:` line of `/boot/limine.conf` from `KERNEL_CMDLINE[...]` variables, read in
this order:

1. every `*.conf` in `/etc/limine-entry-tool.d/` (drop-ins, `+=` appends)
2. `/etc/default/limine` (overrides the drop-ins)

`/boot/limine.conf` is **generated**. Never edit it directly: the next kernel or
mkinitcpio update runs `limine-update` and overwrites your change, and on this machine
that means booting with no `radeon.si_support=1`, i.e. a black screen at a LUKS
passphrase prompt you cannot see.

The machine-specific arguments live in 1 drop-in,
[`files/etc/limine-entry-tool.d/macbookpro11-5.conf`](../files/etc/limine-entry-tool.d/macbookpro11-5.conf).
After any change to it:

```
sudo limine-update
grep 'cmdline:' /boot/limine.conf     # read it back before you reboot
```

## The arguments

`root=`, `cryptdevice=` and `resume=` are not listed: they change with each install and
Omarchy manages them in its own drop-ins.

| Argument | Origin | Why |
|---|---|---|
| `radeon.si_support=1` | Fedora, 2026-09-07 | Makes `radeon` bind the SI card. |
| `amdgpu.si_support=0` | Fedora, 2026-09-07 | Keeps `amdgpu` away from the SI card. |
| `modprobe.blacklist=amdgpu` | Before the sessions | `amdgpu` SI support is reported to leave this panel black. Keep it. |
| `libata.force=noncq` | Before the sessions | The `APPLE SSD SM0512G` gives `READ FPDMA QUEUED` errors without it (Red Hat bug 1084928). Keep it. |
| `drm_kms_helper.poll=0` | Fedora, 2026-09-14 | See [igpu-runtime-suspend.md](igpu-runtime-suspend.md). |
| `intel_iommu=off` | Omarchy, 2026-09-17 | See [iommu-dma-faults.md](iommu-dma-faults.md). Without it the desktop does not render. |

`i915.modeset=1` was in the Fedora arguments. Its origin was unknown and no fix in this
repo needs it. It was not carried over.

## radeon does not bind the panel

**Status:** Applied on Fedora 2026-09-07, carried to Omarchy 2026-09-17 at install time.
Source: session `8fbd21c4`.

**Symptom:** A black screen after resume from suspend. The brightness keys do nothing.
Idle power is 36.4 W.

**Cause:** `amdgpu` is blacklisted. `radeon.si_support` defaults to `-1`, and with that
value `radeon` does not take SI cards, because it expects `amdgpu` to take them. No
driver binds the Radeon, and the desktop falls back to the UEFI framebuffer
(`simpledrm`), which cannot set up the panel again after S3 and has no backlight.

**Fix:** the drop-in above, then `sudo limine-update` and reboot.

**Verify:**

```
grep -o 'radeon.si_support=1' /proc/cmdline
lspci -k -s 01:00.0 | grep 'in use'      # Kernel driver in use: radeon
ls /sys/class/backlight/                  # gmux_backlight
```

**Notes:**

- The backlight is `gmux_backlight` from `apple-gmux`. `radeon` correctly skips its own
  backlight (`Skipping radeon atom DIG backlight registration`).
- `radeon` has no atomic modesetting. Hyprland logs
  `failed to set DRM_CLIENT_CAP_ATOMIC, falling back to legacy` and
  `drmProps.supportsAddFb2Modifiers: false`. This is the cause of the Chromium glitch in
  [electron-glitch.md](electron-glitch.md).
- Do not load or unload the GPU driver while the session runs.

**Revert:** remove the 2 `si_support` arguments from the drop-in, `sudo limine-update`,
reboot. The display then fails after resume.

## The UKI carries a different cmdline

**Status:** Known, not changed. Examined 2026-09-17.

`ENABLE_UKI=yes` (from `/etc/limine-entry-tool.d/omarchy-uki.conf`), so the kernel ships
as a unified image in `/boot/EFI/Linux/`. A UKI embeds the cmdline from
`/etc/kernel/cmdline`, which on this machine holds **only** the base
`cryptdevice=`/`root=` arguments — none of the MacBook ones.

It works today because Limine passes the `cmdline:` line from `/boot/limine.conf` as EFI
LoadOptions, and systemd-stub prefers those over the embedded copy. The trap is the path
that skips Limine: `ENABLE_LIMINE_FALLBACK=yes`, and the firmware can be pointed at a UKI
directly. That boot would come up without `radeon.si_support=1`.

To close it off, mirror the arguments into `/etc/kernel/cmdline` as well and rebuild the
initramfs. Not done.

## GPU mux switch to the Intel iGPU

**Status:** The runtime switch failed on Fedora 2026-09-07. The boot-time switch is not
tried. Sources: session `8fbd21c4`, and the links below, read 2026-09-18.

**Goal:** Move the panel to the Intel iGPU. `i915` supports atomic KMS, which fixes the
Chromium glitch in [electron-glitch.md](electron-glitch.md) at the driver level, and can
lower idle power.

### The runtime switch cannot work

**What the test did:** stop the display manager, then
`echo MIGD > /sys/kernel/debug/vgaswitcheroo/switch`, then `modprobe -r i915` and
`modprobe i915`. The screen went black and the mux did not change.

**Why it failed:**

- `MIGD` and `MDIS` switch only the DDC/EDID lines. The full switch is `IGD` or `DIS`.
- `modprobe -r i915` fails, because `snd_hda_intel` holds `i915`.
- `vga_switcheroo` refuses a switch while a process holds a GPU device file.
- `i915` disables eDP at init, so it never registers the connector. A switcheroo reprobe
  cannot add the connector later. The mux must point to the iGPU before `i915` loads.

Do not try the runtime switch again.

### The boot-time switch

The mux selection for the next boot lives in 1 EFI variable,
`gpu-power-prefs-fa4ce28d-b62f-4c99-9cc3-6815686e30f9`. `gpu-switch` writes 8 bytes to
it: the 4-byte attribute word `07 00 00 00`, then `01 00 00 00` for the iGPU or
`00 00 00 00` for the dGPU. The tool does 2 more things: it mounts `efivarfs` if the
mount is absent, and it runs `chattr -i` on the variable first. `efivarfs` marks each
variable immutable, so a write or a delete fails without that step.

The variable alone is not enough on a MacBookPro11,5. The Apple firmware powers off the
Intel iGPU when the operating system is not macOS, and the result is a black screen. This
is `gpu-switch` issue #27, which is open. 2 users in that issue report a MacBookPro11,5
with a working iGPU after they added an EFI program that reports the OS as macOS.

There are 2 ways to make that call.

1. **rEFInd, `spoof_osx_version`.** rEFInd tells the firmware that the named macOS
   version starts, even when it starts another OS. rEFInd becomes the first stage and
   chainloads `\EFI\limine\limine_x64.efi`. No third-party binary. `limine-update` does
   not touch it. The rEFInd documentation warns that the keyboard or the mouse can stop
   work with this option on.
2. **`apple_set_os.efi`.** The program calls the Apple `set_os_vendor` protocol and then
   returns. It does not start the next boot loader. The
   `Redecorating/apple_set_os-loader` fork makes the call and then starts
   `\EFI\Boot\bootx64_original.efi`. That path is hardcoded in `bootx64_silent.c`, so
   this way needs a copy of `limine_x64.efi` at that path, and the copy goes stale at
   each `limine` package update.

Option 1 is the smaller change.

After a switch to the iGPU, expect a backlight problem. 1 user in issue #27 reports that
the brightness keys stopped work, because `radeon_bl0` registered next to
`gmux_backlight`. This machine already uses `gmux_backlight`.

### State on Omarchy, 2026-09-18

| Item | Value |
|---|---|
| `gpu-power-prefs` variable | Not set. `/sys/firmware/efi/efivars` holds only `gpu-policy` and `gfx-saved-config-restore-status`. |
| Boot entry | `Boot0002* Limine`, `HD(3,GPT,81881c00-...)/\EFI\limine\limine_x64.efi` |
| `refind` | In the Arch `extra` repository. Not installed. |
| `gpu-switch` | AUR package `gpu-switch`. Not installed. |
| `apple_set_os.efi` | Not in the AUR. A prebuilt binary is in the `v1` release. You can also build it with `gnu-efi`. |
| `vga_switcheroo` | Not checked on Omarchy, it needs `sudo`. On Fedora it read `0:DIS:+:Pwr`, `1:IGD: :Pwr`. |
| Remote access | None. See [Remote access](#remote-access) below. |

### Before you try this

The risk is a black screen at the LUKS passphrase prompt, on the only machine.

1. Enable `sshd`, and confirm that the network comes up before a login.
2. Confirm that you can type the LUKS passphrase blind and then reach the machine over
   the network.
3. Write the EFI variable only after step 2 passes.

The recovery order is:

1. Connect with `ssh`. Run `gpu-switch -d`, or run `chattr -i` on the variable and then
   delete it.
2. If the network fails, reset the NVRAM: hold Cmd+Opt+P+R at power-on.

### Sources

| Link | What it gives |
|---|---|
| [`0xbb/gpu-switch`](https://github.com/0xbb/gpu-switch) | The tool. The README lists MacBookPro11,5 as tested hardware, and warns that 11,3 and 11,5 need the EFI OS spoof. |
| [`gpu-switch` issue #27](https://github.com/0xbb/gpu-switch/issues/27) | The MacBookPro11,5 black screen, and the 2 reports of success with `apple_set_os`. |
| [`0xbb/apple_set_os.efi`](https://github.com/0xbb/apple_set_os.efi) | The EFI program and the prebuilt binary. |
| [kernel: vga-switcheroo](https://docs.kernel.org/gpu/vga-switcheroo.html) | The `IGD`, `DIS`, `MIGD` and `MDIS` commands, and the rule that no process can hold a GPU device file during a switch. |
| [dev.to: Arch Linux on an Intel MacBook Pro](https://dev.to/x1unix/archlinux-setup-guide-for-intel-macbook-pro-58b8#turn-off-discrete-amd-gpu) | A `modprobe.d` set, and a systemd unit that writes `OFF` to the switcheroo file. The page writes `IDG`, which is a spelling error for `IGD`. |
| [omarchy discussion #4694](https://github.com/omacom/omarchy/discussions/4694#discussioncomment-15878839) | Not about the mux. The linked comment turns off DMA remapping **for the iGPU** with `intel_iommu=igfx_off`, and its author later reports that Omarchy 3.4.2 needs no change. The thread is where the `--use-gl=desktop` recommendation came from. [electron-glitch.md](electron-glitch.md#--use-gldesktop-does-not-work-on-arch) rejects it on Arch. |

## Remote access

**Status:** Half set up on 2026-09-18. There is still no shell from another machine.

`tailscale` 1.102.3-1 is installed, `tailscaled` is enabled, and this machine is a node
on the tailnet, but Tailscale SSH is off (`tailscale debug prefs` shows
`"RunSSH": false`). `openssh` 10.5p1-1 is installed and `systemctl is-enabled sshd`
reports `disabled`. Turn on one of the 2 before you attempt anything that can leave the
machine without a display.
