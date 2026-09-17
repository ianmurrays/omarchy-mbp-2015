# Wi-Fi dead after a long sleep

**Status:** Not applied on Omarchy. `/usr/lib/systemd/system-sleep/brcmfmac-reload` does
not exist on this install, and no long sleep has been tried yet. The hook was written on
2026-09-13 and installed on the Fedora install; the Omarchy reinstall removed it.
Sources: session `da6cd159` (2026-09-13), 2026-09-17.

> **Caution:** The 2026-09-13 session gave the path `/etc/systemd/system-sleep/`. That
> path is wrong. systemd runs sleep hooks only from `/usr/lib/systemd/system-sleep/`
> (see `man systemd-suspend.service`). It does not read `/etc/systemd/system-sleep/`. A
> hook there never runs, and nothing reports an error.

**Symptom:** After a sleep of about 8 h, Wi-Fi stayed dead from 2026-09-12 17:30 until
a reboot at 2026-09-13 07:37. The laptop did many suspend and resume cycles before. A
turn off and turn on of Wi-Fi (rfkill) did not recover it.

**Hardware:** Broadcom BCM43602 (`04:00.0`, `14e4:43ba`), driver `brcmfmac`.

**Cause:** On resume, `brcmfmac` uses the "hot resume" path (`brcmf_pcie_pm_leave_D3`).
It reads a device register to find if the chip survived the sleep. After a long sleep
the chip can read as alive while its firmware is dead. The driver keeps the dead
firmware and does not load it again. Each command then times out with `-5` (EIO), and
then with `-12` (`Failed to reserve space in commonring`) when the message ring is
full. The log had 1,949 of these errors.

**Ruled out:** PCIe AER errors (none), PM failures (none), TLP (not involved, and TLP
cannot unload modules).

> **Read this first on Omarchy.** Omarchy ships `/etc/modprobe.d/brcmfmac.conf` with
> `options brcmfmac feature_disable=0x82000`, which turns off the firmware supplicant and
> authenticator for this chip. Fedora did not have that file. If the Wi-Fi behaves
> differently from the description above, look at that file before you install the hook.

**Manual recovery** (no reboot):

```
sudo modprobe -r brcmfmac_wcc brcmfmac brcmutil && sudo modprobe brcmfmac
```

**Fix:** A systemd sleep hook,
[`files/usr/lib/systemd/system-sleep/brcmfmac-reload`](../files/usr/lib/systemd/system-sleep/brcmfmac-reload).
Before sleep it unloads `brcmfmac_wcc`, `brcmfmac` and `brcmutil`. After resume it loads
`brcmfmac`. The driver then does a full firmware download on each resume.

1. Install the hook with mode 0755:
   ```
   sudo install -m 0755 -o root -g root files/usr/lib/systemd/system-sleep/brcmfmac-reload /usr/lib/systemd/system-sleep/brcmfmac-reload
   ```
2. Suspend and resume the laptop 1 time.

Arch has no SELinux, so there is no label to set. The Fedora version of this procedure
needed a third step, `sudo restorecon -v` on the hook, to give it the `bin_t` label.

**Verify:**

```
journalctl -b 0 -t systemd-sleep | grep brcmfmac-reload
```

The output shows `unloaded brcmfmac` and `reloaded brcmfmac`.

**Notes:**

- The hook has a cost: Wi-Fi reconnects after each resume, also after a short sleep.
- Other packages put hooks in the same directory. On 2026-09-18 it holds
  `keyboard-backlight` (from `omarchy-settings`) and `unmount-fuse` (from `systemd`). The
  `brcmfmac-reload` file belongs to no package, so `pacman -Qo` on it answers
  `error: No package owns ...`.

**Revert:** `sudo rm /usr/lib/systemd/system-sleep/brcmfmac-reload`
