# Fedora boot splash

> **OBSOLETE — archived.** Fedora Plymouth configured through `grubby` and
> `/etc/default/grub`, neither of which exists on Omarchy. Omarchy sets `quiet splash` in
> `/etc/limine-entry-tool.d/omarchy-defaults.conf` and ships its own theme. See
> [../gpu-kernel-args.md](../gpu-kernel-args.md) for how kernel arguments work now.

**Status:** Applied 2026-09-17. Not yet verified after a reboot. Sources: session
`f8a172cf` (2026-09-14, diagnosis), 2026-09-17 (applied).

**Symptom:** Boot shows kernel text, not the Fedora Plymouth splash.

**Cause:** `rhgb quiet` is not in the kernel arguments. Plymouth is installed and runs,
with the `bgrt` theme. Until 2026-09-17, `rhgb` and `quiet` were absent from
`/proc/cmdline`, `/etc/kernel/cmdline` and `/etc/default/grub`.

On 2026-09-17, steps 1 and 2 put `rhgb quiet` at the end of the arguments in all 4
boot entries (7.2.5, 7.2.4, 7.1.12, rescue), `/etc/kernel/cmdline` and
`/etc/default/grub`. The backups are `/etc/kernel/cmdline.bak.2026-09-17-1521` and
`/etc/default/grub.bak.2026-09-17-1521`. The optional steps are not applied.

**Fix:**

1. Add the arguments to all boot entries:
   ```
   sudo grubby --update-kernel=ALL --args="rhgb quiet"
   ```
2. Examine `/etc/kernel/cmdline` and `GRUB_CMDLINE_LINUX` in `/etc/default/grub`. If
   `rhgb quiet` is not in them, add it:
   ```
   sudo sed -i 's/$/ rhgb quiet/' /etc/kernel/cmdline
   sudo sed -i 's/^GRUB_CMDLINE_LINUX="\(.*\)"$/GRUB_CMDLINE_LINUX="\1 rhgb quiet"/' /etc/default/grub
   ```
   See the caution about `/etc/kernel/cmdline` in [gpu-kernel-args.md](../gpu-kernel-args.md).
3. Reboot.

**Optional:**

- If the LUKS passphrase prompt shows late or as text, put `radeon` in the initramfs:
  ```
  echo 'force_drivers+=" radeon "' | sudo tee /etc/dracut.conf.d/radeon.conf
  sudo dracut -f --regenerate-all
  ```
- `GRUB_TIMEOUT` is 10. A value of 1 or 2 makes boot faster.

**Verify:** `grep -o 'rhgb quiet' /proc/cmdline` after the reboot.

**Revert:** `sudo grubby --update-kernel=ALL --remove-args="rhgb quiet"`, and remove the
words from the 2 files.

**Correction:** That session said that `drm_kms_helper.poll=0` was not active. That was
wrong. The argument was not in `/proc/cmdline` only because no reboot came after the
11:26 grubby run. The live parameter was already `N`.
