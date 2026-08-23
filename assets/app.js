// androidWTF catalogue.
//
// Same shape as the macWTF site: no build step, Preact and htm vendored in
// assets/vendor and resolved by an import map, so this is a static folder that
// serves from GitHub Pages and contacts no third party.
//
// The one structural difference is the tier. macWTF's organising axis is which
// package manager installs a thing. Android's is whether the device can run it
// at all, so tier is a first-class field: it colours every card, it is its own
// filter, and it decides which of the four install methods you are offered.

import { h, render } from "preact";
import { useState, useMemo, useEffect, useCallback } from "preact/hooks";
import htm from "htm";

const html = htm.bind(h);

// ------------------------------------------------------------------- meta

const TIERS = [
  { n: 0, key: "t0", name: "Stock",     req: "Any Android 10+ device",
    blurb: "No unlock, no root, nothing voided. Termux, the whole app catalogue, unprivileged scanning, capture over the VPN service, NFC, BLE, OTG serial." },
  { n: 1, key: "t1", name: "Shizuku",   req: "ADB pairing over wireless debugging",
    blurb: "ADB-level privileges with no root and, on Android 11+, no PC. Debloat, AppOps, package control, on-device dumpsys." },
  { n: 2, key: "t2", name: "Root",      req: "Magisk or KernelSU",
    blurb: "Raw sockets, privileged ports, Frida, real tcpdump, LSPosed and SSL unpinning. Also where Play Integrity stops working." },
  { n: 3, key: "t3", name: "NetHunter", req: "Supported device + NetHunter kernel",
    blurb: "Monitor mode, packet injection, HID attacks, external adapter drivers. The tier that can brick a phone — read the warnings." },
];
const TIER = Object.fromEntries(TIERS.map(t => [t.n, t]));

const SOURCE = {
  termux:    { label: "termux",    kind: "termux", name: "Termux package" },
  fdroid:    { label: "f-droid",   kind: "obtainium", name: "F-Droid" },
  github:    { label: "github",    kind: "obtainium", name: "GitHub Releases" },
  play:      { label: "play",      kind: "manual", name: "Play Store" },
  nethunter: { label: "nethunter", kind: "manual", name: "NetHunter Store" },
  own:       { label: "androidwtf",kind: "manual", name: "First-party" },
  builtin:   { label: "built-in",  kind: "none",   name: "Already on the device" },
  web:       { label: "web",       kind: "none",   name: "Web resource" },
};

const FLAG_LABEL = {
  essential: "ESSENTIAL", legal: "LEGAL", integrity: "INTEGRITY",
  exthw: "EXTERNAL HW", gated: "GATED", gpl: "GPL",
};
const FLAG_HELP = {
  essential: "The catalogue is meaningfully worse without this one.",
  legal: "Carries a legal warning. Authorised engagements only, with the technique named in the scope document.",
  integrity: "Trips Play Integrity. Banking, payment and MDM-enrolled apps will stop working on this device.",
  exthw: "Needs external hardware over USB OTG or BLE. The app alone does nothing.",
  gated: "Distributed by an unverified developer, so under Android's developer verification rules this may need the advanced sideload flow.",
  gpl: "GPL licensing that matters if you vendor the code rather than shelling out to its installer.",
};

// F-Droid and GitHub apps are the two sources Obtainium can track. Everything
// else is a link and a manual tap, and the UI should say so rather than
// generating a command that quietly does nothing.
const url = t => {
  switch (t.source) {
    case "fdroid": return `https://f-droid.org/packages/${t.package}`;
    case "github": return `https://github.com/${t.package}`;
    case "play":   return `https://play.google.com/store/apps/details?id=${t.package}`;
    case "web":    return t.package;
    default:       return "";
  }
};

// Most of the interesting Termux tooling is not an apt package, so the shell
// entries carry an install method and each one gets its real command. Emitting
// "pkg install nuclei" for all of them would be a copy-paste line that fails.
const METHOD = {
  pkg: p => `pkg install -y ${p}`,
  pip: p => `pip install ${p}`,
  go:  p => `go install ${p}@latest`,
  npm: p => `npm install -g ${p}`,
  git: p => `git clone --depth 1 ${p}`,
};
const METHOD_LABEL = {
  pkg: "Termux packages", pip: "Python (pip)", go: "Go modules",
  npm: "npm", git: "Clone and build",
};
const METHOD_ORDER = ["pkg", "pip", "go", "npm", "git"];
const shellCmd = t => (METHOD[t.method] || METHOD.pkg)(t.package);

const STORE = "androidwtf.packs";
const loadSaved = () => { try { return JSON.parse(localStorage.getItem(STORE) || "[]"); } catch { return []; } };
const storeSaved = v => { try { localStorage.setItem(STORE, JSON.stringify(v)); } catch {} };
const shareURL = (name, ids) =>
  `${location.origin}${location.pathname}#/share/${encodeURIComponent(name)}~${ids.join(",")}`;

const toggleIn = (list, v) => list.includes(v) ? list.filter(x => x !== v) : [...list, v];

// ---------------------------------------------------------------- routing

function useRoute() {
  const parse = () => {
    const raw = location.hash.replace(/^#\/?/, "");
    const [name, arg] = raw.split("/");
    return { name: name || "home", arg: arg ? decodeURIComponent(arg) : "" };
  };
  const [route, setRoute] = useState(parse);
  useEffect(() => {
    const on = () => { setRoute(parse()); window.scrollTo(0, 0); };
    addEventListener("hashchange", on);
    return () => removeEventListener("hashchange", on);
  }, []);
  return route;
}

// ------------------------------------------------------------- components

function Copyable({ text }) {
  const [done, setDone] = useState(false);
  return html`
    <div>
      <pre class="cmd">${text}</pre>
      <button class="copy" onClick=${() => {
        navigator.clipboard?.writeText(text).then(() => {
          setDone(true); setTimeout(() => setDone(false), 1200);
        });
      }}>${done ? "copied" : "copy"}</button>
    </div>`;
}

function FilterGroup({ label, options, active, onToggle }) {
  return html`
    <div class="fgroup">
      <div class="flabel">${label}</div>
      <div class="frow">
        ${options.map(o => {
          const [val, text] = Array.isArray(o) ? o : [o, o];
          return html`<button class="chip ${active.includes(val) ? "on" : ""}" key=${val}
                              onClick=${() => onToggle(val)}>${text}</button>`;
        })}
      </div>
    </div>`;
}

function Nav({ route }) {
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [route.name, route.arg]);

  const links = html`
    <a href="#/" class=${route.name === "home" ? "on" : ""}>Home</a>
    <a href="#/tools" class=${route.name === "tools" ? "on" : ""}>Tools</a>
    <a href="#/packs" class=${route.name === "packs" || route.name === "pack" ? "on" : ""}>Packs</a>
    <a href="#/tiers" class=${route.name === "tiers" ? "on" : ""}>Tiers</a>
    <a href="https://github.com/naturalstate/androidWTF_website">GitHub</a>`;

  return html`
    <nav class="top">
      <div class="nav-inner">
        <a class="brand" href="#/"><span class="mark">a</span> androidWTF</a>
        <div class="nav-links">${links}</div>
        <div class="nav-right"><a class="btn sm" href="#/tools">Browse tools</a></div>
        <button class="burger ${open ? "open" : ""}" aria-label="Menu"
                aria-expanded=${String(open)} onClick=${() => setOpen(!open)}>
          <span></span><span></span><span></span>
        </button>
      </div>
      <div class="drawer ${open ? "open" : ""}">${links}</div>
    </nav>`;
}

// packTools resolves a pack definition to the tools it contains. A pack can
// select by curated id list, by category, by maximum tier, or by source.
// Selectors union together: categories, sources, an exact tier, and an explicit
// id list. maxTier is different — it narrows whatever the selectors produced.
// Keeping the two apart matters: "the labs and servers a stock phone can run"
// is a category selection narrowed to Tier 0, not a category selection plus
// every Tier 0 tool in the catalogue.
function packTools(data, pack) {
  const byId = Object.fromEntries(data.tools.map(t => [t.id, t]));
  const ids = new Set();
  const selects = pack.categories || pack.sources || pack.tools || pack.tier !== undefined;

  if (!selects) data.tools.forEach(t => ids.add(t.id));
  (pack.categories || []).forEach(c =>
    data.tools.filter(t => t.category === c).forEach(t => ids.add(t.id)));
  (pack.sources || []).forEach(s =>
    data.tools.filter(t => t.source === s).forEach(t => ids.add(t.id)));
  if (pack.tier !== undefined)
    data.tools.filter(t => t.tier === pack.tier).forEach(t => ids.add(t.id));
  (pack.tools || []).forEach(i => ids.add(i));

  let out = [...ids].map(i => byId[i]).filter(Boolean);
  if (pack.maxTier !== undefined) out = out.filter(t => t.tier <= pack.maxTier);
  return out;
}

function PackGrid({ data, packs }) {
  return html`
    <div class="packs">
      ${packs.featured.map(p => html`
        <a class="pack" key=${p.id} href=${`#/pack/${p.id}`} style=${`--pack:${p.accent}`}>
          <span class="glyph">${p.glyph}</span>
          <div class="tagline">${p.tagline}</div>
          <h3>${p.name}</h3>
          <p>${p.blurb}</p>
          <div class="foot"><span class="n">${packTools(data, p).length} tools</span> · view pack</div>
        </a>`)}
    </div>`;
}

function TierLadder({ data, linkTo }) {
  const total = data.tools.length;
  return html`
    <div class="tiers">
      ${TIERS.map(t => {
        const adds = data.tools.filter(x => x.tier === t.n).length;
        const reach = data.tools.filter(x => x.tier <= t.n).length;
        return html`
          <a class="tierbox" key=${t.n} style=${`--tc:var(--${t.key})`}
             href=${linkTo ? `#/tools/t${t.n}` : "#/tiers"}>
            <div class="tno">Tier ${t.n}</div>
            <h3>${t.name}</h3>
            <div class="req">${t.req}</div>
            <p>${t.blurb}</p>
            <div class="adds">
              ${t.n === 0 ? `${adds} tools run here` : `+${adds} more`}
              <em> · ${reach} of ${total} total</em>
            </div>
          </a>`;
      })}
    </div>`;
}

// ------------------------------------------------------------------- home

const BOOTSTRAP = "curl -fsSL https://raw.githubusercontent.com/naturalstate/androidWTF/main/wtf.sh | bash";

function Home({ data, packs }) {
  const t0 = data.tools.filter(t => t.tier === 0).length;
  const termux = data.tools.filter(t => t.source === "termux").length;

  return html`
    <div class="wrap">
      <header class="hero">
        <span class="stamp">Android 10+ · root optional</span>
        <h1>Your old phone is a lab you <span class="zing">already own</span>.</h1>
        <p class="sub">
          ${data.tools.length} curated tools for pentesting, RF and InfoSec on Android —
          each one labelled with what your phone actually needs to run it, so you find out
          before you install rather than halfway through an engagement.
        </p>
        <div class="cta">
          <a class="btn" href="#/packs">Browse packs</a>
          <a class="btn ghost" href="#/tools">All ${data.tools.length} tools</a>
          <a class="btn ghost" href="#/tiers">Will it work on my phone?</a>
        </div>
        <div class="install-line soon" style="margin-top:26px;max-width:700px">
          <span>${BOOTSTRAP}</span>
          <b class="soon-tag">not published yet</b>
        </div>
        <p class="hero-note">
          The one-line bootstrap is still being built. Everything in the catalogue
          below works today — browse it and take the install steps directly.
        </p>
        <div class="stats">
          <div class="stat"><b>${data.tools.length}</b><span>tools</span></div>
          <div class="stat"><b>${t0}</b><span>need no root</span></div>
          <div class="stat"><b>${termux}</b><span>termux packages</span></div>
          <div class="stat"><b>${data.categories.length}</b><span>categories</span></div>
        </div>
      </header>

      <section id="tiers">
        <div class="sec-head">
          <h2>Will this work on <span class="zing">my phone</span>?</h2>
          <p>Four tiers. Each one is a gate on the next, and every tool says which it needs.</p>
        </div>
        <${TierLadder} data=${data} linkTo=${true} />
      </section>

      <section>
        <div class="sec-head">
          <h2>Start with a <span class="zing">pack</span></h2>
          <p>Curated sets. Take one whole, or open it and pick.</p>
        </div>
        <${PackGrid} data=${data} packs=${packs} />
      </section>

      <section>
        <div class="sec-head"><h2>Why not just a <span class="zing">list of APKs</span>?</h2></div>
        <div class="packs">
          <div class="pack" style="--pack:var(--t2)">
            <span class="glyph">⌬</span>
            <h3>Most of it silently does not work</h3>
            <p>Half the classic Android hacking tools need raw sockets, privileged ports or
               monitor mode, and a stock phone has none of those. They install perfectly and
               then do nothing. Every entry here is tagged with what it actually requires.</p>
          </div>
          <div class="pack" style="--pack:var(--pink)">
            <span class="glyph">⟳</span>
            <h3>Seventy sideloaded APKs do not update themselves</h3>
            <p>This is what kills these projects in six months. The catalogue exports an
               Obtainium config, so anything from F-Droid or GitHub Releases keeps itself
               current without you touching it again.</p>
          </div>
          <div class="pack" style="--pack:var(--purple)">
            <span class="glyph">⛨</span>
            <h3>Google is closing the door</h3>
            <p>Developer verification lands in four markets in September 2026 and globally in
               2027. Termux packages are not APKs and are not affected at all — which is why
               ${termux} of these tools live in the shell rather than the launcher.</p>
          </div>
        </div>
      </section>

      <section>
        <div class="sec-head">
          <h2>One catalogue, <span class="zing">four platforms</span></h2>
          <p>Each tool is described once. Only the install method differs.</p>
        </div>
        <div class="platforms">
          <a class="plat live" href="https://naturalstate.github.io/macwtf_website/">
            <b>macOS</b><span>available now →</span></a>
          <div class="plat"><b>Kali</b><span>coming soon</span></div>
          <div class="plat"><b>Windows</b><span>coming soon</span></div>
          <div class="plat on"><b>Android</b><span>you are here</span></div>
        </div>
      </section>
    </div>`;
}

// ------------------------------------------------------------------ tiers

function Tiers({ data }) {
  return html`
    <div class="wrap">
      <section>
        <div class="sec-head">
          <h2>Capability <span class="zing">tiers</span></h2>
          <p>What your phone can do decides what is worth installing on it.</p>
        </div>
        <${TierLadder} data=${data} linkTo=${true} />
      </section>

      <section style="padding-top:0">
        <div class="sec-head"><h2>Before you climb</h2></div>
        <div class="packs">
          <div class="pack" style="--pack:var(--t1)">
            <span class="glyph">◫</span>
            <div class="tagline">Tier 1 · free</div>
            <h3>Shizuku costs you nothing</h3>
            <p>Pairing over wireless debugging is reversible, voids no warranty, and unlocks
               debloat, AppOps and on-device adb. If you do one thing past stock, do this.
               It has to be re-paired after each reboot unless the device is rooted.</p>
          </div>
          <div class="pack" style="--pack:var(--t2)">
            <span class="glyph">⚠</span>
            <div class="tagline">Tier 2 · irreversible-ish</div>
            <h3>Root breaks your banking apps</h3>
            <p>Play Integrity fails, and banking, payment, ticketing and MDM-enrolled apps
               stop working. Use a dedicated device, or keep the catalogue inside a Shelter
               work profile you can freeze between engagements.</p>
          </div>
          <div class="pack" style="--pack:var(--t3)">
            <span class="glyph">▲</span>
            <div class="tagline">Tier 3 · can brick</div>
            <h3>NetHunter kernels are device-specific</h3>
            <p>Unlocking the bootloader is irreversible on many devices, and blows the Knox
               fuse on Samsung. Flashing the wrong kernel bootloops the phone. Check the
               supported device list first, and never do this to a phone you need.</p>
          </div>
          <div class="pack" style="--pack:var(--orange)">
            <span class="glyph">⇄</span>
            <div class="tagline">Any tier</div>
            <h3>Monitor mode needs an adapter anyway</h3>
            <p>Internal Android WiFi chipsets do not do monitor mode, NetHunter kernel or not.
               In practice Tier 3 means an external adapter over OTG — an Alfa AWUS036ACM or
               AWUS036NHA, or a Panda PAU09.</p>
          </div>
        </div>
      </section>

      <section style="padding-top:0">
        <div class="sec-head"><h2>Developer verification</h2></div>
        <div class="banner" style="max-width:80ch">
          Google's developer verification requirement reaches Brazil, Indonesia, Singapore and
          Thailand on 30 September 2026, and goes global during 2027. Apps from unverified
          developers will need the advanced sideload flow: a one-time confirmation, a reboot,
          and a 24-hour wait, after which you can allow them indefinitely.
          <br/><br/>
          It does not affect Termux packages at all, and it does not affect installs over adb.
          Those are the two paths androidWTF leans on.
        </div>
      </section>
    </div>`;
}

// ------------------------------------------------------------------ packs

function Packs({ data, packs }) {
  const [saved, setSaved] = useState(loadSaved);
  const remove = id => { const next = loadSaved().filter(p => p.id !== id); storeSaved(next); setSaved(next); };

  return html`
    <div class="wrap">
      <section>
        <div class="sec-head">
          <h2>Your <span class="zing">packs</span></h2>
          <p>Built from your own selection. Stored in this browser only.</p>
        </div>
        <div class="packs" style="margin-bottom:18px">
          <a class="pack" href="#/tools" style="--pack:var(--sky)">
            <span class="glyph">✛</span>
            <div class="tagline">Start from scratch</div>
            <h3>Build a pack</h3>
            <p>Browse all ${data.tools.length} tools, filter to the tier your phone is on,
               press + on what you want, then save it.</p>
            <div class="foot"><span class="n">Open the catalogue</span></div>
          </a>
        </div>
        ${saved.length === 0
          ? html`<div class="note" style="margin:0">Nothing saved yet — anything you build will appear here.</div>`
          : html`<div class="packs">
              ${saved.map(p => html`
                <div class="pack" key=${p.id} style="--pack:var(--accent)">
                  <span class="glyph">◆</span>
                  <div class="tagline">Your pack</div>
                  <h3>${p.name}</h3>
                  <p>${p.tools.length} tools, saved in this browser.</p>
                  <div class="foot" style="gap:14px">
                    <a href=${`#/pack/${p.id}`} class="n">Open</a>
                    <a href="#" onClick=${e => {
                      e.preventDefault();
                      navigator.clipboard?.writeText(shareURL(p.name, p.tools));
                      e.target.textContent = "link copied";
                      setTimeout(() => (e.target.textContent = "Share"), 1400);
                    }}>Share</a>
                    <a href="#" onClick=${e => { e.preventDefault(); remove(p.id); }} style="color:var(--dim)">Delete</a>
                  </div>
                </div>`)}
            </div>`}
      </section>

      <section>
        <div class="sec-head">
          <h2>Curated packs</h2>
          <p>Open one to see what is inside, then edit it and save your own.</p>
        </div>
        <${PackGrid} data=${data} packs=${packs} />
      </section>
    </div>`;
}

// ------------------------------------------------------------ tool detail

function Detail({ tool, picked, onToggle, onClose }) {
  if (!tool) return null;
  const t = TIER[tool.tier], src = SOURCE[tool.source], link = url(tool);
  return html`
    <div class="scrim" onClick=${onClose}>
      <div class="modal" onClick=${e => e.stopPropagation()}>
        <div class="modal-head">
          <h2>${tool.name}</h2>
          <span class="tier" style=${`--tc:var(--${t.key})`}>T${t.n} ${t.name}</span>
          <span class="src">${src.label}</span>
          <button class="x" onClick=${onClose}>✕</button>
        </div>
        <div class="modal-body">
          <p style="margin-top:0;color:#c2cec7">${tool.description}</p>
          <dl class="kv">
            <dt>Category</dt><dd>${tool.categoryLabel}</dd>
            <dt>Needs</dt><dd>Tier ${t.n} — ${t.req}</dd>
            <dt>Source</dt><dd>${src.name}</dd>
            <dt>License</dt><dd>${tool.license}</dd>
            ${link && html`<dt>Link</dt><dd><a href=${link} target="_blank" rel="noopener">${link.replace(/^https?:\/\//, "")}</a></dd>`}
          </dl>

          ${tool.flags.map(f => html`
            <div class=${`note ${f === "legal" ? "bad" : f === "integrity" ? "warn" : ""}`} key=${f}>
              <b style="color:var(--ink)">${FLAG_LABEL[f]}</b> — ${FLAG_HELP[f]}
            </div>`)}
          ${tool.notes && html`<div class="note">${tool.notes}</div>`}

          <h4 style="margin:20px 0 9px;font:700 10.5px var(--mono);letter-spacing:.13em;text-transform:uppercase;color:var(--dim)">
            How to install</h4>
          ${src.kind === "termux"
            ? html`<${Copyable} text=${shellCmd(tool)} />
                   ${tool.method !== "pkg" && html`<div class="note">Not an apt package —
                     this is a ${METHOD_LABEL[tool.method].toLowerCase()} install inside Termux.</div>`}`
            : src.kind === "obtainium"
            ? html`<${Copyable} text=${link} />
                   <div class="note">Add this URL in Obtainium, or import the whole pack's config at once from the selection sheet.</div>`
            : src.kind === "manual"
            ? html`<div class="note" style="margin-top:0">
                     ${src.name}${link ? html` — <a href=${link} target="_blank" rel="noopener">open</a>` : ""}.
                     Obtainium cannot track this source, so it is a manual install and a manual update.
                   </div>`
            : html`<div class="note" style="margin-top:0">Nothing to install — this is a workflow, not an app. See the notes above.</div>`}

        </div>
        <div class="modal-head" style="border-top:1px solid var(--line);border-bottom:0">
          <button class=${picked ? "btn ghost sm" : "btn sm"} onClick=${() => onToggle(tool.id)}>
            ${picked ? "Remove from pack" : "Add to pack"}
          </button>
          <button class="btn ghost sm" style="margin-left:auto" onClick=${onClose}>Close</button>
        </div>
      </div>
    </div>`;
}

function Card({ tool, picked, onToggle, onOpen }) {
  const t = TIER[tool.tier];
  const shown = [...tool.flags];
  if (tool.license === "paid") shown.push("paid");
  return html`
    <div class="card ${picked ? "picked" : ""}" style=${`--tc:var(--${t.key})`} onClick=${() => onOpen(tool)}>
      <button class="add ${picked ? "on" : ""}"
              title=${picked ? "Remove from pack" : "Add to pack"}
              aria-label=${picked ? "Remove from pack" : "Add to pack"}
              onClick=${e => { e.stopPropagation(); onToggle(tool.id); }}>
        ${picked ? "✓" : "+"}
      </button>
      <div class="card-top">
        <span class="tier" style=${`--tc:var(--${t.key})`}>T${t.n}</span>
        <h3 title=${tool.name}>${tool.name}</h3>
      </div>
      <p>${tool.description}</p>
      ${shown.length > 0 && html`
        <div class="flags">
          ${shown.map(f => html`<span class="flag ${f}" key=${f} title=${FLAG_HELP[f] || ""}>
            ${FLAG_LABEL[f] || f.toUpperCase()}</span>`)}
        </div>`}
      <div class="cat-note">${tool.categoryLabel} · ${SOURCE[tool.source].label}</div>
    </div>`;
}

// ------------------------------------------------------- selection output

// Four outputs, because Android has four genuinely different install paths and
// pretending otherwise is how you end up with a script that fails silently.
function CommandsModal({ tools, onClose, onClear }) {
  const [tab, setTab] = useState("obtainium");

  const byKind = useMemo(() => {
    const m = { termux: [], obtainium: [], manual: [], none: [] };
    for (const t of tools) m[SOURCE[t.source].kind].push(t);
    return m;
  }, [tools]);

  const obtainiumJSON = useMemo(() => JSON.stringify({
    apps: byKind.obtainium.map(t => ({
      id: t.source === "fdroid" ? t.package : t.id,
      url: url(t),
      author: t.source === "fdroid" ? "F-Droid" : t.package.split("/")[0],
      name: t.name,
      preferredApkIndex: 0,
      additionalSettings: JSON.stringify({ versionExtractionRegEx: "", trackOnly: false }),
      overrideSource: t.source === "fdroid" ? "FDroid" : "GitHub",
    })),
  }, null, 1), [byKind]);

  const termuxCmd = useMemo(() => {
    const list = byKind.termux;
    if (!list.length) return "# nothing from Termux in this selection";
    const by = {};
    for (const t of list) (by[t.method] ||= []).push(t);
    const out = ["# Run inside Termux.", "pkg update", ""];
    for (const m of METHOD_ORDER) {
      const group = by[m];
      if (!group) continue;
      out.push(`# ${METHOD_LABEL[m]} (${group.length})`);
      if (m === "pkg") {
        const names = [...new Set(group.flatMap(t => t.package.split(/\s+/)))];
        // juice-shop lives in the TUR user repo, which has to be added first.
        if (names.includes("juice-shop")) out.push("pkg install -y tur-repo");
        out.push(`pkg install -y ${names.join(" ")}`);
      } else {
        if (m === "pip") out.push("pkg install -y python");
        if (m === "go")  out.push("pkg install -y golang");
        if (m === "git") out.push("pkg install -y git");
        group.forEach(t => out.push(shellCmd(t)));
      }
      out.push("");
    }
    return out.join("\n");
  }, [byKind]);

  const adbScript = useMemo(() => {
    const lines = [
      "#!/usr/bin/env bash",
      "# androidWTF — install a pack over adb from a laptop.",
      "# Pair first:  adb pair <phone-ip>:<port>   then   adb connect <phone-ip>:<port>",
      "# APKs are not redistributed here; drop them in ./apks first.",
      "set -euo pipefail",
      "",
      "adb wait-for-device",
      'test -d ./apks || { echo "put the APKs in ./apks"; exit 1; }',
      "",
      "for apk in ./apks/*.apk; do",
      '  echo "==> $apk"',
      '  adb install -r -g "$apk"',
      "done",
      "",
      "# Expected in ./apks for this selection:",
      ...byKind.obtainium.map(t => `#   ${t.name.padEnd(28)} ${url(t)}`),
    ];
    return lines.join("\n");
  }, [byKind]);

  const manualList = useMemo(() => byKind.manual.map(t =>
    `${t.name}\n  ${SOURCE[t.source].name}${url(t) ? ` — ${url(t)}` : ""}`).join("\n\n")
    || "# nothing manual in this selection", [byKind]);

  const attention = tools.filter(t => t.flags.length > 0);
  const maxTier = tools.reduce((m, t) => Math.max(m, t.tier), 0);

  const TABS = [
    ["obtainium", `Obtainium · ${byKind.obtainium.length}`],
    ["termux",    `Termux · ${byKind.termux.length}`],
    ["manual",    `Manual · ${byKind.manual.length}`],
    ["adb",       "adb script"],
  ];

  return html`
    <div class="scrim" onClick=${onClose}>
      <div class="modal" onClick=${e => e.stopPropagation()}>
        <div class="modal-head">
          <h2>Your selection</h2>
          <span class="tier" style=${`--tc:var(--${TIER[maxTier].key})`}>needs T${maxTier}</span>
          <span class="src">${tools.length} tools</span>
          <button class="x" onClick=${onClose}>✕</button>
        </div>
        <div class="modal-body">
          <div class="banner good">
            This selection needs a <b>Tier ${maxTier}</b> device at most${maxTier > 0
              ? html` — ${TIER[maxTier].req.toLowerCase()}.` : "."}
            ${byKind.termux.length > 0 && html` ${byKind.termux.length} of them are Termux
              packages, which developer verification does not touch.`}
          </div>

          ${attention.length > 0 && html`
            <div class="pack-group">
              <h4>${attention.length} carry a warning</h4>
              ${attention.slice(0, 8).map(t => html`
                <div class="note" key=${t.id}>
                  <b style="color:var(--ink)">${t.name}</b> — ${t.flags.map(f => FLAG_HELP[f]).join(" ")}
                </div>`)}
              ${attention.length > 8 && html`<div class="note">… and ${attention.length - 8} more</div>`}
            </div>`}

          <div class="tabs">
            ${TABS.map(([k, label]) => html`
              <button key=${k} class=${tab === k ? "on" : ""} onClick=${() => setTab(k)}>${label}</button>`)}
          </div>

          ${tab === "obtainium" && html`
            <div class="pack-group">
              <h4>Obtainium import · ${byKind.obtainium.length} apps</h4>
              <${Copyable} text=${obtainiumJSON} />
              <div class="note">Save as a .json file, then Obtainium → Import/Export → Obtainium import.
                Everything in here updates itself from then on.</div>
            </div>`}

          ${tab === "termux" && html`
            <div class="pack-group">
              <h4>Termux · ${byKind.termux.length} packages</h4>
              <${Copyable} text=${termuxCmd} />
              <div class="note">Run inside Termux. No root, no APK, and nothing Google's
                developer verification applies to.</div>
              <div class="note">Only some of these are apt packages. The rest are pip, Go or
                clone-and-build installs, and each is grouped under the command it actually
                needs.</div>
            </div>`}

          ${tab === "manual" && html`
            <div class="pack-group">
              <h4>Manual · ${byKind.manual.length} apps</h4>
              <${Copyable} text=${manualList} />
              <div class="note">Play Store, NetHunter Store and first-party apps. Obtainium
                cannot track these, so they update the ordinary way.</div>
            </div>`}

          ${tab === "adb" && html`
            <div class="pack-group">
              <h4>Install over adb from a laptop</h4>
              <${Copyable} text=${adbScript} />
              <div class="note">The fastest path: pair once over wireless debugging and install
                the whole pack with no per-app taps and no advanced sideload flow. The same
                pairing is what Shizuku needs anyway.</div>
            </div>`}

          ${byKind.none.length > 0 && html`
            <div class="pack-group">
              <h4>${byKind.none.length} need no install</h4>
              <div class="note" style="margin-top:0">
                ${byKind.none.map(t => t.name).join(" · ")} — workflows and references rather
                than apps. Open each one for the steps.
              </div>
            </div>`}
        </div>
        <div class="modal-head" style="border-top:1px solid var(--line);border-bottom:0">
          <button class="btn ghost sm" onClick=${onClear}>Clear</button>
          <button class="btn sm" style="margin-left:auto" onClick=${onClose}>Done</button>
        </div>
      </div>
    </div>`;
}

// -------------------------------------------------------------- catalogue

function Tools({ data, packs, initialPack, shared, initialTier }) {
  const all = data.tools;
  const [q, setQ] = useState("");
  const [cat, setCat] = useState(null);
  const [tier, setTier] = useState(initialTier ?? null);   // maximum tier shown
  const [sources, setSources] = useState([]);
  const [flags, setFlags] = useState([]);
  const [licenses, setLicenses] = useState([]);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [picked, setPicked] = useState(() => new Set());
  const [detail, setDetail] = useState(null);
  const [showCmds, setShowCmds] = useState(false);
  const [catsOpen, setCatsOpen] = useState(false);
  const [scope, setScope] = useState(null);

  useEffect(() => { setTier(initialTier ?? null); }, [initialTier]);

  useEffect(() => {
    if (shared) { setPicked(new Set(shared.ids)); setScope(new Set(shared.ids)); return; }
    if (!initialPack) { setScope(null); return; }
    const p = packs.featured.find(x => x.id === initialPack) || loadSaved().find(x => x.id === initialPack);
    if (!p) return;
    const ids = p.custom ? p.tools : packTools(data, p).map(t => t.id);
    setPicked(new Set(ids));
    setScope(new Set(ids));
  }, [initialPack, shared]);

  const groups = useMemo(() => {
    const general = [], security = [];
    for (const c of data.categories) (c.security ? security : general).push(c);
    return [["", general], ["Security", security]].filter(([, l]) => l.length);
  }, [data]);

  const shown = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return all.filter(t => {
      if (scope && !scope.has(t.id)) return false;
      if (tier !== null && t.tier > tier) return false;
      if (cat && t.category !== cat) return false;
      if (sources.length && !sources.includes(t.source)) return false;
      if (flags.length && !flags.every(f => t.flags.includes(f))) return false;
      if (licenses.length && !licenses.includes(t.license)) return false;
      if (!needle) return true;
      return `${t.name} ${t.description} ${t.categoryLabel} ${t.source} ${t.package} ${t.notes}`
        .toLowerCase().includes(needle);
    });
  }, [all, q, cat, tier, sources, flags, licenses, scope]);

  const toggle = useCallback(id => setPicked(prev => {
    const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n;
  }), []);

  useEffect(() => {
    const onKey = e => {
      if (e.key === "/" && document.activeElement?.tagName !== "INPUT") {
        e.preventDefault(); document.getElementById("q")?.focus();
      }
      if (e.key === "Escape") { setDetail(null); setShowCmds(false); }
    };
    addEventListener("keydown", onKey);
    return () => removeEventListener("keydown", onKey);
  }, []);

  const sourceOptions = useMemo(() => {
    const counts = {};
    for (const t of all) counts[t.source] = (counts[t.source] || 0) + 1;
    return Object.entries(counts).sort((a, b) => b[1] - a[1])
      .map(([s, n]) => [s, `${SOURCE[s].label} ${n}`]);
  }, [all]);

  const activeCount = sources.length + flags.length + licenses.length + (cat ? 1 : 0);
  const pickedTools = all.filter(t => picked.has(t.id));
  const activePack = initialPack
    ? packs.featured.find(p => p.id === initialPack) || loadSaved().find(p => p.id === initialPack)
    : null;

  return html`
    <div class="wrap">
      ${scope && html`
        <div class="scope-head">
          <span class="stamp" style=${activePack ? `color:${activePack.accent};border-color:${activePack.accent}` : ""}>
            ${activePack ? activePack.name : (shared ? shared.name : "Selection")}</span>
          ${activePack && html`<p>${activePack.blurb}</p>`}
          <div class="scope-actions">
            <span class="scope-count">${scope.size} tools in this pack</span>
            <button class="btn ghost sm" onClick=${() => setScope(null)}>Browse all ${all.length}</button>
          </div>
        </div>`}

      <div class="tool-layout">
        <aside class="cats ${catsOpen ? "open" : ""}">
          <div class="side-label">Categories</div>
          <button class="cat ${!cat ? "on" : ""}" onClick=${() => setCat(null)}>
            All <span class="n">${all.length}</span></button>
          ${groups.map(([label, list]) => html`
            <div key=${label || "g"}>
              ${label && html`<div class="side-label">${label}</div>`}
              ${list.map(c => html`
                <button class="cat ${cat === c.slug ? "on" : ""}" key=${c.slug}
                        onClick=${() => { setCat(cat === c.slug ? null : c.slug); setCatsOpen(false); }}>
                  <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${c.label}</span>
                  <span class="n">${c.count}</span>
                </button>`)}
            </div>`)}
        </aside>

        <main>
          <div class="toolbar">
            <div class="searchbar">
              <span class="ic">⌕</span>
              <input id="q" value=${q} placeholder=${`Search ${all.length} tools…`}
                     onInput=${e => setQ(e.target.value)} />
            </div>
            <button class="chip cats-toggle" onClick=${() => setCatsOpen(!catsOpen)}>
              ${cat ? data.categories.find(c => c.slug === cat)?.label : "Categories"}
            </button>
            <button class="chip ${filtersOpen || activeCount ? "on" : ""}"
                    onClick=${() => setFiltersOpen(!filtersOpen)}>
              Filters${activeCount ? ` · ${activeCount}` : ""}
            </button>
          </div>

          <div class="toolbar">
            <span class="flabel" style="margin-right:2px">My phone is</span>
            <div class="tierseg">
              ${TIERS.map(t => html`
                <button key=${t.n} style=${`--tc:var(--${t.key})`}
                        class=${tier === t.n ? "on" : ""}
                        title=${t.req}
                        onClick=${() => setTier(tier === t.n ? null : t.n)}>T${t.n}<i>${t.name}</i></button>`)}
              <button style="--tc:var(--muted)" class=${tier === null ? "on" : ""}
                      onClick=${() => setTier(null)}>Show all</button>
            </div>
          </div>

          ${filtersOpen && html`
            <div class="filters">
              <${FilterGroup} label="Source" options=${sourceOptions}
                              active=${sources} onToggle=${v => setSources(toggleIn(sources, v))} />
              <${FilterGroup} label="Warnings"
                              options=${[["essential","Essential"],["legal","Legal"],["integrity","Breaks Integrity"],["exthw","External hardware"],["gpl","GPL"]]}
                              active=${flags} onToggle=${v => setFlags(toggleIn(flags, v))} />
              <${FilterGroup} label="License"
                              options=${[["free","Free"],["freemium","Freemium"],["paid","Paid"]]}
                              active=${licenses} onToggle=${v => setLicenses(toggleIn(licenses, v))} />
              ${activeCount > 0 && html`
                <button class="btn ghost sm" style="align-self:start;margin-top:6px"
                        onClick=${() => { setSources([]); setFlags([]); setLicenses([]); setCat(null); }}>
                  Clear ${activeCount} filter${activeCount === 1 ? "" : "s"}
                </button>`}
            </div>`}

          <div class="resultbar">
            <span><b>${shown.length}</b> ${shown.length === 1 ? "tool" : "tools"}${
              tier !== null ? ` that run at Tier ${tier}` : ""}${
              cat ? ` in ${data.categories.find(c => c.slug === cat)?.label}` : ""}</span>
            ${shown.length > 0 && html`
              <button class="linkish" onClick=${() => setPicked(prev => {
                const n = new Set(prev); shown.forEach(t => n.add(t.id)); return n;
              })}>Select all ${shown.length}</button>`}
            ${shown.some(t => picked.has(t.id)) && html`
              <button class="linkish" onClick=${() => setPicked(prev => {
                const n = new Set(prev); shown.forEach(t => n.delete(t.id)); return n;
              })}>Deselect these</button>`}
            ${picked.size > 0 && html`
              <button class="linkish dim" onClick=${() => setPicked(new Set())}>Clear all (${picked.size})</button>`}
          </div>

          ${shown.length === 0
            ? html`<div class="empty">Nothing matches${q ? ` “${q}”` : " these filters"}.</div>`
            : html`<div class="grid">
                ${shown.map(t => html`
                  <${Card} key=${t.id} tool=${t} picked=${picked.has(t.id)}
                           onToggle=${toggle} onOpen=${setDetail} />`)}
              </div>`}
        </main>
      </div>
    </div>

    ${picked.size > 0 && !showCmds && html`
      <div class="tray">
        <span><b>${picked.size}</b> selected</span>
        <button class="btn ghost sm" onClick=${() => setPicked(new Set())}>Clear</button>
        <button class="btn ghost sm" onClick=${() => {
          const name = prompt("Name this pack:", activePack ? `${activePack.name} (edited)` : "My pack");
          if (!name) return;
          const saved = loadSaved();
          saved.unshift({ id: "u-" + Date.now().toString(36), name, tools: [...picked], custom: true });
          storeSaved(saved);
          location.hash = "#/packs";
        }}>Save as pack</button>
        <button class="btn sm" onClick=${() => setShowCmds(true)}>Get install steps</button>
      </div>`}

    <${Detail} tool=${detail} picked=${detail && picked.has(detail.id)}
               onToggle=${toggle} onClose=${() => setDetail(null)} />
    ${showCmds && html`<${CommandsModal} tools=${pickedTools} onClose=${() => setShowCmds(false)}
                                         onClear=${() => { setPicked(new Set()); setShowCmds(false); }} />`}`;
}

// -------------------------------------------------------------------- app

function App({ data, packs }) {
  const route = useRoute();

  let body;
  switch (route.name) {
    case "tools": {
      const m = /^t([0-3])$/.exec(route.arg);
      body = html`<${Tools} data=${data} packs=${packs} initialTier=${m ? Number(m[1]) : null} />`;
      break;
    }
    case "packs": body = html`<${Packs} data=${data} packs=${packs} />`; break;
    case "tiers": body = html`<${Tiers} data=${data} />`; break;
    case "pack":  body = html`<${Tools} data=${data} packs=${packs} initialPack=${route.arg} />`; break;
    case "share": {
      const [name, ids] = route.arg.split("~");
      body = html`<${Tools} data=${data} packs=${packs}
                            shared=${{ name: name || "Shared pack", ids: (ids || "").split(",").filter(Boolean) }} />`;
      break;
    }
    default: body = html`<${Home} data=${data} packs=${packs} />`;
  }

  return html`
    <div class="dots"></div>
    <div class="blob a"></div><div class="blob b"></div>
    <div class="grain"></div>
    <div class="page">
      <${Nav} route=${route} />
      ${body}
      <footer class="foot">
        <div class="family">
          <a class="fam live" href="https://naturalstate.github.io/macwtf_website/">macWTF <em>live</em></a>
          <span class="soon">KaliWTF <em>soon</em></span>
          <span class="soon">WindowsWTF <em>soon</em></span>
          <span class="here">androidWTF</span>
        </div>
        <p style="margin:18px 0 0">
          Package identifiers verified against F-Droid, GitHub, PyPI, the Go module proxy and the Termux repos ·
          <a href="https://github.com/naturalstate/androidWTF_website">source on GitHub</a>
        </p>
      </footer>
    </div>`;
}

const [data, packs] = await Promise.all([
  fetch("./data/tools.json").then(r => r.json()),
  fetch("./data/packs.json").then(r => r.json()),
]);
render(html`<${App} data=${data} packs=${packs} />`, document.getElementById("app"));
