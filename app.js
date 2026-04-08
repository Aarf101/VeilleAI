const pages = {
    dashboard: `
        <div class="dashboard-grid">
            <div class="stats-row">
                <div class="card stat-card">
                    <div class="stat-accent accent-blue"></div>
                    <span class="section-title">Total Articles</span>
                    <div class="stat-number blue" id="total-article-count">0</div>
                    <div class="stat-subtitle">From database</div>
                </div>
                <div class="card stat-card">
                    <div class="stat-accent accent-green"></div>
                    <span class="section-title">Active Sources</span>
                    <div class="stat-number" id="active-source-count">0</div>
                    <div class="stat-subtitle">Configured feeds</div>
                </div>
                <div class="card stat-card">
                    <div class="stat-accent accent-amber"></div>
                    <span class="section-title">Topics</span>
                    <div class="stat-number">18</div>
                    <div class="stat-subtitle">3 new this month</div>
                </div>
                <div class="card stat-card">
                    <div class="stat-accent accent-gray"></div>
                    <span class="section-title">RSS Feeds</span>
                    <div class="stat-number">42</div>
                    <div class="stat-subtitle">Last update: 5m ago</div>
                </div>
            </div>

            <div class="main-grid">
                <div class="col-left">
                    <div class="card mb-2">
                        <span class="section-title">Monitored Topics</span>
                        <div class="topic-tags">
                            <span class="badge badge-blue">Artificial Intelligence</span>
                            <span class="badge badge-blue">Machine Learning</span>
                            <span class="badge badge-blue">Cybersecurity</span>
                            <span class="badge badge-blue">Quantum Computing</span>
                            <span class="badge badge-blue">Robotics</span>
                            <span class="badge badge-blue">NLP</span>
                            <span class="badge badge-blue">Edge Computing</span>
                        </div>
                    </div>
                    <div class="card">
                        <span class="section-title">System Status</span>
                        <div class="system-details">
                            <div class="detail-row">
                                <span class="label">Scheduler</span>
                                <span class="badge badge-green">Active</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">Interval</span>
                                <span class="value">Every 15 minutes</span>
                            </div>
                            <div class="detail-row">
                                <span class="label">DB Status</span>
                                <span class="value">Healthy (2.4 GB)</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-right">
                    <div class="card mb-2">
                        <span class="section-title">Quick Actions</span>
                        <div class="actions-list">
                            <button class="btn btn-primary w-full mb-1">
                                <span>🚀</span> Run Full Pipeline
                            </button>
                            <button class="btn btn-secondary w-full mb-1">Clear Cache</button>
                            <button class="btn btn-secondary w-full">Export Data</button>
                        </div>
                    </div>
                    <div class="card">
                        <span class="section-title">Data Sources</span>
                        <div class="feed-list">
                            <div class="feed-item">https://techcrunch.com/feed/</div>
                            <div class="feed-item">https://wired.com/feed/rss</div>
                            <div class="feed-item">https://theverge.com/rss/index.xml</div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card reports-section">
                <span class="section-title">Intelligence Reports</span>
                <div class="report-list">
                    <div class="report-row">
                        <div class="report-info">
                            <div class="report-date">March 17, 2026</div>
                            <div class="report-name">Daily AI Trends Summary</div>
                        </div>
                        <div class="report-actions">
                            <span class="badge badge-blue">MD</span>
                            <span class="badge badge-blue">PDF</span>
                            <span class="badge badge-blue">DOCX</span>
                        </div>
                    </div>
                    <div class="report-row">
                        <div class="report-info">
                            <div class="report-date">March 16, 2026</div>
                            <div class="report-name">Cybersecurity Weekly Brief</div>
                        </div>
                        <div class="report-actions">
                            <span class="badge badge-blue">MD</span>
                            <span class="badge badge-blue">PDF</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card" id="recent-articles-section">
                <span class="section-title">Collected Articles</span>
                <div id="recent-articles-list" class="report-list">
                    <div class="report-row"><div class="report-info"><div class="report-name">Loading articles...</div></div></div>
                </div>
            </div>
        </div>
    `,
    'run-pipeline': `
        <div class="card">
            <span class="section-title">Run Pipeline</span>
            <div class="pipeline-options mb-2">
                <label class="radio-container">
                    <input type="radio" name="mode" checked> Full Collection
                </label>
                <label class="radio-container">
                    <input type="radio" name="mode"> Incremental
                </label>
                <label class="radio-container">
                    <input type="radio" name="mode"> Deep Search
                </label>
            </div>
            <span class="section-title">Pre-flight Check</span>
            <div class="status-grid">
                <div class="grid-item"><span>✅</span> API Connectivity</div>
                <div class="grid-item"><span>✅</span> DB Write Access</div>
                <div class="grid-item"><span>✅</span> Model Availability</div>
                <div class="grid-item"><span>✅</span> Proxy Rotation</div>
            </div>
            <button class="btn btn-primary mt-2">Initialize Collection</button>
        </div>
    `,
    'scheduler': `
        <div class="card mb-2">
            <span class="section-title">Scheduler Control</span>
            <div class="scheduler-status mb-2">
                <div class="status-item">State: <span class="badge badge-green">RUNNING</span></div>
                <div class="status-item">Interval: <span class="value">15m</span></div>
                <div class="status-item">PID: <span class="value">8421</span></div>
            </div>
            <div class="button-group">
                <button class="btn btn-primary">Start</button>
                <button class="btn btn-secondary">Stop</button>
                <button class="btn btn-secondary">Restart</button>
            </div>
        </div>
        <div class="card">
            <span class="section-title">Recent Logs</span>
            <div class="log-viewer">
                <div class="log-line">[2026-03-17 22:30:05] Pipeline started...</div>
                <div class="log-line">[2026-03-17 22:35:12] 124 articles fetched</div>
                <div class="log-line">[2026-03-17 22:40:45] NLP Processing completed</div>
                <div class="log-line success">[2026-03-17 22:41:02] Cycle finished successfully</div>
            </div>
        </div>
    `,
    'topics': `
        <div class="card mb-2">
            <span class="section-title">Add New Topic</span>
            <div class="input-group">
                <input type="text" class="input" placeholder="Enter topic name...">
                <button class="btn btn-primary">Add Topic</button>
            </div>
            <div class="presets mt-1">
                <button class="btn btn-secondary btn-sm">Tech</button>
                <button class="btn btn-secondary btn-sm">Health</button>
                <button class="btn btn-secondary btn-sm">Finance</button>
            </div>
        </div>
        <div class="card">
            <span class="section-title">Active Topics</span>
            <div class="list-container">
                <div class="list-item">
                    <span>Artificial Intelligence</span>
                    <button class="btn btn-danger btn-sm">Remove</button>
                </div>
                <div class="list-item">
                    <span>Cybersecurity</span>
                    <button class="btn btn-danger btn-sm">Remove</button>
                </div>
            </div>
        </div>
    `,
    'data-sources': `
        <div class="card mb-2">
            <span class="section-title">Add RSS Feed</span>
            <div class="input-group">
                <input type="text" class="input" placeholder="https://...">
                <button class="btn btn-primary">Add Feed</button>
            </div>
        </div>
        <div class="card">
            <span class="section-title">RSS Feeds</span>
            <div class="list-container">
                <div class="list-item">
                    <span>TechCrunch</span>
                    <button class="btn btn-danger btn-sm">Remove</button>
                </div>
            </div>
            <div class="mt-2">
                <span class="section-title">Collection Limit</span>
                <input type="range" class="slider" min="10" max="500" value="100">
                <div class="slider-value">100 articles per source</div>
            </div>
        </div>
    `,
    'advanced': `
        <div class="card">
            <span class="section-title">LLM Configuration</span>
            <div class="form-group mb-2">
                <label>Provider</label>
                <select class="select">
                    <option>Groq</option>
                    <option>OpenAI</option>
                    <option>Anthropic</option>
                </select>
            </div>
            <div class="form-group mb-2">
                <label>Model</label>
                <select class="select">
                    <option>llama3-70b-8192</option>
                    <option>mixtral-8x7b-32768</option>
                </select>
            </div>
            <span class="section-title">Thresholds</span>
            <div class="mb-2">
                <label>Relevance Filter</label>
                <input type="range" class="slider" min="0" max="100" value="75">
            </div>
            <span class="section-title">Scheduler Frequency</span>
            <div class="button-group">
                <button class="btn btn-secondary active">Hourly</button>
                <button class="btn btn-secondary">6h</button>
                <button class="btn btn-secondary">Daily</button>
            </div>
        </div>
    `,
    'monitoring': `
        <div class="stats-row mb-2">
            <div class="card stat-card">
                <span class="section-title">CPU Load</span>
                <div class="stat-number">12%</div>
            </div>
            <div class="card stat-card">
                <span class="section-title">RAM Usage</span>
                <div class="stat-number">458MB</div>
            </div>
            <div class="card stat-card">
                <span class="section-title">API Latency</span>
                <div class="stat-number">142ms</div>
            </div>
            <div class="card stat-card">
                <span class="section-title">Uptime</span>
                <div class="stat-number">99.9%</div>
            </div>
        </div>
        <div class="card">
            <span class="section-title">Health Status</span>
            <div class="status-grid">
                <div class="grid-item">DB Connection: OK</div>
                <div class="grid-item">Worker Node 1: OK</div>
                <div class="grid-item">Cache Layer: OK</div>
                <div class="grid-item">Storage: 85% Free</div>
            </div>
        </div>
    `
};

document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');
    const contentArea = document.getElementById('page-content');

    function loadPage(pageId) {
        // Update Nav
        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.dataset.page === pageId) {
                item.classList.add('active');
            }
        });

        // Update Content
        contentArea.innerHTML = pages[pageId] || pages.dashboard;
        
        // Scroll to top
        window.scrollTo(0, 0);
    }

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            loadPage(item.dataset.page);
        });
    });

    async function refreshDashboardMetrics() {
        try {
            const resp = await fetch('/api/article-count', {cache: 'no-store'});
            if (!resp.ok) {
                console.warn('Dashboard API not available', resp.status);
                return;
            }
            const json = await resp.json();
            const count = Number(json.articles || 0);
            const feeds = Number(json.feeds || 0);

            const totalEl = document.getElementById('total-article-count');
            if (totalEl) totalEl.textContent = count.toLocaleString();

            const headerEl = document.getElementById('header-article-count');
            if (headerEl) headerEl.textContent = `${count.toLocaleString()} articles`;

            const feedEl = document.getElementById('active-source-count');
            if (feedEl) feedEl.textContent = feeds.toLocaleString();

            const headerFeedEl = document.getElementById('header-feed-count');
            if (headerFeedEl) headerFeedEl.textContent = `${feeds.toLocaleString()} feeds`;
        } catch (error) {
            console.warn('Error fetching dashboard metrics', error);
        }
    }

    async function refreshRecentArticles() {
        try {
            const resp = await fetch('/api/recent-articles', {cache: 'no-store'});
            if (!resp.ok) return;
            const articles = await resp.json();
            const listEl = document.getElementById('recent-articles-list');
            if (listEl && articles.length > 0) {
                listEl.innerHTML = articles.map(art => `
                    <div class="report-row">
                        <div class="report-info">
                            <div class="report-date">${art.source || 'Unknown'} · ${art.published || ''}</div>
                            <div class="report-name"><a href="${art.url || '#'}" target="_blank" style="color:inherit; text-decoration:none;">${art.title}</a></div>
                        </div>
                    </div>
                `).join('');
            } else if (listEl) {
                listEl.innerHTML = '<div class="report-row"><div class="report-info"><div class="report-name">No articles collected yet.</div></div></div>';
            }
        } catch (error) {
            console.warn('Error fetching recent articles', error);
        }
    }

    // Initial load
    loadPage('dashboard');
    refreshDashboardMetrics();
    refreshRecentArticles();

    // refresh every 60 seconds
    setInterval(() => {
        refreshDashboardMetrics();
        refreshRecentArticles();
    }, 60000);
});
