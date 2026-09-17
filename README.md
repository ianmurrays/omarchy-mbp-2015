# omarchy-mbp-2015

Fixes and changes for [Omarchy](https://omarchy.org) on a MacBook Pro 15" mid-2015
(MacBookPro11,5), with macOS kept bootable on the same disk.

Each doc gives the symptom, the cause, the fix, what did not work, and how to revert.
`files/` contains the real config files, and the path in `files/` is the install path:
`files/etc/...` goes to `/etc/...`, `files/usr/...` to `/usr/...`, and `files/home/...`
to `~/...`. There is 1 exception: the 2 files in `files/home/.local/share/facetimehd/`
are a script and a patch that you run from this checkout. Do not install them.

This machine ran Fedora 44 with GNOME from 2026-09-07 to 2026-09-17. Those docs are
archived in [`docs/fedora/`](docs/fedora/README.md); see that file for why each one no
longer applies. The source is the Claude Code sessions on this machine from 2026-09-07
onwards.

## Machine

| Part | Value |
|---|---|
| Model | MacBookPro11,5 |
| OS | Omarchy 4.0.4, Hyprland 0.56.2 on Wayland, kernel 7.2.5-3-omarchy (2026-09-17) |
| CPU | Intel Core i7-4870HQ (Haswell, 4 cores, 8 threads) |
| Memory | 16 GiB |
| GPU with the panel | AMD Radeon R9 M370X (`1002:6821`), driver `radeon` |
| Other GPU | Intel Iris Pro P5200, no display output |
| Panel | 2880x1800 at scale 1.6, backlight `gmux_backlight` |
| Wi-Fi | Broadcom BCM43602 (`14e4:43ba`), driver `brcmfmac` |
| Camera | Broadcom FaceTime HD (`14e4:1570`), driver `facetimehd` (DKMS, out of tree) |
| SSD | `APPLE SSD SM0512G` (Samsung, PCIe AHCI) |
| Disk | `sda3` ESP (`OMARCHY_EFI`), `sda4` LUKS2 + btrfs. macOS 12.7.6 on `sda2` (APFS). |
| Bootloader | Limine, unified kernel images |
| Secure Boot | Off |
| Remote access | Tailscale node, `tailscaled` enabled. Tailscale SSH off, `sshd` installed and disabled. |

## Index

| Topic | Status | Doc |
|---|---|---|
| IOMMU blocks the Radeon, desktop does not render | **Applied, verified 2026-09-17** | [iommu-dma-faults.md](docs/iommu-dma-faults.md) |
| Radeon kernel arguments (display after resume, brightness keys) | Applied | [gpu-kernel-args.md](docs/gpu-kernel-args.md) |
| Kernel arguments via Limine drop-ins, not `grubby` | Applied | [gpu-kernel-args.md](docs/gpu-kernel-args.md#how-kernel-arguments-reach-the-boot-entry-on-omarchy) |
| The UKI carries a different cmdline | Known, not fixed | [gpu-kernel-args.md](docs/gpu-kernel-args.md#the-uki-carries-a-different-cmdline) |
| GPU mux switch: the runtime path | Tried on Fedora, failed. Do not retry. | [gpu-kernel-args.md](docs/gpu-kernel-args.md#the-runtime-switch-cannot-work) |
| GPU mux switch: the boot-time path (`gpu-switch` + `apple_set_os.efi`) | Researched 2026-09-18, not tried. Needs remote access first. | [gpu-kernel-args.md](docs/gpu-kernel-args.md#the-boot-time-switch) |
| Chromium and Electron glitch | Applied, user confirmed 2026-09-17 | [electron-glitch.md](docs/electron-glitch.md) |
| `--use-gl=desktop` is removed from Chromium 152 | Tested and rejected | [electron-glitch.md](docs/electron-glitch.md#--use-gldesktop-does-not-work-on-arch) |
| Install Omarchy and keep macOS | Done 2026-09-17 | [omarchy-install.md](docs/omarchy-install.md) |
| What Omarchy provides out of the box | Information only | [apps.md](docs/apps.md) |
| GUI password prompt from an agent session | Information only | [apps.md](docs/apps.md#a-gui-password-prompt-from-an-agent-session) |
| Claude Code status line (ccstatusline) | In use, 2026-09-18 | [apps.md](docs/apps.md#claude-code-status-line-ccstatusline) |
| GitHub CLI and SSH commit signing | **Broken: commits are unsigned** | [git-github.md](docs/git-github.md) |
| Wi-Fi dead after a long sleep | Not applied | [wifi-after-sleep.md](docs/wifi-after-sleep.md) |
| Intel iGPU runtime suspend | Nothing to apply, verified 2026-09-18 | [igpu-runtime-suspend.md](docs/igpu-runtime-suspend.md) |
| FaceTime HD camera | **Applied, verified 2026-09-18** | [facetime-camera.md](docs/facetime-camera.md) |
| The stable `facetimehd-dkms` AUR package does not build on kernel 7.2 | Tested and rejected | [facetime-camera.md](docs/facetime-camera.md#2-the-stable-aur-package-does-not-build-on-kernel-72) |
| Camera colour cast: sensor calibration `.dat` | Fixed by `facetimehd-data` | [facetime-camera.md](docs/facetime-camera.md#3-colour-sensor-calibration-files) |
| Camera brightness patch superseded upstream | Do not apply | [facetime-camera.md](docs/facetime-camera.md#4-brightness-and-exposure) |
| TLP instead of power-profiles-daemon | Not applied. Needs `tlp` and `tlp-pd` together | [power.md](docs/power.md) |
| 80% battery charge limit | Not possible on this hardware | [power.md](docs/power.md#battery-charge-limit-80) |
| DNS: the HaGeZi filtering resolvers | **Applied, verified 2026-09-18** | [dns.md](docs/dns.md) |
| `DNSOverTLS=yes` can break DNS via the per-link servers | Not tested, has a test | [dns.md](docs/dns.md#dnsovertlsyes-can-need-one-more-step) |
| `omarchy dns Custom` cannot set up DNS over TLS | Worked around | [dns.md](docs/dns.md#why-omarchy-dns-custom-is-not-enough-on-its-own) |
| No idle suspend | Already true on Omarchy, verified 2026-09-18 | [power.md](docs/power.md#no-idle-suspend) |
| The Fedora install | Archived | [docs/fedora/](docs/fedora/README.md) |

## Open items

These are open on 2026-09-18.

1. **Commits from this machine are unsigned.** There is no `~/.ssh/id_ed25519`, no
   `allowed_signers`, and no `commit.gpgsign`. `user.email` is a personal address here,
   not the GitHub noreply address. See [git-github.md](docs/git-github.md).
2. **The git credential helper points at a versioned mise path.** A mise upgrade of `gh`
   will break HTTPS authentication. See [git-github.md](docs/git-github.md).
3. **`/etc/kernel/cmdline` does not have the MacBook arguments.** Boot paths that skip
   Limine would come up without `radeon.si_support=1`, i.e. blind at the LUKS prompt. See
   [gpu-kernel-args.md](docs/gpu-kernel-args.md#the-uki-carries-a-different-cmdline).
4. **Remote access is half set up.** Tailscale is installed and this machine is a node,
   but Tailscale SSH is off (`RunSSH: false`) and `sshd` is disabled, so there is no shell
   from another machine yet. Everything in this repo that can break the display needs a
   way back in first.
5. **Stale `Ubuntu` and `Fedora` EFI boot entries** still point into the Apple ESP. Dead,
   harmless, removable with `efibootmgr -b <num> -B`.
6. **`iommu=pt` was never tried.** It would probably clear the DMA faults while keeping
   interrupt remapping, which `intel_iommu=off` also disables. See
   [iommu-dma-faults.md](docs/iommu-dma-faults.md).
7. **The Chromium flag is not tested against the flicker in a bundled-Electron app.**
   Slack and 1Password are installed and their desktop entries carry the flag, verified
   2026-09-18, but neither app was seen to flicker before it. `--use-angle=gl` is also
   untested against the flicker.
8. **The Wi-Fi sleep hook is not installed** and no long sleep has been tried.
9. **The camera default brightness is 128.** The ISP meters the full frame, so a backlit
   subject is dark. The udev rule that sets 155 is in the repo but not installed. See
   [facetime-camera.md](docs/facetime-camera.md#4-brightness-and-exposure).

## After a fresh Omarchy install

> **Warning:** Do step 1 first. Without `intel_iommu=off` the desktop renders blank, and
> without `radeon.si_support=1` the display fails after the first resume.

1. Kernel arguments, then reboot: [gpu-kernel-args.md](docs/gpu-kernel-args.md) and
   [iommu-dma-faults.md](docs/iommu-dma-faults.md).
   ```
   sudo tee /etc/limine-entry-tool.d/macbookpro11-5.conf < files/etc/limine-entry-tool.d/macbookpro11-5.conf
   sudo limine-update
   ```
2. Chromium and Electron flags: [electron-glitch.md](docs/electron-glitch.md).
3. Remote access, before anything else that can break the display.
4. Git and GitHub, including signing: [git-github.md](docs/git-github.md).
5. DNS, to put the machine on the HaGeZi filtering resolvers: [dns.md](docs/dns.md).
6. Camera, if you want it: [facetime-camera.md](docs/facetime-camera.md).
   ```
   yay -S facetimehd-dkms-git facetimehd-firmware facetimehd-data
   sudo modprobe facetimehd
   ```
7. Optional, none of it currently applied: [wifi-after-sleep.md](docs/wifi-after-sleep.md),
   [power.md](docs/power.md), [igpu-runtime-suspend.md](docs/igpu-runtime-suspend.md).

## After a kernel update

1. Check that the arguments survived. `/boot/limine.conf` is regenerated on every kernel
   and mkinitcpio update:
   ```
   grep -o -e radeon.si_support=1 -e intel_iommu=off /proc/cmdline
   ```
2. If either is missing, the drop-in was lost. Reinstall it and run `sudo limine-update`.
3. Check that DKMS rebuilt the camera driver: `dkms status`, then `ls /dev/video0`. A
   kernel API break needs a newer upstream `master`, so reinstall
   `facetimehd-dkms-git`. See
   [facetime-camera.md](docs/facetime-camera.md#7-after-a-kernel-update).

## Not in this repo

- Root and LUKS UUIDs.
- SSH keys and tokens.
- The Apple firmware and camera calibration `.dat` files. See
  [facetime-camera.md](docs/facetime-camera.md).

## License

MIT. See [LICENSE](LICENSE). The configuration files are here to be copied.
