/* DSJ Dashboard 0.1.2 — native web components, no external runtime or CDN. */
const NAV = [
  ["hoofdpagina", "Home", "mdi:home"], ["ruimtes", "Ruimtes", "mdi:floor-plan"],
  ["media", "Media", "mdi:television-speaker"], ["energie", "Energie", "mdi:lightning-bolt"],
  ["klimaat", "Klimaat", "mdi:thermometer"], ["beveiliging", "Beveiliging", "mdi:security"],
];
const el = (tag, text, cls) => {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (cls) node.className = cls;
  if (["a", "button", "input"].includes(tag) && text) node.setAttribute("aria-label", String(text));
  return node;
};
const icon = (name) => { const i = el("ha-icon"); i.icon = name; i.setAttribute("aria-hidden", "true"); return i; };
const button = (label, fn, cls) => {
  const b = el("button", label, cls); b.type = "button";
  b.setAttribute("aria-label", label || "Bediening");
  b.addEventListener("click", fn); return b;
};
const navigate = (path) => {
  history.pushState(null, "", path);
  window.dispatchEvent(new Event("location-changed"));
};
const helpers = () => window.loadCardHelpers();
const BASE_CSS = `
:host {display:block;color:var(--primary-text-color);font-family:var(--paper-font-body1_-_font-family,Roboto,Arial,sans-serif);}
* {box-sizing:border-box} button,a,input {font:inherit} button,a {touch-action:manipulation}
button {cursor:pointer;color:inherit;background:var(--secondary-background-color,#eee);border:1px solid var(--divider-color,#ddd);border-radius:18px;padding:10px 16px;min-height:44px}
button:focus-visible,a:focus-visible,input:focus-visible {outline:3px solid var(--dsj-accent,#b98c27);outline-offset:3px}
button:disabled {opacity:.55;cursor:wait} a {color:inherit} .muted {color:var(--secondary-text-color);line-height:1.6}
.error {color:var(--error-color,#db4437);padding:14px;border:1px solid currentColor;border-radius:16px}
`;
const PAGE_CSS = `${BASE_CSS}
:host {--ha-card-border-radius:28px;--ha-card-border-width:1px;--primary-color:var(--dsj-accent,#b98c27)}
.shell {position:relative;display:grid;grid-template-columns:130px minmax(0,1fr);min-height:calc(100dvh - 70px);background:var(--primary-background-color,#fafafa)}
main {width:100%;min-width:0;max-width:1120px;margin:0 auto;padding:28px 30px 110px 24px}
header {display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:24px}
h1 {font-size:clamp(24px,3vw,34px);letter-spacing:-.7px;margin:0 0 8px;font-weight:700}
.brand {font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:2px;color:var(--dsj-accent);margin-bottom:13px}
.user {display:flex;align-items:center;gap:9px}.avatar {border-radius:50%;background:var(--dsj-accent);color:white;width:40px;height:40px;display:grid;place-items:center;font-weight:700}
section {margin-bottom:28px} h2 {font-size:18px;margin:0 0 14px;letter-spacing:-.2px}
.grid {display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;align-items:start}.grid>* {min-width:0}
nav {position:sticky;align-self:start;z-index:5;margin:30px 0 30px 16px;top:20px;height:calc(100dvh - 120px);width:104px;display:flex;flex-direction:column;justify-content:space-evenly;gap:5px;background:var(--dsj-accent);padding:15px 8px;border-radius:32px;box-shadow:0 10px 22px #0002}
nav a {display:flex;flex-direction:column;align-items:center;justify-content:center;gap:6px;text-decoration:none;color:#fff;border-radius:22px;padding:12px 2px;font-size:11px;font-weight:600;opacity:.78}
nav a[aria-current=page] {background:#ffffff29;opacity:1} nav a:hover {opacity:1;background:#ffffff1c} nav ha-icon {--mdc-icon-size:24px}
.summary {display:flex;gap:8px;flex-wrap:wrap;margin:0 0 25px}.chip {background:color-mix(in srgb,var(--dsj-accent) 15%,transparent);border-radius:24px;padding:9px 14px;font-size:13px}
.actions {display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}.actions a {display:inline-flex;align-items:center;min-height:44px;padding:10px 16px;background:var(--secondary-background-color);border-radius:18px;text-decoration:none}
dialog {width:min(680px,calc(100vw - 24px));max-height:88dvh;border:1px solid var(--divider-color);border-radius:32px;padding:24px;background:var(--primary-background-color,#fff);color:var(--primary-text-color);box-shadow:0 25px 90px #0005;overflow:auto}
dialog::backdrop {background:#0008;backdrop-filter:blur(5px)} dialog .grid {grid-template-columns:1fr} dialog header {position:sticky;top:-24px;z-index:2;padding:12px 0;background:var(--primary-background-color,#fff)}
@media(min-width:1500px) {.grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:800px) {.shell{display:block}main{padding:22px 16px 120px} nav{position:fixed;margin:0;height:auto;top:auto;left:12px;right:12px;bottom:max(12px,env(safe-area-inset-bottom));width:auto;flex-direction:row;padding:8px 5px;border-radius:26px;gap:0}nav a{flex:1;padding:10px 1px;font-size:9px;border-radius:18px;gap:4px}nav ha-icon{--mdc-icon-size:22px}.user .username{display:none}}
@media(max-width:480px) {.grid{gap:10px}.grid:not(.rooms-grid){grid-template-columns:1fr}header{gap:10px}.user button{padding:10px}dialog{padding:18px}dialog header{top:-18px}h1{font-size:25px}}
`;

class DSJPageCard extends HTMLElement {
  constructor() {
    super(); this.attachShadow({mode:"open"}); this._children = []; this._revision = 0;
    this._location = () => this._syncHash();
  }
  setConfig(config) {
    if (!config || typeof config !== "object") throw new Error("DSJ: ongeldige dashboardconfiguratie");
    this._config = {...config, groups:config.groups || [], rooms:config.rooms || []};
    this._startRender();
  }
  _startRender() {
    this._render().catch(error => {
      console.error("[DSJ Dashboard] Pagina opbouwen mislukt", error);
      this.shadowRoot.replaceChildren(el("style", BASE_CSS), el("p", `DSJ-dashboard kon niet worden opgebouwd: ${error.message || error}`, "error"));
    });
  }
  set hass(hass) {
    this._hass = hass;
    if (!hass || !this._config) return;
    this._children = this._children.filter(card => card.getRootNode() === this.shadowRoot);
    for (const card of this._children) card.hass = hass;
    const title = this.shadowRoot.querySelector("h1");
    if (title && this._config.page === "hoofdpagina") {
      const hour = new Date().getHours();
      title.textContent = `${hour >= 18 ? "Goedenavond" : hour >= 12 ? "Goedemiddag" : hour >= 5 ? "Goedemorgen" : "Hallo"}, ${hass.user?.name || "welkom"}!`;
    }
    const username = this.shadowRoot.querySelector(".username");
    if (username) username.textContent = hass.user?.name || "";
    const avatar = this.shadowRoot.querySelector(".avatar");
    if (avatar) avatar.textContent = (hass.user?.name || "D").slice(0,1).toUpperCase();
    const summary = this.shadowRoot.querySelector(".summary");
    if (summary) {
      // The ids come from the filtered generated config; hidden entities never enter counts.
      const lights = this._config.groups.flatMap(g => g.cards).filter(c => c.type === "entity-filter").flatMap(c => c.entities);
      const count = lights.filter(id => hass.states[id]?.state === "on").length;
      summary.replaceChildren(el("span", `${count} ${this._config.light_summary === "groups" ? (count === 1 ? "lichtgroep aan" : "lichtgroepen aan") : (count === 1 ? "lamp aan" : "lampen aan")}`, "chip"), el("span", new Date().toLocaleDateString("nl-NL", {weekday:"long",day:"numeric",month:"long"}), "chip"));
    }
    const settings = this.shadowRoot.querySelector("dsj-settings-card");
    if (settings) settings.hass = hass;
  }
  getCardSize() { return 12; }
  connectedCallback() {
    for (const event of ["hashchange", "popstate", "location-changed"]) window.addEventListener(event, this._location);
    if (this._config) this._startRender();
  }
  disconnectedCallback() {
    for (const event of ["hashchange", "popstate", "location-changed"]) window.removeEventListener(event, this._location);
    this._revision++;
    const dialog = this.shadowRoot.querySelector("dialog");
    if (dialog?.open) dialog.close();
  }
  async _card(config, container, revision) {
    try {
      const helper = await helpers();
      if (revision !== this._revision || container.getRootNode() !== this.shadowRoot) return;
      const selected = config.type === "custom:dsj-optional-card" ? (customElements.get(config.element) ? config.preferred : config.fallback) : config;
      const card = helper.createCardElement(selected);
      if (this._hass) card.hass = this._hass;
      this._children.push(card); container.append(card);
    } catch (error) {
      if (revision === this._revision) container.append(el("p", `Kaart kon niet worden geladen: ${error.message}`, "error"));
    }
  }
  async _groups(groups, container, revision) {
    for (const group of groups) {
      if (revision !== this._revision) return;
      const section = el("section"); section.append(el("h2", group.title));
      const grid = el("div", undefined, `grid${group.cards.some(c => c.type === "custom:dsj-room-card") ? " rooms-grid" : ""}`);
      section.append(grid); container.append(section);
      // Preserve order even when the HA helpers lazily load cards.
      for (const config of group.cards) await this._card(config, grid, revision);
    }
  }
  async _render() {
    if (!this._config) return;
    const revision = ++this._revision; this._children = []; this._ready = false; this._bubbleMode = false;
    const config = this._config;
    this.style.setProperty("--dsj-accent", /^#[0-9a-f]{6}$/i.test(config.accent) ? config.accent : "#b98c27");
    const style = el("style", PAGE_CSS); const shell = el("div", undefined, "shell");
    const main = el("main"); const header = el("header"); const heading = el("div");
    heading.append(el("div", "De Slimme Jongens", "brand"), el("h1", config.title)); header.append(heading);
    const user = el("div", undefined, "user"); user.append(el("span", "", "username"), el("span", "D", "avatar"));
    const settingsLink = el("a"); settingsLink.href = `/${config.url_path}/instellingen`; settingsLink.title = "Instellingen"; settingsLink.setAttribute("aria-label", "Instellingen"); settingsLink.append(icon("mdi:cog")); user.append(settingsLink);
    header.append(user); main.append(header);
    if (config.page === "hoofdpagina") main.append(el("div", undefined, "summary"));
    const nav = el("nav"); nav.setAttribute("aria-label", "Dashboard");
    for (const [path, label, name] of NAV) {
      const a = el("a"); a.href = `/${config.url_path}/${path}`; a.setAttribute("aria-label", label); a.append(icon(name), el("span", label));
      if (config.page === path) a.setAttribute("aria-current", "page");
      nav.append(a);
    }
    shell.append(nav, main); this.shadowRoot.replaceChildren(style, shell);
    if (config.page === "instellingen") {
      const settings = el("dsj-settings-card"); main.append(settings);
      if (this._hass) settings.hass = this._hass;
    } else {
      if (config.page === "energie") {
        const actions = el("div", undefined, "actions");
        const link = el("a", "Home Assistant-energie openen"); link.href = "/energy"; actions.append(link); main.append(actions);
      }
      if (!config.groups.length) main.append(el("p", "Er zijn nog geen zichtbare apparaten voor deze pagina. Koppel apparaten aan ruimtes in Home Assistant.", "muted"));
      await this._groups(config.groups, main, revision);
    }
    if (revision !== this._revision) return;
    // Nested Bubble pop-ups can suspend the ancestor hui-card and hide this
    // entire page. Keep room dialogs owned by DSJ, even if Bubble is installed.
    // Navroom still navigates to the same hashes and opens these dialogs.
    this._bubbleMode = false;
    if (revision !== this._revision) return;
    this._ready = true;
    if (this._hass) this.hass = this._hass;
    this._syncHash();
  }
  async _syncHash() {
    if (!this._ready || !this._config || this._config.page !== "ruimtes" || this._bubbleMode) return;
    const room = this._config.rooms.find(r => `#dsj-${r.id}` === location.hash);
    const existing = this.shadowRoot.querySelector("dialog");
    if (!room) { if (existing?.open) existing.close(); existing?.remove(); this._openRoom = null; return; }
    if (existing?.open && this._openRoom === room.id) return;
    if (existing) { existing.close(); existing.remove(); }
    this._openRoom = room.id;
    const dialog = el("dialog"); const header = el("header"); header.append(el("h2", room.name));
    const close = button("Sluiten", () => { navigate(location.pathname + location.search); });
    header.append(close); dialog.append(header); this.shadowRoot.append(dialog);
    dialog.setAttribute("aria-label", room.name);
    dialog.addEventListener("cancel", e => { e.preventDefault(); navigate(location.pathname + location.search); });
    dialog.addEventListener("click", e => { if (e.target === dialog) { const rect = dialog.getBoundingClientRect(); if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) navigate(location.pathname + location.search); } });
    dialog.showModal();
    await this._groups(room.groups, dialog, this._revision);
  }
}

class DSJRoomCard extends HTMLElement {
  constructor() { super(); this.attachShadow({mode:"open"}); }
  setConfig(config) { this._config = config; this._render(); }
  set hass(hass) {
    this._hass = hass;
    if (!hass || !this._config) return;
    if (this._original) { this._original.hass = hass; return; }
    const room = this._config.room;
    const count = room.lights.filter(id => hass.states[id]?.state === "on").length;
    const status = this.shadowRoot.querySelector(".status");
    if (status) status.textContent = count ? `${count} ${count === 1 ? "lamp aan" : "lampen aan"}` : "Verlichting uit";
    const power = this.shadowRoot.querySelector(".power");
    if (power) { power.classList.toggle("on", count > 0); power.setAttribute("aria-label", `${room.name}: verlichting ${count ? "uitschakelen" : "inschakelen"}`); }
    const sensors = this.shadowRoot.querySelector(".sensors");
    if (sensors) sensors.replaceChildren(...Object.values(room.sensors).filter(Boolean).map(id => {
      const state = hass.states[id]; const value = state && !["unknown","unavailable"].includes(state.state) ? `${state.state}${state.attributes.unit_of_measurement || ""}` : "—";
      return el("span", value, "sensor");
    }));
  }
  getCardSize() { return 2; }
  async _render() {
    const room = this._config.room;
    this._original = null;
    this.shadowRoot.replaceChildren(el("style", `${BASE_CSS}
ha-card {border-radius:32px;overflow:hidden;background:color-mix(in srgb,var(--dsj-accent,#b98c27) 8%,var(--ha-card-background,var(--card-background-color,#fff)));position:relative;min-height:150px}
.room {width:100%;border:0;border-radius:32px;background:transparent;text-align:left;padding:18px;padding-right:54px;min-height:150px}
.room ha-icon {color:var(--dsj-accent,#b98c27);--mdc-icon-size:28px;margin-bottom:10px} .name{display:block;font-size:17px;font-weight:700;line-height:1.3}.status{display:block;font-size:11px;color:var(--secondary-text-color);margin-top:5px}.sensors{display:flex;gap:5px;margin-top:10px;flex-wrap:wrap}.sensor{border-radius:18px;padding:4px 9px;font-size:11px;background:var(--card-background-color,#fff)}
.power{position:absolute;right:12px;top:14px;width:38px;min-height:38px;padding:7px;border:0;border-radius:50%}.power ha-icon{--mdc-icon-size:20px}.power.on{background:var(--dsj-accent,#b98c27);color:#fff}
@media(max-width:480px){.room{padding:15px;padding-right:40px}.name{font-size:15px}.power{right:8px;width:32px;min-height:32px;padding:4px}}
`));
    if (this._config.original_cards && customElements.get("navroom-card")) {
      const card = document.createElement("navroom-card");
      card.setConfig({type:"custom:navroom-card",area:room.id,name:room.name,icon:room.icon,variant:"badge",height:150,radius:32,padding:15,head_height:40,row_gap:6,icon_size:26,name_size:17,name_weight:700,chip_height:24,chip_font:11.5,chip_pad:10,chip_gap:6,pwr_size:38,pwr_icon:20,badge_size:18,bg_tint:0.1,accent_fallback:"255,183,77",auto_discover:false,haptics:true,...(room.lights[0] ? {light:room.lights[0]} : {}),...(room.sensors.temperature ? {temp:room.sensors.temperature} : {}),...(room.sensors.humidity ? {humidity:room.sensors.humidity} : {}),tap_action:{action:"navigate",navigation_path:`#dsj-${room.id}`},hold_action:{action:"none"}});
      this._original = card; this.shadowRoot.append(card); if (this._hass) card.hass = this._hass; return;
    }
    const card = el("ha-card"); const open = button("", () => navigate(location.pathname + location.search + `#dsj-${room.id}`), "room");
    open.setAttribute("aria-label", `${room.name} openen`);
    open.append(icon(room.icon),el("span",room.name,"name"),el("span","","status"),el("div",undefined,"sensors")); card.append(open);
    if (room.lights.length) {
      const power = button("", async () => {
        if (!this._hass) return;
        power.disabled = true;
        const anyOn = room.lights.some(id => this._hass.states[id]?.state === "on");
        try { await this._hass.callService("light", anyOn ? "turn_off" : "turn_on", {entity_id:room.lights}); }
        catch (error) { card.append(el("p", error.message || "Lampen konden niet worden bediend", "error")); }
        finally { power.disabled = false; }
      }, "power"); power.setAttribute("aria-label", `${room.name}: verlichting bedienen`); power.append(icon("mdi:power")); card.append(power);
    }
    this.shadowRoot.append(card); if (this._hass) this.hass = this._hass;
  }
}

class DSJSettingsCard extends HTMLElement {
  constructor() { super(); this.attachShadow({mode:"open"}); this._filter = ""; this._offset = 0; }
  set hass(hass) {
    this._hass = hass;
    if (this._admin !== !!hass.user?.is_admin) { this._admin = !!hass.user?.is_admin; this._render(); }
  }
  connectedCallback() { if (this._hass) this._render(); }
  async _load() {
    try { this._items = await this._hass.callWS({type:"dsj_dashboard/inventory"}); this._rows(); }
    catch (error) { this._error.textContent = error.message || "Instellingen konden niet worden geladen"; }
  }
  _render() {
    this.shadowRoot.replaceChildren(el("style", `${BASE_CSS}
.tools{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px}.tools a{min-height:44px;padding:12px 16px;text-decoration:none;background:var(--secondary-background-color);border-radius:18px}input{width:100%;padding:15px 18px;border:1px solid var(--divider-color);background:var(--card-background-color);color:inherit;border-radius:20px;margin:16px 0}.row{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:8px;align-items:center;padding:14px 0;border-bottom:1px solid var(--divider-color)}.name{font-weight:600}.id{font-size:12px;overflow-wrap:anywhere;color:var(--secondary-text-color);margin:5px 0}.row button{padding:9px 12px;font-size:12px}.row button[aria-pressed=true]{background:var(--dsj-accent);color:#fff}.paging{display:flex;gap:10px;align-items:center;margin-top:18px}.error:empty{display:none}@media(max-width:480px){.row{grid-template-columns:1fr 1fr}.row .info{grid-column:1/-1}}
`));
    if (!this._admin) { this.shadowRoot.append(el("p", "Het dashboard wordt automatisch opgebouwd. Alleen beheerders kunnen apparaten verbergen of favorieten aanpassen.", "muted")); return; }
    this.shadowRoot.append(el("p", "Koppel apparaten aan ruimtes in Home Assistant. Verberg hier wat je niet wilt tonen en kies de favorieten voor de hoofdpagina. Deze keuzes gelden voor alle gebruikers van dit dashboard.", "muted"));
    const tools = el("div",undefined,"tools");
    for (const [label,path] of [["Ruimtes beheren","/config/areas"],["Energie instellen","/config/energy"],["Thema en kaarten","/config/integrations/integration/dsj_dashboard"]]) { const a=el("a",label);a.href=path;tools.append(a); }
    tools.append(button("Vernieuwen",()=>this._load())); this.shadowRoot.append(tools);
    const search = el("input"); search.type="search";search.placeholder="Zoek een apparaat, entiteit of ruimte…";search.setAttribute("aria-label","Apparaten zoeken");search.value=this._filter;
    search.addEventListener("input",()=>{this._filter=search.value;this._offset=0;this._rows();});this.shadowRoot.append(search);
    this._error=el("p","","error");this._list=el("div");this._paging=el("div",undefined,"paging");this.shadowRoot.append(this._error,this._list,this._paging);this._load();
  }
  _rows() {
    if (!this._list || !this._items) return;
    const query=this._filter.toLocaleLowerCase("nl-NL");
    const items=this._items.filter(item=>`${item.name} ${item.entity_id} ${item.area}`.toLocaleLowerCase("nl-NL").includes(query));
    this._list.replaceChildren();
    for (const item of items.slice(this._offset,this._offset+100)) {
      const row=el("div",undefined,"row");const info=el("div",undefined,"info");
      info.append(el("div",item.name,"name"),el("div",`${item.area} · ${item.entity_id}`,"id"));
      if (item.reason) info.append(el("div",item.reason,"muted")); row.append(info);
      for (const [operation,key] of [["hide","hidden"],["favorite","favorite"]]) {
        const label=operation==="hide"?(item.hidden?"Tonen":"Verbergen"):(item.favorite?"★ Favoriet":"☆ Favoriet");
        const action=button(label,async()=>{
          action.disabled=true;this._error.textContent="";
          try {await this._hass.callWS({type:"dsj_dashboard/change",entity_id:item.entity_id,operation,value:!item[key]});item[key]=!item[key];this._rows();}
          catch(error) {this._error.textContent=error.message||"Opslaan mislukt";action.disabled=false;}
        });action.setAttribute("aria-pressed",String(item[key]));action.setAttribute("aria-label",`${label}: ${item.name}`);if(item.reason)action.disabled=true;row.append(action);
      }
      this._list.append(row);
    }
    if (!items.length) this._list.append(el("p","Geen apparaten gevonden.","muted"));
    this._paging.replaceChildren();
    if(this._offset>0)this._paging.append(button("Vorige",()=>{this._offset-=100;this._rows();}));
    this._paging.append(el("span",`${items.length ? this._offset+1 : 0}–${Math.min(this._offset+100,items.length)} van ${items.length}`,"muted"));
    if(this._offset+100<items.length)this._paging.append(button("Volgende",()=>{this._offset+=100;this._rows();}));
  }
}

for (const [name, constructor] of [["dsj-page-card",DSJPageCard],["dsj-room-card",DSJRoomCard],["dsj-settings-card",DSJSettingsCard]]) {
  if (!customElements.get(name)) customElements.define(name,constructor);
}
window.customCards=window.customCards||[];
if(!window.customCards.some(c=>c.type==="dsj-page-card"))window.customCards.push({type:"dsj-page-card",name:"De Slimme Jongens",description:"Automatisch dashboard vanuit ruimtes en apparaten"});

console.info("[DSJ Dashboard] 0.1.2 frontend geladen");
