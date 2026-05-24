const API_BASE = 'http://127.0.0.1:5000';

// ========== Sidebar Toggle ==========
function toggleSidebar() {
    const section = document.getElementById('formSection');
    section.classList.toggle('collapsed');
    const isCollapsed = section.classList.contains('collapsed');
    const btn = section.querySelector('.collapse-btn');
    btn.innerHTML = isCollapsed ? '▶' : '◀';
    btn.title = isCollapsed ? '展开表单' : '收起表单';
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
    window._lastTop10 = top10;  // 保存供复制/导出使用
    const budgetAlloc = result.budget_allocation || {};
    const platformSummary = result.platform_summary || {};

    const avgScore = top10.length
        ? (top10.reduce((s, r) => s + r.total_score, 0) / top10.length).toFixed(1)
        : 0;
    const totalBudget = demand.total_budget || 15000;

    let html = '';

    // Stats cards
    html += `
        <div class="stats-row">
            <div class="stat-card">
                <div class="stat-value">${top10.length}</div>
                <div class="stat-label">推荐达人</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${avgScore}</div>
                <div class="stat-label">平均匹配分</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${totalBudget.toLocaleString()}</div>
                <div class="stat-label">总预算（元）</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${Object.keys(platformSummary).length}</div>
                <div class="stat-label">覆盖平台</div>
            </div>
        </div>
    `;

    // Two-column layout
    html += '<div class="result-layout">';

    // Left: TOP10 Table
    html += '<div class="result-left">';
    if (top10.length > 0) {
        html += '<div class="card"><h2>TOP 10 达人推荐</h2>';
        html += '<table class="result-content" style="width:100%;"><thead><tr>';
        html += '<th>排名</th><th>达人名称</th><th>平台</th><th>粉丝数</th><th>报价</th>';
        html += '<th>匹配分数</th><th>预估 ROI</th><th>风险</th>';
        html += '</tr></thead><tbody>';

        top10.forEach((kol, idx) => {
            const rank = kol.rank || (idx + 1);
            const rankIcon = rank <= 3 ? ['🥇', '🥈', '🥉'][rank - 1] : rank;
            const platformClass = { '小红书': 'xhs', '抖音': 'dy', 'B站': 'bz', '微博': 'wb' }[kol.platform] || '';
            const scoreClass = kol.total_score >= 80 ? 'high' : (kol.total_score >= 60 ? 'medium' : 'low');
            const riskClass = kol.risk_level === '高' ? 'high' : (kol.risk_level === '中' ? 'medium' : 'low');
            const riskText = kol.risk_level === '高' ? '广告比例高' : (kol.risk_level === '中' ? '需谨慎' : '无风险');
            const followers = kol.followers >= 10000 ? (kol.followers / 10000).toFixed(0) + '万' : kol.followers;

            html += `<tr onmouseenter="showDetail(this, ${idx})" onmouseleave="hideDetail(this)">`;
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
            html += `</tr>`;

            html += `<tr class="detail-row" id="detail-${idx}" style="display:none; background:#f8f9ff;">`;
            html += `<td colspan="8" style="padding:16px;">`;
            html += `<div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; margin-bottom:12px;">`;
            html += `<div><strong>互动率</strong><br>${kol.engagement_rate}%</div>`;
            html += `<div><strong>转化率</strong><br>${kol.conversion_rate}%</div>`;
            html += `<div><strong>合作次数</strong><br>${kol.cooperation_count}次</div>`;
            html += `<div><strong>受众</strong><br>${kol.audience}</div>`;
            html += `</div>`;
            html += `<div><strong>推荐理由：</strong>${kol.recommend_reason || '-'}</div>`;
            html += `<div style="margin-top:8px;"><a href="detail.html?id=${kol.kol_id}" style="color:#667eea;">查看完整详情 →</a></div>`;
            html += `</td></tr>`;
        });

        html += '</tbody></table></div>';
    }
    html += '</div>';

    // Right: Charts
    html += '<div class="result-right">';
    if (budgetAlloc.allocations && budgetAlloc.allocations.length > 0) {
        html += `<div class="chart-card"><h4>预算分配</h4><div id="budgetPie" style="width:100%; height:220px;"></div></div>`;
    }
    if (Object.keys(platformSummary).length > 0) {
        html += `<div class="chart-card"><h4>平台分布</h4><div id="platformBar" style="width:100%; height:220px;"></div></div>`;
    }
    html += '</div>';

    html += '</div>';

    // Advice cards
    html += '<div class="advice-cards">';

    // Budget advice
    if (budgetAlloc.allocations && budgetAlloc.allocations.length > 0) {
        html += '<div class="advice-card"><h4>💰 预算分配</h4><ul>';
        budgetAlloc.allocations.forEach(a => {
            html += `<li>${a.kol_name}：${a.allocated.toLocaleString()}元（${a.percentage}%）</li>`;
        });
        html += `<li>预留测试：${budgetAlloc.reserve?.toLocaleString() || 0}元</li>`;
        html += '</ul></div>';
    }

    // Platform advice
    if (Object.keys(platformSummary).length > 0) {
        html += '<div class="advice-card"><h4>📊 平台组合</h4><ul>';
        Object.entries(platformSummary).forEach(([platform, count]) => {
            html += `<li>${platform}：${count}位达人</li>`;
        });
        html += '</ul></div>';
    }

    // Risk advice from report
    const reportText = result.report || '';
    const cautionMatch = reportText.match(/注意事项[：:]([\s\S]*?)(?=$|##)/);
    const caution = cautionMatch ? cautionMatch[1].trim() : '';
    if (caution) {
        const bullets = caution.split(/\n|- /).filter(s => s.trim()).slice(0, 4);
        html += '<div class="advice-card"><h4>⚠️ 注意事项</h4><ul>';
        bullets.forEach(b => html += `<li>${b.trim().replace(/^-\s*/, '')}</li>`);
        html += '</ul></div>';
    } else {
        html += '<div class="advice-card"><h4>⚠️ 注意事项</h4><ul><li>最终投放决策需人工复核</li><li>建议优先核实排名前3达人的数据真实性</li></ul></div>';
    }

    html += '</div>';

    // Action bar
    html += `<div class="action-bar">`;
    html += `<button class="btn-secondary" onclick="copyReport()">📋 复制报告</button>`;
    html += `<button class="btn-secondary" onclick="exportCSV()">📊 导出 CSV</button>`;
    html += `<button class="btn-secondary" onclick="location.reload()">🔄 重新推荐</button>`;
    html += `</div>`;

    document.getElementById('resultArea').innerHTML = html;

    if (budgetAlloc.allocations) {
        setTimeout(() => {
            renderBudgetPie(budgetAlloc.allocations);
            renderPlatformBar(platformSummary);
        }, 100);
    }
}

function showDetail(row, idx) {
    const detailRow = document.getElementById(`detail-${idx}`);
    if (detailRow) detailRow.style.display = 'table-row';
}

function hideDetail(row) {
    let next = row.nextElementSibling;
    while (next && !next.classList.contains('detail-row')) {
        next = next.nextElementSibling;
    }
    if (next) next.style.display = 'none';
}

function renderBudgetPie(allocations) {
    const chartDom = document.getElementById('budgetPie');
    if (!chartDom) return;
    const chart = echarts.init(chartDom);
    const data = allocations.map(a => ({ value: a.allocated, name: a.kol_name }));
    if (allocations.length > 0) {
        const reserve = allocations[0].allocated * 0.25;
        data.push({ value: reserve, name: '预留测试' });
    }

    chart.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c}元 ({d}%)' },
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: true,
            label: { show: false },
            emphasis: { label: { show: true, fontSize: 12, fontWeight: 'bold' } },
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
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: platforms },
        yAxis: { type: 'value', minInterval: 1 },
        series: [{
            type: 'bar',
            data: platforms.map((p, i) => ({
                value: counts[i],
                itemStyle: { color: colors[p] || '#667eea' }
            })),
            barWidth: '50%'
        }]
    });
}

function copyReport() {
    const top10 = window._lastTop10 || [];
    if (top10.length === 0) {
        alert('暂无推荐数据可复制');
        return;
    }
    const lines = ['排名,达人名称,平台,粉丝数,报价,匹配分,预估ROI,风险'];
    top10.forEach((kol, idx) => {
        lines.push(`${idx + 1},${kol.kol_name},${kol.platform},${kol.followers},${kol.price},${kol.total_score},${kol.roi || '-'},${kol.risk_level || '低'}`);
    });
    navigator.clipboard.writeText(lines.join('\n')).then(() => {
        showToast('报告已复制到剪贴板');
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
    const lines = ['﻿排名,达人名称,平台,粉丝数,报价,匹配分,预估ROI,风险'];
    top10.forEach((kol, idx) => {
        lines.push(`${idx + 1},${kol.kol_name},${kol.platform},${kol.followers},${kol.price},${kol.total_score},${kol.roi || '-'},${kol.risk_level || '低'}`);
    });
    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `KOL推荐_${new Date().toLocaleDateString()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('CSV 已导出');
}

window.addEventListener('resize', () => {
    document.querySelectorAll('.chart-container').forEach(dom => {
        const chart = echarts.getInstanceByDom(dom);
        if (chart) chart.resize();
    });
});

// ========== Restore from History ==========
document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(location.search);
    if (params.get('mode') === 'history') {
        const historyData = localStorage.getItem('kol_history_view');
        if (historyData) {
            try {
                const entry = JSON.parse(historyData);
                const result = {
                    top10: entry.top10 || [],
                    report: '',
                    budget_allocation: entry.budget_allocation || null,
                    platform_summary: entry.budget_allocation?.platform_summary || {},
                };
                renderResult(result, entry.demand || {});
                localStorage.removeItem('kol_history_view');
                // 移除 URL 参数
                history.replaceState(null, '', location.pathname);
            } catch (e) {
                console.error('恢复历史记录失败:', e);
            }
        }
    }
});
