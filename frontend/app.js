/* HAI — no server-side business logic lives in this file.
 * The Python API is the source of truth for tokens, AST, diagnostics and execution.
 * Vendored CodeMirror 5 is used for an offline-capable editor; see docs/ARCHITECTURE.md.
 */
(() => {
'use strict';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const EXAMPLES = {
  hello: 'HAI\n\nBTW My first LOLCODE program\nVISIBLE "HAI, WORLD!"\n\nKTHXBYE\n',
  math: 'HAI\n\nWAZZUP\n    I HAS A first ITZ 12\n    I HAS A second ITZ 8\nBUHBYE\n\nVISIBLE SUM OF first AN second\n\nKTHXBYE\n',
  conditional: 'HAI\n\nBOTH SAEM 5 AN 5\nO RLY?\n    YA RLY\n        VISIBLE "They match!"\n    NO WAI\n        VISIBLE "Try again."\nOIC\n\nKTHXBYE\n',
  input: 'HAI\n\nWAZZUP\n    I HAS A age\nBUHBYE\n\nGIMMEH age\nVISIBLE SUM OF age AN 1\n\nKTHXBYE\n',
  nested: 'HAI\n\nWAZZUP\n    I HAS A x ITZ 12\n    I HAS A y ITZ 3\nBUHBYE\n\nVISIBLE "Result: " + SUM OF PRODUKT OF x AN y AN 4\n\nKTHXBYE\n'
};
const KEYWORDS = [
  'IM OUTTA YR','IM IN YR','I HAS A','IS NOW A','HOW IZ I','IF U SAY SO',
  'SUM OF','DIFF OF','PRODUKT OF','QUOSHUNT OF','MOD OF','BIGGR OF','SMALLR OF',
  'BOTH SAEM','BOTH OF','EITHER OF','WON OF','ALL OF','ANY OF','O RLY?','YA RLY',
  'NO WAI','FOUND YR','I IZ','AN YR','WAZZUP','BUHBYE','KTHXBYE','OMGWTF',
  'SMOOSH','DIFFRINT','GIMMEH','VISIBLE','MAEK','MKAY','UPPIN','NERFIN',
  'WILE','TIL','WTF?','OMG','OIC','GTFO','NOT','HAI','ITZ','AN','YR','R','A',
  'NUMBR','NUMBAR','YARN','TROOF','NOOB','WIN','FAIL'
].sort((a, b) => b.length - a.length);
const regexp = new RegExp('^(?:' + KEYWORDS.map(word => word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|') + ')(?![A-Za-z0-9_])');
const operators = new Set(['SUM OF','DIFF OF','PRODUKT OF','QUOSHUNT OF','MOD OF', 'BIGGR OF','SMALLR OF','BOTH OF','EITHER OF','WON OF','ALL OF','ANY OF','BOTH SAEM','DIFFRINT','SMOOSH','MAEK','NOT']);
const types = new Set(['NUMBR','NUMBAR','YARN','TROOF','NOOB']);
const bools = new Set(['WIN','FAIL']);

CodeMirror.defineMode('lolcode', () => ({
  startState: () => ({ blockComment: false }),
  token(stream, state) {
    if (state.blockComment) {
      if (stream.match(/TLDR\b/)) { state.blockComment = false; return 'comment'; }
      stream.skipToEnd(); return 'comment';
    }
    if (stream.eatSpace()) return null;
    if (stream.match(/OBTW\b/)) { state.blockComment = true; stream.skipToEnd(); return 'comment'; }
    if (stream.match(/BTW\b/)) { stream.skipToEnd(); return 'comment'; }
    if (stream.peek() === '"') {
      stream.next(); let escaped = false;
      while (!stream.eol()) { const c = stream.next(); if (c === '"' && !escaped) break; escaped = c === ':' && !escaped; }
      return 'string';
    }
    if (stream.match(/-?\d+(?:\.\d+)?(?![A-Za-z_])/)) return 'number';
    const match = stream.match(regexp);
    if (match) {
      const word = match[0];
      if (types.has(word)) return 'type';
      if (bools.has(word)) return 'atom';
      return operators.has(word) ? 'operator' : 'keyword';
    }
    if (stream.match(/[A-Za-z][A-Za-z0-9_]*/)) return 'variable';
    stream.next(); return 'punctuation';
  }
}));

const state = {
  revision: 0, analyzedRevision: -1, busy: false, abort: null,
  tokens: [], tokenLocations: [], ast: null, astLocations: {}, records: new Map(),
  selectedPath: null, selectedToken: -1, collapsed: new Set(), astMode: 'outline', zoom: 1, astQuery: '',
  inspectorView: 'ast', consoleView: 'output', mobileView: 'code',
  diagnostics: [], output: '', symbols: [], inputs: [], waiting: false,
  filename: 'playground.lol', dirty: false, selectedMarker: null, previewMarker: null,
  diagnosticMarkers: [], programmaticSelection: false, runningSerial: 0
};
const editor = CodeMirror.fromTextArea($('#source'), {
  mode: 'lolcode', lineNumbers: true, lineWrapping: false, styleActiveLine: true,
  indentUnit: 2, tabSize: 2, indentWithTabs: false, autofocus: false,
  gutters: ['CodeMirror-linenumbers','diagnostic-gutter'],
  extraKeys: {
    Tab(cm) { cm.replaceSelection('  ', 'end'); },
    'Shift-Tab'(cm) { cm.execCommand('indentLess'); },
    'Cmd-Enter'() { run(true); }, 'Ctrl-Enter'() { run(true); },
    Esc(cm) { cm.getInputField().blur(); $('#analyze').focus(); }
  }
});
editor.setValue(EXAMPLES.hello);
editor.clearHistory();

const el = (tag, cls = '', text = null) => {
  const item = document.createElement(tag);
  if (cls) item.className = cls;
  if (text !== null) item.textContent = String(text);
  return item;
};
const sourceText = () => editor.getValue();
const safeCount = list => Array.isArray(list) ? list.length : 0;
const escapeNewline = text => String(text).replaceAll('\n', '↵').replaceAll('\t', '⇥');
function setStatus(label, message, kind = '') {
  $('#status-label').textContent = label;
  $('#status-message').textContent = message;
  $('#status-message').title = message;
  $('#status-indicator').className = 'status-indicator ' + kind;
}
function updateButtons() { ['#tokenize','#analyze','#run','#reset'].forEach(id => { $(id).disabled = state.busy; }); }
function setStages(last = '', failed = false, waiting = false) {
  const order = ['lexer','parser','runtime'];
  const end = order.indexOf(last);
  $$('.stages [data-stage]').forEach(item => {
    const i = order.indexOf(item.dataset.stage);
    item.dataset.state = end < 0 || i > end ? '' : i < end ? 'ok' : failed ? 'error' : waiting ? 'active' : 'ok';
  });
}
function stamp(text) { $('#analysis-stamp').textContent = text; }
function dirtyState(value) { state.dirty = value; $('#dirty-indicator').hidden = !value; }
function setFilename(name) { state.filename = (name || 'playground.lol').replace(/[\\/]/g,'').slice(0,90); $('#filename').textContent = state.filename; }
function toEditorOffset(codepoint) {
  if (!Number.isInteger(codepoint) || codepoint < 0) return null;
  return Array.from(sourceText()).slice(0, codepoint).join('').length;
}
function toCodepointOffset(utf16) { return Array.from(sourceText().slice(0,utf16)).length; }
function selectionFromLocation(loc, focus = true) {
  if (!loc) return false;
  let begin = toEditorOffset(loc.start_offset), end = toEditorOffset(loc.end_offset);
  if (begin === null || end === null) {
    if (!Number.isInteger(loc.line)) return false;
    const line = Math.max(0,Math.min(editor.lineCount()-1,loc.line-1));
    begin = editor.indexFromPos({line, ch:0}); end = editor.indexFromPos({line,ch:editor.getLine(line).length});
  }
  state.programmaticSelection = true;
  editor.setSelection(editor.posFromIndex(begin), editor.posFromIndex(end));
  editor.scrollIntoView({from:editor.posFromIndex(begin),to:editor.posFromIndex(end)},70);
  if (focus) editor.focus();
  state.programmaticSelection = false;
  if (state.mobileView !== 'code' && focus) showMobileView('code');
  return true;
}
function clearMarker(marker) { if (marker) try { marker.clear(); } catch (_) {} }
function paintRange(loc, preview = false) {
  if (preview) { clearMarker(state.previewMarker); state.previewMarker = null; }
  else { clearMarker(state.selectedMarker); state.selectedMarker = null; }
  if (!loc || !Number.isInteger(loc.start_offset) || !Number.isInteger(loc.end_offset)) return;
  const a = toEditorOffset(loc.start_offset), b = toEditorOffset(loc.end_offset);
  if (a === null || b === null || b <= a) return;
  const marker = editor.markText(editor.posFromIndex(a), editor.posFromIndex(b),
    {className:preview ? 'cm-mapped-preview' : 'cm-mapped-range', clearWhenEmpty:false});
  if (preview) state.previewMarker = marker;
  else state.selectedMarker = marker;
}
function clearDiagnostics() {
  state.diagnosticMarkers.forEach(marker => { try { marker.clear(); } catch (_) {} });
  state.diagnosticMarkers = [];
  editor.clearGutter('diagnostic-gutter');
}
function setDiagnostics(list) {
  state.diagnostics = list.filter(Boolean);
  clearDiagnostics();
  for (const d of state.diagnostics) {
    // A network or runtime error without a location must never mark line 1.
    if (!Number.isInteger(d.line) || d.line < 1) continue;
    const line = Math.max(0, Math.min(editor.lineCount()-1, d.line-1));
    const marker = el('span','cm-diagnostic-gutter');
    marker.title = `${d.stage || 'error'}: ${d.message}`;
    marker.setAttribute('aria-label',marker.title); marker.tabIndex = 0;
    marker.addEventListener('click', () => { selectConsole('problems'); selectionFromLocation(d); });
    marker.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); marker.click(); } });
    editor.setGutterMarker(line,'diagnostic-gutter',marker);
    let a = toEditorOffset(d.start_offset), b = toEditorOffset(d.end_offset);
    const exact = a !== null && b !== null && b > a;
    if (!exact) {
      // Line-only diagnostic: highlight the row without implying an exact column.
      const text = editor.getLine(line) || '';
      if (!text.length) continue;
      a = editor.indexFromPos({line,ch:0}); b = a + text.length;
    }
    const start = editor.posFromIndex(Math.min(a,sourceText().length));
    const end = editor.posFromIndex(Math.min(b,sourceText().length));
    state.diagnosticMarkers.push(editor.markText(start,end,{
      className: exact ? 'cm-diagnostic-error' : 'cm-diagnostic-line', title:d.message
    }));
  }
  $('#problem-count').textContent = state.diagnostics.length;
  renderProblems();
}
function renderProblems() {
  const surface = $('#console-problems'); surface.replaceChildren();
  if (!state.diagnostics.length) {
    surface.append(el('div','console-empty','No diagnostics.'));
    return;
  }
  for (const d of state.diagnostics) {
    const row = el('div','problem');
    const main = el('div','problem-main');
    const header = el('div','problem-header');
    header.append(el('strong','',String(d.stage || 'error').toUpperCase()));
    if (Number.isInteger(d.line)) {
      header.append(el('span','problem-location',`Line ${d.line}${Number.isInteger(d.column) ? `:${d.column}` : ''}`));
    }
    const message = String(d.message || 'Unknown error');
    const locationPrefix = Number.isInteger(d.line) ? new RegExp(`^Line\\s+${d.line}(?:,\\s*column\\s+\\d+)?\\s*:\\s*`, 'i') : null;
    const concise = locationPrefix ? message.replace(locationPrefix, '') : message;
    main.append(header,el('p','',concise));
    row.append(main);
    if (Number.isInteger(d.line)) {
      const go = el('button','problem-jump','Go to line');
      go.type = 'button';
      go.addEventListener('click',()=>selectionFromLocation(d));
      row.append(go);
    }
    surface.append(row);
  }
}
function renderOutput() {
  const area = $('#console-output'); area.replaceChildren();
  if (state.output) area.append(el('pre','console-output',state.output));
  else if (!state.waiting && !state.diagnostics.length) area.append(el('div','console-empty','Run a program to see its output.'));
  if (state.waiting) {
    const form = el('form','prompt-row');
    form.setAttribute('aria-label','Program input');
    const caption = el('div','prompt-caption');
    caption.append(el('span','prompt-kicker','GIMMEH'));
    const label = el('label','',state.prompt || 'Enter a value');
    label.htmlFor='prompt-answer';
    caption.append(label);
    const controls = el('div','prompt-controls');
    const input = el('input'); input.type='text'; input.id='prompt-answer'; input.name='answer';
    input.autocomplete='off'; input.placeholder='Type a value';
    const submit = el('button','prompt-send','Send'); submit.type='submit';
    controls.append(input,submit); form.append(caption,controls);
    form.addEventListener('submit',e => {
      e.preventDefault(); if (state.busy) return;
      state.inputs.push(input.value); state.waiting = false; renderOutput(); run(false);
    });
    area.append(form);
    requestAnimationFrame(()=>input.focus());
  }
  if (!state.output && state.diagnostics.length) {
    const link = el('button','problem-shortcut','View diagnostics');
    link.type='button'; link.addEventListener('click',()=>selectConsole('problems')); area.append(link);
  }
}
function clearResults(silent = false) {
  state.tokens = []; state.tokenLocations=[]; state.ast=null; state.astLocations={}; state.records=new Map();
  state.selectedPath=null; state.selectedToken=-1; state.collapsed.clear();
  state.astQuery=''; $('#ast-find').value='';
  state.diagnostics=[]; state.output=''; state.symbols=[]; state.inputs=[]; state.waiting=false;
  state.analyzedRevision=-1;
  clearMarker(state.selectedMarker); clearMarker(state.previewMarker);
  state.selectedMarker=null; state.previewMarker=null;
  setDiagnostics([]);
  renderTokens(); renderSymbols(); renderAST(); renderOutput();
  for(const id of ['#token-count','#ast-count','#symbol-count']) { $(id).textContent=''; $(id).hidden=true; }
  $('#run-duration').textContent='';
  $('#selected-range').textContent=''; $('#selected-range').hidden=true;
  stamp('Not analyzed'); setStages();
  if (!silent) setStatus('READY','Results cleared.');
}
function sourceEdited() {
  state.revision++;
  if (state.abort) state.abort.abort();
  clearResults(true);
  dirtyState(true);
  stamp('Changed · analysis needed');
  setStatus('EDITED','Analysis out of date.');
}
function renderPosition() {
  const cursor = editor.getCursor();
  $('#editor-where').textContent=`Ln ${cursor.line + 1} · Col ${cursor.ch + 1}`;
}
editor.on('change', sourceEdited);
editor.on('cursorActivity', () => { renderPosition(); if (!state.programmaticSelection) syncFromEditor(); });

function nodeChildren(node,path) {
  const result=[];
  const collect=(value,valuePath,field)=>{
    if (!value || typeof value !== 'object') return;
    if (value.node && typeof value.node === 'string') { result.push({node:value,path:valuePath,field}); return; }
    if (Array.isArray(value)) { value.forEach((v,i)=>collect(v,`${valuePath}[${i}]`,`${field}[${i}]`)); return; }
    Object.entries(value).forEach(([k,v])=>collect(v,`${valuePath}.${k}`,k));
  };
  Object.entries(node).forEach(([field,value])=>{ if(field!=='node') collect(value,`${path}.${field}`,field); });
  return result;
}
function shortValue(value, max = 38) {
  const display = typeof value === 'string' ? JSON.stringify(value) : String(value);
  return display.length > max ? `${display.slice(0, max - 1)}…` : display;
}
function summarizeNode(node) {
  // Use the actual AST fields, not placeholder labels or invented semantic descriptions.
  if (node.node === 'Literal') return `${node.kind ?? 'literal'} · ${shortValue(node.value)}`;
  if (typeof node.op === 'string') return node.op.replaceAll('_', ' ');
  if (typeof node.name === 'string') return shortValue(node.name);
  if (node.node === 'Program') {
    const count = Array.isArray(node.body) ? node.body.length : 0;
    return `${count} top-level ${count === 1 ? 'statement' : 'statements'}`;
  }
  if (node.node === 'VariableSection' && Array.isArray(node.declarations)) {
    return `${node.declarations.length} ${node.declarations.length === 1 ? 'declaration' : 'declarations'}`;
  }
  if (node.node === 'PrintStmt' && Array.isArray(node.values)) {
    return `${node.values.length} ${node.values.length === 1 ? 'expression' : 'expressions'}`;
  }
  const label = node.label ?? node.value;
  return label === undefined ? '' : shortValue(label);
}
function matchingAstPaths() {
  const query = state.astQuery.trim().toLocaleLowerCase();
  if (!query || !state.records.size) return [];
  return [...state.records.values()].filter(rec => {
    const fields = Object.entries(rec.node).filter(([key,value]) =>
      key !== 'node' && (value === null || typeof value !== 'object'));
    return [rec.node.node, rec.field, ...fields.flatMap(([key,value]) => [key, String(value)])]
      .some(part => String(part).toLocaleLowerCase().includes(query));
  }).map(rec => rec.path);
}
function updateAstFindCount(matches) {
  const count = $('#ast-find-count');
  count.textContent = state.astQuery.trim() ? `${matches.length}` : '';
  count.title = matches.length === 1 ? '1 matching AST node' : `${matches.length} matching AST nodes`;
  count.setAttribute('aria-label',count.title);
}
function expandAstAncestors(paths) {
  for (const path of paths) {
    let parent = state.records.get(path)?.parent;
    while (parent) {
      state.collapsed.delete(parent);
      parent = state.records.get(parent)?.parent || null;
    }
  }
}
function updateFoldControl() {
  const branches = [...state.records.values()].filter(rec => rec.children.length && rec.path !== '$');
  const folded = branches.length > 0 && branches.every(rec => state.collapsed.has(rec.path));
  const button = $('#ast-fold');
  button.textContent = folded ? 'Expand' : 'Collapse';
  button.title = folded ? 'Expand all AST branches' : 'Collapse AST branches';
  button.setAttribute('aria-label', button.title);
}
function buildRecords() {
  state.records=new Map();
  if (!state.ast) return;
  const visit=(node,path,field,depth,parent)=>{
    const kids=nodeChildren(node,path);
    state.records.set(path,{path,node,field,depth,parent,children:kids.map(child=>child.path),summary:summarizeNode(node)});
    kids.forEach(child=>visit(child.node,child.path,child.field,depth+1,path));
  };
  visit(state.ast,'$','root',0,null);
  $('#ast-count').textContent=state.records.size; $('#ast-count').hidden=false;
}
function selectPath(path, navigate = false) {
  const rec = state.records.get(path);
  if (!rec) return;
  state.selectedPath = path; state.selectedToken = -1;
  $('#selected-range').textContent=rec.node.node;
  $('#selected-range').hidden=false;
  const loc = state.astLocations[path];
  paintRange(loc);
  if (navigate) selectionFromLocation(loc,false);
  let revealed = false;
  let p=rec.parent;
  while (p) {
    if (state.collapsed.delete(p)) revealed = true;
    p=state.records.get(p)?.parent || null;
  }
  if (revealed && state.astMode === 'outline') renderOutline();
  highlightSelected(); renderDetails();
}
function hoverPath(path) { paintRange(state.astLocations[path],true); }
function unhoverPath() { clearMarker(state.previewMarker); state.previewMarker=null; }
function highlightSelected() {
  $$('.tree-node, .graph-node').forEach(node=>{
    const active=node.dataset.path === state.selectedPath;
    node.classList.toggle('selected',active);
    if(active) node.setAttribute('aria-current','location'); else node.removeAttribute('aria-current');
  });
  const activePath=new Set();
  let selected=state.selectedPath;
  while(selected){activePath.add(selected);selected=state.records.get(selected)?.parent || null;}
  $$('.graph-branch').forEach(line=>line.classList.toggle('selected',activePath.has(line.dataset.to)));
}
function syncFromEditor() {
  if (state.analyzedRevision!==state.revision || !state.records.size) return;
  const from = editor.indexFromPos(editor.getCursor('from'));
  const to = editor.indexFromPos(editor.getCursor('to'));
  const start = toCodepointOffset(from), end=toCodepointOffset(to);
  const matches=[...state.records.keys()].filter(path=>{
    const l=state.astLocations[path];
    return l && l.start_offset <= start && (end>start ? l.end_offset>=end : l.end_offset>start);
  }).sort((a,b)=> {
    const x=state.astLocations[a],y=state.astLocations[b];
    return (x.end_offset-x.start_offset)-(y.end_offset-y.start_offset) || (state.records.get(b).depth-state.records.get(a).depth);
  });
  if(matches.length && matches[0]!==state.selectedPath){
    selectPath(matches[0]);
    if(state.astMode==='outline') { const selected=$('.tree-node.selected'); if (selected) selected.scrollIntoView({block:'nearest'}); }
  } else if(!matches.length && state.selectedPath){
    // Do not leave an unrelated AST node selected when the cursor moves outside mapped source.
    state.selectedPath=null;
    clearMarker(state.selectedMarker);state.selectedMarker=null;
    $('#selected-range').textContent='';$('#selected-range').hidden=true;
    highlightSelected();renderDetails();
  }
}
function renderDetails() {
  const root=$('#node-details'); root.replaceChildren();
  const rec=state.records.get(state.selectedPath);
  if (!rec) {root.hidden=true;return;}
  root.hidden=false;
  const loc=state.astLocations[rec.path];
  const heading=el('div','details-heading');
  const headingLeft=el('div','details-heading-left');
  headingLeft.append(el('span','details-kicker','Selected node'),el('strong','',rec.node.node));
  heading.append(headingLeft);
  if (loc) {
    const jump=el('button','details-link','Reveal in source');
    jump.type='button'; jump.addEventListener('click',()=>selectionFromLocation(loc));
    heading.append(jump);
  }
  root.append(heading);
  const path=[];
  let current=rec;
  while(current) {path.unshift(current);current=state.records.get(current.parent);}
  const crumbs=el('nav','details-ancestors');
  crumbs.setAttribute('aria-label','AST ancestor path');
  path.forEach((item,index)=>{
    if(index)crumbs.append(el('span','details-divider','/'));
    const part=el('button','details-ancestor',item.node.node);
    part.type='button';part.disabled=item.path===rec.path;
    part.title=item.field;
    part.addEventListener('click',()=>selectPath(item.path,true));
    crumbs.append(part);
  });
  root.append(crumbs);
  const grid=el('dl','details-grid');
  const field=(key,value)=>{
    const item=el('div','details-item');
    item.append(el('dt','',key),el('dd','',String(value)));
    grid.append(item);
  };
  if (loc) field('Source',`${loc.line}:${loc.column} – ${loc.end_line}:${loc.end_column}`);
  if (rec.field !== 'root') field('Relation',rec.field);
  Object.entries(rec.node).forEach(([key,value])=>{
    if (key==='node'||(value!==null&&typeof value==='object'))return;
    field(key,value===null?'null':value);
  });
  if(rec.children.length)field('Children',rec.children.length);
  if(grid.childNodes.length)root.append(grid);
}
function makeEmpty(h,p) {
  const div=el('div','empty-state');
  div.textContent = p || h;
  return div;
}
function renderOutline() {
  const root=$('#ast-surface'); root.replaceChildren();
  const container=el('div','ast-outline');
  const matches=matchingAstPaths();
  updateAstFindCount(matches);
  const matchSet=new Set(matches);
  const build=(path)=>{
    const rec=state.records.get(path);if(!rec)return null;
    const item=el('li','tree-item'); const row=el('div','tree-line');
    const closed=state.collapsed.has(path);
    if(rec.children.length){
      const toggle=el('button','tree-chevron',closed?'▸':'▾'); toggle.type='button';
      toggle.setAttribute('aria-label',`${closed?'Expand':'Collapse'} ${rec.node.node}`);
      toggle.setAttribute('aria-expanded',String(!closed));
      toggle.dataset.path=path;
      toggle.addEventListener('click',()=>{
        if(closed)state.collapsed.delete(path);else state.collapsed.add(path);
        renderOutline();renderDetails();
        const replacement=[...document.querySelectorAll('.tree-chevron')]
          .find(button=>button.dataset.path===path);
        replacement?.focus({preventScroll:true});
      });
      row.append(toggle);
    } else row.append(el('span','tree-chevron-spacer'));
    const button=el('button','tree-node');button.type='button';button.dataset.path=path;
    button.classList.toggle('search-match',matchSet.has(path));
    button.setAttribute('aria-label',`${rec.node.node}${rec.summary ? `, ${rec.summary}` : ''}${rec.field !== 'root' ? `, ${rec.field}` : ''}`);
    button.append(el('span','node-type',rec.node.node));
    if(rec.summary)button.append(el('span','node-property',rec.summary));
    button.addEventListener('click',()=>selectPath(path,true));
    button.addEventListener('mouseenter',()=>hoverPath(path));
    button.addEventListener('mouseleave',unhoverPath);
    row.append(button);item.append(row);
    if(rec.children.length && !closed){
      const childList=el('ul','tree-list');
      rec.children.forEach(child=>{const n=build(child);if(n)childList.append(n);});
      item.append(childList);
    }
    return item;
  };
  const list=el('ul','tree-list');list.append(build('$'));container.append(list);root.append(container);
  highlightSelected();updateFoldControl();
}
function renderGraph() {
  const root=$('#ast-surface');const scroll=el('div','ast-graph-scroll');const stage=el('div','graph-stage');
  const visible=[];let leaves=0;let maxDepth=0;
  const visit=(path,depth)=>{
    if(visible.length>=210)return null;
    const rec=state.records.get(path);if(!rec)return null;
    maxDepth=Math.max(depth,maxDepth);
    const item={...rec,depth,x:24+depth*205,y:0,childrenVisible:[]};
    visible.push(item);
    if(!rec.children.length||state.collapsed.has(path)||visible.length>=210){ item.y=50+leaves++*80;return item; }
    item.childrenVisible=rec.children.map(ch=>visit(ch,depth+1)).filter(Boolean);
    if(item.childrenVisible.length)item.y=(item.childrenVisible[0].y+item.childrenVisible.at(-1).y)/2;
    else item.y=50+leaves++*80;
    return item;
  };
  visit('$',0);
  const w=Math.max(600,(maxDepth+1)*205+50),h=Math.max(300,leaves*80+100);
  const zoom=state.zoom;
  const scaleBox=el('div','graph-scale-box');
  scaleBox.style.width=(w*zoom)+'px';scaleBox.style.height=(h*zoom)+'px';
  stage.style.width=w+'px';stage.style.height=h+'px';
  stage.style.transform=`scale(${zoom})`;stage.style.transformOrigin='top left';
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');
  svg.setAttribute('width',String(w));svg.setAttribute('height',String(h));svg.setAttribute('viewBox',`0 0 ${w} ${h}`);svg.classList.add('graph-lines');
  for(const entry of visible){
    for(const child of entry.childrenVisible){
      const x1=entry.x+163,y1=entry.y+23,x2=child.x,y2=child.y+23;
      const link=document.createElementNS('http://www.w3.org/2000/svg','path');
      const mid=(x1+x2)/2;link.setAttribute('d',`M ${x1} ${y1} H ${mid} V ${y2} H ${x2}`);
      link.classList.add('graph-branch');link.dataset.to=child.path;svg.append(link);
    }
  }
  stage.append(svg);
  for(const item of visible){
    const button=el('button','graph-node');button.type='button';button.dataset.path=item.path;
    button.style.left=item.x+'px';button.style.top=item.y+'px';
    button.append(el('strong','',item.node.node),el('small','',item.summary||item.field));
    button.title=`${item.path}${state.astLocations[item.path]?' · Select source':''}`;
    button.addEventListener('click',()=>selectPath(item.path,true));
    if (item.children.length) {
      button.title += ' · Double-click to collapse or expand';
      button.addEventListener('dblclick',()=>{
        if (state.collapsed.has(item.path)) state.collapsed.delete(item.path);
        else state.collapsed.add(item.path);
        renderGraph();
      });
    }
    button.addEventListener('mouseenter',()=>hoverPath(item.path));button.addEventListener('mouseleave',unhoverPath);
    stage.append(button);
  }
  if(visible.length>=210) stage.append(el('div','graph-limit','Large tree: showing the first 210 nodes. Use Outline to inspect all nodes.'));
  scaleBox.append(stage);scroll.append(scaleBox);root.append(scroll);highlightSelected();
  // Show the actual selected construct (or Program) when entering / resizing the graph.
  // The graph is larger than the inspector, so the origin alone is rarely useful.
  const target = visible.find(item => item.path === state.selectedPath) || visible[0];
  if (target) requestAnimationFrame(() => {
    if (!scroll.isConnected || !scroll.clientWidth || !scroll.clientHeight) return;
    scroll.scrollLeft = Math.max(0, (target.x + 82) * zoom - scroll.clientWidth / 2);
    scroll.scrollTop = Math.max(0, (target.y + 24) * zoom - scroll.clientHeight / 2);
  });
}
function renderAST() {
  const root=$('#ast-surface');root.replaceChildren();
  $('#tree-hint').textContent='';
  $('#outline-tools').hidden = !state.ast || state.astMode !== 'outline';
  $('#graph-controls').hidden = !state.ast || state.astMode !== 'graph';
  if(!state.ast){
    root.append(makeEmpty('No tree','Analyze to inspect the program structure.'));
    $('#node-details').hidden=true;updateAstFindCount([]);return;
  }
  if(state.astMode==='outline')renderOutline();
  else if(state.astMode==='graph')renderGraph();
  else {root.append(el('pre','ast-raw',JSON.stringify(state.ast,null,2)));}
  renderDetails();
}
function selectAstMode(mode) {
  state.astMode=mode;
  $$('[data-mode]').forEach(b=>{const yes=b.dataset.mode===mode;b.classList.toggle('active',yes);b.setAttribute('aria-pressed',String(yes));});
  renderAST();
}
function tokenClass(kind){
  if(['NUMBR','NUMBAR','YARN','TROOF'].includes(kind))return 'literal';
  if(kind==='IDENTIFIER')return 'identifier';
  if(['NEWLINE','PLUS','COMMA','EXCLAMATION'].includes(kind))return 'punct';
  if(kind==='COMMENT')return 'comment';
  if(['SUM_OF','DIFF_OF','PRODUKT_OF','QUOSHUNT_OF','MOD_OF','SMOOSH','BOTH_OF','EITHER_OF','WON_OF'].includes(kind))return 'operator';
  return 'keyword';
}
function renderTokens() {
  const surface=$('#token-surface');surface.replaceChildren();
  const q=($('#token-filter').value||'').toLowerCase().trim();
  const filtered=state.tokens.map((t,i)=>({t,i})).filter(({t})=>!q||t.some(v=>String(v).toLowerCase().includes(q)));
  if(!state.tokens.length){surface.append(el('div','table-empty','No tokens. Use Tokenize or Analyze to inspect the source.'));return;}
  if(!filtered.length){surface.append(el('div','table-empty','No matching tokens.'));return;}
  const table=el('table','data-table token-table');
  const head=el('thead'),row=el('tr');
  for(const name of ['LEXEME','TYPE','LINE:COL'])row.append(el('th','',name));
  head.append(row);table.append(head);
  const body=el('tbody');
  filtered.forEach(({t,i})=>{
    const [kind,lexeme,line]=t,loc=state.tokenLocations[i];
    const r=el('tr','clickable'+(i===state.selectedToken?' selected':''));r.tabIndex=0;
    const cleanLexeme=escapeNewline(lexeme);
    r.setAttribute('aria-label',`${kind} ${cleanLexeme}, line ${line}${loc?.column?`, column ${loc.column}`:''}`);
    const lex=el('td','token-lexeme',cleanLexeme);lex.title=String(lexeme);
    const type=el('td','token-kind');type.append(el('span','token-class '+tokenClass(kind),kind));
    const place=el('td','token-loc',`${line}:${loc?.column??'—'}`);
    r.append(lex,type,place);
    const jump=()=>{
      state.selectedToken=i;$$('#token-surface tbody tr').forEach(x=>x.classList.remove('selected'));r.classList.add('selected');
      if(loc){paintRange(loc);selectionFromLocation(loc);}else selectionFromLocation({line});
      $('#selected-range').textContent=`Token ${i+1} / ${state.tokens.length}`;
      $('#selected-range').hidden=false;
    };
    r.addEventListener('click',jump);
    r.addEventListener('keydown',e=>{
      if(e.key==='Enter'||e.key===' '){e.preventDefault();jump();}
      else if(e.key==='ArrowDown'||e.key==='ArrowUp'){
        e.preventDefault();
        const rows=[...body.querySelectorAll('tr')];
        const next=rows[(rows.indexOf(r)+(e.key==='ArrowDown'?1:-1)+rows.length)%rows.length];
        next?.focus();
      }
    });
    body.append(r);
  });
  table.append(body);surface.append(table);
}
function renderSymbols() {
  const surface=$('#symbol-surface');surface.replaceChildren();
  if(!state.symbols.length){surface.append(el('div','table-empty','Run to inspect variable values.'));return;}
  const table=el('table','data-table');const head=el('thead');const tr=el('tr');['NAME','TYPE','CURRENT VALUE'].forEach(h=>tr.append(el('th','',h)));head.append(tr);table.append(head);
  const body=el('tbody');
  state.symbols.forEach(s=>{const row=el('tr');row.append(el('td','',s.name),el('td','symbol-type',s.type),el('td','',s.value));body.append(row);});
  table.append(body);surface.append(table);
  $('#symbol-caption').textContent='Values from the latest run';
}
function setInspector(tab) {
  state.inspectorView=tab;
  $$('[data-inspector]').forEach(button=>{
    const yes=button.dataset.inspector===tab;button.classList.toggle('active',yes);
    button.setAttribute('aria-selected',String(yes));button.tabIndex=yes?0:-1;
    $('#'+button.getAttribute('aria-controls')).hidden=!yes;
  });
  if(tab==='ast') { editor.refresh(); renderAST(); }
}

function selectConsole(tab) {
  state.consoleView=tab;
  $$('[data-console]').forEach(button=>{const yes=button.dataset.console===tab;button.classList.toggle('active',yes);button.setAttribute('aria-selected',String(yes));button.tabIndex=yes?0:-1;$('#'+button.getAttribute('aria-controls')).hidden=!yes;});
  if (state.mobileView==='console') showMobileView('console');
}
function showMobileView(view) {
  state.mobileView=view;$('#workbench').dataset.mobileView=view;
  $$('.mobile-view').forEach(button=>{const yes=button.id===`mobile-${view}`;button.classList.toggle('active',yes);button.setAttribute('aria-pressed',String(yes));});
  $('#console-pane').classList.toggle('mobile-console-active',view==='console');
  if(view==='code')requestAnimationFrame(()=>editor.refresh());
}
async function api(endpoint,extra={}) {
  if(state.busy)return null;
  state.busy=true;updateButtons();setStatus('WORKING','Processing source…','busy');
  const revision=state.revision;
  const controller=new AbortController();state.abort=controller;
  try {
    const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({source:sourceText(),...extra}),signal:controller.signal});
    let data;try{data=await response.json();}catch{throw new Error('The server returned an unreadable response.');}
    if(!response.ok)throw new Error(data.message||`Request failed (${response.status})`);
    if(revision!==state.revision)return null;
    return data;
  }catch(error){
    if(error.name!=='AbortError'&&revision===state.revision){
      setStatus('CONNECTION ERROR',error.message+' Check that the Python server is running.','error');
      setDiagnostics([{stage:'network',message:error.message}]);selectConsole('problems');showMobileView('console');
    }
    return null;
  }finally{state.busy=false;state.abort=null;updateButtons();}
}
function receiveTokens(data) {
  state.tokens=Array.isArray(data.tokens)?data.tokens:[];
  state.tokenLocations=Array.isArray(data.token_locations)?data.token_locations:[];
  $('#token-count').textContent=state.tokens.length; $('#token-count').hidden=false;
  renderTokens();
}
function receiveAST(data) {
  state.ast=data.ast||null;state.astLocations=data.ast_locations||{};
  state.analyzedRevision=state.ast?state.revision:-1;
  state.collapsed.clear();state.selectedPath=null;
  buildRecords();renderAST();
  stamp(state.ast?`Mapped · ${state.records.size} nodes`:'No tree');
}
async function tokenizeOnly() {
  const response=await api('/api/tokenize');if(!response)return;
  state.ast=null;state.astLocations={};state.records=new Map();state.analyzedRevision=-1;renderAST();
  $('#ast-count').textContent=''; $('#ast-count').hidden=true;
  receiveTokens(response);setInspector('tokens');showMobileView('inspect');
  if(response.ok){setDiagnostics([]);setStages('lexer');setStatus('TOKENIZED',`${state.tokens.length} tokens`, 'success');stamp('Tokenized');}
  else {setDiagnostics([response.error]);setStages('lexer',true);selectConsole('problems');showMobileView('console');setStatus('LEXER ERROR',response.error.message,'error');stamp('Lexer error');}
}
async function analyzeProgram(fromRun=false) {
  const response=await api('/api/analyze');if(!response)return false;
  receiveTokens(response);
  if(response.ok){
    receiveAST(response);setDiagnostics([]);setStages('parser');
    setStatus('ANALYZED',`${state.records.size} AST nodes`, 'success');
    if(!fromRun){setInspector('ast');showMobileView('inspect');}
    return true;
  }
  state.ast=null;state.records=new Map();state.astLocations={};state.analyzedRevision=-1;renderAST();
  $('#ast-count').textContent=''; $('#ast-count').hidden=true;
  setDiagnostics([response.error]);setStages(response.error.stage,true);
  setStatus(`${response.error.stage.toUpperCase()} ERROR`,response.error.message,'error');stamp('Analysis failed');
  selectConsole('problems');
  if(!fromRun)showMobileView('console');
  return false;
}
async function run(fresh=true) {
  if(state.busy)return;
  const serial=++state.runningSerial;
  if(fresh){state.inputs=[];state.output='';state.waiting=false;}
  if(state.analyzedRevision!==state.revision){
    const analyzed=await analyzeProgram(true);
    if(!analyzed||serial!==state.runningSerial){if(!analyzed){state.output='';renderOutput();}return;}
  }
  const presets=$('#stdin').value ? $('#stdin').value.split('\n') : [];
  const start=performance.now();
  const data=await api('/api/run',{inputs:[...presets,...state.inputs]});
  if(!data||serial!==state.runningSerial)return;
  state.output=typeof data.output==='string'?data.output:'';
  state.symbols=Array.isArray(data.symbols)?data.symbols:[];
  state.waiting=Boolean(data.needs_input);
  state.prompt=data.prompt||'GIMMEH';
  $('#symbol-count').textContent=state.symbols.length; $('#symbol-count').hidden=false;
  $('#run-duration').textContent=`${Math.round(performance.now()-start)} ms`;
  renderOutput();renderSymbols();selectConsole('output');
  if(state.waiting){setDiagnostics([]);setStages('runtime',false,true);setStatus('INPUT NEEDED','');}
  else if(data.ok){setDiagnostics([]);setStages('runtime');setStatus('EXECUTED','Run complete.', 'success');}
  else {setDiagnostics([data.error]);setStages(data.error.stage,true);setStatus(`${data.error.stage.toUpperCase()} ERROR`,data.error.message,'error');selectConsole('problems');}
  showMobileView('console');
}
function updateSource(value,name='playground.lol') {
  editor.setValue(value);editor.clearHistory();setFilename(name);dirtyState(false);
  editor.setCursor(0,0);renderPosition();
  setStatus('READY','Source loaded.');
  showMobileView('code');
}
function downloadSource(filename) {
  const url=URL.createObjectURL(new Blob([sourceText()],{type:'text/plain;charset=utf-8'}));
  const anchor=el('a');anchor.href=url;anchor.download=filename;
  document.body.append(anchor);anchor.click();anchor.remove();
  window.setTimeout(()=>URL.revokeObjectURL(url),1200);
  setFilename(filename);dirtyState(false);setStatus('DOWNLOADED',`Downloaded ${state.filename}.`,'success');
}

// These are application-owned confirmations: the OS file picker and download
// destination (if shown by the browser) are necessarily browser-controlled.
const decisionDialog=$('#workbench-dialog');
const decisionForm=$('#dialog-form');
async function requestDecision({context='SOURCE',title,message,action='Continue',filename=null}) {
  if(decisionDialog.open)return false;
  $('#dialog-context').textContent=context;
  $('#dialog-title').textContent=title;
  $('#dialog-copy').textContent=message;
  $('#dialog-confirm').textContent=action;
  const field=$('#dialog-file-field'),input=$('#dialog-filename');
  const withFilename=typeof filename==='string';
  field.hidden=!withFilename;
  input.value=withFilename?filename:'';
  input.classList.remove('invalid');
  return new Promise(resolve=>{
    let finished=false;
    const finish=result=>{
      if(finished)return;
      finished=true;decisionDialog.close();resolve(result);
    };
    const cancel=()=>finish(false);
    decisionForm.onsubmit=e=>{
      e.preventDefault();
      if(withFilename){
        let name=input.value.trim().replace(/[\\/:*?"<>|]/g,'_');
        if(!name || /^\.+$/.test(name)){
          input.classList.add('invalid');input.focus();return;
        }
        if(!/\.(lol|txt)$/i.test(name))name+='.lol';
        finish(name);
      }else finish(true);
    };
    $('#dialog-cancel').onclick=cancel;
    $('#dialog-close').onclick=cancel;
    decisionDialog.oncancel=e=>{e.preventDefault();cancel();};
    decisionDialog.onclose=()=>{if(!finished){finished=true;resolve(false);}};
    decisionDialog.showModal();
    requestAnimationFrame(()=>withFilename?input.select():$('#dialog-cancel').focus());
  });
}
async function save() {
  const filename=await requestDecision({
    context:'SOURCE FILE', title:'Download source',
    message:'Save a local copy of the current program.',
    action:'Download',filename:state.filename||'playground.lol'
  });
  if(filename)downloadSource(filename);
}

// The default browser select popup does not share app styling. Keep the
// hidden select for sample state, but use an accessible in-app menu.
const sampleSelect=$('#example');
const sampleTrigger=$('#sample-trigger');
const sampleMenu=$('#sample-menu');
const sampleCurrent=$('#sample-current');
function updateSampleLabel(){
  sampleCurrent.textContent='Examples';
  for(const button of sampleMenu.querySelectorAll('[role="menuitemradio"]')){
    button.setAttribute('aria-checked',String(button.dataset.value===sampleSelect.value));
  }
}
function closeSampleMenu(returnFocus=false){
  sampleMenu.hidden=true;sampleTrigger.setAttribute('aria-expanded','false');
  if(returnFocus)sampleTrigger.focus();
}
function openSampleMenu(focusLast=false){
  sampleMenu.hidden=false;sampleTrigger.setAttribute('aria-expanded','true');
  const items=[...sampleMenu.querySelectorAll('[role="menuitemradio"]')];
  if(!items.length)return;
  const selected=items.find(item=>item.dataset.value===sampleSelect.value);
  (focusLast?items[items.length-1]:selected||items[0]).focus();
}
for(const option of [...sampleSelect.options]){
  const item=el('button','sample-choice');item.type='button';item.role='menuitemradio';
  item.dataset.value=option.value;item.textContent=option.textContent;
  item.addEventListener('click',()=>loadSelectedSample(option.value));
  sampleMenu.append(item);
}
sampleSelect.addEventListener('change',updateSampleLabel);
updateSampleLabel();
sampleTrigger.addEventListener('click',()=>sampleMenu.hidden?openSampleMenu():closeSampleMenu(true));
sampleTrigger.addEventListener('keydown',e=>{
  if(['ArrowDown','ArrowUp',' ','Enter'].includes(e.key)){
    e.preventDefault();if(sampleMenu.hidden)openSampleMenu(e.key==='ArrowUp');
  }
});
sampleMenu.addEventListener('keydown',e=>{
  const items=[...sampleMenu.querySelectorAll('[role="menuitemradio"]')];
  const current=items.indexOf(document.activeElement);
  if(e.key==='Escape'){e.preventDefault();closeSampleMenu(true);}
  else if(e.key==='Tab')closeSampleMenu();
  else if(['ArrowDown','ArrowUp','Home','End'].includes(e.key)){
    e.preventDefault();
    const next=e.key==='Home'?0:e.key==='End'?items.length-1:(current+(e.key==='ArrowDown'?1:-1)+items.length)%items.length;
    items[next].focus();
  }
});
document.addEventListener('pointerdown',e=>{
  if(!sampleMenu.hidden&&!$('#sample-selector').contains(e.target))closeSampleMenu();
});

const keymapsDialog=$('#keymaps-dialog');
function openKeymaps(){if(decisionDialog.open||keymapsDialog.open)return;keymapsDialog.showModal();$('#keymaps-close').focus();}
function closeKeymaps(){keymapsDialog.close();}
$('#show-keymaps').addEventListener('click',openKeymaps);
$('#keymaps-close').addEventListener('click',closeKeymaps);
$('#keymaps-done').addEventListener('click',closeKeymaps);
function attachTabKeys(selector,setter) {
  const tabs=$$(selector);
  tabs.forEach((item,index)=>item.addEventListener('keydown',e=>{
    if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;
    e.preventDefault();const step=e.key==='ArrowRight'?1:-1;
    const next=e.key==='Home'?0:e.key==='End'?tabs.length-1:(index+step+tabs.length)%tabs.length;
    setter(tabs[next]);tabs[next].focus();
  }));
}
$$('[data-mode]').forEach(b=>b.addEventListener('click',()=>selectAstMode(b.dataset.mode)));
$('#ast-find').addEventListener('input',event=>{
  state.astQuery=event.target.value;
  expandAstAncestors(matchingAstPaths());
  if(state.ast && state.astMode==='outline')renderOutline();
});
$('#ast-find').addEventListener('keydown',event=>{
  if(event.key==='Escape'){
    event.preventDefault();event.target.value='';state.astQuery='';renderOutline();event.target.blur();
  } else if(event.key==='Enter'){
    event.preventDefault();
    const matches=matchingAstPaths();
    if(!matches.length)return;
    const current=matches.indexOf(state.selectedPath);
    const index=(current+(event.shiftKey?-1:1)+matches.length)%matches.length;
    selectPath(matches[index],true);
    const row=[...document.querySelectorAll('.tree-node')].find(node=>node.dataset.path===matches[index]);
    row?.scrollIntoView({block:'nearest'});
  }
});
$('#ast-fold').addEventListener('click',()=>{
  const branches=[...state.records.values()].filter(rec=>rec.children.length&&rec.path!=='$');
  const folded=branches.length>0&&branches.every(rec=>state.collapsed.has(rec.path));
  if(folded)state.collapsed.clear();
  else {state.collapsed.clear();branches.forEach(rec=>state.collapsed.add(rec.path));}
  expandAstAncestors(matchingAstPaths());
  renderOutline();
});
function setGraphZoom(value) {
  state.zoom=Math.max(.45,Math.min(1.8,Math.round(value*100)/100));
  $('#zoom-fit').title=`Fit tree · currently ${Math.round(state.zoom*100)}%`;
  if(state.astMode==='graph')renderAST();
}
$('#zoom-out').addEventListener('click',()=>setGraphZoom(state.zoom-.2));
$('#zoom-in').addEventListener('click',()=>setGraphZoom(state.zoom+.2));
$('#zoom-fit').addEventListener('click',()=>{
  const scroll=$('.ast-graph-scroll'),stage=$('.graph-stage');
  if(!scroll||!stage)return;
  const width=parseFloat(stage.style.width),height=parseFloat(stage.style.height);
  setGraphZoom(Math.min(1,(scroll.clientWidth-20)/width,(scroll.clientHeight-20)/height));
});
$$('[data-inspector]').forEach(b=>b.addEventListener('click',()=>setInspector(b.dataset.inspector)));
$$('[data-console]').forEach(b=>b.addEventListener('click',()=>selectConsole(b.dataset.console)));
attachTabKeys('[data-inspector]',b=>setInspector(b.dataset.inspector));
attachTabKeys('[data-console]',b=>selectConsole(b.dataset.console));
$('#tokenize').addEventListener('click',tokenizeOnly);
$('#analyze').addEventListener('click',()=>analyzeProgram());
$('#run').addEventListener('click',()=>run(true));
$('#reset').addEventListener('click',()=>{if(state.busy)return;clearResults();selectConsole('output');setInspector('ast');});
$('#token-filter').addEventListener('input',renderTokens);
$('#toggle-input').addEventListener('click',()=>{
  const open=$('#preset-input-wrap').hidden;
  $('#preset-input-wrap').hidden=!open;const toggle=$('#toggle-input');toggle.setAttribute('aria-expanded',String(open));toggle.classList.toggle('open',open);
});
$('#stdin').addEventListener('keydown',e=>{
  if(e.key==='Escape'){e.preventDefault();$('#preset-input-wrap').hidden=true;$('#toggle-input').setAttribute('aria-expanded','false');$('#toggle-input').classList.remove('open');$('#toggle-input').focus();}
});
$('#stdin').addEventListener('input',()=>{
  $('#clear-input').disabled=!$('#stdin').value;
  state.inputs=[];state.waiting=false;state.output='';renderOutput();$('#run-duration').textContent='';
  setStatus('INPUT UPDATED','Run again to apply changes.');
});
$('#clear-input').addEventListener('click',async()=>{
  if(!$('#stdin').value)return;
  const okay=await requestDecision({
    context:'INPUT',title:'Clear preset input?',
    message:'The values prepared for GIMMEH will be removed. Your source code is unaffected.',
    action:'Clear values'
  });
  if(!okay)return;
  $('#stdin').value=''; $('#stdin').dispatchEvent(new Event('input',{bubbles:true})); $('#stdin').focus();
});
$('#clear-input').disabled=true;
const mobileExamples=$('#mobile-samples-panel');
const mobileSamplesToggle=$('#mobile-samples-toggle');
function setMobileSamples(open) {
  $('#app-shell').classList.toggle('samples-open',open);
  if(!open)closeSampleMenu();
  mobileSamplesToggle.setAttribute('aria-expanded',String(open));
  mobileSamplesToggle.setAttribute('aria-label',open?'Close sample programs':'Choose a sample program');
}
mobileSamplesToggle.addEventListener('click',()=>setMobileSamples(mobileSamplesToggle.getAttribute('aria-expanded')!=='true'));
mobileExamples.addEventListener('keydown',event=>{
  if(event.key==='Escape') {event.preventDefault();setMobileSamples(false);mobileSamplesToggle.focus();}
});
async function loadSelectedSample(value){
  if(!Object.hasOwn(EXAMPLES,value))return;
  const name=[...sampleSelect.options].find(option=>option.value===value)?.textContent || 'this sample';
  closeSampleMenu();
  if(state.dirty){
    const okay=await requestDecision({
      context:'SAMPLE',title:'Replace current source?',
      message:`Loading “${name}” replaces your unsaved edits. Download a copy first if you need them.`,
      action:'Replace source'
    });
    if(!okay){sampleTrigger.focus();return;}
  }
  sampleSelect.value=value;
  updateSampleLabel();
  updateSource(EXAMPLES[value], 'playground.lol');
  setMobileSamples(false);
  sampleTrigger.focus();
}
$('#open').addEventListener('click',()=>{closeSampleMenu();$('#file').click();});
$('#file').addEventListener('change',async event=>{
  const file=event.target.files?.[0];if(!file)return;
  try {
    if(file.size>90_000)throw new Error('Choose a file smaller than 90 KB.');
    if(!/\.(lol|txt)$/i.test(file.name))throw new Error('Choose a .lol or .txt source file.');
    if(state.dirty){
      const okay=await requestDecision({
        context:'OPEN FILE',title:'Replace current source?',
        message:`Opening “${file.name}” will replace your unsaved edits. Download a copy first if you need them.`,
        action:'Open file'
      });
      if(!okay)return;
    }
    updateSource(await file.text(),file.name);
  }catch(error){setStatus('FILE ERROR',error.message,'error');}
  finally {event.target.value='';}
});
$('#download').addEventListener('click',save);
$('#explore').addEventListener('click',()=>{
  const active=$('#workbench').classList.toggle('expanded');
  $('#explore').setAttribute('aria-pressed',String(active));
  $('#explore').textContent=active?'Restore':'Expand';
  requestAnimationFrame(()=>editor.refresh());
});
$$('.mobile-view').forEach(b=>b.addEventListener('click',()=>showMobileView(b.id.slice(7))));
const divider=$('#pane-resizer'),workbench=$('#workbench');
const resize=x=>{
  if(workbench.classList.contains('expanded'))return;
  const rect=workbench.getBoundingClientRect();const share=Math.max(30,Math.min(70,Math.round((x-rect.left)/rect.width*100)));
  workbench.style.setProperty('--source-share',`${share}%`);divider.setAttribute('aria-valuenow',String(share));editor.refresh();
};
divider.addEventListener('pointerdown',e=>{if(window.matchMedia('(max-width:740px)').matches)return;e.preventDefault();divider.setPointerCapture(e.pointerId);});
divider.addEventListener('pointermove',e=>{if(divider.hasPointerCapture(e.pointerId))resize(e.clientX);});
divider.addEventListener('keydown',e=>{
  if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();
  const amount=Number(divider.getAttribute('aria-valuenow'))+(e.key==='ArrowLeft'?-2:e.key==='ArrowRight'?2:0);
  const share=e.key==='Home'?30:e.key==='End'?70:Math.max(30,Math.min(70,amount));
  workbench.style.setProperty('--source-share',`${share}%`);divider.setAttribute('aria-valuenow',String(share));editor.refresh();
});
window.addEventListener('resize',()=>editor.refresh());
window.addEventListener('beforeunload',e=>{if(state.dirty){e.preventDefault();e.returnValue='';}});
document.addEventListener('keydown', e => {
  if (!document.body.classList.contains('workbench-ready')) return;
  const command = e.metaKey || e.ctrlKey;
  if (e.altKey || e.isComposing) return;

  // '?' is the discoverable shortcut. Some keyboard layouts report the
  // combination as Shift+Slash rather than the '?' character.
  const questionMark = !command && (
    e.key === '?' || (e.shiftKey && (e.key === '/' || e.code === 'Slash'))
  );
  const commandSlash = command && (e.key === '/' || e.code === 'Slash');
  if (questionMark || commandSlash) {
    // In inputs and LOLCODE string/comment literals, '?' is text, not a
    // command. Everywhere else (including the editor) it opens help.
    const target = e.target;
    const nativeField = target && target.matches &&
      target.matches('input, textarea, [contenteditable="true"]');
    const insideEditor = target && target.closest && target.closest('.CodeMirror');
    const tokenType = insideEditor && editor && editor.getTokenTypeAt(editor.getCursor());
    const typingLiteral = questionMark && insideEditor &&
      /\b(string|comment)\b/.test(tokenType || '');
    if (!typingLiteral && (!questionMark || !nativeField || insideEditor)) {
      e.preventDefault();
      if (!decisionDialog.open && !keymapsDialog.open) openKeymaps();
    }
    return;
  }

  if (!command || decisionDialog.open || keymapsDialog.open) return;
  if (e.key === 'Enter') { e.preventDefault(); run(true); }
  else if (e.key.toLowerCase() === 's') { e.preventDefault(); save(); }
  else if (e.key.toLowerCase() === 'o') { e.preventDefault(); $('#file').click(); }
});

// The initial HAI loading line is short; once ready, the welcome screen
// offers one clear path into the editor. Subsequent reloads in the same tab
// bypass the extra click without bypassing application initialization.
state.revision=0;dirtyState(false);clearResults(true);renderPosition();showMobileView('code');
setStatus('READY','');
const loading = $('#boot-screen');
const launchEditor = $('#launch-editor');
const appShell = $('#app-shell');
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const minimumBootMs = reducedMotion ? 180 : 1650;
const bootStart = Number.isFinite(window.__haiBootStart) ? window.__haiBootStart : performance.now();
const remainingBootMs = Math.max(0, minimumBootMs - (performance.now() - bootStart));
const launchedInThisTab = (() => {
  try { return sessionStorage.getItem('hai.editor.launched') === '1'; }
  catch { return false; }
})();
let editorOpened = false;
function enterWorkbench() {
  if (editorOpened) return;
  editorOpened = true;
  try { sessionStorage.setItem('hai.editor.launched', '1'); } catch { /* optional */ }
  appShell.inert = false;
  document.body.classList.add('workbench-ready');
  if (loading) {
    loading.setAttribute('aria-hidden', 'true');
    loading.inert = true;
    window.setTimeout(() => loading.remove(), reducedMotion ? 0 : 190);
  }
  requestAnimationFrame(() => editor.refresh());
}
launchEditor.addEventListener('click', enterWorkbench);
window.setTimeout(() => {
  document.body.classList.add('boot-complete');
  if (launchedInThisTab) {
    enterWorkbench();
    return;
  }
  launchEditor.hidden = false;
  $('#boot-status').textContent = 'Editor ready';
  launchEditor.focus({preventScroll:true});
}, remainingBootMs);
})();
