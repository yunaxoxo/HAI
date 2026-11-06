// --- Elements ---
const source = document.querySelector('#source');
const stdin = document.querySelector('#stdin');
const lines = document.querySelector('#lines');
const buttons = ['#tokenize', '#analyze', '#run'].map(id => document.querySelector(id));
const panels = {
  output: document.querySelector('#output-panel'),
  tokens: document.querySelector('#tokens-panel'),
  tree: document.querySelector('#tree-panel'),
  symbols: document.querySelector('#symbols-panel')
};
const examples = {
  hello: 'HAI\n\nBTW My first LOLCODE program\nVISIBLE "HAI, WORLD!"\n\nKTHXBYE\n',
  math: 'HAI\n\nWAZZUP\n    I HAS A first ITZ 12\n    I HAS A second ITZ 8\nBUHBYE\n\nVISIBLE SUM OF first AN second\n\nKTHXBYE\n',
  conditional: 'HAI\n\nBOTH SAEM 5 AN 5\nO RLY?\n    YA RLY\n        VISIBLE "They match!"\n    NO WAI\n        VISIBLE "Try again."\nOIC\n\nKTHXBYE\n',
  input: 'HAI\n\nWAZZUP\n    I HAS A age\nBUHBYE\n\nGIMMEH age\nVISIBLE SUM OF age AN 1\n\nKTHXBYE\n'
};
const LITERALS = ['NUMBR', 'NUMBAR', 'YARN', 'TROOF'];
const PUNCTUATION = ['NEWLINE', 'PLUS', 'COMMA', 'EXCLAMATION'];
let revision = 0;
let busy = false;
let tabTrapReleased = false;
let liveInputs = [];

// --- Pipeline rail ---
const STAGES = ['lexer', 'parser', 'runtime'];
function showStages(reached, failed = false, waiting = false) {
  const last = STAGES.indexOf(reached);
  document.querySelectorAll('.pipeline li').forEach(item => {
    const index = STAGES.indexOf(item.dataset.stage);
    item.dataset.state = index > last ? 'idle' : index < last ? 'ok' : failed ? 'error' : waiting ? 'active' : 'ok';
  });
}

// --- Small helpers ---
function setStatus(label, message, error = false) {
  document.querySelector('#status').classList.toggle('error', error);
  document.querySelector('#status-label').textContent = label;
  document.querySelector('#status-message').textContent = message;
}

function empty(message, glyph = '[ ]') {
  const box = document.createElement('div');
  box.className = 'empty';
  const mark = document.createElement('span');
  mark.className = 'glyph';
  mark.textContent = glyph;
  box.append(mark, message);
  return box;
}

function errorBox(error) {
  const box = document.createElement('div');
  box.className = 'error-box';
  const label = document.createElement('b');
  label.textContent = `ERROR · ${error.stage.toUpperCase()}`;
  box.append(label, document.createElement('br'), error.message);
  return box;
}

function makeTable(headings, rows, onRowClick) {
  const table = document.createElement('table');
  const head = table.createTHead().insertRow();
  for (const heading of headings) {
    const cell = document.createElement('th');
    cell.scope = 'col';
    cell.textContent = heading;
    head.append(cell);
  }
  const body = table.createTBody();
  rows.forEach((row, index) => {
    const tableRow = body.insertRow();
    tableRow.style.setProperty('--i', Math.min(index, 30));
    row.forEach(cell => {
      const td = tableRow.insertCell();
      td.textContent = cell.text;
      if (cell.className) td.className = cell.className;
    });
    if (onRowClick) {
      tableRow.className = 'jump';
      tableRow.title = 'Jump to this line';
      tableRow.addEventListener('click', () => onRowClick(row));
    }
  });
  return table;
}

function selectTab(name) {
  document.querySelectorAll('[role="tab"]').forEach(tab => {
    const selected = tab.id === `${name}-tab`;
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
    document.getElementById(tab.getAttribute('aria-controls')).hidden = !selected;
  });
}

function jumpToLine(lineNumber) {
  const all = source.value.split('\n');
  const start = all.slice(0, lineNumber - 1).join('\n').length + (lineNumber > 1 ? 1 : 0);
  source.focus();
  source.setSelectionRange(start, start + (all[lineNumber - 1] || '').length);
  source.scrollTop = Math.max(0, (lineNumber - 3) * 22);
  updateEditor();
}

// --- Editor ---
function updateEditor() {
  lines.textContent = source.value.split('\n').map((_, index) => index + 1).join('\n');
  const before = source.value.slice(0, source.selectionStart).split('\n');
  document.querySelector('#position').textContent = `Ln ${before.length}, Col ${before.at(-1).length + 1}`;
  lines.scrollTop = source.scrollTop;
  source.style.backgroundPositionY = `${(before.length - 1) * 22 - source.scrollTop}px`;
}

function resetResults() {
  panels.output.replaceChildren(empty('Run your program to see its output here.', '>_'));
  panels.tokens.replaceChildren(empty('Tokenize or analyze to list the lexer output.'));
  panels.tree.replaceChildren(empty('Analyze or run a valid program to see its syntax tree.', '{ }'));
  panels.symbols.replaceChildren(empty('Run your program to see its variables.', 'x='));
  document.querySelector('#token-count').textContent = '0';
}

function changed() {
  revision++;
  liveInputs = [];
  updateEditor();
  resetResults();
  showStages('none');
  setStatus('EDITED', 'Code changed. Tokenize, Analyze, or Run to refresh the results.');
}

// --- Rendering ---
function showTokens(tokens) {
  document.querySelector('#token-count').textContent = tokens.length;
  if (!tokens.length) {
    panels.tokens.replaceChildren(empty('The lexer produced no tokens.'));
    return;
  }
  const rows = tokens.map(([kind, lexeme, line]) => {
    const className = LITERALS.includes(kind) ? 'lit' : PUNCTUATION.includes(kind) ? 'punct' : kind === 'IDENTIFIER' ? 'ident' : 'kw';
    return [{text: line}, {text: kind, className}, {text: lexeme === '\n' ? '↵' : lexeme}];
  });
  panels.tokens.replaceChildren(makeTable(['LINE', 'TOKEN', 'LEXEME'], rows, row => jumpToLine(Number(row[0].text))));
}

function showTree(ast) {
  const tree = document.createElement('pre');
  tree.className = 'tree';
  tree.textContent = JSON.stringify(ast, null, 2);
  panels.tree.replaceChildren(tree);
}

function showSymbols(symbols) {
  if (!symbols.length) {
    panels.symbols.replaceChildren(empty('No variables were set.'));
    return;
  }
  const rows = symbols.map(item => [{text: item.name, className: 'kw'}, {text: item.type}, {text: item.value}]);
  panels.symbols.replaceChildren(makeTable(['NAME', 'TYPE', 'VALUE'], rows));
}

// --- Requests ---
async function request(endpoint, extra = {}) {
  if (busy) return null;
  busy = true;
  buttons.forEach(button => { button.disabled = true; });
  document.body.classList.add('busy');
  const current = revision;
  try {
    const response = await fetch(endpoint, {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({source: source.value, ...extra})
    });
    const result = await response.json();
    if (current !== revision) return null;
    if (!response.ok) throw new Error(result.message || 'The request failed.');
    return result;
  } catch (error) {
    if (current === revision) setStatus('OFFLINE', `${error.message} Is the Python server still running?`, true);
    return null;
  } finally {
    busy = false;
    document.body.classList.remove('busy');
    buttons.forEach(button => { button.disabled = false; });
  }
}

async function tokenizeOnly() {
  setStatus('WORKING', 'Reading tokens…');
  const result = await request('/api/tokenize');
  if (!result) return;
  showTokens(result.tokens);
  selectTab('tokens');
  showStages('lexer', !result.ok);
  if (result.ok) setStatus('TOKENS OK', `${result.tokens.length} tokens from the lexer.`);
  else {
    setStatus('LEXER ERROR', result.error.message, true);
    if (result.error.line) jumpToLine(result.error.line);
  }
}

async function analyze() {
  setStatus('WORKING', 'Tokenizing and parsing…');
  const result = await request('/api/analyze');
  if (!result) return;
  showTokens(result.tokens);
  showStages(result.ok ? 'parser' : result.error.stage, !result.ok);
  if (result.ok) {
    showTree(result.ast);
    selectTab('tree');
    setStatus('SYNTAX OK', `${result.tokens.length} tokens · ${result.ast.body.length} top-level statements · ${result.ast.functions.length} functions.`);
  } else {
    panels.tree.replaceChildren(errorBox(result.error));
    selectTab('tree');
    setStatus(`${result.error.stage.toUpperCase()} ERROR`, result.error.message, true);
  }
}

function promptRow(prompt) {
  const row = document.createElement('div');
  row.className = 'prompt-row';
  const label = document.createElement('label');
  label.textContent = prompt;
  const field = document.createElement('input');
  field.type = 'text';
  field.autocomplete = 'off';
  field.setAttribute('aria-label', `Answer for ${prompt.trim()}`);
  const send = document.createElement('button');
  send.textContent = 'Send';
  const submit = () => { liveInputs.push(field.value); run(false); };
  field.addEventListener('keydown', event => { if (event.key === 'Enter') { event.preventDefault(); submit(); } });
  send.addEventListener('click', submit);
  label.append(field);
  row.append(label, send);
  return row;
}

async function run(fresh = true) {
  if (fresh) liveInputs = [];
  setStatus('RUNNING', 'Running (stops after 5 seconds)…');
  const presets = stdin.value ? stdin.value.split('\n') : [];
  const result = await request('/api/run', {inputs: [...presets, ...liveInputs]});
  if (!result) return;
  const children = [];
  if (result.output) {
    const out = document.createElement('pre');
    out.className = 'out';
    out.textContent = result.output;
    children.push(out);
  } else if (result.ok && !result.needs_input) {
    children.push(empty('The program finished without printing anything.'));
  }
  if (!result.ok) children.push(errorBox(result.error));
  if (result.needs_input) children.push(promptRow(result.prompt));
  panels.output.replaceChildren(...children);
  showSymbols(result.symbols);
  showStages(result.ok ? 'runtime' : result.error.stage, !result.ok, result.needs_input);
  selectTab('output');
  if (result.needs_input) {
    setStatus('WAITING', `The program is asking for input (${result.prompt.trim()}). Type a value and press Enter.`);
    panels.output.querySelector('.prompt-row input').focus();
  } else if (result.ok) setStatus('DONE', 'Program finished.');
  else setStatus(`${result.error.stage.toUpperCase()} ERROR`, result.error.message, true);
}

// --- Events ---
const tabs = [...document.querySelectorAll('[role="tab"]')];
tabs.forEach((tab, index) => {
  tab.addEventListener('click', () => selectTab(tab.id.replace('-tab', '')));
  tab.addEventListener('keydown', event => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    const step = event.key === 'ArrowRight' ? 1 : -1;
    const next = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 : (index + step + tabs.length) % tabs.length;
    selectTab(tabs[next].id.replace('-tab', ''));
    tabs[next].focus();
  });
});
source.addEventListener('input', changed);
source.addEventListener('click', updateEditor);
source.addEventListener('keyup', updateEditor);
source.addEventListener('scroll', updateEditor);
source.addEventListener('keydown', event => {
  if (event.key === 'Escape') { tabTrapReleased = true; return; }
  if (event.key === 'Tab' && !tabTrapReleased && !event.shiftKey) {
    event.preventDefault();
    source.setRangeText('    ', source.selectionStart, source.selectionEnd, 'end');
    changed();
  }
  tabTrapReleased = false;
});
document.addEventListener('keydown', event => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    event.preventDefault();
    run();
  }
});
document.querySelector('#tokenize').addEventListener('click', tokenizeOnly);
document.querySelector('#analyze').addEventListener('click', analyze);
document.querySelector('#run').addEventListener('click', () => run());
document.querySelector('#clear').addEventListener('click', () => { resetResults(); showStages('none'); setStatus('READY', 'Results cleared.'); });
document.querySelector('#load').addEventListener('click', () => {
  if (source.value.trim() && !confirm('Replace the current code with this example?')) return;
  source.value = examples[document.querySelector('#example').value];
  changed();
});
document.querySelector('#open').addEventListener('click', () => document.querySelector('#file').click());
document.querySelector('#file').addEventListener('change', async event => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    if (file.size > 90000) throw new Error('Choose a file smaller than 90 KB.');
    if (source.value.trim() && !confirm('Replace the current code with this file?')) return;
    source.value = await file.text();
    changed();
  } catch (error) {
    setStatus('FILE ERROR', error.message, true);
  } finally {
    event.target.value = '';
  }
});
document.querySelector('#download').addEventListener('click', () => {
  const url = URL.createObjectURL(new Blob([source.value], {type: 'text/plain;charset=utf-8'}));
  const link = document.createElement('a');
  link.href = url;
  link.download = 'playground.lol';
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

// --- Startup ---
source.value = examples.hello;
resetResults();
updateEditor();

