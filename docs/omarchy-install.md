# Installing Omarchy alongside macOS

**Status:** Done 2026-09-17. Omarchy 4.0.4 runs, macOS 12.7.6 is still bootable. The
plan came from session `0e48bf40`; the outcome below was read off the machine in session
`317384bf` after the install. The install itself was run by the user, so the steps are
the plan as written, annotated with what the result shows.

**Goal:** Replace Fedora with [Omarchy](https://omarchy.org) 4, and keep macOS on
`/dev/sda2` bootable.

The Omarchy manual says Omarchy must be the only OS and that the install wipes the disk
(`manual/44-mac-support.md`). The installer code does not agree: it has a second mode
that writes only into unallocated space. That mode is what this used.

## The disk before

| Device | Size | Label | Content |
|---|---|---|---|
| `/dev/sda1` | 200 MiB | `EFI System Partition` | Apple ESP, FAT32 |
| `/dev/sda2` | 279.1 GiB | `Customer` | APFS, macOS 12.7.6 |
| `/dev/sda3` | 2 GiB | `fedoraboot` | ext4, Fedora `/boot` |
| `/dev/sda4` | 184.7 GiB | `fedoraroot` | LUKS2, Fedora root |

`sda3` and `sda4` were adjacent and ended at the disk end, so deleting both gave 1 free
region of 186.7 GiB. The installer needs 32 GiB.

## The disk after

```
sda1   200M  vfat         EFI                 <- Apple ESP, untouched
sda2 279.1G  apfs                             <- macOS 12.7.6, untouched
sda3     2G  vfat         OMARCHY_EFI         <- new ESP, /boot
sda4 184.7G  crypto_LUKS                      <- LUKS2
  omarchy_root 184.6G btrfs OMARCHY           <- subvolumes @ @home @log @pkg
```

The installer took the freed numbers, so the new ESP became `sda3` and the new root
`sda4`, as predicted.

## What the installer does in free-space mode

Source: `configs/airootfs/root/configurator` in
[omacom/omarchy-iso](https://github.com/omacom/omarchy-iso).

- `install_mode_form()` offers "Free space install (alongside existing data)" on any UEFI
  machine with unallocated space. It is not Windows-specific; the BitLocker and Windows
  ESP tests only print a message.
- `run_partition_decide()` always makes a new 2 GiB ESP and never adopts an existing one.
  The code gives 3 reasons: an ESP of 100–260 MiB is too small for unified kernel images,
  a shared ESP prevents encryption, and a separate ESP keeps the 2 systems independent.
  The 200 MiB Apple ESP was therefore left alone.
- `run_partition_execute()` makes `OMARCHY_EFI` and `OMARCHY_ROOT`, clears old signatures
  with `wipefs -af`, makes LUKS2, btrfs, and the subvolumes `@`, `@home`, `@log`, `@pkg`,
  mounted `noatime,compress=zstd`.
- The mode registers an EFI boot entry. The firmware obeys it: `efibootmgr` now shows
  `BootCurrent: 0002`, `Boot0002* Limine`.

## Procedure

> **Warning:** Step 3 deletes the Fedora root. It cannot be undone. Do step 1 first.

1. Push this repo, and copy to another machine or a USB device:
   - `/usr/lib/firmware/facetimehd/` (firmware and the 11 calibration files)
   - `/usr/src/facetimehd-0.7.2` (the patched driver source)
   - `~/.ssh/id_ed25519` and `~/.ssh/id_ed25519.pub`
2. Write the Omarchy ISO to a USB device. Start the Mac holding Option, select the USB
   device. Apple Secure Boot is already off on this machine.

   > **Caution:** `linux-omarchy` 7.2.5 gives the SI card to `amdgpu`, and a user with
   > the same model reports `amdgpu` leaves this panel black. The ISO boots with GRUB on
   > UEFI. If the panel stays black, press `e` at the GRUB menu and add
   > `radeon.si_support=1 amdgpu.si_support=0 modprobe.blacklist=amdgpu`.

3. Select `/dev/sda`, then "Open partition tool". In `cfdisk`, delete `/dev/sda3`
   (`fedoraboot`) and `/dev/sda4` (`fedoraroot`). Keep `sda1` and `sda2`. Write, quit.
4. Optional: leave the installer and run `/root/configurator dry`. It walks the same
   screens and prints the partitions it would make, without writing.
5. Select "Free space install (alongside existing data)". Keep the encrypted default.
6. Complete the installer screens.

## After the install

> **Warning:** Do step 1 before the first suspend, and before expecting a usable desktop.

1. Kernel arguments. Both the display fix and the IOMMU fix are required:
   ```
   sudo tee /etc/limine-entry-tool.d/macbookpro11-5.conf < files/etc/limine-entry-tool.d/macbookpro11-5.conf
   sudo limine-update
   ```
   Reboot, then verify with
   `grep -o -e radeon.si_support=1 -e intel_iommu=off /proc/cmdline`.
   See [gpu-kernel-args.md](gpu-kernel-args.md) and
   [iommu-dma-faults.md](iommu-dma-faults.md).

   On the first boot without `intel_iommu=off`, the desktop came up blank. That is the
   IOMMU bug, not a failed install.
2. Chromium flag: [electron-glitch.md](electron-glitch.md).
3. Everything else in the index is optional and none of it is installed yet. See the
   status column in the [README](../README.md).

## What Omarchy already provides

Do not port these from the Fedora docs:

| Fedora fix | Omarchy equivalent |
|---|---|
| Boot splash | `quiet splash` in `/etc/limine-entry-tool.d/omarchy-defaults.conf`, plus a Plymouth theme |
| No idle suspend | the idle toggle in the Omarchy menu, `~/.config/omarchy/shell.json` |
| Node via mise | `mise-bin` |
| Docker | `docker` |
| Menus, keys, agent hotkey | the Omarchy shell and its keys |
| Crash capture | `omarchy-crash-watch` and the `diagnose-crash` skill |
| brcmfmac tuning | `/etc/modprobe.d/brcmfmac.conf`, `options brcmfmac feature_disable=0x82000` |

## Loose ends

- **Stale EFI boot entries.** `sda1` still holds `EFI/fedora` and `EFI/ubuntu`, and the
  firmware still lists `Boot0000* Ubuntu` and `Boot0001* Fedora`. They are dead but
  harmless. Remove with `sudo efibootmgr -b 0000 -B` and `-b 0001 -B`.
- **The Apple firmware picker with 2 ESPs** was the main risk in the plan. It worked:
  Limine is `BootCurrent`, and both `Mac OS X` entries (`Boot0080`, `Boot0081`) survive.
- **Free-space mode was only tested upstream against a Windows dual boot.** It worked
  against macOS unchanged. No step in the code depends on Windows.
- **TLP is a decision, not a default.** Arch `tlp` has no `tlp-pd`, and the Omarchy menu
  wants `power-profiles-daemon`, which is installed. See [power.md](power.md).

**Revert:** macOS is untouched, so a revert is a new install into the same free space.
The `.dat` files for the camera stay available because macOS stays on the disk.
