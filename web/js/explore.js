const API_BASE = 'http://127.0.0.1:5000';
let allKOLs = [];
let platformChart = null;
let fieldChart = null;

// Platform colors
const PLATFORM_COLORS = {
    '小红书': '#ff2442',
    '抖音': '#1c1c1c',
    'B站': '#00a1d6',
    '微博': '#fa7d3c'
};

async function loadKOLs() {
    const grid = document.getElementById('kolGrid');
    grid.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;"><div class="empty-icon">📋</div><h3>加载中...</h3></div>';

    try {
        const resp = await fetch(`${API_BASE}/api/kols`);
        const result = await resp.json();
        if (result.success) {
            allKOLs = result.data || [];
            updateAll(allKOLs);
        }
    } catch (e) {
        grid.innerHTML = `<div class="empty-state" style="grid-column: 1 / -1; color: #e74c3c;"><h3>加载失败</h3><p>${e.message}</p></div>`;
    }
}

function updateAll(kols) {
    renderStats(kols);
    renderCharts(kols);
    renderCards(kols);
}

function renderStats(kols) {
    const container = document.getElementById('statsOverview');
    if (!container) return;

    const total = kols.length;
    const platforms = new Set(kols.map(k => k.platform)).size;
    const avgEngagement = total > 0 ? (kols.reduce((s, k) => s + k.engagement_rate, 0) / total).toFixed(1) : 0;
    const avgConversion = total > 0 ? (kols.reduce((s, k) => s + k.conversion_rate, 0) / total).toFixed(1) : 0;

    container.innerHTML = `
        <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-value">${total}</div>
            <div class="stat-label">达人总数</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🌐</div>
            <div class="stat-value">${platforms}</div>
            <div class="stat-label">覆盖平台</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-value">${avgEngagement}%</div>
            <div class="stat-label">平均互动率</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🎯</div>
            <div class="stat-value">${avgConversion}%</div>
            <div class="stat-label">平均转化率</div>
        </div>
    `;
}

function renderCharts(kols) {
    // Platform pie chart
    const platformData = {};
    kols.forEach(k => {
        platformData[k.platform] = (platformData[k.platform] || 0) + 1;
    });

    const pieDom = document.getElementById('platformChart');
    if (pieDom) {
        if (!platformChart) platformChart = echarts.init(pieDom);
        platformChart.setOption({
            title: { text: '平台分布', left: 'center', textStyle: { fontSize: 14 } },
            tooltip: { trigger: 'item', formatter: '{b}: {c}人 ({d}%)' },
            series: [{
                type: 'pie',
                radius: ['40%', '70%'],
                center: ['50%', '55%'],
                data: Object.entries(platformData).map(([name, value]) => ({
                    name, value,
                    itemStyle: { color: PLATFORM_COLORS[name] || '#667eea' }
                })),
                label: { show: true, formatter: '{b}\n{c}人' }
            }]
        });
    }

    // Field bar chart
    const fieldData = {};
    kols.forEach(k => {
        if (k.field) {
            k.field.split('/').forEach(f => {
                const trimmed = f.trim();
                if (trimmed) fieldData[trimmed] = (fieldData[trimmed] || 0) + 1;
            });
        }
    });

    const sortedFields = Object.entries(fieldData).sort((a, b) => b[1] - a[1]).slice(0, 8);

    const barDom = document.getElementById('fieldChart');
    if (barDom) {
        if (!fieldChart) fieldChart = echarts.init(barDom);
        fieldChart.setOption({
            title: { text: '领域分布', left: 'center', textStyle: { fontSize: 14 } },
            tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
            grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
            xAxis: { type: 'value', minInterval: 1 },
            yAxis: { type: 'category', data: sortedFields.map(([name]) => name), inverse: true },
            series: [{
                type: 'bar',
                data: sortedFields.map(([_, value]) => value),
                itemStyle: {
                    color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                        { offset: 0, color: '#667eea' },
                        { offset: 1, color: '#764ba2' }
                    ])
                },
                barWidth: '60%'
            }]
        });
    }
}

function renderCards(kols) {
    const grid = document.getElementById('kolGrid');
    if (kols.length === 0) {
        grid.innerHTML = '<div class="empty-state" style="grid-column: 1 / -1;"><div class="empty-icon">🔍</div><h3>未找到符合条件的达人</h3></div>';
        return;
    }

    const avgEngagement = kols.length > 0 ? kols.reduce((s, k) => s + k.engagement_rate, 0) / kols.length : 0;

    grid.innerHTML = kols.map(kol => {
        const platformClass = { '小红书': 'xhs', '抖音': 'dy', 'B站': 'bz', '微博': 'wb' }[kol.platform] || '';
        const followers = kol.followers >= 10000 ? (kol.followers / 10000).toFixed(0) + '万' : kol.followers;
        const erColor = kol.engagement_rate >= 4.0 ? '#52c41a' : (kol.engagement_rate >= 3.0 ? '#faad14' : '#f5222d');
        const riskClass = kol.risk_note?.includes('广告') ? 'high' : (kol.risk_note?.includes('需') ? 'medium' : 'low');
        const conversionArrow = kol.conversion_rate >= avgEngagement ? '↑' : '↓';
        const conversionColor = kol.conversion_rate >= avgEngagement ? '#52c41a' : '#f5222d';

        return `
            <div class="kol-card" onclick="location.href='detail.html?id=${kol.kol_id}'">
                <div class="kol-card-header">
                    <div class="kol-avatar-small">${kol.kol_name.charAt(0)}</div>
                    <div class="kol-card-title">
                        <div class="kol-name">${kol.kol_name}</div>
                        <span class="platform-badge ${platformClass}">${kol.platform}</span>
                    </div>
                    <div class="risk-dot ${riskClass}"></div>
                </div>
                <div class="kol-card-body">
                    <div class="kol-metric">
                        <span class="metric-label">粉丝</span>
                        <span class="metric-value">${followers}</span>
                    </div>
                    <div class="kol-metric">
                        <span class="metric-label">报价</span>
                        <span class="metric-value">¥${kol.price.toLocaleString()}</span>
                    </div>
                    <div class="kol-metric">
                        <span class="metric-label">互动率</span>
                        <div class="mini-bar">
                            <div class="mini-bar-fill" style="width: ${Math.min(kol.engagement_rate * 20, 100)}%; background: ${erColor};"></div>
                        </div>
                        <span class="metric-value">${kol.engagement_rate}%</span>
                    </div>
                    <div class="kol-metric">
                        <span class="metric-label">转化率</span>
                        <span class="metric-value" style="color: ${conversionColor};">${kol.conversion_rate}% ${conversionArrow}</span>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function applyFilters() {
    const platform = document.getElementById('filterPlatform').value;
    const field = document.getElementById('filterField').value;
    const search = document.getElementById('searchName').value.toLowerCase();
    const sort = document.getElementById('sortBy').value;

    let filtered = allKOLs;

    if (platform) filtered = filtered.filter(k => k.platform === platform);
    if (field) filtered = filtered.filter(k => k.field && k.field.includes(field));
    if (search) filtered = filtered.filter(k => k.kol_name.toLowerCase().includes(search));

    filtered.sort((a, b) => (b[sort] || 0) - (a[sort] || 0));

    updateAll(filtered);
}

function resetFilters() {
    document.getElementById('searchName').value = '';
    document.getElementById('filterPlatform').value = '';
    document.getElementById('filterField').value = '';
    document.getElementById('sortBy').value = 'followers';
    updateAll(allKOLs);
}

// Handle resize
window.addEventListener('resize', () => {
    if (platformChart) platformChart.resize();
    if (fieldChart) fieldChart.resize();
});

loadKOLs();
