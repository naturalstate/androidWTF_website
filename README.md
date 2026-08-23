# androidWTF — website

Catalogue browser for androidWTF. Find out what your phone can actually run,
build a pack, and get the install steps for it.

**Live at <https://naturalstate.github.io/androidWTF_website/>**

Sibling of **[macWTF](https://naturalstate.github.io/macwtf_website/)** and
**[windowsWTF](https://naturalstate.github.io/windowsWTF_website/)**, and
deliberately built on the same visual system.

> **Preview.** The catalogue is curated but the project's own tooling — the
> `wtf.sh` Termux bootstrap and the adb pack installer — does not exist yet.
> Package identifiers *are* verified (see below).

## What is different from macWTF

macWTF's organising axis is *which package manager installs this*. Android's is
*can this device run it at all*, so **tier** is a first-class field:

| Tier | Needs | Unlocks |
|---|---|---|
| T0 | any Android 10+ device | Termux, the app catalogue, unprivileged scanning, VPN-mode capture, NFC, BLE, OTG serial |
| T1 | Shizuku, paired over wireless debugging | debloat, AppOps, package control, on-device adb |
| T2 | Magisk or KernelSU | raw sockets, privileged ports, Frida, tcpdump, LSPosed |
| T3 | NetHunter kernel | monitor mode, injection, HID attacks, external adapters |

Every card is edged in its tier's colour, tier is its own filter, and the
selection sheet tells you the highest tier your pack needs before you install
anything.

The other difference is the output. macOS has one install path; Android has
four, and they are not interchangeable:

- **Obtainium** — an importable JSON config for everything from F-Droid and
  GitHub Releases, which then keeps itself updated
- **Termux** — grouped shell commands. Not APKs, so Google's developer
  verification does not apply to any of it
- **Manual** — Play Store, NetHunter Store and first-party apps, which
  Obtainium cannot track
- **adb** — a laptop-side script that installs a whole pack over wireless
  debugging with no per-app taps

## Package verification

Every identifier in the catalogue has been checked against its live source:

| Source | Count | Checked against |
|---|---:|---|
| F-Droid | 42 | `f-droid.org/api/v1/packages/<id>` |
| Play Store | 44 | store listing returns 200 |
| GitHub Releases | 29 | GitHub repos API, redirects followed |
| Termux `pkg` | 25 | termux-main / x11 / root / TUR `Packages` indexes |
| Termux `pip` | 7 | PyPI JSON API |
| Termux `go` | 7 | `proxy.golang.org` module index |
| Termux `git` | 12 | repository exists on GitHub / GitLab |

Notable corrections found this way: Bitwarden, WireGuard, Orbot, Tor Browser,
Telegram and APRSdroid are no longer in the main F-Droid repo; Syncthing was
discontinued and replaced by Syncthing-Fork; JuiceSSH has been pulled from the
Play Store; and **30 of the 54 original Termux entries were not apt packages at
all** — they are pip, Go or clone-and-build installs, and now say so.

## Running it

No build step. It is a static folder:

```bash
python3 -m http.server 8000
```

Preact and htm are vendored in `assets/vendor` and resolved by an import map,
and the fonts are self-hosted, so the page contacts no third party.

## Layout

```
index.html                     markup and style links
assets/app.js                  the whole app: tiers, search, packs, install steps
assets/app.css                 dark theme, tier colour system
assets/vendor/                 vendored preact + htm
data/tools.json                generated catalogue
data/packs.json                curated packs
scripts/build_catalogue.py     catalogue source of truth -> tools.json
```

## Regenerating the catalogue

The catalogue lives as literal data inside the build script, because androidWTF
has no manifest repo yet:

```bash
python3 scripts/build_catalogue.py data/tools.json
```

When the CLI side grows TOML manifests, this should read those instead, so the
site and the installer cannot disagree about what exists.

## Not done yet

A real `wtf.sh` bootstrap · the adb pack installer · first-party app entries ·
offline reference pack manifest · re-running verification on a schedule so the
catalogue does not rot.

## License

MIT
