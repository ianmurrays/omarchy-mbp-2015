# Wi-Fi dead after a long sleep

**Status:** **Applied and verified on Omarchy on 2026-09-21.** The hook is
`/usr/lib/systemd/system-sleep/brcmfmac-reload`, mode 0755, owner `root:root`. It ran
through 2 suspend and resume cycles, and Wi-Fi came back in 3 s each time. The hook was
written on
2026-09-13 and installed on the Fedora install; the Omarchy reinstall removed it. The
failure happened again on Omarchy on 2026-09-19, on the first suspend and resume cycle of
this install. Sources: session `da6cd159` (2026-09-13), 2026-09-17, session `bc839296`
(2026-09-19 and 2026-09-21).

> **Caution:** The 2026-09-13 session gave the path `/etc/systemd/system-sleep/`. That
> path is wrong. systemd runs sleep hooks only from `/usr/lib/systemd/system-sleep/`
> (see `man systemd-suspend.service`). It does not read `/etc/systemd/system-sleep/`. A
> hook there never runs, and nothing reports an error.

**Symptom:** Wi-Fi is dead after a resume. When it failed, a turn off and turn on of
Wi-Fi (rfkill) did not recover it, and only a reboot recovered it.

The failure is intermittent. These are the 3 measured sleeps:

| Suspend at | Operating system | Sleep length | Resume cycles since boot | Result |
|---|---|---|---|---|
| 2026-09-12 | Fedora | about 8 h | many | Wi-Fi dead. Reboot at 2026-09-13 07:37 |
| 2026-09-19 15:13 | Omarchy | 2 h 24 min | 0 | Wi-Fi dead. Reboot at 17:40 |
| 2026-09-19 19:58 | Omarchy | 37 h | 0 | Wi-Fi came back. Connected 29 s after the resume |

> **Do not read the page title as a threshold.** The name says "a long sleep" because
> that was the first description. The measurements refute it: the shortest sleep failed
> and the longest sleep did not. The third sleep ran without the hook, and the boot has
> 0 `brcmf` errors. The trigger is not known.

**Hardware:** Broadcom BCM43602 (`04:00.0`, `14e4:43ba`), driver `brcmfmac`.

**Cause:** On resume, `brcmfmac` uses the "hot resume" path (`brcmf_pcie_pm_leave_D3`).
It reads a device register to find if the chip survived the sleep. The chip can read as
alive while its firmware is dead. The driver keeps the dead firmware and does not load it
again. Each command then times out with `-5` (EIO), and then with `-12` (`Failed to
reserve space in commonring`) when the message ring is full. The 2026-09-12 log had 1,949
of these errors. The 2026-09-19 log had 63 `brcmf_msgbuf_query_dcmd` timeouts and 35
`Failed to reserve space in commonring` errors in the 2 min 11 s between the resume and
the reboot.

**Evidence from the 2026-09-19 log:**

- The first error came 2 s after `PM: suspend exit`.
- `brcmf_fw_alloc_request` appears 1 time in the boot, at the boot itself. The driver did
  not download the firmware again on resume. This is the hot resume path.
- `facetimehd` is on the same PCIe complex. It resumed and loaded its firmware again in
  the same second. The bus resume is good, and only the BCM43602 failed.
- NetworkManager never brought the interface up. It logged `Couldn't initialize
  supplicant interface: Timeout was reached` 6 times, and it failed to set the MAC
  address with `NME_UNSPEC`.

**Ruled out:** PCIe AER errors (none in either log), PM failures (none), TLP (not
involved, and TLP cannot unload modules).

> **Read this first on Omarchy.** Omarchy ships `/etc/modprobe.d/brcmfmac.conf` with
> `options brcmfmac feature_disable=0x82000`, which turns off the firmware supplicant and
> authenticator for this chip. Fedora did not have that file. It is not a cause of this
> failure: the 2026-09-19 log shows the same errors as the Fedora log.

**Manual recovery** (no reboot):

```
sudo modprobe -r brcmfmac_wcc brcmfmac brcmutil && sudo modprobe brcmfmac
```

This command is not tested against a dead chip on Omarchy. On 2026-09-19 the reboot came
first. All 3 modules are loaded on this install, so the command runs. Try it before you
reboot the next time.

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

The output of 1 cycle is 3 lines:

```
brcmfmac-reload: unloaded brcmfmac_wcc
brcmfmac-reload: unloaded brcmutil
brcmfmac-reload: reloaded brcmfmac
```

There is no `unloaded brcmfmac` line, and that is correct. `modprobe -r brcmfmac_wcc`
also removes `brcmfmac`, because `brcmfmac` is then unused. The hook finds no
`/sys/module/brcmfmac` and goes to the next module. The `unloaded brcmutil` line is the
proof: `brcmfmac` holds `brcmutil`, so `brcmutil` can only go after `brcmfmac` goes.

**Result of the 2 cycles on 2026-09-21** (09:12:38 to 09:12:59, and 09:13:12 to 09:21:30):

- `brcmf_fw_alloc_request: using brcm/brcmfmac43602-pcie` appears at each resume. The
  driver downloads the firmware again, which is the purpose of the hook. Compare this
  with the 2026-09-19 boot, where the line appears 1 time only, at the boot.
- Wi-Fi reconnected 3 s after each resume.
- The `-5` and `-12` errors did not come back.

**Notes:**

- The hook has a cost: Wi-Fi reconnects after each resume, also after a short sleep. The
  measured cost is 3 s.
- The unload writes 1 kernel message, `brcmf_msgbuf_delete_flowring: timed out waiting
  for txstatus`. It came 1 time, in the first of the 2 cycles, and it did no harm.
- The 2 Omarchy rows in the table are the same on every axis but the sleep length and the
  result. Each one was the first resume of its boot.
- Other packages put hooks in the same directory. On 2026-09-18 it holds
  `keyboard-backlight` (from `omarchy-settings`) and `unmount-fuse` (from `systemd`). The
  `brcmfmac-reload` file belongs to no package, so `pacman -Qo` on it answers
  `error: No package owns ...`.

**Revert:** `sudo rm /usr/lib/systemd/system-sleep/brcmfmac-reload`
