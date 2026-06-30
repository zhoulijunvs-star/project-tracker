/**
 * Project Tracker - Frontend Application
 * SPA with all CRUD + Dashboard + Import functionality
 */

const API = '/api';
let currentPeriod = 'month';
let myCharts = {};

// ═══════════════ Navigation ═══════════════

function switchPage(name) {
    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelector(`.nav-item[onclick="switchPage('${name}')"]`)?.classList.add('active');
    document.getElementById(`page-${name}`)?.classList.add('active');

    if (name === 'dashboard') loadDashboard(currentPeriod);
    if (name === 'projects') loadProjects();
    if (name === 'customers') loadCustomers();
    if (name === 'prices') loadPriceRefs();
    if (name === 'import') loadImportPage();
}

// ═══════════════ HTTP Helpers ═══════════════

async function apiGet(url, params = {}) {
    const qs = new URLSearchParams(params).toString();
    const r = await fetch(`${API}${url}${qs ? '?' + qs : ''}`);
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || 'Request failed'); }
    return r.json();
}

async function apiPost(url, data) {
    const r = await fetch(`${API}${url}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || 'Create failed'); }
    return r.json();
}

async function apiPut(url, data) {
    const r = await fetch(`${API}${url}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
    });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || 'Update failed'); }
    return r.json();
}

async function apiDel(url) {
    const r = await fetch(`${API}${url}`, { method: 'DELETE' });
    if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || 'Delete failed'); }
    return r.json();
}

// ═══════════════ Toast ═══════════════

function toast(msg, type = 'success') {
    const el = document.getElementById('toast');
    el.className = 'copied-toast';
    el.style.background = type === 'error' ? '#E24B4A' : '#1D9E75';
    el.textContent = msg;
    el.style.animation = 'none';
    void el.offsetWidth;
    el.style.animation = 'fadeInOut 2s forwards';
}

// ═══════════════ Copy Helper ═══════════════

function copyText(text) {
    navigator.clipboard.writeText(text).then(() => toast('已复制到剪贴板'));
}

function buildCopyBlock(label, value) {
    if (!value) return '';
    return `<span style="cursor:pointer" title="点击复制" onclick="copyText('${value.replace(/'/g, "\\'")}')">${value} &#128203;</span>`;
}

// ═══════════════ Modal ═══════════════

function openModal(html) {
    document.getElementById('modalContent').innerHTML = html;
    document.getElementById('modalOverlay').classList.add('show');
}

function closeModal() {
    document.getElementById('modalOverlay').classList.remove('show');
}

document.getElementById('modalOverlay').addEventListener('click', function(e) {
    if (e.target === this) closeModal();
});

// ═══════════════ Dashboard ═══════════════

async function loadDashboard(period) {
    currentPeriod = period;
    document.querySelectorAll('#page-dashboard .btn').forEach(b => b.classList.remove('active'));
    document.querySelector(`#page-dashboard .btn[onclick="loadDashboard('${period}')"]`)?.classList.add('active');

    try {
        const data = await apiGet('/dashboard/summary', { period });
        renderDashboardSummary(data.summary);
        renderDashboardCharts(data.groups, period);
    } catch (e) {
        console.error(e);
        document.getElementById('dashboard-summary').innerHTML = '<p style="color:var(--danger)">加载失败: ' + e.message + '</p>';
    }
}

function renderDashboardSummary(s) {
    document.getElementById('dashboard-summary').innerHTML = `
    <div class="stat-card"><div class="stat-label">项目总数</div><div class="stat-value">${s.total_count}</div></div>
    <div class="stat-card"><div class="stat-label">已落地</div><div class="stat-value" style="color:var(--success)">${s.landed_count}</div></div>
    <div class="stat-card"><div class="stat-label">落地率</div><div class="stat-value" style="color:var(--primary)">${s.win_rate}%</div></div>
    <div class="stat-card"><div class="stat-label">总出街金额</div><div class="stat-value">&yen;${fmtNum(s.total_final_price)}</div></div>
    <div class="stat-card"><div class="stat-label">总毛利</div><div class="stat-value" style="color:var(--success)">&yen;${fmtNum(s.total_margin)}</div></div>
    `;
}

function fmtNum(n) {
    if (n == null || n === 0) return '0';
    if (n >= 10000) return (n / 10000).toFixed(1) + '万';
    return n.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function renderDashboardCharts(groups, period) {
    const labels = groups.map(g => g.period);
    const counts = groups.map(g => g.count);
    const landed = groups.map(g => g.landed);
    const prices = groups.map(g => g.price);
    const margins = groups.map(g => g.margin);

    // Chart 1: Project landing
    if (myCharts.landing) myCharts.landing.destroy();
    const ctx1 = document.getElementById('chartLanding').getContext('2d');
    myCharts.landing = new Chart(ctx1, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                { label: '项目总数', data: counts, backgroundColor: '#AFA9EC', borderRadius: 4 },
                { label: '已落地', data: landed, backgroundColor: '#1D9E75', borderRadius: 4 },
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { title: { display: true, text: '项目落地统计', font: { size: 14 } } },
            scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
        }
    });

    // Chart 2: Amount & Margin
    if (myCharts.amount) myCharts.amount.destroy();
    const ctx2 = document.getElementById('chartAmount').getContext('2d');
    myCharts.amount = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels,
            datasets: [
                { label: '出街金额 (元)', data: prices, backgroundColor: '#378ADD', borderRadius: 4, yAxisID: 'y' },
                { label: '毛利 (元)', data: margins, backgroundColor: '#F0997B', borderRadius: 4, yAxisID: 'y' },
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false,
            plugins: { title: { display: true, text: '金额与毛利统计', font: { size: 14 } } },
            scales: { y: { beginAtZero: true, ticks: { callback: v => fmtNum(v) } } }
        }
    });
}

// ═══════════════ Projects ═══════════════

async function loadProjects() {
    const search = document.getElementById('projSearch')?.value || '';
    try {
        const projects = await apiGet('/projects', { search });
        const customers = await apiGet('/customers');
        const custMap = {};
        customers.forEach(c => custMap[c.id] = c);

        const tbody = document.querySelector('#projTable tbody');
        if (projects.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-secondary);padding:30px">暂无项目，点击"新建项目"开始</td></tr>';
            return;
        }
        tbody.innerHTML = projects.map(p => `
        <tr>
            <td><span class="clickable" onclick="editProject(${p.id})">${esc(p.name)}</span></td>
            <td>${custMap[p.customer_id] ? esc(custMap[p.customer_id].company_name) : '-'}</td>
            <td>${p.quotation_date || '-'}</td>
            <td>${p.final_price != null ? '&yen;' + fmtNum(p.final_price) : '-'}</td>
            <td>${p.final_margin != null ? '&yen;' + fmtNum(p.final_margin) : '-'}</td>
            <td><span class="tag ${p.is_landed ? 'tag-success' : 'tag-pending'}">${p.is_landed ? '已落地' : '进行中'}</span></td>
            <td>
                <button class="btn btn-sm" onclick="editProject(${p.id})">编辑</button>
                <button class="btn btn-sm btn-danger" onclick="deleteProject(${p.id})">删除</button>
            </td>
        </tr>`).join('');
    } catch (e) {
        console.error(e);
    }
}

function showProjectModal(id = null) {
    if (id) { editProject(id); return; }
    loadCustomerOptions().then(custOpts => {
        openModal(`
        <div class="modal-header"><h3>新建项目</h3><button class="modal-close" onclick="closeModal()">&times;</button></div>
        <form id="projForm" onsubmit="saveProject(event, null)">
            ${projectFormHTML(null, custOpts)}
            <div style="margin-top:16px">
                <button type="button" class="btn" onclick="closeModal()">取消</button>
                <button type="submit" class="btn btn-primary">保存</button>
            </div>
        </form>`);
    });
}

async function editProject(id) {
    try {
        const p = await apiGet(`/projects/${id}`);
        const custOpts = await loadCustomerOptions();
        openModal(`
        <div class="modal-header"><h3>编辑项目</h3><button class="modal-close" onclick="closeModal()">&times;</button></div>
        <form id="projForm" onsubmit="saveProject(event, ${id})">
            ${projectFormHTML(p, custOpts)}
            <div id="supplierQuotesSection" style="margin-top:16px">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
                    <h4 style="font-size:14px;font-weight:500">供应商报价</h4>
                    <button type="button" class="btn btn-sm" onclick="addQuoteRow()">+ 添加供应商</button>
                </div>
                <div id="quoteRows"></div>
            </div>
            <div style="margin-top:16px">
                <button type="button" class="btn" onclick="closeModal()">取消</button>
                <button type="submit" class="btn btn-primary">保存</button>
            </div>
        </form>`);
        // Render quote rows
        const container = document.getElementById('quoteRows');
        if (p.supplier_quotes && p.supplier_quotes.length > 0) {
            p.supplier_quotes.forEach(q => container.appendChild(createQuoteRow(q)));
        }
    } catch (e) {
        toast(e.message, 'error');
    }
}

function projectFormHTML(p, custOpts) {
    const d = p || {};
    return `
    <div class="form-row">
    <div class="form-group"><label>项目名称 *</label><input class="form-control" name="name" value="${esc(d.name || '')}" required></div>
    <div class="form-group"><label>关联客户 *</label><select class="form-control" name="customer_id" required>${custOpts}</select></div>
    </div>
    <div class="form-group"><label>项目信息/描述</label><textarea class="form-control" name="description">${esc(d.description || '')}</textarea></div>
    <div class="form-row">
    <div class="form-group"><label>报价完成时间</label><input class="form-control" type="date" name="quotation_date" value="${d.quotation_date || ''}"></div>
    <div class="form-group"><label>项目类别</label><input class="form-control" name="category" value="${esc(d.category || '')}" placeholder="如：安防监控、综合布线"></div>
    </div>
    <div class="form-row">
    <div class="form-group"><label>出街价格</label><input class="form-control" type="number" step="0.01" name="final_price" value="${d.final_price || ''}" onchange="calcMargin()"></div>
    <div class="form-group"><label>出街价格备注</label><input class="form-control" name="final_price_notes" value="${esc(d.final_price_notes || '')}"></div>
    </div>
    <div class="form-row">
    <div class="form-group"><label>成本价格</label><input class="form-control" type="number" step="0.01" name="cost_price" value="${d.cost_price || ''}" onchange="calcMargin()"></div>
    <div class="form-group"><label>出街毛利</label><input class="form-control" type="number" step="0.01" name="final_margin" value="${d.final_margin || ''}" readonly style="background:#F3F4F6"></div>
    </div>
    <div class="form-group"><label>出街毛利备注</label><input class="form-control" name="final_margin_notes" value="${esc(d.final_margin_notes || '')}"></div>
    <div class="form-row">
    <div class="checkbox-group"><input type="checkbox" name="is_landed" ${d.is_landed ? 'checked' : ''}><label>项目已落地</label></div>
    <div class="form-group"><label>落地日期</label><input class="form-control" type="date" name="landed_date" value="${d.landed_date || ''}"></div>
    </div>`;
}

function createQuoteRow(q) {
    const div = document.createElement('div');
    div.className = 'quote-item';
    div.innerHTML = `
    <button type="button" class="btn-icon" onclick="this.parentElement.remove()" title="删除">&times;</button>
    <div class="form-row" style="grid-template-columns:repeat(3,1fr)">
    <div class="form-group"><label>供应商公司 *</label><input class="form-control q-supplier" value="${esc(q.supplier_company || '')}" required></div>
    <div class="form-group"><label>联系人</label><input class="form-control q-contact" value="${esc(q.contact_name || '')}"></div>
    <div class="form-group"><label>电话</label><input class="form-control q-phone" value="${esc(q.phone || '')}"></div>
    </div>
    <div class="form-row" style="grid-template-columns:repeat(3,1fr)">
    <div class="form-group"><label>邮箱</label><input class="form-control q-email" value="${esc(q.email || '')}"></div>
    <div class="form-group"><label>产品类别</label><input class="form-control q-category" value="${esc(q.category || '')}"></div>
    <div class="form-group"><label>币种</label><select class="form-control q-currency"><option value="CNY" ${q.currency === 'CNY' ? 'selected' : ''}>人民币 CNY</option><option value="HKD" ${q.currency === 'HKD' ? 'selected' : ''}>港币 HKD</option><option value="MOP" ${q.currency === 'MOP' ? 'selected' : ''}>澳门元 MOP</option></select></div>
    </div>
    <div class="form-row">
    <div class="form-group"><label>产品/服务详细情况</label><textarea class="form-control q-detail" rows="2">${esc(q.product_service_detail || '')}</textarea></div>
    <div class="form-group"><label>价格</label><input class="form-control q-price" type="number" step="0.01" value="${q.price || ''}"></div>
    </div>`;
    div._quoteData = q;
    return div;
}

function addQuoteRow() {
    const container = document.getElementById('quoteRows');
    if (!container) {
        // If viewing new project, add section dynamically
        const form = document.getElementById('projForm');
        const sec = document.createElement('div');
        sec.id = 'supplierQuotesSection';
        sec.style.marginTop = '16px';
        sec.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px"><h4 style="font-size:14px;font-weight:500">供应商报价</h4><button type="button" class="btn btn-sm" onclick="addQuoteRow()">+ 添加供应商</button></div><div id="quoteRows"></div>`;
        form.insertBefore(sec, form.querySelector('div:last-child'));
        addQuoteRow();
        return;
    }
    container.appendChild(createQuoteRow({}));
}

function calcMargin() {
    const form = document.getElementById('projForm');
    if (!form) return;
    const fp = parseFloat(form.elements['final_price']?.value) || 0;
    const cp = parseFloat(form.elements['cost_price']?.value) || 0;
    if (form.elements['final_margin']) {
        form.elements['final_margin'].value = (fp - cp).toFixed(2);
    }
}

function collectQuotes() {
    const rows = document.querySelectorAll('#quoteRows .quote-item');
    const quotes = [];
    rows.forEach(row => {
        quotes.push({
            supplier_company: row.querySelector('.q-supplier')?.value || '',
            contact_name: row.querySelector('.q-contact')?.value || '',
            phone: row.querySelector('.q-phone')?.value || '',
            email: row.querySelector('.q-email')?.value || '',
            product_service_detail: row.querySelector('.q-detail')?.value || '',
            price: parseFloat(row.querySelector('.q-price')?.value) || null,
            currency: row.querySelector('.q-currency')?.value || 'CNY',
            category: row.querySelector('.q-category')?.value || '',
        });
    });
    return quotes;
}

async function saveProject(e, id) {
    e.preventDefault();
    const form = document.getElementById('projForm');
    const fd = new FormData(form);
    const data = {
        name: fd.get('name'),
        description: fd.get('description') || '',
        customer_id: parseInt(fd.get('customer_id')),
        quotation_date: fd.get('quotation_date') || null,
        category: fd.get('category') || '',
        final_price: parseFloat(fd.get('final_price')) || null,
        final_price_notes: fd.get('final_price_notes') || '',
        final_margin: parseFloat(fd.get('final_margin')) || null,
        final_margin_notes: fd.get('final_margin_notes') || '',
        cost_price: parseFloat(fd.get('cost_price')) || null,
        is_landed: fd.get('is_landed') === 'on',
        landed_date: fd.get('landed_date') || null,
        supplier_quotes: collectQuotes(),
    };
    try {
        if (id) {
            await apiPut(`/projects/${id}`, data);
        } else {
            await apiPost('/projects', data);
        }
        closeModal();
        loadProjects();
        toast(id ? '项目已更新' : '项目已创建');
    } catch (e) {
        toast(e.message, 'error');
    }
}

async function deleteProject(id) {
    if (!confirm('确定要删除此项目吗？此操作不可撤销。')) return;
    try {
        await apiDel(`/projects/${id}`);
        loadProjects();
        toast('项目已删除');
    } catch (e) {
        toast(e.message, 'error');
    }
}

// ═══════════════ Customers ═══════════════

async function loadCustomers() {
    const search = document.getElementById('custSearch')?.value || '';
    try {
        const customers = await apiGet('/customers', { search });
        const projects = await apiGet('/projects');
        const projCount = {};
        projects.forEach(p => projCount[p.customer_id] = (projCount[p.customer_id] || 0) + 1);

        const tbody = document.querySelector('#custTable tbody');
        if (customers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align:center;color:var(--text-secondary);padding:30px">暂无客户</td></tr>';
            return;
        }
        tbody.innerHTML = customers.map(c => `
        <tr>
            <td><span class="clickable" onclick="editCustomer(${c.id})">${esc(c.company_name)}</span></td>
            <td>${buildCopyBlock('', c.contact_name) || '-'}</td>
            <td>${buildCopyBlock('', c.phone) || '-'}</td>
            <td>${buildCopyBlock('', c.email) || '-'}</td>
            <td>${esc(c.address || '-')}</td>
            <td>${projCount[c.id] || 0} 个项目</td>
            <td>
                <button class="btn btn-sm" onclick="editCustomer(${c.id})">编辑</button>
                <button class="btn btn-sm btn-danger" onclick="deleteCustomer(${c.id})">删除</button>
            </td>
        </tr>`).join('');
    } catch (e) {
        console.error(e);
    }
}

async function loadCustomerOptions() {
    try {
        const customers = await apiGet('/customers');
        return customers.map(c => `<option value="${c.id}" ${c.customer_id === c.id ? 'selected' : ''}>${esc(c.company_name)}</option>`).join('');
    } catch (e) { return ''; }
}

function showCustomerModal(id = null) {
    const d = id ? null : {};
    const title = id ? '编辑客户' : '新增客户';
    apiGet(id ? `/customers/${id}` : '/customers').then(c => {
        const data = id ? c : {};
        openModal(`
        <div class="modal-header"><h3>${title}</h3><button class="modal-close" onclick="closeModal()">&times;</button></div>
        <form onsubmit="saveCustomer(event, ${id || 'null'})">
            <div class="form-row">
            <div class="form-group"><label>公司名称 *</label><input class="form-control" name="company_name" value="${esc(data.company_name || '')}" required></div>
            <div class="form-group"><label>联系人</label><input class="form-control" name="contact_name" value="${esc(data.contact_name || '')}"></div>
            </div>
            <div class="form-row">
            <div class="form-group"><label>电话</label><input class="form-control" name="phone" value="${esc(data.phone || '')}"></div>
            <div class="form-group"><label>邮箱</label><input class="form-control" name="email" value="${esc(data.email || '')}"></div>
            </div>
            <div class="form-group"><label>公司地址</label><input class="form-control" name="address" value="${esc(data.address || '')}"></div>
            <div style="margin-top:16px">
                <button type="button" class="btn" onclick="closeModal()">取消</button>
                <button type="submit" class="btn btn-primary">保存</button>
            </div>
        </form>`);
    }).catch(e => {
        if (id) { toast(e.message, 'error'); return; }
        // New customer - open form directly
        openModal(`
        <div class="modal-header"><h3>新增客户</h3><button class="modal-close" onclick="closeModal()">&times;</button></div>
        <form onsubmit="saveCustomer(event, null)">
            <div class="form-row">
            <div class="form-group"><label>公司名称 *</label><input class="form-control" name="company_name" required></div>
            <div class="form-group"><label>联系人</label><input class="form-control" name="contact_name"></div>
            </div>
            <div class="form-row">
            <div class="form-group"><label>电话</label><input class="form-control" name="phone"></div>
            <div class="form-group"><label>邮箱</label><input class="form-control" name="email"></div>
            </div>
            <div class="form-group"><label>公司地址</label><input class="form-control" name="address"></div>
            <div style="margin-top:16px">
                <button type="button" class="btn" onclick="closeModal()">取消</button>
                <button type="submit" class="btn btn-primary">保存</button>
            </div>
        </form>`);
    });
}

async function editCustomer(id) { showCustomerModal(id); }

async function saveCustomer(e, id) {
    e.preventDefault();
    const form = e.target;
    const fd = new FormData(form);
    const data = {
        company_name: fd.get('company_name'),
        contact_name: fd.get('contact_name') || '',
        phone: fd.get('phone') || '',
        email: fd.get('email') || '',
        address: fd.get('address') || '',
    };
    try {
        if (id) {
            await apiPut(`/customers/${id}`, data);
        } else {
            await apiPost('/customers', data);
        }
        closeModal();
        loadCustomers();
        toast(id ? '客户已更新' : '客户已创建');
    } catch (e) {
        toast(e.message, 'error');
    }
}

async function deleteCustomer(id) {
    if (!confirm('确定要删除此客户吗？关联的项目也会被删除！')) return;
    try {
        await apiDel(`/customers/${id}`);
        loadCustomers();
        toast('客户已删除');
    } catch (e) {
        toast(e.message, 'error');
    }
}

// ═══════════════ Price References ═══════════════

async function loadPriceRefs() {
    const search = document.getElementById('priceSearch')?.value || '';
    const category = document.getElementById('priceCatFilter')?.value || '';
    try {
        const refs = await apiGet('/price-references', { search, category });
        const cats = await apiGet('/price-references/categories');
        const catSelect = document.getElementById('priceCatFilter');
        if (catSelect) {
            catSelect.innerHTML = '<option value="">全部类别</option>' + cats.map(c => `<option value="${esc(c)}">${esc(c)}</option>`).join('');
        }

        const tbody = document.querySelector('#priceTable tbody');
        if (refs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="text-align:center;color:var(--text-secondary);padding:30px">暂无价格参考，录入供应商报价后自动生成</td></tr>';
            return;
        }
        tbody.innerHTML = refs.map(r => {
            let suppliers = [];
            try { suppliers = JSON.parse(r.supplier_list || '[]'); } catch (e) {}
            return `
            <tr>
                <td><span class="tag tag-success">${esc(r.category)}</span></td>
                <td>${esc(r.product_service_name)}</td>
                <td>${r.avg_price != null ? r.currency + ' ' + r.avg_price.toFixed(2) : '-'}</td>
                <td>${r.min_price != null ? r.currency + ' ' + r.min_price.toFixed(2) : '-'}</td>
                <td>${r.max_price != null ? r.currency + ' ' + r.max_price.toFixed(2) : '-'}</td>
                <td>${r.currency}</td>
                <td>${r.quote_count}</td>
                <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis">${suppliers.join(', ')}</td>
                <td>${r.latest_quote_date || '-'}</td>
            </tr>`;
        }).join('');
    } catch (e) {
        console.error(e);
    }
}

async function refreshPriceRefs() {
    try {
        await apiPost('/price-references', {});
        loadPriceRefs();
        toast('价格参考已刷新');
    } catch (e) {
        // If no dedicated refresh endpoint, trigger by loading
        loadPriceRefs();
    }
}

// ═══════════════ Import ═══════════════

async function loadImportPage() {
    try {
        const projects = await apiGet('/projects');
        const sel = document.getElementById('importProjectId');
        sel.innerHTML = '<option value="">不关联（仅入库）</option>' +
            projects.map(p => `<option value="${p.id}">${esc(p.name)}</option>`).join('');
    } catch (e) { console.error(e); }
}

function handleFileUpload(files) {
    if (!files || files.length === 0) return;
    const file = files[0];
    const projectId = document.getElementById('importProjectId')?.value || '';

    const formData = new FormData();
    formData.append('file', file);
    if (projectId) formData.append('project_id', projectId);

    const resultDiv = document.getElementById('importResult');
    resultDiv.innerHTML = '<p style="color:var(--text-secondary)">正在解析文件...</p>';

    fetch(`${API}/import/quote`, { method: 'POST', body: formData })
        .then(r => r.json())
        .then(data => {
            if (data.ok) {
                resultDiv.innerHTML = `
                <div class="card" style="margin-top:12px;border-color:var(--success)">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
                        <p style="color:var(--success);font-weight:500;margin:0">导入成功！共解析 ${data.count} 条报价记录。</p>
                        <div class="btn-group">
                            <button class="btn btn-sm" onclick="toggleAllQuotes(this)">全选</button>
                            <button class="btn btn-sm btn-danger" onclick="batchDeleteQuotes()">删除选中</button>
                        </div>
                    </div>
                    <table style="margin-top:8px" id="importResultTable"><thead><tr>
                    <th style="width:30px"><input type="checkbox" onchange="toggleAllQuotes(this)" style="cursor:pointer"></th>
                    <th>供应商</th><th>产品/服务</th><th>价格</th><th>币种</th><th>类别</th>
                    <th style="width:50px">操作</th>
                    </tr></thead><tbody>
                    ${data.quotes.map(q => `<tr id="qrow-${q.id}">
                        <td><input type="checkbox" class="qcheck" value="${q.id}" style="cursor:pointer"></td>
                        <td>${esc(q.supplier_company || '-')}</td>
                        <td>${esc(q.product_service_detail || '-')}</td>
                        <td>${q.price != null ? q.price : '-'}</td>
                        <td>${q.currency || '-'}</td>
                        <td>${esc(q.category || '-')}</td>
                        <td><button class="btn btn-sm btn-danger" onclick="deleteQuote(${q.id})" title="删除">✕</button></td>
                    </tr>`).join('')}
                    </tbody></table>
                </div>`;
                toast('导入成功');
            } else {
                resultDiv.innerHTML = `<p style="color:var(--danger)">导入失败: ${data.detail || '未知错误'}</p>`;
            }
        })
        .catch(e => {
            resultDiv.innerHTML = `<p style="color:var(--danger)">导入失败: ${e.message}</p>`;
        });
}

// ── Quote Delete Functions ──

async function deleteQuote(id) {
    if (!confirm('确定要删除这条报价吗？')) return;
    try {
        await apiDel(`/quotes/${id}`);
        const row = document.getElementById(`qrow-${id}`);
        if (row) row.remove();
        toast('已删除');
    } catch (e) {
        toast(e.message, 'error');
    }
}

async function batchDeleteQuotes() {
    const checks = document.querySelectorAll('.qcheck:checked');
    if (checks.length === 0) { toast('请先选择要删除的报价', 'error'); return; }
    if (!confirm(`确定要删除选中的 ${checks.length} 条报价吗？`)) return;
    const ids = Array.from(checks).map(c => parseInt(c.value));
    try {
        const r = await fetch(`${API}/quotes/batch-delete`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ids }),
        });
        const data = await r.json();
        ids.forEach(id => {
            const row = document.getElementById(`qrow-${id}`);
            if (row) row.remove();
        });
        toast(`已删除 ${data.deleted} 条报价`);
    } catch (e) {
        toast(e.message, 'error');
    }
}

function toggleAllQuotes(el) {
    const checked = el.checked !== undefined ? el.checked : !el._allChecked;
    if (el.tagName === 'BUTTON') el._allChecked = checked;
    document.querySelectorAll('.qcheck').forEach(cb => { cb.checked = checked; });
    const thCheck = document.querySelector('#importResultTable thead input[type=checkbox]');
    if (thCheck) thCheck.checked = checked;
}

// Drag & drop
document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    if (!dropZone) return;
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, e => { e.preventDefault(); e.stopPropagation(); });
    });
    ['dragenter', 'dragover'].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.add('dragover'));
    });
    ['dragleave', 'drop'].forEach(evt => {
        dropZone.addEventListener(evt, () => dropZone.classList.remove('dragover'));
    });
    dropZone.addEventListener('drop', e => {
        handleFileUpload(e.dataTransfer.files);
    });
});

// ═══════════════ Utils ═══════════════

function esc(s) {
    if (!s) return '';
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
