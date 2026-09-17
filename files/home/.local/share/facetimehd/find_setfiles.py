#!/usr/bin/env python3
"""Locate FaceTime HD sensor calibration blobs inside AppleCameraAssistant.

The upstream extractor keys off hardcoded offsets for the 10.12.6 binary and
refuses anything else. The blobs themselves are unchanged across macOS
versions, so find them by content: every candidate is accepted only if it
matches the known SHA-256, which makes a wrong extraction impossible.
"""
import hashlib
import pathlib
import sys

# name -> (size, sha256), from patjak/facetimehd-firmware extract-firmware.sh
KNOWN = {
    "9112": (33060, "4dd756fa8460d8dc3d78d0d76944b2f92275d1fe9c83181bbc8292c81c005f1a"),
    "1771": (19040, "756c2bb7c5e55b395449e43a0be1cb7c40c37dfc6c2b5abfaffb8ae70ff0fc4b"),
    "1871": (19040, "bf36fbde0668ab7e44368b584f9fa64b5945b01003d04c6e3c6f22c0be0fd5f3"),
    "1874": (19040, "ffde89e7819ac16a9eb1c8f0bc6dba0e980b508b2022507679d901c190f7cef8"),
    "1222": (20076, "04a6aa0d67c0353505a56187c573b27dfdef703dfb4b98329b1ee74f59e4ba7e"),
    "8221": (30240, "2e041686cf2484345b08b18207266abe725f41f8869e04d427aa092071d9edde"),
    "1571": (18652, "0f73f550b65121115fe0b999f016fb3be3d109057597863df9fe01fd4678c300"),
    "1575": (18652, "31068eab65ba25a480fd4d0463e86f8e2807828a2e251a20b6f107499e0f7936"),
    "1674": (18044, "32377ac603d764f33f1466b5e4a7e3e08780d7becc50ad5b00292e29e2dd0374"),
    "1675": (18044, "b7a38aef2755721bb28c92d84a15654b17e9fb3b0a0f088a384a981fc8fe16d6"),
    "1671": (18044, "0b90133936bf0bbcdde4b85df8d3fc18722b58d2f8a1afc2564c6c242b6c57fa"),
}


def find(blob, size, want, step):
    for off in range(0, len(blob) - size + 1, step):
        if hashlib.sha256(blob[off:off + size]).hexdigest() == want:
            return off
    return None


def main(path, outdir):
    blob = pathlib.Path(path).read_bytes()
    out = pathlib.Path(outdir)
    print(f"scanning {path} ({len(blob)} bytes)")

    hits = 0
    for name, (size, want) in KNOWN.items():
        off = None
        for step in (4096, 16, 1):          # page-aligned is how 10.12.6 stored them
            off = find(blob, size, want, step)
            if off is not None:
                break
        if off is None:
            print(f"  {name}_01XX.dat  not found")
            continue
        dest = out / f"{name}_01XX.dat"
        dest.write_bytes(blob[off:off + size])
        assert hashlib.sha256(dest.read_bytes()).hexdigest() == want
        print(f"  {name}_01XX.dat  offset {off} size {size}  OK")
        hits += 1

    print(f"{hits}/{len(KNOWN)} extracted")
    return 0 if hits else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
