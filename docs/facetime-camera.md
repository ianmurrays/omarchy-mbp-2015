# FaceTime HD camera

**Status:** Applied 2026-09-18 on Omarchy. `/dev/video0` is present and captures.
Source: this session. The Fedora procedure is in section 6.

**Hardware:** Broadcom 720p FaceTime HD camera, PCI `14e4:1570` at `05:00.0`. The
mainline kernel has no driver for it. Secure Boot is off, so module signatures are not
necessary.

State on 2026-09-18:

| Item | Value |
|---|---|
| Kernel | `7.2.5-3-omarchy` |
| Driver | `facetimehd-dkms-git 0.7.2.r10.gc5c7fac-1` (upstream commit `c5c7fac`) |
| Firmware | `facetimehd-firmware 1:1.43_5-2`, `firmware.bin`, 1425412 bytes |
| Calibration | `facetimehd-data 5.1.5769-2`, 4 `.dat` files |
| Device | `/dev/video0`, card type `Apple Facetime HD` |
| Format | 1280x720, `YUYV` or `YVYU`, 30 fps |
| Sensor set file | `1871_01XX.dat` |

## 1. Install

> **Caution:** Do not install `facetimehd-dkms`. That package builds tag `0.7.0.2`,
> which does not compile on kernel 7.2. Section 2 gives the error.

1. Install the driver, the firmware, and the calibration data:
   ```
   yay -S facetimehd-dkms-git facetimehd-firmware facetimehd-data
   ```
2. Load the module:
   ```
   sudo modprobe facetimehd
   ```

`dkms` comes in as a dependency. `linux-omarchy-headers` must match the running kernel.

**Verify:**

```
dkms status
ls -l /dev/video0
v4l2-ctl -d /dev/video0 --info
journalctl -k -b | grep -c '_01XX.dat failed'
```

`dkms status` shows `facetimehd/0.7.2.r10.gc5c7fac, 7.2.5-3-omarchy, x86_64: installed`.
The last command must give `0`. A count above 0 means the calibration file is absent.
Section 3 explains the effect.

**What each package downloads:**

- `facetimehd-firmware` reads a byte range of `OSXUpd10.11.5.dmg` from the Apple CDN.
  The download is 2.69 MB, not the full 723 MB image. The PKGBUILD compares 2 SHA-256
  values, and both matched on 2026-09-18.
- `facetimehd-data` reads `bootcamp5.1.5769.zip` from the Apple CDN. That download is
  517.2 MB, because the PKGBUILD must unpack `AppleCamera64.exe`.
- `facetimehd-dkms-git` clones upstream `master`. The version number in the AUR is
  stale. The package builds the commit that is current on the build date.

## 2. The stable AUR package does not build on kernel 7.2

**Symptom:** `yay -S facetimehd-dkms` fails in the DKMS build step.

```
fthd_v4l2.c:399:9: error: implicit declaration of function 'strncpy'
```

**Cause:** The AUR package `facetimehd-dkms` builds upstream tag `0.7.0.2`. That tag is
from 2026-06-15. The upstream fix for kernel 7.2 is merge commit `54fb8f2` from
2026-08-25, which is 2 months later. The tag does not contain the fix.

**Fix:** Use `facetimehd-dkms-git`, which builds `master`.

**Verified 2026-09-18:** A manual build of tag `0.7.0.2` against
`/lib/modules/7.2.5-3-omarchy/build` failed with the error above. A manual build of
`master` succeeded and gave `vermagic: 7.2.5-3-omarchy`.

## 3. Colour: sensor calibration files

**Symptom:** The driver loads and captures, but each frame has a strong brown or orange
colour, also in daylight.

**Cause:** `facetimehd/1871_01XX.dat` is absent. Without it, `fthd_isp.c` does not do the
sensor calibration. The code comment says "The set file is allowed to be missing but we
don't get calibration", and the function returns 0. The only sign is this line:

```
Direct firmware load for facetimehd/1871_01XX.dat failed with error -2
```

The first Fedora diagnosis called that line harmless. That was wrong.

**Fix on Omarchy:** `facetimehd-data` supplies the file. The macOS extraction procedure
in section 6 is not necessary for this machine.

> **Caution:** The set file loads one time, when the ISP starts. Load the module again
> after you install the `.dat` files. A reboot also works.

```
sudo modprobe -r facetimehd && sudo modprobe facetimehd
```

Close each application that uses the camera first. If not, `modprobe -r` fails.

**Which sensor:** `fthd_isp_cmd_set_loadfile()` selects the file from `sensor_id1` and
`sensor_id0`. This machine has `sensor_id1 = 0x9770` and a `sensor_id0` that is not 4,
and the board name is not a MacBookAir, so the driver asks for `1871_01XX.dat`. The
driver does not log the identifiers at the default log level. Read the requested file
name from the load failure instead.

**Coverage:** The driver names 9 files: 8221, 1222, 9112, 1771, 1874, 1871, 1674, 1675,
and 1671. `facetimehd-data` supplies 4: 9112, 1771, 1871, and 1874. The 5 files 8221,
1222, 1674, 1675, and 1671 are not in the package. This machine needs 1871, which the
package supplies.

**The 2 extraction routes give the same bytes.** On 2026-09-18 the 4 files from
`facetimehd-data` matched the SHA-256 table in
[`find_setfiles.py`](../files/home/.local/share/facetimehd/find_setfiles.py) exactly:

| File | Size | SHA-256 match |
|---|---|---|
| `1771_01XX.dat` | 19040 | yes |
| `1871_01XX.dat` | 19040 | yes |
| `1874_01XX.dat` | 19040 | yes |
| `9112_01XX.dat` | 33060 | yes |

`facetimehd-data` reads the blobs from `AppleCamera.sys`, a Windows driver in the Boot
Camp archive. `find_setfiles.py` reads them from `AppleCameraAssistant`, a macOS binary.
The blobs are identical. The APFS mount is therefore only necessary for a sensor that
needs one of the other 5 files.

## 4. Brightness and exposure

Upstream fixed the control bug. The local patch is no longer necessary.

**The old symptom:** A subject with a bright background is dark. `v4l2-ctl --set-ctrl`
has no effect, but `--get-ctrl` shows the new value.

**The old cause:** `fthd_start_channel()` called `brightness_set(0x80)` and
`contrast_set(0x80)` on each stream start, and overwrote each V4L2 control value.

**Now:** Upstream commit `78e72b4` ("v4l2: apply the current control values when the
channel starts") is an ancestor of the installed commit `c5c7fac`. Do not apply
[`persist-v4l2-controls.patch`](../files/home/.local/share/facetimehd/persist-v4l2-controls.patch).
Keep that file for the record only.

The suspend fix `5aa0cef` is also in `c5c7fac`.

**Optional default brightness.** The default value is 128. The ISP measures exposure on
the full frame, so a backlit subject is dark at 128. To set 155 on each device add:

1. Copy the rule:
   ```
   sudo install -m 0644 files/etc/udev/rules.d/72-facetimehd-brightness.rules /etc/udev/rules.d/
   ```
2. Load the rules and the driver again:
   ```
   sudo udevadm control --reload
   sudo modprobe -r facetimehd && sudo modprobe facetimehd
   ```

**Status of the rule on Omarchy, 2026-09-18: not installed.** `/dev/video0` reports
`brightness ... value=128`.

**Notes from the Fedora work, still true:**

- `brightness` changes the mean luma almost 1:1. It is the only useful exposure control.
  There is no AE bias control.
- AE metering modes 0 to 7 do not change centre luma relative to the full frame. Mode 1
  overexposes. Modes 4 to 7 are the same as mode 3.
- `CISP_CMD_CH_AE_BIAS_EXPOSURE_SET` (0x204) is declared in the driver but not
  implemented.

## 5. View the camera

Omarchy installs `mpv`, `ffmpeg`, `v4l-utils`, and `obs-studio`. No new package is
necessary.

| Command | Use |
|---|---|
| `mpv av://v4l2:/dev/video0` | Quickest view |
| `ffplay /dev/video0` | The ffmpeg viewer |
| `qv4l2` | Live control sliders. Use this to judge colour and brightness. |
| OBS Studio | Add a "Video Capture Device (V4L2)" source |

A mirrored view with low delay:

```
mpv av://v4l2:/dev/video0 --profile=low-latency --untimed --vf=hflip
```

`mpv` prints `ioctl(VIDIOC_QBUF): Inappropriate ioctl for device` on exit. The message
is a teardown effect and does not show a capture problem.

`snapshot` (GNOME Camera) is in `extra` and gives a shutter button. Cheese is no longer
in the Arch repositories.

**Permissions:** The user is not in the `video` group. systemd-logind gives access with
a seat ACL (`user:<you>:rw-` on `/dev/video0`). No group change is necessary.

## 6. Extract the other calibration files from macOS

Use this only for a sensor that needs 8221, 1222, 1674, 1675, or 1671. macOS 12.7.6 is
on `/dev/sda2` (APFS).

1. Install the APFS driver from the AUR. The package is `apfs-fuse-git`; it provides
   `apfs-fuse`, and there is no package under that plain name:
   ```
   yay -S apfs-fuse-git
   ```
2. Mount the macOS system volume read-only:
   ```
   sudo mkdir -p /run/apfs-ro
   sudo apfs-fuse -o vol=0,ro /dev/sda2 /run/apfs-ro
   ```
   The volume root is under `root/` in the mount point.
3. Copy the binary:
   ```
   cp /run/apfs-ro/root/System/Library/Frameworks/CoreMediaIO.framework/Versions/A/Resources/AppleCamera.plugin/Contents/Resources/AppleCameraAssistant .
   ```
4. Unmount:
   ```
   sudo umount /run/apfs-ro && sudo rmdir /run/apfs-ro
   ```
5. Extract the set files:
   ```
   python3 files/home/.local/share/facetimehd/find_setfiles.py AppleCameraAssistant setfiles
   ```
   The script searches the binary for each known size and SHA-256. It writes a file only
   on a hash match, so a wrong file is not possible. Its table has 11 entries, which is 2
   more than the driver names: 1571 and 1575.
6. Install the files and load the driver again:
   ```
   sudo install -m 0644 setfiles/*.dat /usr/lib/firmware/facetimehd/
   sudo modprobe -r facetimehd && sudo modprobe facetimehd
   ```

**Tried on Fedora, did not work:**

- The upstream path `/Library/CoreMediaIO/Plug-Ins/DAL/AppleCamera.plugin` does not exist
  on macOS 12.
- Upstream `extract-firmware.sh -s` refuses the Monterey binary
  (`Mismatching AppleCameraAssistant hash`). Its `-i` option does not skip that check.
- APFS volume 4 ("Macintosh HD - Data") is FileVault encrypted. It is not necessary.

## 7. After a kernel update

DKMS builds the module again for each new kernel. Check it:

```
dkms status
ls /dev/video0
```

Only a new upstream release fixes a kernel API break. This happened for kernel 7.2, as
section 2 describes. If the camera fails after a kernel update, install the package
again to get a newer `master`:

```
yay -S facetimehd-dkms-git
```

## 8. Revert

```
sudo modprobe -r facetimehd
yay -Rns facetimehd-dkms-git facetimehd-firmware facetimehd-data
sudo rm -f /etc/udev/rules.d/72-facetimehd-brightness.rules
```

## Notes

- The module taints the kernel: `loading out-of-tree module taints kernel` and
  `module verification failed`. Both are expected without Secure Boot.
- DKMS makes a signing key at `/var/lib/dkms/mok.key`. It is not enrolled, and it is not
  necessary without Secure Boot.
- dkms 3.4.3 ignores `MODULES_CONF[0]="blacklist bdc_pci"`. The AUR PKGBUILD deletes the
  deprecated `CLEAN` and `MODULES_CONF` lines. `bdc_pci` is not loaded, and the camera
  works.
- The firmware and the `.dat` files are Apple binaries. This repository does not contain
  them.
