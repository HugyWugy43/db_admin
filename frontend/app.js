// DB Administrator Frontend — API относительно текущего хоста (как в /static/)
const API = `${window.location.origin}/api`;

let state = {
  user: null,
  token: null,
  currentDB: null,
  currentSchema: 'public',
  currentTable: null,
  pageNum: 0,
  pageSize: 20
};

async function parseErrorResponse(r) {
  try {
    const data = await r.json();
    if (typeof data.detail === 'string') return data.detail;
    if (Array.isArray(data.detail)) return data.detail.map((e) => e.msg || JSON.stringify(e)).join(', ');
    if (data.detail) return String(data.detail);
    return r.statusText || `HTTP ${r.status}`;
  } catch {
    return r.statusText || `HTTP ${r.status}`;
  }
}

function formatBytes(n) {
  if (n == null || Number.isNaN(n)) return '—';
  const units = ['Б', 'КиБ', 'МиБ', 'ГиБ', 'ТиБ'];
  let v = Number(n);
  if (v < 1024) return `${v} ${units[0]}`;
  let i = 1;
  v /= 1024;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i++;
  }
  return `${v < 10 ? v.toFixed(1) : Math.round(v)} ${units[i]}`;
}

// INIT
window.addEventListener('DOMContentLoaded', () => {
  const token = localStorage.getItem('token');
  if (token) {
    state.token = token;
    state.user = localStorage.getItem('user');
    showApp();
    loadStats();
  }
});

// ===== AUTH =====
function switchTab(t, evt) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.form').forEach(f => f.classList.remove('active'));
  evt?.target?.classList.add('active');
  document.getElementById(t + 'Form').classList.add('active');
}

async function handleRegister(e) {
  e.preventDefault();
  const payload = {
    username: document.getElementById('regUser').value.trim(),
    email: document.getElementById('regEmail').value.trim(),
    password: document.getElementById('regPass').value
  };

  try {
    const r = await fetch(`${API}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await r.json();
    if (!r.ok) {
      const message = data.detail || (Array.isArray(data) ? data.map(err => err.msg).join(', ') : 'Ошибка регистрации');
      throw new Error(message);
    }

    document.getElementById('regMsg').textContent = '✅ Успешно! Теперь войдите';
    setTimeout(() => switchTab('login', null), 1500);
  } catch (err) {
    document.getElementById('regMsg').textContent = '❌ ' + err.message;
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const payload = {
    username: document.getElementById('loginUser').value.trim(),
    password: document.getElementById('loginPass').value
  };

  try {
    const r = await fetch(`${API}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await r.json();
    if (!r.ok) {
      const message = data.detail || 'Неверные учетные данные';
      throw new Error(message);
    }

    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', data.username);
    localStorage.setItem('userId', String(data.user_id));

    state.token = data.access_token;
    state.user = data.username;
    showApp();
    loadStats();
  } catch (err) {
    document.getElementById('loginMsg').textContent = '❌ ' + err.message;
  }
}

function logout() {
  localStorage.clear();
  location.reload();
}

// ===== UI =====
function showApp() {
  document.getElementById('loginPage').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
  document.getElementById('userName').textContent = state.user;
}

function go(page, evt) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
  document.getElementById('page-' + page).classList.add('active');
  evt?.target?.classList.add('active');
  if (page === 'dash') loadStats();
  if (page === 'db') loadDBList();
  if (page === 'logs') loadLogs();
  if (page === 'profile') loadProfile();
}

// ===== DASHBOARD =====
async function loadStats() {
  const hint = document.getElementById('dashHint');
  const tbody = document.getElementById('dashConnectionsBody');
  try {
    const r = await fetch(`${API}/admin/dashboard`, {
      headers: { Authorization: `Bearer ${state.token}` }
    });
    if (!r.ok) {
      hint.textContent = 'Не удалось загрузить дашборд: ' + (await parseErrorResponse(r));
      return;
    }
    const data = await r.json();
    const s = data.summary || {};
    document.getElementById('stat-users').textContent = s.total_users ?? 0;
    document.getElementById('stat-dbs').textContent = s.total_databases ?? 0;
    document.getElementById('stat-active').textContent = s.active_connections ?? 0;
    const totalB = s.remote_databases_total_bytes;
    document.getElementById('stat-remote-size').textContent =
      typeof totalB === 'number' && totalB > 0 ? formatBytes(totalB) : (totalB === 0 ? '0 Б' : '—');
    const reach = s.remote_databases_reachable_count ?? 0;
    const totalConn = (data.connections || []).length;
    hint.textContent =
      `Доступно для опроса размера: ${reach} из ${totalConn} подключений. ` +
      'Размер — это pg_database_size (данные в кластере), не свободное место на диске сервера.';
    tbody.innerHTML = (data.connections || [])
      .map((c) => {
        const m = c.metrics || {};
        const sz = m.reachable && m.database_size_bytes != null ? formatBytes(m.database_size_bytes) : '—';
        const sess = m.reachable && m.active_backends != null ? m.active_backends : '—';
        const err = m.error ? `<span title="${escapeHtml(m.error)}">ошибка</span>` : '';
        return `<tr>
          <td>${escapeHtml(c.name)}</td>
          <td>${escapeHtml(c.host)}:${c.port}</td>
          <td>${escapeHtml(c.database_name)}</td>
          <td>${escapeHtml(c.status || '—')}${err ? ' ' + err : ''}</td>
          <td>${sz}</td>
          <td>${sess}</td>
        </tr>`;
      })
      .join('');
    if (!data.connections || !data.connections.length) {
      tbody.innerHTML = '<tr><td colspan="6">Нет сохранённых подключений</td></tr>';
    }
  } catch (e) {
    console.error(e);
    hint.textContent = 'Ошибка сети при загрузке дашборда';
  }
}

// ===== DATABASES =====
async function loadDBList() {
  const grid = document.getElementById('dbGrid');
  const msg = document.getElementById('dbListMsg');
  msg.textContent = '';
  grid.innerHTML = '<p class="empty">Загрузка…</p>';
  try {
    const r = await fetch(`${API}/admin/databases?skip=0&limit=100`, {
      headers: { Authorization: `Bearer ${state.token}` }
    });
    if (!r.ok) {
      const err = await parseErrorResponse(r);
      grid.innerHTML = '';
      msg.textContent = '❌ ' + err;
      return;
    }
    const dbs = await r.json();
    grid.innerHTML = '';
    if (!dbs.length) {
      grid.innerHTML = '<p class="empty">Нет сохранённых подключений. Нажмите «Новое подключение».</p>';
      return;
    }
    dbs.forEach(db => {
      const card = document.createElement('div');
      card.className = 'db-card';
      const statusClass = db.status === 'connected' ? 'status-ok' : db.status === 'error' ? 'status-err' : '';
      card.innerHTML = `
        <h3>${escapeHtml(db.name)}</h3>
        <p class="db-status ${statusClass}"><strong>Статус:</strong> ${escapeHtml(db.status || '—')}</p>
        <p><strong>Хост:</strong> ${escapeHtml(db.host)}:${db.port}</p>
        <p><strong>БД:</strong> ${escapeHtml(db.database_name)}</p>
        <p><strong>Пользователь:</strong> ${escapeHtml(db.username)}</p>
        <div class="card-actions">
          <button type="button" class="btn btn-sm" onclick="openDB(${db.id})">Открыть</button>
          <button type="button" class="btn btn-sm" onclick="testDB(${db.id})">Тест</button>
          <button type="button" class="btn btn-sm" onclick="backupDB(${db.id})" title="pg_dump в каталог backups">Бэкап</button>
          <button type="button" class="btn btn-sm btn-danger" onclick="delDB(${db.id})">Удалить</button>
        </div>
      `;
      grid.appendChild(card);
    });
  } catch (e) {
    console.error(e);
    grid.innerHTML = '';
    msg.textContent = '❌ ' + (e.message || 'Ошибка сети');
  }
}

function escapeHtml(s) {
  if (s == null) return '';
  const div = document.createElement('div');
  div.textContent = s;
  return div.innerHTML;
}

async function openDB(id) {
  try {
    const r = await fetch(`${API}/admin/databases?skip=0&limit=100`, {
      headers: { Authorization: `Bearer ${state.token}` }
    });
    if (!r.ok) {
      alert('❌ ' + (await parseErrorResponse(r)));
      return;
    }
    const dbs = await r.json();
    state.currentDB = dbs.find(d => d.id === id);
    if (!state.currentDB) {
      alert('Подключение не найдено');
      return;
    }
    state.currentSchema = 'public';
    state.currentTable = null;
    state.pageNum = 0;
    document.getElementById('dbList').classList.add('hidden');
    document.getElementById('dbDetail').classList.remove('hidden');
    document.getElementById('dbName').textContent = state.currentDB.name;
    document.getElementById('tablePanel').classList.add('hidden');
    loadSchemas();
    loadTables();
  } catch (e) { console.error(e); }
}

function backDB() {
  document.getElementById('dbList').classList.remove('hidden');
  document.getElementById('dbDetail').classList.add('hidden');
  state.currentDB = null;
  state.currentTable = null;
  loadDBList();
}

async function testDB(id) {
  try {
    const r = await fetch(`${API}/admin/databases/${id}/test-connection`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${state.token}` }
    });
    const data = r.ok ? await r.json() : null;
    if (r.ok && data?.status === 'connected') alert('✅ Подключение успешно!');
    else alert('❌ ' + (data?.message || (await parseErrorResponse(r))));
    loadDBList();
    loadStats();
  } catch (e) { alert('❌ Ошибка'); }
}

async function backupDB(id) {
  if (!confirm('Запустить pg_dump для этой БД? Файл появится в каталоге backups на сервере приложения.')) return;
  try {
    const r = await fetch(`${API}/admin/databases/${id}/backup`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${state.token}` }
    });
    const data = r.ok ? await r.json() : null;
    if (r.ok && data?.filename) {
      const dl = confirm(
        `Готово: ${data.filename} (${formatBytes(data.size_bytes)})\n\nСкачать файл сейчас?`
      );
      if (dl) {
        const dr = await fetch(
          `${API}/admin/databases/${id}/backups/download?filename=${encodeURIComponent(data.filename)}`,
          { headers: { Authorization: `Bearer ${state.token}` } }
        );
        if (dr.ok) {
          const blob = await dr.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = data.filename;
          a.click();
          URL.revokeObjectURL(url);
        } else {
          alert('Скачивание: ' + (await parseErrorResponse(dr)));
        }
      }
      loadStats();
    } else {
      alert('❌ ' + (await parseErrorResponse(r)));
    }
  } catch (e) {
    alert('❌ ' + e.message);
  }
}

async function delDB(id) {
  if (!confirm('Удалить?')) return;
  try {
    const r = await fetch(`${API}/admin/databases/${id}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${state.token}` }
    });
    if (r.ok) {
      if (state.currentDB?.id === id) backDB();
      loadDBList();
    } else alert(await parseErrorResponse(r));
  } catch (e) { console.error(e); }
}

// ===== SCHEMAS & TABLES =====
async function loadSchemas() {
  if (!state.currentDB) return;
  try {
    const r = await fetch(`${API}/admin/databases/${state.currentDB.id}/schemas`, {
      headers: { Authorization: `Bearer ${state.token}` }
    });
    if (!r.ok) return;
    const schemas = await r.json();
    const list = document.getElementById('schemasList');
    list.innerHTML = '';
    schemas.forEach(s => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'list-item' + (s.name === state.currentSchema ? ' active' : '');
      btn.textContent = s.name;
      btn.onclick = () => {
        state.currentSchema = s.name;
        state.currentTable = null;
        state.pageNum = 0;
        document.getElementById('tablePanel').classList.add('hidden');
        loadSchemas();
        loadTables();
      };
      list.appendChild(btn);
    });
  } catch (e) { console.error(e); }
}

async function loadTables() {
  if (!state.currentDB) return;
  try {
    const r = await fetch(
      `${API}/admin/databases/${state.currentDB.id}/tables?schema=${encodeURIComponent(state.currentSchema)}`,
      { headers: { Authorization: `Bearer ${state.token}` } }
    );
    if (!r.ok) return;
    const tables = await r.json();
    const list = document.getElementById('tablesList');
    list.innerHTML = '';
    if (!tables.length) {
      list.innerHTML = '<p class="empty">Нет таблиц</p>';
      return;
    }
    tables.forEach(t => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'list-item';
      btn.textContent = t.name;
      btn.onclick = () => selectTable(t.name);
      list.appendChild(btn);
    });
  } catch (e) { console.error(e); }
}

async function selectTable(name) {
  state.currentTable = name;
  state.pageNum = 0;
  document.getElementById('tableName').textContent = `${state.currentSchema}.${name}`;
  document.getElementById('tablePanel').classList.remove('hidden');
  loadTableSchema();
  loadTableData();
}

async function loadTableSchema() {
  if (!state.currentDB || !state.currentTable) return;
  try {
    const r = await fetch(
      `${API}/admin/databases/${state.currentDB.id}/tables/${encodeURIComponent(state.currentTable)}/columns?schema=${encodeURIComponent(state.currentSchema)}`,
      { headers: { Authorization: `Bearer ${state.token}` } }
    );
    if (!r.ok) return;
    const cols = await r.json();
    const info = document.getElementById('tableSchemaInfo');
    info.innerHTML = cols.map(c => `<span><strong>${escapeHtml(c.name)}</strong> (${escapeHtml(c.type)})</span>`).join(' | ');
  } catch (e) { console.error(e); }
}

async function loadTableData() {
  if (!state.currentDB || !state.currentTable) return;
  try {
    const offset = state.pageNum * state.pageSize;
    const r = await fetch(
      `${API}/admin/databases/${state.currentDB.id}/tables/${encodeURIComponent(state.currentTable)}/rows?schema=${encodeURIComponent(state.currentSchema)}&limit=${state.pageSize}&offset=${offset}`,
      { headers: { Authorization: `Bearer ${state.token}` } }
    );
    if (!r.ok) return;
    const rows = await r.json();
    renderTable(rows);
    document.getElementById('pageNum').textContent = state.pageNum + 1;
  } catch (e) { console.error(e); }
}

function renderTable(rows) {
  const table = document.getElementById('dataTable');
  const thead = table.querySelector('thead');
  const tbody = table.querySelector('tbody');
  thead.innerHTML = '';
  tbody.innerHTML = '';
  if (!rows.length) {
    thead.innerHTML = '<tr><td colspan="99">Нет данных</td></tr>';
    return;
  }
  const cols = Object.keys(rows[0]);
  thead.innerHTML = `<tr>${cols.map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr>`;
  tbody.innerHTML = rows.map(row =>
    `<tr>${cols.map(c => `<td>${row[c] !== null ? escapeHtml(String(row[c])).substring(0, 100) : ''}</td>`).join('')}</tr>`
  ).join('');
}

function prevPage() {
  if (state.pageNum > 0) {
    state.pageNum--;
    loadTableData();
  }
}

function nextPage() {
  state.pageNum++;
  loadTableData();
}

// ===== ADD DB MODAL =====
function openAddDB() {
  document.getElementById('addDBMsg').textContent = '';
  document.getElementById('addDBModal').classList.remove('hidden');
}

function closeAddDB() {
  document.getElementById('addDBModal').classList.add('hidden');
}

async function handleAddDB(e) {
  e.preventDefault();
  const msgEl = document.getElementById('addDBMsg');
  msgEl.textContent = '';
  const name = document.getElementById('newDbName').value.trim();
  const host = document.getElementById('newDbHost').value.trim();
  const port = document.getElementById('newDbPort').value;
  const user = document.getElementById('newDbUser').value;
  const pass = document.getElementById('newDbPass').value;
  const db = document.getElementById('newDbDatabase').value.trim();
  const uid = localStorage.getItem('userId');
  try {
    const body = new URLSearchParams();
    body.append('name', name);
    body.append('host', host);
    body.append('port', port);
    body.append('username', user);
    body.append('password', pass);
    body.append('database_name', db);
    if (uid) body.append('owner_id', uid);
    const r = await fetch(`${API}/admin/databases`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded', Authorization: `Bearer ${state.token}` },
      body: body.toString()
    });
    if (r.ok) {
      closeAddDB();
      e.target.reset();
      document.getElementById('newDbPort').value = '5432';
      loadDBList();
      loadStats();
    } else {
      msgEl.textContent = '❌ ' + (await parseErrorResponse(r));
    }
  } catch (e) {
    msgEl.textContent = '❌ ' + e.message;
  }
}

// ===== LOGS =====
async function loadLogs() {
  try {
    const r = await fetch(`${API}/admin/logs?skip=0&limit=50`, {
      headers: { Authorization: `Bearer ${state.token}` }
    });
    if (!r.ok) return;
    const logs = await r.json();
    const tbody = document.getElementById('logsList');
    tbody.innerHTML = logs.map(l => `
      <tr>
        <td>${l.user_id ?? '-'}</td>
        <td>${l.query_text ? escapeHtml(l.query_text.substring(0, 80)) : '-'}</td>
        <td>${escapeHtml(l.status || '-')}</td>
        <td>${l.created_at ? new Date(l.created_at).toLocaleString('ru-RU') : '-'}</td>
      </tr>
    `).join('');
    if (!logs.length) tbody.innerHTML = '<tr><td colspan="4">Пока нет записей в логах</td></tr>';
  } catch (e) { console.error(e); }
}

// ===== PROFILE =====
async function loadProfile() {
  try {
    const uid = localStorage.getItem('userId');
    const r = await fetch(`${API}/auth/me?user_id=${encodeURIComponent(uid)}`, {
      headers: { Authorization: `Bearer ${state.token}` }
    });
    if (r.ok) {
      const u = await r.json();
      document.getElementById('profUser').value = u.username || '';
      document.getElementById('profEmail').value = u.email || '';
      document.getElementById('profName').value = u.full_name || '';
    }
  } catch (e) { console.error(e); }
}

async function saveProfile() {
  const uid = localStorage.getItem('userId');
  const email = document.getElementById('profEmail').value.trim();
  const fullName = document.getElementById('profName').value.trim();
  try {
    const params = new URLSearchParams();
    if (email) params.append('email', email);
    if (fullName !== '') params.append('full_name', fullName);
    const r = await fetch(`${API}/users/${encodeURIComponent(uid)}?${params.toString()}`, {
      method: 'PUT',
      headers: { Authorization: `Bearer ${state.token}` }
    });
    if (r.ok) {
      alert('✅ Профиль сохранён');
      loadProfile();
    } else {
      alert('❌ ' + (await parseErrorResponse(r)));
    }
  } catch (e) {
    alert('❌ ' + e.message);
  }
}
