#!/usr/bin/env python3
"""Build data/tools.json for the androidWTF site.

The catalogue lives here as literal data rather than being parsed out of a
markdown draft, because androidWTF has no manifest repo yet. When the CLI side
grows TOML manifests this should read those instead, so the site and the
installer cannot disagree about what exists.

Each row is:
    (id, name, description, tier, source, package, license, flags, notes[, method])

tier    0  runs on any stock Android 10+ device
        1  needs Shizuku (ADB pairing, no root)
        2  needs root (Magisk / KernelSU)
        3  needs a NetHunter kernel

source  how it is obtained, which decides the generated command:
        termux    runs in the Termux shell. The optional 10th element says how
                  it is actually installed, because most of the interesting
                  tooling is NOT an apt package:
                    pkg  pkg install <package>      (the default)
                    pip  pip install <package>
                    go   go install <module>@latest
                    npm  npm install -g <package>
                    git  git clone <url> and build
        fdroid    F-Droid app id, installable via Obtainium
        github    owner/repo, installable via Obtainium
        play      Play Store app id (manual, or via Aurora)
        nethunter NetHunter Store
        builtin   already on the device, a documented workflow
        web       a web resource, not an install
        own       first-party androidWTF app

flags   essential  the catalogue is much worse without it
        legal      carries a legal warning, see the docs
        integrity  will trip Play Integrity / break banking apps
        exthw      needs external hardware over USB OTG
        gated      unverified developer; may need the advanced sideload flow
        gpl        GPL licensing that matters if you vendor it
"""

import json
import sys
from pathlib import Path

CATEGORIES = [
    ("core",       "Core Runtime & Terminal",   False),
    ("control",    "App & Device Control",      False),
    ("netrecon",   "Network Recon & Analysis",  True),
    ("wireless",   "Wireless & Wardriving",     True),
    ("hardware",   "NFC, RFID, BLE & Serial",   True),
    ("sdr",        "SDR & Radio",               True),
    ("vpn",        "VPN, Proxy & Tunneling",    False),
    ("web",        "Web & API Testing",         True),
    ("mobile",     "Mobile App Assessment",     True),
    ("osint",      "OSINT & Recon",             True),
    ("creds",      "Credentials & Auth",        False),
    ("remote",     "Remote Access & Transfer",  False),
    ("evidence",   "Evidence & Reporting",      False),
    ("server",     "Servers & Listeners",       True),
    ("labs",       "Labs & Vulnerable Targets", True),
    ("desktop",    "Linux Desktop",             False),
    ("dev",        "Development",               False),
    ("comms",      "Comms",                     False),
    ("socialeng",  "Social Engineering",        True),
    ("automation", "Automation",                False),
    ("reference",  "Reference Library",         False),
]

E = "essential"

TOOLS = {

# ---------------------------------------------------------------------- core
"core": [
 ("termux", "Termux", "Terminal emulator and full Linux package environment. The backbone of the whole toolkit — everything in here that matters most is a Termux package, not an APK.", 0, "fdroid", "com.termux", "free", [E], "F-Droid or GitHub only. The Play Store build is abandoned and its packages are years stale."),
 ("termux-api", "Termux:API", "Bridges the shell to SMS, clipboard, sensors, camera, GPS, notifications and TTS. Every interesting automation script needs it.", 0, "fdroid", "com.termux.api", "free", [E], "Also requires 'pkg install termux-api' inside Termux."),
 ("termux-boot", "Termux:Boot", "Run scripts at device boot. Needed for anything that has to survive a reboot — listeners, honeypots, sync jobs.", 0, "fdroid", "com.termux.boot", "free", [], ""),
 ("termux-widget", "Termux:Widget", "Home screen shortcuts that launch a script with one tap. This is how field workflows get usable.", 0, "fdroid", "com.termux.widget", "free", [E], ""),
 ("termux-styling", "Termux:Styling", "Fonts and colour schemes for Termux. Where the androidWTF theme gets applied.", 0, "fdroid", "com.termux.styling", "free", [], ""),
 ("termux-float", "Termux:Float", "A floating terminal window over other apps. Useful when you need a shell while driving a GUI tool.", 0, "fdroid", "com.termux.window", "free", [], ""),
 ("termux-tasker", "Termux:Tasker", "Exposes Termux scripts as Tasker actions. Combined with Tasker this is the automation backbone.", 0, "fdroid", "com.termux.tasker", "free", [], ""),
 ("termux-x11", "Termux:X11", "X11 display server for Termux, for running GUI Linux applications.", 0, "github", "termux/termux-x11", "free", [], "Pairs with the Linux Desktop module."),
 ("nethunter", "Kali NetHunter", "Kali's Android platform. Rootless mode installs a full Kali chroot on a stock unrooted phone; full mode needs a NetHunter kernel.", 0, "nethunter", "com.offsec.nethunter", "free", [E], "Rootless works on any device. Monitor mode and HID attacks need Tier 3."),
 ("nethunter-store", "NetHunter Store", "Offensive Security's app repository. The supported source for the NetHunter apps.", 0, "nethunter", "com.offsec.nethunter.store", "free", [], ""),
 ("hackers-keyboard", "Hacker's Keyboard", "A keyboard with real Ctrl, Alt, Esc, Tab, arrows and function keys. Non-negotiable for terminal work.", 0, "fdroid", "org.pocketworkstation.pckeyboard", "free", [E], ""),
 ("connectbot", "ConnectBot", "Lightweight open source SSH client. No account, no sync, no telemetry.", 0, "fdroid", "org.connectbot", "free", [], ""),
 ("termius", "Termius", "Polished SSH and SFTP client with cross-device sync. Free tier is usable; sync is paid.", 0, "play", "com.server.auditor.ssh.client", "freemium", [], ""),
],

# ------------------------------------------------------------------- control
"control": [
 ("shizuku", "Shizuku", "Grants apps ADB-level privileges with no root, by pairing over wireless debugging. On Android 11+ this needs no PC at all. The single highest-value install in the catalogue after Termux.", 0, "github", "RikkaApps/Shizuku", "free", [E], "Installing it is Tier 0; the privileges it unlocks are Tier 1. Must be re-paired after every reboot unless rooted."),
 ("app-manager", "App Manager", "Manifest viewer, component blocker, AppOps control, signature checks, APK extraction and tracker analysis. Best-in-class, and directly useful for mobile app assessments.", 1, "github", "MuntashirAkon/AppManager", "free", [E], ""),
 ("canta", "Canta", "Uninstall system bloat through Shizuku, with a crowd-sourced safety rating per package. The debloat engine.", 1, "github", "samolego/Canta", "free", [], ""),
 ("obtainium", "Obtainium", "Installs and auto-updates sideloaded apps straight from GitHub Releases, F-Droid and arbitrary URLs. Without this, maintaining seventy sideloaded APKs by hand is what kills the project in six months.", 0, "github", "ImranR98/Obtainium", "free", [E], "androidWTF ships an Obtainium config you can import in one go."),
 ("shelter", "Shelter", "Runs the catalogue inside an isolated Android work profile you can freeze when you are not on an engagement. Keeps the pentest apps away from your banking apps.", 0, "fdroid", "net.typeblog.shelter", "free", [E], ""),
 ("insular", "Insular", "Work profile isolation, a fork of Island. Alternative to Shelter — pick one.", 0, "fdroid", "com.oasisfeng.island.fdroid", "free", [], ""),
 ("aurora-store", "Aurora Store", "Play Store apps without a Google account, using anonymous sessions.", 0, "fdroid", "com.aurora.store", "free", [], "Anonymous sessions break periodically. Paid apps still need a real account."),
 ("magisk", "Magisk", "Systemless root. The gate for everything in Tier 2.", 2, "github", "topjohnwu/Magisk", "free", ["integrity"], "Breaks Play Integrity. Banking, payment and MDM apps will refuse to run."),
 ("kernelsu", "KernelSU", "Kernel-based root, an alternative to Magisk on supported kernels.", 2, "github", "tiann/KernelSU", "free", ["integrity"], ""),
 ("lsposed", "LSPosed", "Xposed framework for hooking app internals at runtime. The base for SSL unpinning modules.", 2, "github", "LSPosed/LSPosed", "free", ["integrity"], ""),
 ("ssl-unpinning", "TrustMeAlready", "Xposed module that disables SSL verification and pinning system-wide, so an intercepting proxy can see app traffic.", 2, "github", "ViRb3/TrustMeAlready", "free", [], "Needed for most real mobile app assessments. objection can do the same per-process without a module."),
],

# ------------------------------------------------------------------ netrecon
"netrecon": [
 ("pcapdroid", "PCAPdroid", "Packet capture with no root, by running a local VPN service. Exports real PCAP for Wireshark. With root it captures the full interface instead of just app traffic.", 0, "github", "emanuele-f/PCAPdroid", "free", [E], "Tier 0 gives you app traffic only. Tier 2 gives you the whole interface."),
 ("reqable", "Reqable", "Modern on-device intercepting HTTP(S) proxy, the successor to HttpCanary. Inspect, rewrite and replay requests without a laptop.", 0, "play", "com.reqable.android", "freemium", [E], ""),
 ("http-toolkit", "HTTP Toolkit", "Alternative intercepting proxy with strong ADB integration and one-click certificate setup.", 0, "github", "httptoolkit/httptoolkit-android", "free", [], ""),
 ("fing", "Fing", "Fast network discovery with good device fingerprinting. Heavy upsell, but the free tier does the job.", 0, "play", "com.overlook.android.fing", "freemium", [], ""),
 ("portdroid", "PortDroid", "Port scanner, host discovery, DNS lookup, whois and traceroute in one app.", 0, "play", "com.stealthcopter.portdroid", "freemium", [], ""),
 ("network-survey", "Network Survey", "Cellular, WiFi, GNSS and Bluetooth survey with logging to file. Underrated for site surveys and RF mapping.", 0, "fdroid", "com.craxiom.networksurvey", "free", [], ""),
 ("wifianalyzer", "WiFiAnalyzer", "Channel and signal analysis. Open source, no ads, no telemetry — prefer it over the closed alternatives.", 0, "fdroid", "com.vrem.wifianalyzer", "free", [], ""),
 ("wifiman", "WiFiman", "Ubiquiti's analyser. Clean, fast, with a good speed test and device discovery.", 0, "play", "com.ubnt.usurvey", "free", [], ""),
 ("port-authority", "Port Authority", "Open source LAN scanner and port scanner.", 0, "fdroid", "com.aaronjwood.portauthority", "free", [], ""),
 ("network-cell-info", "Network Cell Info Lite", "Cell tower mapping, band and signal detail, neighbouring cells.", 0, "play", "com.wilysis.cellinfolite", "freemium", [], ""),
 ("cellmapper", "CellMapper", "Crowd-sourced cell site mapping and coverage data.", 0, "play", "cellmapper.net.cellmapper", "free", [], ""),
 ("snoopsnitch", "SnoopSnitch", "IMSI catcher and SS7 attack detection from the baseband's own diagnostic messages.", 2, "fdroid", "de.srlabs.snoopsnitch", "free", [], "Needs root and a Qualcomm chipset. Will not work on Exynos or Tensor."),
 ("nmap", "nmap", "The scanner. Connect scan works unprivileged; SYN scan, OS detection and anything raw-socket needs root.", 0, "termux", "nmap", "free", [E], "nmap -sT works at Tier 0. nmap -sS needs Tier 2."),
 ("masscan", "masscan", "Mass port scanner. Raw sockets only, so it is root-or-nothing.", 2, "termux", "https://github.com/robertdavidgraham/masscan", "free", [], "Build from source; there is no Termux package.", "git"),
 ("tcpdump", "tcpdump", "Interface capture from the shell. Needs raw socket access.", 2, "termux", "tcpdump", "free", [], "At Tier 0 use PCAPdroid instead."),
 ("bettercap", "bettercap", "Network attack and MITM framework. Needs raw sockets for anything beyond passive use.", 2, "termux", "github.com/bettercap/bettercap", "free", [], "", "go"),
 ("netcat", "netcat / socat", "The two tools you actually reach for. Listeners, relays, port forwards.", 0, "termux", "netcat-openbsd socat", "free", [], "Ports below 1024 need root."),
 ("responder", "Responder", "LLMNR, NBT-NS and MDNS poisoner.", 2, "termux", "https://github.com/lgandx/Responder", "free", [], "Binds privileged ports, so root is mandatory.", "git"),
],

# ------------------------------------------------------------------ wireless
"wireless": [
 ("muon", "Muon", "Terminal WiFi manager, first-party. Brings adapters up and down, toggles monitor mode, matches chipsets against a driver database, and puts 100+ wireless and pentest commands behind a menu with variable substitution — so you stop typing airodump-ng syntax from memory.", 0, "termux", "https://github.com/naturalstate/muon", "free", [E], "Single Python 3 file, no pip dependencies. Detects two modes at launch: full with root, limited without. In limited mode the root-only actions are greyed out rather than hidden, and you still get scanning, the command reference, the adapter/driver database and the troubleshooting guide. Termux limited mode also wants 'pkg install termux-api' and the Termux:API app.", "git"),
 ("wigle", "WiGLE WiFi Wardriving", "Logs every network you drive past with GPS, and exports CSV. Works on a completely stock phone.", 0, "fdroid", "net.wigle.wigleandroid", "free", [E], ""),
 ("aircrack-ng", "aircrack-ng suite", "The classic wireless attack suite. Everything in it needs monitor mode.", 3, "nethunter", "aircrack-ng", "free", ["exthw"], "Internal Android chipsets do not do monitor mode. You need a NetHunter kernel, and in practice an external adapter over OTG."),
 ("kismet", "Kismet", "Wireless detector, sniffer and IDS. Wants monitor mode on a real interface.", 3, "nethunter", "kismet", "free", ["exthw"], ""),
 ("wifite2", "Wifite2", "Automation wrapper over the aircrack suite. Same monitor mode requirement.", 3, "nethunter", "wifite", "free", ["exthw"], ""),
 ("hcxdumptool", "hcxdumptool", "PMKID and handshake capture, the modern path to WPA2 material.", 3, "nethunter", "hcxdumptool", "free", ["exthw"], "Capture on the phone, crack on your homelab. There is no usable GPU path on Android."),
 ("wifi-warden", "WiFi Warden", "WPS analysis and network detail. Legally sensitive — connecting to a network you do not own is a CFAA problem regardless of how easy the app makes it.", 0, "play", "com.xti.wifiwarden", "freemium", ["legal"], "Authorised engagements only, with the technique named in scope."),
],

# ------------------------------------------------------------------ hardware
"hardware": [
 ("nrf-connect", "nRF Connect for Mobile", "The real BLE tool: scan, connect, enumerate services, read and write characteristics, log advertising. Not a generic 'BLE scanner'.", 0, "play", "no.nordicsemi.android.mcp", "free", [E], "Pairs directly with any Nordic nRF development board."),
 ("serial-usb-terminal", "Serial USB Terminal", "USB OTG serial console. This is how you talk to an ESP32, a Proxmark3, a Chameleon Ultra, or anything else with a UART.", 0, "play", "de.kai_morich.serial_usb_terminal", "free", [E, "exthw"], ""),
 ("usb-device-info", "USB Device Info", "Identify what is plugged into OTG and confirm the phone actually supports USB host mode.", 0, "play", "aws.apps.usbDeviceEnumerator", "free", ["exthw"], "Run this first — plenty of phones do not do USB host at all."),
 ("nfc-tools", "NFC Tools", "Read, write and emulate NDEF tags. The PRO version adds tasks and scripting.", 0, "play", "com.wakdev.wdnfc", "freemium", [], ""),
 ("mifare-classic-tool", "MIFARE Classic Tool", "Key dictionary attacks and sector dumping on MIFARE Classic. The core on-phone RFID tool.", 0, "fdroid", "de.syss.MifareClassicTool", "free", [E], "Needs an NXP NFC controller. Many phones cannot read Classic at all."),
 ("nxp-taginfo", "NXP TagInfo", "Deep tag identification — chip type, memory layout, capability container.", 0, "play", "com.nxp.taginfolite", "free", [], ""),
 ("chameleon-ultra-gui", "Chameleon Ultra GUI", "Controls a Chameleon Ultra over BLE or USB. Slot management, card emulation, reads.", 0, "github", "GameTec-live/ChameleonUltraGUI", "free", ["exthw"], ""),
 ("proxmark3", "Proxmark3 client", "Compiles in Termux. The serial device permission is the hard part, not the build.", 2, "termux", "proxmark3", "free", ["exthw"], "OTG serial access from Termux normally needs root or a udev-equivalent workaround."),
 ("flipper", "Flipper Mobile App", "Official companion for the Flipper Zero.", 0, "play", "com.flipperdevices.app", "free", ["exthw"], ""),
 ("bt-hci-snoop", "Bluetooth HCI snoop log", "Not an app. Enable the toggle in Developer Options, reproduce the pairing, then pull btsnoop_hci.log and open it in Wireshark.", 1, "builtin", "btsnoop", "free", [], "adb bugreport, or adb pull /data/misc/bluetooth/logs/btsnoop_hci.log with Shizuku or root."),
],

# ----------------------------------------------------------------------- sdr
"sdr": [
 ("rtl2832u-driver", "RTL2832U driver", "Martin Marinov's driver. A prerequisite for every RTL-SDR app on Android — install it before anything else in this category.", 0, "play", "marto.rtl_tcp_andro", "free", [E, "exthw"], ""),
 ("sdr-touch", "SDR Touch", "RTL-SDR receiver with a waterfall and demodulation. Free tier is time-limited.", 0, "play", "marto.androsdr2", "freemium", ["exthw"], ""),
 ("rf-analyzer", "RF Analyzer", "Open source spectrum analyser supporting RTL-SDR and HackRF.", 0, "github", "demantz/RFAnalyzer", "free", ["exthw"], ""),
 ("sdrpp", "SDR++", "Modern multi-SDR receiver, actively developed, supports most hardware.", 0, "github", "AlexandreRouma/SDRPlusPlus", "free", ["exthw"], ""),
 ("meshtastic", "Meshtastic", "LoRa mesh networking. Talks to Heltec, T-Beam and RAK boards over BLE.", 0, "fdroid", "com.geeksville.mesh", "free", ["exthw"], ""),
 ("aprsdroid", "APRSdroid", "Amateur packet radio over APRS-IS or a real TNC.", 0, "github", "ge0rg/aprsdroid", "free", [], "Not in the main F-Droid repo — take it from GitHub Releases."),
 ("look4sat", "Look4Sat", "Open source satellite pass prediction and tracking.", 0, "fdroid", "com.rtbishop.look4sat", "free", [], ""),
 ("gpstest", "GPSTest", "GNSS constellation view, accuracy, and which satellite systems the phone actually uses.", 0, "fdroid", "com.android.gpstest.osmdroid", "free", [], ""),
 ("nmea-tools", "NMEA Tools", "Read an external GPS dongle over OTG and feed it to the system location provider.", 0, "play", "com.peterhohsy.nmeatools", "freemium", ["exthw"], ""),
 ("repeaterbook", "RepeaterBook", "Amateur repeater directory with offline data.", 0, "play", "com.zbm2.repeaterbook", "free", [], ""),
 ("dump1090", "dump1090", "ADS-B aircraft tracking off an RTL-SDR, from the Termux shell.", 0, "termux", "https://github.com/flightaware/dump1090", "free", ["exthw"], "", "git"),
 ("rtl-433", "rtl_433", "Decodes the 433MHz sensor soup — weather stations, TPMS, doorbells, remotes.", 0, "termux", "https://github.com/merbanan/rtl_433", "free", ["exthw"], "", "git"),
],

# ----------------------------------------------------------------------- vpn
"vpn": [
 ("wireguard", "WireGuard", "The VPN you will actually use for lab and client access. Fast, simple config, no daemon to babysit.", 0, "play", "com.wireguard.android", "free", [E], "Not in the main F-Droid repo. WireGuard run their own F-Droid-compatible repo at f-droid.wireguard.com if you would rather avoid Play."),
 ("tailscale", "Tailscale", "Mesh VPN over WireGuard with SSO. Gets the phone onto your homelab with no port forwarding.", 0, "play", "com.tailscale.ipn", "freemium", [], ""),
 ("twingate", "Twingate", "Zero-trust network access. Alternative path to the same homelab.", 0, "play", "com.twingate", "freemium", [], ""),
 ("rethinkdns", "RethinkDNS", "Per-app firewall, DNS filtering and a WireGuard client in one. Arguably strictly better than NetGuard now.", 0, "github", "celzero/rethink-app", "free", [E], "Uses the VPN slot, so it conflicts with PCAPdroid and other VPN-mode apps."),
 ("netguard", "NetGuard", "Per-app firewall with no root, via the VPN service. The simpler, more predictable option.", 0, "github", "M66B/NetGuard", "free", [], "Same VPN slot conflict. Pick one of NetGuard or RethinkDNS."),
 ("openvpn-android", "OpenVPN for Android", "Open source OpenVPN client. Plenty of clients still hand you a .ovpn file.", 0, "fdroid", "de.blinkt.openvpn", "free", [], ""),
 ("orbot", "Orbot", "Tor as a transparent proxy or VPN for selected apps.", 0, "github", "guardianproject/orbot-android", "free", [], "Not in the main F-Droid repo — Guardian Project run their own, or take it from GitHub Releases."),
 ("tor-browser", "Tor Browser", "The browser, not the proxy. Use with or without Orbot.", 0, "play", "org.torproject.torbrowser", "free", [], "Not in the main F-Droid repo. The Guardian Project repo carries it too."),
 ("every-proxy", "Every Proxy", "Turns the phone into an HTTP and SOCKS5 proxy. Genuinely handy for pivoting a laptop through the phone's connection.", 0, "play", "com.gorillasoftware.everyproxy", "freemium", [], ""),
 ("proxychains", "proxychains-ng", "Force any Termux CLI tool through a SOCKS proxy.", 0, "termux", "proxychains-ng", "free", [], ""),
 ("cloudflared", "cloudflared", "Expose a service running on the phone to the internet without a public IP.", 0, "termux", "cloudflared", "free", [], "Also useful for getting a callback to a device behind carrier NAT."),
],

# ----------------------------------------------------------------------- web
"web": [
 ("firefox-nightly", "Firefox Nightly", "The only mainstream mobile browser that runs real desktop extensions. Wappalyzer, Cookie Editor, FoxyProxy and friends all work.", 0, "play", "org.mozilla.fenix", "free", [E], "Custom add-on collections need a one-time setup in the debug menu."),
 ("kiwi-browser", "Kiwi Browser", "Chromium with Chrome Web Store extension support. Development has been intermittent — treat Firefox Nightly as the primary.", 0, "github", "kiwibrowser/src.next", "free", [], ""),
 ("urlcheck", "URLCheck", "Inspect, unshorten and strip tracking from a URL before it opens. Set it as the default handler.", 0, "fdroid", "com.trianguloy.urlchecker", "free", [], ""),
 ("hermit", "Hermit", "Wraps any web app as a standalone lite app. Good for PortSwigger Academy, your own dashboards, or anything you want off the browser tab pile.", 0, "play", "com.chimbori.hermitcrab", "freemium", [], ""),
 ("burp-ca", "Burp / system CA install", "Not an app. On Android 7+ user-added CAs are not trusted by apps, so an intercepting proxy sees nothing until the certificate lands in the system store.", 2, "builtin", "system-ca", "free", [], "Magisk modules like AlwaysTrustUserCerts handle this. At Tier 0 you are limited to apps that opt into user CAs."),
 ("ffuf", "ffuf", "Content and parameter fuzzing. Runs at full speed in Termux.", 0, "termux", "github.com/ffuf/ffuf/v2", "free", [E], "", "go"),
 ("nuclei", "nuclei", "Template-driven vulnerability scanning. Works well on a phone.", 0, "termux", "github.com/projectdiscovery/nuclei/v3/cmd/nuclei", "free", [E], "", "go"),
 ("httpx-tool", "httpx", "Fast HTTP probing and fingerprinting across a host list.", 0, "termux", "github.com/projectdiscovery/httpx/cmd/httpx", "free", [], "", "go"),
 ("sqlmap", "sqlmap", "SQL injection automation. Slow on a phone but entirely functional.", 0, "termux", "sqlmap", "free", [], "", "pip"),
 ("mitmproxy", "mitmproxy", "Scriptable intercepting proxy from the shell, for when Reqable's UI is not enough.", 0, "termux", "mitmproxy", "free", [], "", "pip"),
 ("nikto", "nikto", "Old, noisy, still finds things.", 0, "termux", "https://github.com/sullo/nikto", "free", [], "", "git"),
 ("feroxbuster", "feroxbuster", "Recursive content discovery in Rust.", 0, "termux", "feroxbuster", "free", [], ""),
],

# -------------------------------------------------------------------- mobile
"mobile": [
 ("jadx", "jadx", "Decompiles an APK to readable Java. Runs fine in Termux with a JDK, and this is where most mobile assessment actually starts.", 0, "termux", "jadx", "free", [E], ""),
 ("apktool", "apktool", "Smali disassembly and rebuild. For patching an app rather than just reading it.", 0, "termux", "apktool", "free", [E], ""),
 ("apksigner", "apksigner / zipalign", "Re-sign and align a patched APK so the device will install it.", 0, "termux", "apksigner", "free", [], "Under developer verification your own signing key will need to be registered to install on a certified device without the advanced flow."),
 ("frida", "Frida server", "Runtime instrumentation — hook methods, dump arguments, bypass checks live.", 2, "github", "frida/frida", "free", [], "The server binary needs root. The client can run in Termux or on your laptop."),
 ("objection", "objection", "Frida wrapper that does the common jobs without writing hooks: SSL pinning bypass, storage dump, class enumeration.", 2, "termux", "objection", "free", [], "", "pip"),
 ("mobsf", "MobSF", "Static and dynamic analysis framework. Technically runs in Termux; realistically run it on your homelab and reach it from the phone.", 0, "termux", "https://github.com/MobSF/Mobile-Security-Framework-MobSF", "free", [], "Heavy. A phone is the wrong place for this.", "git"),
 ("apk-analyzer", "APK Analyzer", "Quick on-device look at permissions, activities, certificates and manifest.", 0, "play", "sk.styk.martin.apkanalyzer", "free", [], ""),
 ("ecliptic", "Ecliptic", "Technology stack detection. First-party androidWTF tooling.", 0, "own", "ecliptic", "free", [], ""),
 ("adb-shizuku", "On-device adb shell", "Not an app. With Shizuku paired you get pm, dumpsys, content and settings from a local shell — most of what you would otherwise plug into a laptop for.", 1, "builtin", "adb", "free", [E], ""),
],

# --------------------------------------------------------------------- osint
"osint": [
 ("shodan", "Shodan", "Host and service intelligence lookup.", 0, "play", "io.shodan.app", "freemium", [], ""),
 ("sherlock", "Sherlock", "Username enumeration across hundreds of sites.", 0, "termux", "sherlock-project", "free", [], "", "pip"),
 ("theharvester", "theHarvester", "Email, subdomain and host gathering from public sources.", 0, "termux", "theHarvester", "free", [], "", "pip"),
 ("amass", "amass", "Subdomain enumeration and attack surface mapping.", 0, "termux", "github.com/owasp-amass/amass/v4/...", "free", [], "", "go"),
 ("subfinder", "subfinder", "Fast passive subdomain discovery.", 0, "termux", "github.com/projectdiscovery/subfinder/v2/cmd/subfinder", "free", [], "", "go"),
 ("organic-maps", "Organic Maps", "Offline maps with no account and no tracking. For physical engagements where you need site layout with no signal.", 0, "fdroid", "app.organicmaps", "free", [E], ""),
 ("osmand", "OsmAnd", "Offline maps with heavier features — routing profiles, custom overlays, GPX recording.", 0, "fdroid", "net.osmand.plus", "freemium", [], ""),
 ("google-earth", "Google Earth", "Aerial and street-level site recon before a physical engagement.", 0, "play", "com.google.earth", "free", [], ""),
],

# --------------------------------------------------------------------- creds
"creds": [
 ("bitwarden", "Bitwarden", "Password manager. Self-hostable with Vaultwarden if you would rather not use their cloud.", 0, "github", "bitwarden/android", "freemium", [E], "No longer in the main F-Droid repo — GitHub Releases or Play."),
 ("aegis", "Aegis Authenticator", "Open source TOTP with an encrypted, exportable vault. Prefer it over Google Authenticator — you can actually get your seeds back out.", 0, "fdroid", "com.beemdevelopment.aegis", "free", [E], ""),
 ("keepassdx", "KeePassDX", "Offline KDBX vault. Useful for engagement-scoped credentials you want kept out of your personal manager entirely.", 0, "fdroid", "com.kunzisoft.keepass.libre", "free", [E], ""),
 ("ms-authenticator", "Microsoft Authenticator", "Needed for client Entra tenants whether you like it or not.", 0, "play", "com.azure.authenticator", "free", [], ""),
 ("google-authenticator", "Google Authenticator", "Same reasoning. Keep it for client accounts, not your own.", 0, "play", "com.google.android.apps.authenticator2", "free", [], ""),
 ("hashcat-note", "Cracking — do it elsewhere", "Not an app. There is no usable GPU acceleration path for hashcat on Android. Capture on the phone, crack on the homelab.", 0, "builtin", "hashcat", "free", [], "john the ripper runs in Termux on CPU, and is slow enough to be a novelty."),
],

# -------------------------------------------------------------------- remote
"remote": [
 ("realvnc", "RealVNC Viewer", "Required for NetHunter KeX, and generally the most reliable VNC client on Android.", 0, "play", "com.realvnc.viewer.android", "free", [E], ""),
 ("ms-rdp", "Microsoft Remote Desktop", "RDP into Windows targets and jump boxes.", 0, "play", "com.microsoft.rdc.androidx", "free", [], ""),
 ("rustdesk", "RustDesk", "Open source remote desktop with a self-hostable relay. Fits a homelab better than any commercial option.", 0, "github", "rustdesk/rustdesk", "free", [], ""),
 ("syncthing", "Syncthing-Fork", "Continuous peer-to-peer sync with no cloud. This is how engagement artifacts get off the phone and onto your homelab without touching a third party.", 0, "fdroid", "com.github.catfriend1.syncthingfork", "free", [E], "The original com.nutomic.syncthingandroid was discontinued and pulled from F-Droid. This fork is the maintained one."),
 ("localsend", "LocalSend", "AirDrop-equivalent over the local network, cross platform, open source.", 0, "github", "localsend/localsend", "free", [], ""),
 ("kde-connect", "KDE Connect", "Shared clipboard, file push and remote input between the phone and your laptop.", 0, "fdroid", "org.kde.kdeconnect_tp", "free", [], ""),
 ("material-files", "Material Files", "Open source file manager with SMB, SFTP and FTP built in. Actively maintained.", 0, "fdroid", "me.zhanghai.android.files", "free", [E], ""),
 ("amaze", "Amaze File Manager", "Open source file manager, root-aware. The alternative to Material Files.", 0, "fdroid", "com.amaze.filemanager", "free", [], ""),
 ("openssh", "OpenSSH", "sshd on the phone as well as ssh from it. The phone becomes something you can reach.", 0, "termux", "openssh", "free", [E], "Must listen above port 1024 without root. 8022 is the Termux convention."),
 ("rsync", "rsync", "Move artifacts around properly, resumable, over SSH.", 0, "termux", "rsync", "free", [], ""),
],

# ------------------------------------------------------------------ evidence
"evidence": [
 ("obsidian", "Obsidian", "Markdown notes over a plain folder. Combined with Syncthing this is a complete engagement notes pipeline with no vendor in it.", 0, "play", "md.obsidian", "freemium", [E], ""),
 ("joplin", "Joplin", "Open source notes with self-hostable sync. The alternative if you want the whole stack open.", 0, "fdroid", "net.cozic.joplin", "free", [], ""),
 ("markor", "Markor", "Lightweight markdown editor over local files. No database, no sync, no lock-in.", 0, "fdroid", "net.gsantner.markor", "free", [], ""),
 ("open-camera", "Open Camera", "Manual camera with GPS stamping and EXIF control. For physical engagement evidence that has to hold up later.", 0, "fdroid", "net.sourceforge.opencamera", "free", [E], ""),
 ("timestamp-camera", "Timestamp Camera", "Burns date, time and coordinates into the image itself rather than only the metadata.", 0, "play", "com.jeyluta.timestampcamerafree", "freemium", [], ""),
 ("screen-recorder", "ADV Screen Recorder", "Screen capture of exploitation steps, for the report and for proving it worked.", 0, "play", "com.blogspot.byterevapps.lollipopscreenrecorder", "freemium", [], ""),
 ("nextcloud", "Nextcloud", "Self-hosted artifact storage, if you would rather have a server than peer sync.", 0, "fdroid", "com.nextcloud.client", "free", [], ""),
 ("exiftool", "exiftool", "Read, strip and verify metadata before anything goes into a report.", 0, "termux", "exiftool", "free", [], ""),
],

# -------------------------------------------------------------------- server
"server": [
 ("python-http", "python -m http.server", "Payload hosting and exfil endpoint in one command. Works unprivileged as long as the port is above 1024.", 0, "termux", "python", "free", [E], ""),
 ("caddy", "Caddy", "A real web server with automatic HTTPS, from the phone.", 0, "termux", "caddy", "free", [], ""),
 ("nginx", "nginx", "The other real web server, when you want the config you already know.", 0, "termux", "nginx", "free", [], ""),
 ("cowrie", "Cowrie", "SSH and Telnet honeypot that records the whole session. Python, so it runs in Termux.", 0, "termux", "https://github.com/cowrie/cowrie", "free", [], "Remap ports above 1024 at Tier 0, or bind the real ports at Tier 2.", "git"),
 ("opencanary", "OpenCanary", "Multi-protocol honeypot daemon. Pairs naturally with a canary token deployment.", 0, "termux", "opencanary", "free", [], "", "pip"),
 ("ntfy-server", "ntfy", "Self-hosted push notifications. This is what a honeypot or a canary token fires into.", 0, "termux", "heckel.io/ntfy/v2", "free", [], "", "go"),
 ("metasploit", "Metasploit Framework", "Installs and runs in Termux. Heavy, and listeners are limited to unprivileged ports without root.", 0, "termux", "https://github.com/rapid7/metasploit-framework", "free", [], "", "git"),
 ("impacket", "impacket", "The Windows protocol toolkit. Most of it works; anything binding 445 needs root.", 0, "termux", "impacket", "free", [], "", "pip"),
],

# ---------------------------------------------------------------------- labs
"labs": [
 ("diva", "DIVA", "Damn Insecure and Vulnerable App. The standard first target for Android app assessment practice.", 0, "github", "payatu/diva-android", "free", [E], ""),
 ("insecureshop", "InsecureShop", "Modern intentionally vulnerable Android app, covering current issue classes rather than 2015 ones.", 0, "github", "hax0rgb/InsecureShop", "free", [], ""),
 ("uncrackable", "OWASP MASTG Crackmes", "UnCrackable levels 1 to 4. Root detection, anti-tamper, native code, obfuscation.", 0, "github", "OWASP/mastg", "free", [E], "Levels 3 and 4 realistically need Frida, so Tier 2."),
 ("androgoat", "AndroGoat", "Kotlin vulnerable app with a broad, well-labelled issue set.", 0, "github", "satishpatnayak/AndroGoat", "free", [], ""),
 ("insecurebankv2", "InsecureBankv2", "Vulnerable banking app with a companion backend, so you get network issues as well as app ones.", 0, "github", "dineshshetty/Android-InsecureBankv2", "free", [], ""),
 ("pivaa", "PIVAA", "Purposely Insecure and Vulnerable Android Application.", 0, "github", "HTBridge/pivaa", "free", [], ""),
 ("juice-shop", "OWASP Juice Shop", "The web target. Node, so it runs directly in Termux with no Docker and no root.", 0, "termux", "juice-shop", "free", [E], "In the TUR user repo, so run 'pkg install tur-repo' first. Docker does not work reliably on non-rooted Android, so do not build the lab story around it."),
 ("vampi", "VAmPI", "Deliberately vulnerable API, Python. Good pairing with Reqable on the same device.", 0, "termux", "https://github.com/erev0s/VAmPI", "free", [], "", "git"),
 ("dvwa", "DVWA", "The classic. Needs PHP and MariaDB in Termux, which is more setup than Juice Shop but works.", 0, "termux", "https://github.com/digininja/DVWA", "free", [], "", "git"),
],

# ------------------------------------------------------------------- desktop
"desktop": [
 ("nethunter-kex", "NetHunter KeX", "Full Kali desktop over VNC. Offensive Security maintained, works in NetHunter Rootless on a stock phone. The recommended desktop backend.", 0, "nethunter", "kex", "free", [E], "Needs a VNC client — RealVNC Viewer is the reliable one."),
 ("termux-x11-desktop", "Termux:X11 + XFCE", "A lighter desktop straight out of Termux, no chroot involved. Faster than VNC, fewer batteries included.", 0, "github", "termux/termux-x11", "free", [], ""),
 ("droiddesk", "DroidDesk", "Community desktop option. Supported as a documented recipe that shells out to their installer, never as vendored code.", 0, "github", "orailnoor/DroidDesk", "free", ["gpl"], "GPL-3.0. Bundling or linking its code would make androidWTF GPL-3.0 too. Their own COMPLIANCE.md flags unresolved provenance issues."),
 ("avf-terminal", "Android Linux Terminal", "Not an app. Android 15+ ships a native Linux terminal on the Android Virtualization Framework — a real VM with a real kernel, not PRoot. It will obsolete most of this category.", 0, "builtin", "avf", "free", [], "Enable in Developer Options where your device supports it. Design the Linux layer with a pluggable backend so you can move to this."),
],

# ----------------------------------------------------------------------- dev
"dev": [
 ("github-app", "GitHub", "Issues, PRs and code review from the phone.", 0, "play", "com.github.android", "free", [], ""),
 ("acode", "Acode", "Capable code editor with plugin support and SFTP. The better default of the mobile editors.", 0, "fdroid", "com.foxdebug.acode", "freemium", [], ""),
 ("spck", "Spck Editor", "Git-aware editor with a built-in preview. Alternative to Acode.", 0, "play", "io.spck", "freemium", [], ""),
 ("neovim", "neovim", "The editor you already use, in Termux, with your existing config.", 0, "termux", "neovim", "free", [E], ""),
 ("tmux", "tmux", "Sessions that survive Termux being backgrounded and killed. Not optional on a phone.", 0, "termux", "tmux", "free", [E], ""),
 ("git", "git", "Version control, and how most of the catalogue's source actually arrives.", 0, "termux", "git", "free", [E], ""),
 ("starship", "Starship", "The prompt, shared with the other WTF builds so every shell looks the same.", 0, "termux", "starship", "free", [], ""),
 ("python", "Python", "The runtime most of the tooling in here is written in.", 0, "termux", "python", "free", [E], ""),
 ("golang", "Go", "Needed to build the ProjectDiscovery tooling from source when a package lags.", 0, "termux", "golang", "free", [], ""),
 ("nodejs", "Node.js", "Runs Juice Shop and most of the JS-based tooling directly.", 0, "termux", "nodejs", "free", [], ""),
 ("ripgrep", "ripgrep / fd / jq", "The search and parse trio. You will use these more than anything else in here.", 0, "termux", "ripgrep fd jq", "free", [E], ""),
],

# --------------------------------------------------------------------- comms
"comms": [
 ("signal", "Signal", "Default for engagement comms. The GitHub build avoids Play Services where you would rather not have it.", 0, "github", "signalapp/Signal-Android", "free", [E], ""),
 ("element", "Element", "Matrix client. Self-hostable, so team comms during an engagement can stay on infrastructure you control.", 0, "fdroid", "im.vector.app", "free", [], ""),
 ("briar", "Briar", "Peer-to-peer messaging over Tor, WiFi or Bluetooth, with no server at all. Works when the network does not.", 0, "fdroid", "org.briarproject.briar.android", "free", [], ""),
 ("ntfy", "ntfy", "Open source push notifications, self-hostable. Where honeypot and canary alerts land.", 0, "fdroid", "io.heckel.ntfy", "free", [E], ""),
 ("pushover", "Pushover", "Commercial push notifications. Simpler than ntfy if you do not want to host anything.", 0, "play", "net.superblock.pushover", "paid", [], ""),
 ("telegram", "Telegram", "Client-driven. Keep it if your clients use it.", 0, "play", "org.telegram.messenger", "free", [], "Not in the main F-Droid repo."),
],

# ----------------------------------------------------------------- socialeng
"socialeng": [
 ("trust-me-bro", "Trust Me Bro", "Pretext soundboard. First-party androidWTF tooling.", 0, "own", "trust-me-bro", "free", [], ""),
 ("pentest-reference", "Pentest Reference", "Offline command and methodology reference. First-party androidWTF tooling.", 0, "own", "pentest-reference", "free", [], ""),
 ("spoofcard", "SpoofCard", "Caller ID spoofing. The US Truth in Caller ID Act makes spoofing with intent to defraud or harm illegal, and the TRACED Act raised the penalties.", 0, "play", "com.spoofcard.app", "paid", ["legal"], "Requires written client authorisation naming caller ID spoofing as an in-scope technique. Most consumer spoofing services have also shut down or restricted signups."),
 ("hacker-tracker", "Hacker Tracker", "DEF CON conference companion. Not a tool, but it is always on the phone anyway.", 0, "play", "com.shortstack.hackertracker", "free", [], ""),
],

# ---------------------------------------------------------------- automation
"automation": [
 ("tasker", "Tasker", "Combined with Termux:Tasker this is how field workflows get built — trigger a script on arriving at a location, on a WiFi join, on a notification.", 0, "play", "net.dinglisch.android.taskerm", "paid", [E], ""),
 ("macrodroid", "MacroDroid", "Friendlier automation with a gentler learning curve. Less powerful than Tasker.", 0, "play", "com.arlosoft.macrodroid", "freemium", [], ""),
 ("automate", "Automate", "Flowchart-based automation. The third option, and the most visual.", 0, "play", "com.llamalab.automate", "freemium", [], ""),
 ("home-assistant", "Home Assistant", "Companion app, and a surprisingly good generic sensor and webhook source for automations.", 0, "fdroid", "io.homeassistant.companion.android.minimal", "free", [], "The F-Droid build is the 'minimal' flavour, which drops the Play Services dependencies."),
],

# ----------------------------------------------------------------- reference
"reference": [
 ("hacktricks", "HackTricks", "The single most useful practical reference. Mirror it offline — site work rarely has signal.", 0, "web", "https://book.hacktricks.wiki", "free", [E], ""),
 ("owasp-mastg", "OWASP MASTG / MASVS", "The mobile testing standard. Directly relevant to everything in the Mobile App Assessment category.", 0, "web", "https://mas.owasp.org", "free", [E], ""),
 ("owasp-wstg", "OWASP WSTG / ASVS", "The web testing standard, and the verification requirements to test against.", 0, "web", "https://owasp.org/www-project-web-security-testing-guide/", "free", [], ""),
 ("payloads", "PayloadsAllTheThings", "Payload and technique reference by injection class.", 0, "web", "https://github.com/swisskyrepo/PayloadsAllTheThings", "free", [E], ""),
 ("gtfobins", "GTFOBins / LOLBAS", "Living-off-the-land binaries for Unix and Windows.", 0, "web", "https://gtfobins.github.io", "free", [], ""),
 ("attack", "MITRE ATT&CK for Mobile", "Technique taxonomy, and the vocabulary clients expect findings mapped to.", 0, "web", "https://attack.mitre.org/matrices/mobile/", "free", [], ""),
 ("nist-800-115", "NIST SP 800-115", "Technical guide to information security testing. The methodology citation for a report.", 0, "web", "https://csrc.nist.gov/pubs/sp/800/115/final", "free", [], ""),
 ("seclists", "SecLists", "Wordlists. Mirror them locally — you will not want to download these on a client site.", 0, "termux", "https://github.com/danielmiessler/SecLists", "free", [E], "", "git"),
 ("searchsploit", "Exploit-DB / searchsploit", "Offline exploit database with local search.", 0, "termux", "https://gitlab.com/exploit-database/exploitdb", "free", [], "", "git"),
 ("koreader", "KOReader", "Document reader for the offline reference pack. Handles PDF, EPUB and HTML.", 0, "fdroid", "org.koreader.launcher.fdroid", "free", [], ""),
 ("librera", "Librera Reader", "The alternative reader, better on large PDFs.", 0, "fdroid", "com.foobnix.pro.pdf.reader", "free", [], ""),
],
}


def build():
    cat_label = {c[0]: c[1] for c in CATEGORIES}
    cat_sec = {c[0]: c[2] for c in CATEGORIES}
    tools, counts = [], {}

    for slug, rows in TOOLS.items():
        if slug not in cat_label:
            sys.exit(f"unknown category: {slug}")
        for row in rows:
            (tid, name, desc, tier, source, package, lic, flags, notes) = row[:9]
            method = row[9] if len(row) > 9 else ("pkg" if source == "termux" else "")
            tools.append({
                "id": tid,
                "name": name,
                "description": desc,
                "category": slug,
                "categoryLabel": cat_label[slug],
                "isSecurity": cat_sec[slug],
                "tier": tier,
                "source": source,
                "package": package,
                "method": method,
                "license": lic,
                "flags": list(flags),
                "notes": notes,
                "unverified": True,
            })
            counts[slug] = counts.get(slug, 0) + 1

    ids = [t["id"] for t in tools]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        sys.exit(f"duplicate ids: {sorted(dupes)}")

    return {
        "generated": "scripts/build_catalogue.py",
        "categories": [
            {"slug": s, "label": l, "security": sec, "count": counts.get(s, 0)}
            for (s, l, sec) in CATEGORIES if counts.get(s)
        ],
        "tools": tools,
    }


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "data/tools.json")
    data = build()
    out.write_text(json.dumps(data, indent=1) + "\n")
    print(f"{len(data['tools'])} tools across {len(data['categories'])} categories -> {out}")
