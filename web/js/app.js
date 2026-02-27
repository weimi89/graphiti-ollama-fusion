/**
 * Graphiti Web 管理介面 - 主應用邏輯
 */
const App = {
    // 狀態
    state: {
        page: 'dashboard',
        groupId: '',
        currentPage: 1,
        searchValue: '',
        searchMode: 'filter', // 'filter' | 'vector'
    },

    _searchTimer: null,

    // ============================================================
    // 初始化
    // ============================================================

    async init() {
        this._initTheme();
        this._initRouter();
        this._initEvents();
        await this._loadGroups();
        this._handleRoute();
    },

    _initTheme() {
        const saved = localStorage.getItem('graphiti-theme') || 'dark';
        document.documentElement.setAttribute('data-theme', saved);

        document.getElementById('theme-toggle').addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('graphiti-theme', next);
        });
    },

    _initRouter() {
        window.addEventListener('hashchange', () => this._handleRoute());
    },

    _initEvents() {
        // Group 篩選
        document.getElementById('group-filter').addEventListener('change', (e) => {
            this.state.groupId = e.target.value;
            this.state.currentPage = 1;
            this._renderCurrentPage();
        });

        // 搜尋框 Enter
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.target.id === 'search-input') {
                this.doSearch();
            }
        });

        // 實時搜尋（debounce 500ms）
        document.addEventListener('input', (e) => {
            if (e.target.id === 'search-input') {
                clearTimeout(this._searchTimer);
                this._searchTimer = setTimeout(() => this.doSearch(), 500);
            }
        });

        // Dialog
        document.getElementById('confirm-cancel').addEventListener('click', () => {
            document.getElementById('confirm-dialog').close();
            this._confirmResolve?.(false);
        });
        document.getElementById('confirm-ok').addEventListener('click', () => {
            document.getElementById('confirm-dialog').close();
            this._confirmResolve?.(true);
        });
    },

    // ============================================================
    // 路由
    // ============================================================

    _handleRoute() {
        const hash = location.hash.replace('#', '') || '/';
        const parts = hash.split('/').filter(Boolean);
        const page = parts[0] || 'dashboard';

        // 更新導航高亮
        document.querySelectorAll('.nav-link').forEach(link => {
            const linkPage = link.dataset.page;
            link.classList.toggle('active', linkPage === page || (!linkPage && page === 'dashboard'));
        });

        // 頁面切換時重設狀態
        if (this.state.page !== page) {
            this.state.page = page;
            this.state.currentPage = 1;
            this.state.searchValue = '';
            this.state.searchMode = 'filter';
        }

        this._renderCurrentPage();
    },

    async _renderCurrentPage() {
        const app = document.getElementById('app');
        app.innerHTML = '<div class="loading-spinner">載入中...</div>';

        try {
            switch (this.state.page) {
                case 'dashboard':
                    await this._renderDashboard(app);
                    break;
                case 'nodes':
                    await this._renderNodes(app);
                    break;
                case 'facts':
                    await this._renderFacts(app);
                    break;
                case 'episodes':
                    await this._renderEpisodes(app);
                    break;
                default:
                    app.innerHTML = '<div class="empty-state"><div class="empty-state-text">頁面不存在</div></div>';
            }
        } catch (err) {
            console.error('Render error:', err);
            app.innerHTML = `<div class="empty-state"><div class="empty-state-text">載入失敗: ${err.message}</div></div>`;
        }
    },

    // ============================================================
    // 頁面渲染
    // ============================================================

    async _renderDashboard(app) {
        const [stats, nodesData, factsData, episodesData] = await Promise.all([
            API.stats(this.state.groupId),
            API.nodes({ groupId: this.state.groupId, limit: 5 }),
            API.facts({ groupId: this.state.groupId, limit: 5 }),
            API.episodes({ groupId: this.state.groupId, limit: 5 }),
        ]);

        app.innerHTML = Components.renderDashboard(
            stats,
            nodesData.nodes || [],
            factsData.facts || [],
            episodesData.episodes || [],
        );
    },

    async _renderNodes(app) {
        let data;
        if (this.state.searchMode === 'vector' && this.state.searchValue) {
            data = await API.searchNodes(this.state.searchValue, {
                groupIds: this.state.groupId ? [this.state.groupId] : [],
                limit: 20,
            });
            data.page = 1;
            data.pages = 1;
        } else {
            data = await API.nodes({
                groupId: this.state.groupId,
                page: this.state.currentPage,
                search: this.state.searchValue,
            });
        }
        app.innerHTML = Components.renderNodesPage(data, this.state.searchValue, this.state.searchMode);
    },

    async _renderFacts(app) {
        let data;
        if (this.state.searchMode === 'vector' && this.state.searchValue) {
            data = await API.searchFacts(this.state.searchValue, {
                groupIds: this.state.groupId ? [this.state.groupId] : [],
                limit: 20,
            });
            data.page = 1;
            data.pages = 1;
        } else {
            data = await API.facts({
                groupId: this.state.groupId,
                page: this.state.currentPage,
                search: this.state.searchValue,
            });
        }
        app.innerHTML = Components.renderFactsPage(data, this.state.searchValue, this.state.searchMode);
    },

    async _renderEpisodes(app) {
        const data = await API.episodes({
            groupId: this.state.groupId,
            page: this.state.currentPage,
        });
        app.innerHTML = Components.renderEpisodesPage(data);
    },

    // ============================================================
    // 資料載入
    // ============================================================

    async _loadGroups() {
        try {
            const data = await API.groups();
            const select = document.getElementById('group-filter');
            const groups = data.groups || [];
            // 保留第一個 "全部" option
            select.innerHTML = '<option value="">全部群組</option>' +
                groups.map(g => `<option value="${g}">${g}</option>`).join('');
        } catch (err) {
            console.error('Load groups error:', err);
        }
    },

    // ============================================================
    // 使用者操作
    // ============================================================

    doSearch() {
        const input = document.getElementById('search-input');
        if (!input) return;
        this.state.searchValue = input.value.trim();
        this.state.currentPage = 1;
        this._renderCurrentPage();
    },

    setSearchMode(mode) {
        this.state.searchMode = mode;
        this.state.currentPage = 1;
        this._renderCurrentPage();
    },

    goPage(page) {
        this.state.currentPage = page;
        this._renderCurrentPage();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    async deleteEpisode(uuid) {
        const ok = await this._confirm(`確定要刪除此記憶片段？\n\nUUID: ${uuid}`);
        if (!ok) return;
        try {
            await API.deleteEpisode(uuid);
            this._toast('記憶片段已刪除', 'success');
            this._renderCurrentPage();
            this._loadGroups();
        } catch (err) {
            this._toast(`刪除失敗: ${err.message}`, 'error');
        }
    },

    async deleteFact(uuid) {
        const ok = await this._confirm(`確定要刪除此事實？\n\nUUID: ${uuid}`);
        if (!ok) return;
        try {
            await API.deleteFact(uuid);
            this._toast('事實已刪除', 'success');
            this._renderCurrentPage();
            this._loadGroups();
        } catch (err) {
            this._toast(`刪除失敗: ${err.message}`, 'error');
        }
    },

    copyText(text) {
        navigator.clipboard.writeText(text).then(() => {
            this._toast('已複製 UUID', 'info');
        }).catch(() => {
            this._toast('複製失敗', 'error');
        });
    },

    async exportJSON() {
        try {
            this._toast('正在匯出資料...', 'info');
            const data = await API.exportData({ groupId: this.state.groupId });
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `graphiti-export-${new Date().toISOString().slice(0, 10)}.json`;
            a.click();
            URL.revokeObjectURL(url);
            this._toast('匯出完成', 'success');
        } catch (err) {
            this._toast(`匯出失敗: ${err.message}`, 'error');
        }
    },

    toggleDetail(uuid) {
        const el = document.getElementById(`detail-${uuid}`);
        if (el) el.classList.toggle('hidden');
    },

    // ============================================================
    // UI 工具
    // ============================================================

    _confirm(message) {
        return new Promise(resolve => {
            this._confirmResolve = resolve;
            document.getElementById('confirm-message').textContent = message;
            document.getElementById('confirm-dialog').showModal();
        });
    },

    _toast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    },
};

// 啟動
document.addEventListener('DOMContentLoaded', () => App.init());
