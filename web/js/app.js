const API_BASE = 'http://127.0.0.1:5000';

// Contact status cache
let _contactStatus = {};
let _companySettings = {};
let _currentDemand = {};

// ========== Load Contact Status on startup ==========
async function loadContactStatus() {
    try {
        const resp = await fetch(`${API_BASE}/api/contact_status`);
        const result = await resp.json();
        if (result.success && result.data) {
            _contactStatus = result.data;
        }
    } catch (e) {
        console.error('加载联系状态失败:', e);
    }
}

async function loadCompanySettings() {
    try {
        const resp = await fetch(`${API_BASE}/api/company_settings`);
        const result = await resp.json();
        if (result.success && result.data) {
            _companySettings = result.data;
        }
    } catch (e) {
        console.error('加载公司设置失败:', e);
    }
}

loadContactStatus();
loadCompanySettings();

// ========== Sidebar Toggle ==========
function toggleSidebar() {
    const section = document.getElementById('formSection');
    section.classList.toggle('collapsed');
    const isCollapsed = section.classList.contains('collapsed');
    const btn = section.querySelector('.collapse-btn');
    btn.innerHTML = isCollapsed ? '▶' : '◀';
    btn.title = isCollapsed ? '展开表单' : '收起表单';

    setTimeout(() => {
        ['budgetBar', 'platformBar'].forEach(id => {
            const dom = document.getElementById(id);
            if (!dom) return;
            const chart = echarts.getInstanceByDom(dom);
            if (chart) chart.resize();
        });
    }, 300);
}

// ========== Toast Notification ==========
function showToast(message) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => toast.remove(), 2500);
}

// ========== Audience Input Toggle ==========
function switchAudienceMode(mode) {
    document.getElementById('btnSplit').classList.toggle('active', mode === 'split');
    document.getElementById('btnFree').classList.toggle('active', mode === 'free');
    document.getElementById('audienceSplit').style.display = mode === 'split' ? 'block' : 'none';
    document.getElementById('audienceFree').style.display = mode === 'free' ? 'block' : 'none';
}

// ========== Platform Tag Toggle ==========
function togglePlatform(label) {
    const cb = label.querySelector('input[type="checkbox"]');
    cb.checked = !cb.checked;
    label.classList.toggle('active', cb.checked);
}

// ========== Allocation Mode Toggle ==========
function switchAllocMode() {
    const mode = document.querySelector('input[name="alloc_mode"]:checked').value;
    document.getElementById('field_num_kols').style.display = mode === 'num' ? 'block' : 'none';
    document.getElementById('field_target_roi').style.display = mode === 'roi' ? 'block' : 'none';
}

// Bind mode toggle listeners
document.querySelectorAll('input[name="alloc_mode"]').forEach(radio => {
    radio.addEventListener('change', switchAllocMode);
});

// ========== Parse Demand from Free Text ==========
async function parseDemand() {
    const text = document.getElementById('freeText').value.trim();
    const resultDiv = document.getElementById('parseResult');

    if (!text) {
        resultDiv.innerHTML = '<p style="color:#e74c3c;">请输入需求描述</p>';
        return;
    }

    resultDiv.innerHTML = '<p style="color:#667eea;">AI 正在解析...</p>';

    try {
        const resp = await fetch(`${API_BASE}/api/parse_demand`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
        });
        const result = await resp.json();

        if (!result.success) {
            resultDiv.innerHTML = `<p style="color:#e74c3c;">解析失败: ${result.error}</p>`;
            return;
        }

        const d = result.data;

        if (d.gender) {
            const rb = document.querySelector(`input[name="gender"][value="${d.gender}"]`);
            if (rb) rb.checked = true;
        }
        if (d.age_min) document.getElementById('age_min').value = d.age_min;
        if (d.age_max) document.getElementById('age_max').value = d.age_max;
        if (d.occupation) document.getElementById('occupation').value = d.occupation;
        if (d.content_field) document.getElementById('content_field').value = d.content_field;
        if (d.budget_min) document.getElementById('budget_min').value = d.budget_min;
        if (d.budget_max) document.getElementById('budget_max').value = d.budget_max;
        if (d.total_budget) document.getElementById('total_budget').value = d.total_budget;
        if (d.num_kols) document.getElementById('num_kols').value = d.num_kols;
        if (d.target_roi) document.getElementById('target_roi').value = d.target_roi;
        if (d.engagement_rate_min) document.getElementById('engagement_rate_min').value = d.engagement_rate_min;
        if (d.conversion_rate_min) document.getElementById('conversion_rate_min').value = d.conversion_rate_min;
        if (d.risk_preference) document.getElementById('risk_preference').value = d.risk_preference;

        if (d.platforms && d.platforms.length > 0) {
            document.querySelectorAll('input[name="platforms"]').forEach(cb => {
                cb.checked = d.platforms.includes(cb.value);
                cb.closest('.platform-tag').classList.toggle('active', cb.checked);
            });
        }

        const fields = [
            ['性别', d.gender], ['年龄', d.age_min && d.age_max ? `${d.age_min}-${d.age_max}岁` : null],
            ['职业', d.occupation], ['领域', d.content_field],
            ['预算范围', d.budget_min && d.budget_max ? `${d.budget_min}-${d.budget_max}元` : null],
            ['总预算', d.total_budget ? `${d.total_budget}元` : null],
            ['平台', d.platforms?.join(', ')],
            ['置信度', d.confidence ? `${(d.confidence * 100).toFixed(0)}%` : null],
        ];

        resultDiv.innerHTML = `
            <div class="parse-preview">
                <h4>解析结果（已自动填充到表单）</h4>
                ${fields.filter(([_, v]) => v).map(([label, value]) => `
                    <div class="parse-field"><span class="label">${label}</span><span class="value">${value}</span></div>
                `).join('')}
            </div>
        `;

        switchAudienceMode('split');

    } catch (e) {
        resultDiv.innerHTML = `<p style="color:#e74c3c;">请求失败: ${e.message}</p>`;
    }
}

// ========== Toggle Advanced Panel ==========
function toggleAdvanced() {
    const panel = document.getElementById('advancedPanel');
    const btn = document.querySelector('.toggle-btn');
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        btn.textContent = '高级筛选 ▲';
    } else {
        panel.style.display = 'none';
        btn.textContent = '高级筛选 ▼';
    }
}

// ========== Quick Form Fillers ==========
function fillForm(type) {
    const presets = {
        campus: { gender: '不限', age_min: 18, age_max: 25, occupation: '大学生', content_field: '校园', budget_min: 1000, budget_max: 3000, total_budget: 15000, platforms: ['小红书', '抖音'] },
        beauty: { gender: '女', age_min: 18, age_max: 30, occupation: '学生党', content_field: '美妆', budget_min: 1500, budget_max: 5000, total_budget: 20000, platforms: ['小红书'] },
        workplace: { gender: '不限', age_min: 22, age_max: 35, occupation: '职场新人', content_field: '职场', budget_min: 2000, budget_max: 5000, total_budget: 25000, platforms: ['B站', '抖音'] },
        mother: { gender: '女', age_min: 25, age_max: 40, occupation: '宝妈', content_field: '母婴', budget_min: 1500, budget_max: 4000, total_budget: 18000, platforms: ['小红书', '微博'] },
    };
    const p = presets[type];
    if (!p) return;

    document.querySelector(`input[name="gender"][value="${p.gender}"]`).checked = true;
    document.getElementById('age_min').value = p.age_min;
    document.getElementById('age_max').value = p.age_max;
    document.getElementById('occupation').value = p.occupation;
    document.getElementById('content_field').value = p.content_field;
    document.getElementById('budget_min').value = p.budget_min;
    document.getElementById('budget_max').value = p.budget_max;
    document.getElementById('total_budget').value = p.total_budget;

    document.querySelectorAll('input[name="platforms"]').forEach(cb => {
        cb.checked = p.platforms.includes(cb.value);
        cb.closest('.platform-tag').classList.toggle('active', cb.checked);
    });

    const names = { campus: '校园推广', beauty: '美妆新品', workplace: '职场课程', mother: '母婴产品' };
    showToast(`已填充：${names[type]}`);
}

// ========== Form Submit ==========
document.getElementById('demandForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    // 清除旧缓存，避免新搜索后显示旧结果
    sessionStorage.removeItem('kol_recommend_result');
    sessionStorage.removeItem('kol_recommend_demand');
    sessionStorage.removeItem('kol_recommend_timestamp');

    const btn = e.target.querySelector('.btn-primary');
    const btnText = btn.querySelector('.btn-text');
    const spinner = btn.querySelector('.spinner');
    const resultArea = document.getElementById('resultArea');

    const mode = document.getElementById('audienceSplit').style.display !== 'none' ? 'split' : 'free';
    let targetAudience = '';

    if (mode === 'split') {
        const gender = document.querySelector('input[name="gender"]:checked').value;
        const ageMin = document.getElementById('age_min').value;
        const ageMax = document.getElementById('age_max').value;
        const occupation = document.getElementById('occupation').value;
        targetAudience = `${gender}、${ageMin}-${ageMax}岁、${occupation}`;
    } else {
        targetAudience = document.getElementById('freeText').value.trim() || '未指定';
    }

    const contentField = document.getElementById('content_field').value;
    const budgetMin = document.getElementById('budget_min').value;
    const budgetMax = document.getElementById('budget_max').value;
    const totalBudget = document.getElementById('total_budget').value;
    const allocMode = document.querySelector('input[name="alloc_mode"]:checked').value;
    const numKols = document.getElementById('num_kols').value;
    const targetRoi = document.getElementById('target_roi').value;
    const platforms = Array.from(document.querySelectorAll('input[name="platforms"]:checked')).map(cb => cb.value);

    if (platforms.length === 0) {
        alert('请至少选择一个投放平台');
        return;
    }

    const data = {
        target_audience: targetAudience,
        content_field: contentField,
        budget_range: `${budgetMin}-${budgetMax}`,
        platforms: platforms.join(','),
        total_budget: parseInt(totalBudget) || 15000,
        num_kols: allocMode === 'num' && numKols ? parseInt(numKols) : undefined,
        target_roi: allocMode === 'roi' && targetRoi ? parseFloat(targetRoi) : undefined,
        engagement_rate_min: document.getElementById('engagement_rate_min').value || undefined,
        conversion_rate_min: document.getElementById('conversion_rate_min').value || undefined,
        followers_min: document.getElementById('followers_min').value || undefined,
        followers_max: document.getElementById('followers_max').value || undefined,
        risk_preference: document.getElementById('risk_preference').value,
    };

    btn.disabled = true;
    btnText.textContent = 'AI 分析中...';
    spinner.style.display = 'inline-block';
    resultArea.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <div class="loading-text">AI 正在分析达人数据...</div>
            <div class="loading-step">约需 15-30 秒，请稍候</div>
        </div>
    `;

    try {
        const response = await fetch(`${API_BASE}/api/recommend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const err = await response.json().catch(() => ({ error: '请求失败' }));
            throw new Error(err.error || `HTTP ${response.status}`);
        }

        const result = await response.json();
        if (!result.success) {
            throw new Error(result.error || '分析失败');
        }

        if ((data.num_kols || data.target_roi) && result.top10) {
            const allocResp = await fetch(`${API_BASE}/api/allocate_budget`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    top10: result.top10,
                    total_budget: data.total_budget,
                    num_kols: data.num_kols,
                    target_roi: data.target_roi,
                }),
            });
            const allocResult = await allocResp.json();
            if (allocResult.success) {
                result.budget_allocation = allocResult.budget_allocation;
                result.platform_summary = allocResult.platform_summary;
            }
        }

        renderResult(result, data);
    } catch (error) {
        resultArea.innerHTML = `
            <div class="empty-state" style="color: #e74c3c;">
                <div class="empty-icon">⚠️</div>
                <h3>请求失败</h3>
                <p>${error.message}</p>
                <p style="font-size: 0.85rem; margin-top: 12px; color: #999;">
                    请确保后端服务已启动：python web/app.py
                </p>
            </div>
        `;
    } finally {
        btn.disabled = false;
        btnText.textContent = '开始推荐';
        spinner.style.display = 'none';
    }
});

function renderResult(result, demand) {
    const top10 = result.top10 || [];
    window._lastTop10 = top10;
    window._lastResult = result;
    window._lastDemand = demand;
    const budgetAlloc = result.budget_allocation || {};
    const platformSummary = result.platform_summary || {};
    const allocations = budgetAlloc.allocations || [];
    const totalBudget = demand.total_budget || 15000;

    let html = '';

    // ===== Stats Cards =====
    const kolCount = allocations.length;
    const platformSet = new Set(allocations.map(a => a.platform).filter(Boolean));
    const platformCombo = Array.from(platformSet).join(' + ') || '-';

    let avgRoi = '-';
    if (allocations.length > 0) {
        const roiValues = [];
        allocations.forEach(a => {
            const kol = top10.find(k => k.kol_id === a.kol_id);
            if (kol && kol.roi) {
                const m = String(kol.roi).match(/(\d+(\.\d+)?)/);
                if (m) roiValues.push(parseFloat(m[1]));
            }
        });
        if (roiValues.length > 0) {
            const avg = roiValues.reduce((s, v) => s + v, 0) / roiValues.length;
            avgRoi = `1:${avg.toFixed(1)}`;
        }
    }

    html += `
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-value">${kolCount}位</div>
                <div class="stat-label">合作达人</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">¥${totalBudget.toLocaleString()}</div>
                <div class="stat-label">总预算</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${platformCombo}</div>
                <div class="stat-label">平台组合</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${avgRoi}</div>
                <div class="stat-label">平均ROI</div>
            </div>
        </div>
    `;

    // ===== Allocation Layout (投放名单 + 图表) =====
    html += '<div class="allocation-layout">';

    // Left: 建议实际投放名单
    html += '<div class="allocation-left">';
    if (allocations.length > 0) {
        html += '<div class="card"><h2>建议实际投放名单</h2>';
        html += '<div class="allocation-list">';
        allocations.forEach(a => {
            const kol = top10.find(k => k.kol_id === a.kol_id);
            const platformClass = { '小红书': 'xhs', '抖音': 'dy', 'B站': 'bz', '微博': 'wb' }[a.platform] || '';
            const contactInfo = _contactStatus[a.kol_id];
            const isContacted = contactInfo && contactInfo.status === 'sent';
            const statusClass = isContacted ? 'sent' : '';
            const statusText = isContacted ? '已合作' : '未联系';
            const contactBtnText2 = isContacted ? '查看联系' : '立即联系';
            const contactBtnClass2 = isContacted ? 'btn-contact sent' : 'btn-contact';
            const followers2 = kol ? kol.followers : 0;
            const price2 = kol ? kol.price : 0;

            html += `
                <div class="allocation-card">
                    <div class="allocation-card-main">
                        <div class="kol-info">
                            <div class="kol-name">${a.kol_name}</div>
                            <div class="kol-meta">
                                <span class="platform-badge ${platformClass}">${a.platform || '-'}</span>
                                <span class="contact-status ${statusClass}">${statusText}</span>
                            </div>
                        </div>
                        <div class="kol-budget-info">
                            <div class="kol-budget">¥${Math.round(a.allocated).toLocaleString()}</div>
                            <div class="kol-percentage">${a.percentage}%</div>
                            <button class="${contactBtnClass2} btn-contact-sm" onclick="event.stopPropagation(); openContactModal('${a.kol_id}', '${a.kol_name}', '${a.platform || ''}', ${followers2}, ${price2}, '${(kol && kol.recommend_reason || '').replace(/'/g, "\\'")}')">${contactBtnText2}</button>
                        </div>
                    </div>
                    <div class="allocation-card-detail">
                        <div class="allocation-detail-grid">
                            <div><strong>互动率</strong><span>${kol ? kol.engagement_rate + '%' : '-'}</span></div>
                            <div><strong>转化率</strong><span>${kol ? kol.conversion_rate + '%' : '-'}</span></div>
                            <div><strong>合作次数</strong><span>${kol ? kol.cooperation_count + '次' : '-'}</span></div>
                            <div><strong>受众</strong><span>${kol ? kol.audience : '-'}</span></div>
                        </div>
                        <div class="allocation-detail-reason"><strong>推荐理由：</strong>${kol ? (kol.recommend_reason || '-') : '-'}</div>
                        <div class="allocation-detail-link"><a href="detail.html?id=${a.kol_id}" target="_blank" rel="noopener">查看完整详情 →</a></div>
                    </div>
                </div>
            `;
        });
        html += '</div></div>';
    }
    html += '</div>';

    // Right: Charts
    html += '<div class="allocation-right chart-stack">';
    if (allocations.length > 0) {
        html += `<div class="chart-card"><h4>预算分配</h4><div id="budgetPie" style="width:100%; height:240px;"></div></div>`;
    }
    if (Object.keys(platformSummary).length > 0) {
        html += `<div class="chart-card"><h4>平台分布</h4><div id="platformBar" style="width:100%; height:240px;"></div></div>`;
    }
    html += '</div>';

    html += '</div>';

    // ===== 候选达人池 (全宽表格) =====
    if (top10.length > 0) {
        html += '<div class="candidate-pool card"><h2>候选达人池</h2>';
        html += '<table class="result-content" style="width:100%;"><thead><tr>';
        html += '<th>排名</th><th>达人名称</th><th>平台</th><th>粉丝数</th><th>报价</th>';
        html += '<th>匹配分数</th><th>预估 ROI</th><th>风险</th><th>操作</th>';
        html += '</tr></thead>';

        top10.forEach((kol, idx) => {
            const rank = kol.rank || (idx + 1);
            const rankIcon = rank <= 3 ? ['🥇', '🥈', '🥉'][rank - 1] : rank;
            const platformClass = { '小红书': 'xhs', '抖音': 'dy', 'B站': 'bz', '微博': 'wb' }[kol.platform] || '';
            const scoreClass = kol.total_score >= 80 ? 'high' : (kol.total_score >= 60 ? 'medium' : 'low');
            const riskClass = kol.risk_level === '高' ? 'high' : (kol.risk_level === '中' ? 'medium' : 'low');
            const riskText = kol.risk_level === '高' ? '广告比例高' : (kol.risk_level === '中' ? '需谨慎' : '无风险');
            const followers = kol.followers >= 10000 ? (kol.followers / 10000).toFixed(0) + '万' : kol.followers;

            const contactInfo = _contactStatus[kol.kol_id];
            const isContacted = contactInfo && contactInfo.status === 'sent';
            const contactBtnText = isContacted ? '查看联系' : '立即联系';
            const contactBtnClass = isContacted ? 'btn-contact sent' : 'btn-contact';

            html += '<tbody class="kol-group">';
            html += `<tr class="kol-main">`;
            html += `<td>${rankIcon}</td>`;
            html += `<td><strong>${kol.kol_name}</strong></td>`;
            html += `<td><span class="platform-badge ${platformClass}">${kol.platform}</span></td>`;
            html += `<td>${followers}</td>`;
            html += `<td>¥${kol.price.toLocaleString()}</td>`;
            html += `<td>
                <div class="match-bar"><div class="match-bar-fill ${scoreClass}" style="width:${kol.total_score}%"></div></div>
                ${kol.total_score}分
            </td>`;
            html += `<td>${kol.roi || '-'}</td>`;
            html += `<td><span class="risk-badge ${riskClass}">${riskText}</span></td>`;
            html += `<td><button class="${contactBtnClass}" onclick="event.stopPropagation(); openContactModal('${kol.kol_id}', '${kol.kol_name}', '${kol.platform}', ${kol.followers}, ${kol.price}, '${(kol.recommend_reason || '').replace(/'/g, "\\'")}')">${contactBtnText}</button></td>`;
            html += `</tr>`;

            html += `<tr class="detail-row">`;
            html += `<td colspan="9">`;
            html += `<div class="detail-grid">`;
            html += `<div><strong>互动率</strong><span>${kol.engagement_rate}%</span></div>`;
            html += `<div><strong>转化率</strong><span>${kol.conversion_rate}%</span></div>`;
            html += `<div><strong>合作次数</strong><span>${kol.cooperation_count}次</span></div>`;
            html += `<div><strong>受众</strong><span>${kol.audience}</span></div>`;
            html += `</div>`;
            html += `<div class="detail-reason"><strong>推荐理由：</strong>${kol.recommend_reason || '-'}</div>`;
            html += `<div class="detail-link"><a href="detail.html?id=${kol.kol_id}" target="_blank" rel="noopener">查看完整详情 →</a></div>`;
            html += `</td></tr>`;
            html += '</tbody>';
        });

        html += '</table></div>';
    }

    // ===== Advice Cards =====
    html += '<div class="advice-cards">';

    // 为什么选这几位
    html += '<div class="advice-card"><h4>🎯 为什么选这几位</h4><ul>';
    top10.slice(0, 3).forEach(kol => {
        html += `<li><strong>${kol.kol_name}</strong>：${kol.recommend_reason || '综合匹配度高'}</li>`;
    });
    html += '</ul></div>';

    // 预算怎么分
    if (allocations.length > 0) {
        html += '<div class="advice-card"><h4>💰 预算怎么分</h4><ul>';
        allocations.forEach(a => {
            html += `<li>${a.kol_name}：${a.allocated.toLocaleString()}元（${a.percentage}%）</li>`;
        });
        html += `<li>预留测试：${budgetAlloc.reserve?.toLocaleString() || 0}元</li>`;
        html += '</ul></div>';
    }

    // 投放注意事项
    const reportText = result.report || '';
    const cautionMatch = reportText.match(/注意事项[：:]([\s\S]*?)(?=$|##)/);
    const caution = cautionMatch ? cautionMatch[1].trim() : '';
    if (caution) {
        const bullets = caution.split(/\n|- /).filter(s => s.trim()).slice(0, 4);
        html += '<div class="advice-card"><h4>⚠️ 投放注意事项</h4><ul>';
        bullets.forEach(b => html += `<li>${b.trim().replace(/^-\s*/, '')}</li>`);
        html += '</ul></div>';
    } else {
        html += '<div class="advice-card"><h4>⚠️ 投放注意事项</h4><ul><li>最终投放决策需人工复核</li><li>建议优先核实排名前3达人的数据真实性</li></ul></div>';
    }

    html += '</div>';

    // Action bar
    html += `<div class="action-bar">`;
    html += `<button class="btn-secondary" onclick="copyReport()">📋 复制表格</button>`;
    html += `<button class="btn-secondary" onclick="exportCSV()">📊 导出表格报告</button>`;
    html += `<button class="btn-secondary" onclick="location.reload()">🔄 重新推荐</button>`;
    html += `</div>`;

    document.getElementById('resultArea').innerHTML = html;

    if (budgetAlloc.allocations) {
        setTimeout(() => {
            renderBudgetPie(budgetAlloc.allocations, budgetAlloc.reserve);
            renderPlatformBar(platformSummary);
        }, 100);
    }

    sessionStorage.setItem('kol_recommend_result', JSON.stringify(result));
    sessionStorage.setItem('kol_recommend_demand', JSON.stringify(demand));
    sessionStorage.setItem('kol_recommend_timestamp', Date.now().toString());
}

function renderBudgetPie(allocations, reserveAmount) {
    const chartDom = document.getElementById('budgetPie');
    if (!chartDom) return;
    const chart = echarts.init(chartDom);
    const data = allocations.map(a => ({ value: a.allocated, name: a.kol_name }));
    const reserve = reserveAmount || 0;
    if (reserve > 0) {
        data.push({ value: reserve, name: '预留测试' });
    }

    chart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c}元 ({d}%)' },
        legend: {
            orient: 'vertical',
            right: 10,
            top: 'center',
            type: 'scroll',
            textStyle: { fontSize: 11 }
        },
        series: [{
            type: 'pie',
            radius: ['40%', '65%'],
            center: ['40%', '50%'],
            avoidLabelOverlap: true,
            label: {
                show: true,
                formatter: '{d}%',
                fontSize: 11
            },
            labelLine: { show: true },
            emphasis: {
                label: { show: true, fontSize: 12, fontWeight: 'bold' }
            },
            data: data
        }]
    });
}

function renderPlatformBar(platformSummary) {
    const chartDom = document.getElementById('platformBar');
    if (!chartDom) return;
    const chart = echarts.init(chartDom);
    const platforms = Object.keys(platformSummary);
    const counts = Object.values(platformSummary);
    const colors = { '小红书': '#ff2442', '抖音': '#1c1c1c', 'B站': '#00a1d6', '微博': '#fa7d3c' };

    chart.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        xAxis: { type: 'category', data: platforms },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{
            type: 'bar',
            data: platforms.map((p, i) => ({
                value: counts[i],
                itemStyle: { color: colors[p] || '#667eea' }
            })),
            barWidth: '50%',
            label: {
                show: true,
                position: 'top',
                formatter: '{c}位',
                fontSize: 12,
                fontWeight: 'bold'
            }
        }]
    });
}

// Helper: escape CSV field (wrap in quotes if contains comma/newline/quote)
function _csvEscape(val) {
    const s = String(val ?? '');
    if (s.includes(',') || s.includes('"') || s.includes('\n') || s.includes('\r')) {
        return '"' + s.replace(/"/g, '""') + '"';
    }
    return s;
}

function _buildReportRows() {
    const top10 = window._lastTop10 || [];
    const result = window._lastResult || {};
    const demand = window._lastDemand || {};
    const budgetAlloc = result.budget_allocation || {};
    const platformSummary = result.platform_summary || {};
    const reportText = result.report || '';

    const rows = [];
    const now = new Date().toLocaleString('zh-CN');

    // ===== Section 1: Report Header =====
    rows.push(['AI KOL 达人推荐报告']);
    rows.push(['生成时间', now]);
    rows.push([]);

    // ===== Section 2: Demand Summary =====
    rows.push(['【投放需求】']);
    rows.push(['目标受众', demand.target_audience || '-']);
    rows.push(['内容领域', demand.content_field || '-']);
    rows.push(['预算范围（元/达人）', demand.budget_range || '-']);
    rows.push(['总预算（元）', demand.total_budget || '-']);
    rows.push(['投放平台', demand.platforms || '-']);
    rows.push([]);

    // ===== Section 3: KOL Recommendation Table =====
    rows.push(['【TOP 10 达人推荐明细】']);
    rows.push([
        '排名', '达人名称', '平台', '粉丝数', '报价（元）', '匹配分数',
        '预估ROI', '风险等级', '互动率（%）', '转化率（%）', '合作次数', '受众', '推荐理由'
    ]);

    top10.forEach((kol, idx) => {
        const rank = kol.rank || (idx + 1);
        const riskText = kol.risk_level === '高' ? '广告比例高' : (kol.risk_level === '中' ? '需谨慎' : '无风险');
        rows.push([
            rank,
            kol.kol_name,
            kol.platform,
            kol.followers,
            kol.price,
            kol.total_score,
            kol.roi || '-',
            riskText,
            kol.engagement_rate != null ? kol.engagement_rate : '-',
            kol.conversion_rate != null ? kol.conversion_rate : '-',
            kol.cooperation_count != null ? kol.cooperation_count : '-',
            kol.audience || '-',
            kol.recommend_reason || '-'
        ]);
    });
    rows.push([]);

    // ===== Section 4: Budget Allocation =====
    rows.push(['【预算分配方案】']);
    const allocations = budgetAlloc.allocations || [];
    if (allocations.length > 0) {
        rows.push(['达人名称', '分配金额（元）', '占比（%）']);
        allocations.forEach(a => {
            rows.push([a.kol_name, a.allocated, a.percentage]);
        });
        rows.push(['预留测试', budgetAlloc.reserve || 0, '-']);
    } else {
        rows.push(['暂无预算分配数据']);
    }
    rows.push([]);

    // ===== Section 5: Platform Summary =====
    rows.push(['【平台分布】']);
    const platforms = Object.keys(platformSummary);
    if (platforms.length > 0) {
        rows.push(['平台', '达人数量']);
        platforms.forEach(p => rows.push([p, platformSummary[p]]));
    } else {
        rows.push(['暂无平台分布数据']);
    }
    rows.push([]);

    // ===== Section 6: Advice / Notes =====
    rows.push(['【投放建议与注意事项】']);
    const cautionMatch = reportText.match(/注意事项[：:]([\s\S]*?)(?=$|##)/);
    const caution = cautionMatch ? cautionMatch[1].trim() : '';
    if (caution) {
        const bullets = caution.split(/\n|- /).filter(s => s.trim()).slice(0, 6);
        bullets.forEach(b => {
            const text = b.trim().replace(/^-\s*/, '');
            if (text) rows.push([text]);
        });
    }
    rows.push(['最终投放决策需人工复核']);
    rows.push(['对于首次合作的达人，建议人工核实数据真实性']);

    return rows;
}

function copyReport() {
    const top10 = window._lastTop10 || [];
    if (top10.length === 0) {
        alert('暂无推荐数据可复制');
        return;
    }
    const rows = _buildReportRows();
    const text = rows.map(r => r.map(_csvEscape).join(',')).join('\n');
    navigator.clipboard.writeText(text).then(() => {
        showToast('表格报告已复制到剪贴板');
    }).catch(() => {
        alert('复制失败，请手动复制');
    });
}

function exportCSV() {
    const top10 = window._lastTop10 || [];
    if (top10.length === 0) {
        alert('暂无推荐数据可导出');
        return;
    }
    const rows = _buildReportRows();
    const csvContent = '﻿' + rows.map(r => r.map(_csvEscape).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const dateStr = new Date().toISOString().slice(0, 10);
    a.download = `KOL推荐报告_${dateStr}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('表格报告已导出');
}

window.addEventListener('resize', () => {
    ['budgetPie', 'platformBar'].forEach(id => {
        const dom = document.getElementById(id);
        if (!dom) return;
        const chart = echarts.getInstanceByDom(dom);
        if (chart) chart.resize();
    });
});

// ========== Restore from History / Session ==========
document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(location.search);

    // 从历史记录页面恢复
    if (params.get('mode') === 'history') {
        const historyData = localStorage.getItem('kol_history_view');
        if (historyData) {
            try {
                const entry = JSON.parse(historyData);
                const budgetAlloc = entry.budget_allocation || {};
                const result = {
                    top10: entry.top10 || [],
                    report: '',
                    budget_allocation: budgetAlloc,
                    platform_summary: budgetAlloc.platform_summary || {},
                };
                renderResult(result, entry.demand || {});
                localStorage.removeItem('kol_history_view');
                // 移除 URL 参数
                history.replaceState(null, '', location.pathname);
            } catch (e) {
                console.error('恢复历史记录失败:', e);
            }
        }
        return;
    }

    // 从 sessionStorage 恢复推荐结果（详情页返回）
    const cachedResult = sessionStorage.getItem('kol_recommend_result');
    const cachedDemand = sessionStorage.getItem('kol_recommend_demand');
    const timestamp = sessionStorage.getItem('kol_recommend_timestamp');

    if (cachedResult && cachedDemand && timestamp) {
        const age = Date.now() - parseInt(timestamp);
        // 缓存有效期 30 分钟
        if (age < 30 * 60 * 1000) {
            try {
                renderResult(JSON.parse(cachedResult), JSON.parse(cachedDemand));
            } catch (e) {
                console.error('恢复推荐结果失败:', e);
                sessionStorage.removeItem('kol_recommend_result');
                sessionStorage.removeItem('kol_recommend_demand');
                sessionStorage.removeItem('kol_recommend_timestamp');
            }
        } else {
            // 缓存过期，清除
            sessionStorage.removeItem('kol_recommend_result');
            sessionStorage.removeItem('kol_recommend_demand');
            sessionStorage.removeItem('kol_recommend_timestamp');
        }
    }
});

// ========== Contact Modal ==========

function openContactModal(kolId, kolName, platform, followers, price, recommendReason) {
    const existing = document.getElementById('contactModal');
    if (existing) existing.remove();

    const followersText = followers >= 10000 ? (followers / 10000).toFixed(0) + '万' : followers;
    const company = _companySettings || {};
    const isContacted = _contactStatus[kolId] && _contactStatus[kolId].status === 'sent';

    const modal = document.createElement('div');
    modal.id = 'contactModal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>${isContacted ? '查看联系' : '立即联系'} — ${kolName}</h3>
                <button class="modal-close" onclick="closeContactModal()">×</button>
            </div>
            <div class="modal-body">
                <div class="modal-kol-card">
                    <div class="modal-kol-avatar">${kolName.charAt(0)}</div>
                    <div class="modal-kol-name">${kolName}</div>
                    <div class="modal-kol-meta">
                        <div><span class="platform-badge ${platform === '小红书' ? 'xhs' : platform === '抖音' ? 'dy' : platform === 'B站' ? 'bz' : 'wb'}">${platform}</span></div>
                        <div>粉丝：${followersText}</div>
                        <div>报价：¥${price.toLocaleString()}</div>
                    </div>
                </div>
                <div class="modal-form">
                    <label>品牌信息</label>
                    <div class="modal-company-info">
                        <div><strong>公司/品牌：</strong>${company.company_name || '【未填写】'}</div>
                        <div><strong>联系人：</strong>${company.contact_person || '【未填写】'}</div>
                        <div><strong>电话：</strong>${company.contact_phone || '【未填写】'}</div>
                        <div><strong>邮箱：</strong>${company.contact_email || '【未填写】'}</div>
                        ${(company.accounts && company.accounts[platform] && company.accounts[platform].username) ? `<div><strong>${platform}账号：</strong>${company.accounts[platform].username}</div>` : ''}
                    </div>
                    <label>邀约话术（可编辑）</label>
                    <textarea id="invitationText" placeholder="正在生成邀约话术...">${isContacted && _contactStatus[kolId].invitation_text ? _contactStatus[kolId].invitation_text : ''}</textarea>
                    <div class="modal-platform-tip">
                        💡 请复制上方话术，前往 ${platform} APP 私信达人。后续获得开发者资质后，可在此直接发送。
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button class="btn-secondary" onclick="closeContactModal()">取消</button>
                <button class="btn-primary" id="btnCopyContact" style="width: auto; padding: 10px 24px;" onclick="copyAndMarkContacted('${kolId}', '${kolName.replace(/'/g, "\\'")}', '${platform}')">${isContacted ? '复制话术' : '复制话术并标记为已联系'}</button>
            </div>
        </div>
    `;
    document.body.appendChild(modal);

    if (!isContacted) {
        generateInvitation(kolId, kolName, platform, recommendReason);
    }
}

function closeContactModal() {
    const modal = document.getElementById('contactModal');
    if (modal) {
        modal.style.opacity = '0';
        setTimeout(() => modal.remove(), 200);
    }
}

async function generateInvitation(kolId, kolName, platform, recommendReason) {
    const textarea = document.getElementById('invitationText');
    if (!textarea) return;

    const demand = _currentDemand || {};
    const payload = {
        kol_id: kolId,
        kol_name: kolName,
        platform: platform,
        content_field: demand.content_field || '校园',
        target_audience: demand.target_audience || '大学生、应届生',
        budget_range: demand.budget_range || '1000-3000',
        recommend_reason: recommendReason || '',
    };

    try {
        const resp = await fetch(`${API_BASE}/api/generate_invitation`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const result = await resp.json();
        if (result.success && textarea) {
            textarea.value = result.invitation_text;
        }
    } catch (e) {
        console.error('生成邀约失败:', e);
        if (textarea) {
            textarea.value = '生成邀约话术失败，请手动编辑。';
        }
    }
}

async function copyAndMarkContacted(kolId, kolName, platform) {
    const textarea = document.getElementById('invitationText');
    if (!textarea) return;

    const text = textarea.value.trim();
    if (!text) {
        showToast('邀约话术为空，请先填写');
        return;
    }

    try {
        await navigator.clipboard.writeText(text);
    } catch (e) {
        showToast('复制失败，请手动复制');
        return;
    }

    try {
        const resp = await fetch(`${API_BASE}/api/contact_status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                kol_id: kolId,
                kol_name: kolName,
                platform: platform,
                status: 'sent',
                invitation_text: text,
            }),
        });
        const result = await resp.json();
        if (result.success) {
            _contactStatus[kolId] = result.data;
            showToast('已复制话术并标记为已联系');
            closeContactModal();
            // 刷新当前推荐结果以更新按钮状态
            const cachedResult = sessionStorage.getItem('kol_recommend_result');
            const cachedDemand = sessionStorage.getItem('kol_recommend_demand');
            if (cachedResult && cachedDemand) {
                renderResult(JSON.parse(cachedResult), JSON.parse(cachedDemand));
            }
        } else {
            showToast('标记状态失败：' + (result.error || '未知错误'));
        }
    } catch (e) {
        showToast('请求失败：' + e.message);
    }
}

// 在 renderResult 调用时保存当前需求上下文
const _originalRenderResult = renderResult;
renderResult = function(result, demand) {
    _currentDemand = demand;
    _originalRenderResult(result, demand);
};
