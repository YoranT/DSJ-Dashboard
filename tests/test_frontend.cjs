/* Component logic tests with a minimal DOM double; no browser or HA runtime. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
class Node {
  constructor(tag='element') {
    this.tagName=tag;this.children=[];this.parentNode=null;this.attributes={};this._text='';this.handlers={};
    this.style={setProperty(){}};this.classList={toggle(){}};
  }
  set textContent(value){this._text=String(value ?? '');this.children=[];}
  get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}
  setAttribute(key,value){this.attributes[key]=String(value);}
  getAttribute(key){return this.attributes[key] ?? null;}
  append(...nodes){for(const node of nodes){node.parentNode=this;this.children.push(node);}}
  replaceChildren(...nodes){for(const c of this.children)c.parentNode=null;this.children=[];this._text='';this.append(...nodes);}
  getRootNode(){return this.parentNode ? this.parentNode.getRootNode() : this;}
  addEventListener(event,fn){this.handlers[event]=fn;}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null;}
  querySelectorAll(selector){
    const result=[];
    const visit=node=>{for(const c of node.children){if(selector.startsWith('.') ? c.className?.split(' ').includes(selector.slice(1)) : c.tagName===selector)result.push(c);visit(c);}};
    visit(this);return result;
  }
  showModal(){this.open=true;}
  close(){this.open=false;}
  remove(){if(this.parentNode){this.parentNode.children=this.parentNode.children.filter(child=>child!==this);this.parentNode=null;}}
  attachShadow(){this.shadowRoot=new Node('shadow');this.shadowRoot.host=this;return this.shadowRoot;}
}
const customElements={classes:new Map(),get(name){return this.classes.get(name)},define(name,cls){this.classes.set(name,cls)}};
const document={createElement(tag){const C=customElements.get(tag);const node=C?new C():new Node(tag);node.tagName=tag;return node;}};
const hass={user:{name:'Tester',is_admin:false},states:{'light.living':{state:'on',attributes:{}}},callWS:async()=>[],callService:async()=>{}};
const window={customCards:[],addEventListener(){},removeEventListener(){},dispatchEvent(){},loadCardHelpers:async()=>({createCardElement(config){const card=new Node('native-card');card.config=config;return card;}})};
const source=fs.readFileSync(path.join(__dirname,'../custom_components/dsj_dashboard/frontend/dsj-dashboard.js'),'utf8');
const context=vm.createContext({HTMLElement:Node,document,customElements,window,console,history:{pushState(){}},location:{hash:'',pathname:'/dsj-dashboard/hoofdpagina',search:''},Event:class{},Date});
const load=()=>vm.runInContext(`(()=>{${source}\n})();`,context);
const flush=async()=>{for(let n=0;n<12;n++)await new Promise(resolve=>setImmediate(resolve));};
(async()=>{
 load();load();
 assert.equal(customElements.classes.size,3);
 assert.equal(window.customCards.length,1);
 const Page=customElements.get('dsj-page-card');
 for(const page of ['hoofdpagina','ruimtes','media','energie','klimaat','beveiliging','instellingen']) {
  const card=new Page();
  card.hass=hass; // HA may provide state before config.
  card.setConfig({page,title:page,url_path:'dsj-dashboard',accent:'#b98c27',groups:page==='instellingen'?[]:[{title:'Test',cards:[{type:'tile',entity:'light.living'}]}]});
  card.connectedCallback();card.hass=hass;
  await flush();
  assert(card.shadowRoot.querySelector('h1'),`${page} renders its header`);
  assert(!card.shadowRoot.querySelector('.error'),`${page} has no render error`);
  for(const link of card.shadowRoot.querySelectorAll('a'))assert(link.getAttribute('aria-label')?.trim(),`${page} link has an aria-label`);
  if(page!=='instellingen')assert.equal(card._children.length,1);
 }
 const room=document.createElement('dsj-room-card');
 room.hass=hass;
 room.setConfig({original_cards:false,room:{id:'living',name:'Woonkamer',icon:'mdi:sofa',lights:['light.living'],sensors:{}}});
 room.hass=hass;
 for(const button of room.shadowRoot.querySelectorAll('button'))assert(button.getAttribute('aria-label')?.trim());
 assert.equal(room.shadowRoot.querySelector('.status').textContent,'1 lamp aan');
 const requestedTypes=[];
 customElements.define('bubble-card',class extends Node {});
 window.loadCardHelpers=async()=>({createCardElement(config){requestedTypes.push(config.type);const card=new Node('native-card');card.config=config;return card;}});
 const roomsPage=new Page();
 const roomModel={id:'living',name:'Woonkamer',icon:'mdi:sofa',lights:['light.living'],sensors:{},groups:[{title:'Verlichting',cards:[{type:'tile',entity:'light.living'}]}]};
 roomsPage.setConfig({page:'ruimtes',title:'Ruimtes',url_path:'dsj-dashboard',original_cards:true,groups:[{title:'Begane grond',cards:[{type:'custom:dsj-room-card',room:roomModel}]}],rooms:[roomModel]});
 roomsPage.hass=hass;roomsPage.connectedCallback();await flush();
 assert.equal(roomsPage._bubbleMode,false,'installed Bubble must not hide the page');
 assert(!requestedTypes.includes('custom:bubble-card'),'no nested Bubble popups');
 assert(roomsPage.shadowRoot.querySelector('nav'));
 context.location.hash='#dsj-living';await roomsPage._syncHash();
 assert.equal(roomsPage.shadowRoot.querySelector('dialog').open,true,'room dialog opens');
 assert(roomsPage.shadowRoot.querySelector('h1'),'page remains present behind popup');
 context.location.hash='';await roomsPage._syncHash();
 assert.equal(roomsPage.shadowRoot.querySelector('dialog'),null,'room dialog closes');
 const summaryPage=new Page();
 summaryPage.setConfig({page:'hoofdpagina',title:'Home',url_path:'dsj-dashboard',light_summary:'groups',groups:[{title:'Aanstaande lampen',cards:[{type:'entity-filter',entities:['light.living']}]}]});
 summaryPage.hass=hass;await flush();
 assert.match(summaryPage.shadowRoot.querySelector('.summary').textContent,/1 lichtgroep aan/);
 console.log('PASS: room rendering with Bubble installed, dialog open/close, group summary, module registration, repeated load, all seven page startups, state-before-config, links/buttons labelled, live room status. DOM double only; no visual browser verification.');
})().catch(error=>{console.error(error);process.exitCode=1;});
