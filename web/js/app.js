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
        selectedItems: new Set(),
        batchMode: false,
        timelineDays: 30,
        graphCenterUuid: '',
        selectedGroupIds: [],
    },

    _searchTimer: null,

    // ============================================================
    // 初始化
    // ============================================================

    async init() {
        this._initTheme();
        this._initRouter();
        this._initEvents();
        this._initTripletForm();
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
        // Group 搜尋下拉 — 點擊外部關閉
        document.addEventListener('click', (e) => {
            const wrapper = document.querySelector('.group-filter-wrapper');
            if (wrapper && !wrapper.contains(e.target)) {
                const dd = wrapper.querySelector('.group-dropdown');
                if (dd) dd.classList.remove('open');
            }
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

        // 新增記憶表單
        document.getElementById('add-memory-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('memory-name').value.trim();
            const content = document.getElementById('memory-content').value.trim();
            const groupId = document.getElementById('memory-group').value.trim();
            const source = document.getElementById('memory-source').value;
            if (!name || !content) return;

            const submitBtn = e.target.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = '添加中...';

            try {
                await API.addMemory({ name, content, groupId, source });
                this._toast(`記憶 "${name}" 已成功添加`, 'success');
                this.closeAddMemory();
                this._renderCurrentPage();
                this._loadGroups();
            } catch (err) {
                this._toast(`添加失敗: ${err.message}`, 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '添加';
            }
        });
    },

    // ============================================================
    // 路由
    // ============================================================

    _handleRoute() {
        const hash = location.hash.replace('#', '') || '/';
        const parts = hash.split('/').filter(Boolean);
        const page = parts[0] || 'dashboard';

        // 更新導航高亮與 ARIA
        document.querySelectorAll('.nav-link').forEach(link => {
            const linkPage = link.dataset.page;
            const isActive = linkPage === page || (!linkPage && page === 'dashboard');
            link.classList.toggle('active', isActive);
            if (isActive) {
                link.setAttribute('aria-current', 'page');
            } else {
                link.removeAttribute('aria-current');
            }
        });

        // 頁面切換時重設狀態
        if (this.state.page !== page) {
            this.state.page = page;
            this.state.currentPage = 1;
            this.state.searchValue = '';
            this.state.searchMode = 'filter';
            this.state.batchMode = false;
            this.state.selectedItems.clear();
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
                case 'overview':
                    await this._renderOverview(app);
                    break;
                case 'timeline':
                    await this._renderTimeline(app);
                    break;
                case 'graph':
                    await this._renderGraph(app);
                    break;
                case 'ask':
                    await this._renderAsk(app);
                    break;
                case 'communities':
                    await this._renderCommunities(app);
                    break;
                default:
                    app.innerHTML = '<div class="empty-state"><div class="empty-state-text">頁面不存在</div></div>';
            }
        } catch (err) {
            console.error('Render error:', err);
            app.innerHTML = `<div class="empty-state">
                <div class="empty-state-text">載入失敗: ${Components._esc(err.message)}</div>
                <button class="btn btn-primary" onclick="App._renderCurrentPage()" style="margin-top:1rem">重試</button>
            </div>`;
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
        let searchMeta = null;
        if (this.state.searchMode === 'vector' && this.state.searchValue) {
            data = await API.searchNodes(this.state.searchValue, {
                groupIds: this.state.groupId ? [this.state.groupId] : [],
                limit: 20,
            });
            searchMeta = { duration: data.duration };
            data.page = 1;
            data.pages = 1;
        } else {
            data = await API.nodes({
                groupId: this.state.groupId,
                page: this.state.currentPage,
                search: this.state.searchValue,
            });
            if (data.duration != null) searchMeta = { duration: data.duration };
        }
        app.innerHTML = Components.renderNodesPage(data, this.state.searchValue, this.state.searchMode, searchMeta);
    },

    async _renderFacts(app) {
        let data;
        let searchMeta = null;
        if (this.state.searchMode === 'vector' && this.state.searchValue) {
            data = await API.searchFacts(this.state.searchValue, {
                groupIds: this.state.groupId ? [this.state.groupId] : [],
                limit: 20,
            });
            searchMeta = { duration: data.duration };
            data.page = 1;
            data.pages = 1;
        } else {
            data = await API.facts({
                groupId: this.state.groupId,
                page: this.state.currentPage,
                search: this.state.searchValue,
            });
            if (data.duration != null) searchMeta = { duration: data.duration };
        }
        app.innerHTML = Components.renderFactsPage(data, this.state.searchValue, this.state.searchMode, searchMeta);
    },

    async _renderEpisodes(app) {
        let data;
        let searchMeta = null;
        if (this.state.searchMode === 'vector' && this.state.searchValue) {
            data = await API.searchEpisodes(this.state.searchValue, {
                groupIds: this.state.groupId ? [this.state.groupId] : [],
                limit: 20,
            });
            searchMeta = { duration: data.duration };
            data.page = 1;
            data.pages = 1;
        } else {
            data = await API.episodes({
                groupId: this.state.groupId,
                page: this.state.currentPage,
                search: this.state.searchValue,
            });
            if (data.duration != null) searchMeta = { duration: data.duration };
        }
        app.innerHTML = Components.renderEpisodesPage(data, this.state.searchValue, this.state.searchMode, searchMeta);
    },

    // ============================================================
    // 新頁面渲染
    // ============================================================

    async _renderOverview(app) {
        const [groupsData, quality, topNodes] = await Promise.all([
            API.groupsStats(),
            API.quality({ groupId: this.state.groupId }),
            API.topNodes({ groupId: this.state.groupId, limit: 10 }),
        ]);
        app.innerHTML = Components.renderOverviewPage(groupsData, quality, topNodes);
    },

    async _renderTimeline(app) {
        const data = await API.timeline({
            groupId: this.state.groupId,
            days: this.state.timelineDays,
        });
        app.innerHTML = Components.renderTimelinePage(data, this.state.timelineDays);
    },

    async _renderGraph(app) {
        app.innerHTML = Components.renderGraphPage(null, this.state.graphCenterUuid);
        if (this.state.graphCenterUuid) {
            await this._loadGraph(this.state.graphCenterUuid);
        } else {
            // Auto-load top node
            try {
                const topData = await API.topNodes({ groupId: this.state.groupId, limit: 1 });
                if (topData.nodes && topData.nodes.length) {
                    this.state.graphCenterUuid = topData.nodes[0].uuid;
                    await this._loadGraph(topData.nodes[0].uuid);
                }
            } catch (e) { /* ignore */ }
        }
    },

    async _loadGraph(uuid) {
        const container = document.getElementById('graph-container');
        if (!container) return;
        container.innerHTML = '<div class="loading-spinner">載入圖譜...</div>';
        try {
            const data = await API.subgraph({ uuid, depth: 2, limit: 50 });
            Components.renderD3Graph(container, data, uuid);
        } catch (err) {
            container.innerHTML = `<div class="empty-state"><div class="empty-state-text">載入失敗: ${Components._esc(err.message)}</div></div>`;
        }
    },

    async _renderAsk(app) {
        app.innerHTML = Components.renderAskPage(null);
    },

    // ============================================================
    // 新頁面操作
    // ============================================================

    setTimelineDays(days) {
        this.state.timelineDays = days;
        this._renderCurrentPage();
    },

    async searchGraph() {
        const input = document.getElementById('graph-search-input');
        if (!input || !input.value.trim()) return;
        const q = input.value.trim();
        // 先搜尋節點找到 UUID
        try {
            const data = await API.searchNodes(q, {
                groupIds: this.state.groupId ? [this.state.groupId] : [],
                limit: 1,
            });
            if (data.nodes && data.nodes.length) {
                this.state.graphCenterUuid = data.nodes[0].uuid;
                await this._loadGraph(data.nodes[0].uuid);
            } else {
                this._toast('未找到匹配的節點', 'info');
            }
        } catch (err) {
            this._toast(`搜尋失敗: ${err.message}`, 'error');
        }
    },

    viewInGraph(uuid) {
        this.state.graphCenterUuid = uuid;
        location.hash = '#/graph';
    },

    async expandGraphNode(uuid) {
        this.state.graphCenterUuid = uuid;
        await this._loadGraph(uuid);
    },

    async doAsk() {
        const input = document.getElementById('ask-input');
        if (!input || !input.value.trim()) return;
        const q = input.value.trim();
        const resultEl = document.getElementById('ask-result');
        if (resultEl) resultEl.innerHTML = '<div class="loading-spinner">搜尋中...</div>';
        try {
            const data = await API.ask({
                q,
                groupIds: this.state.groupId ? [this.state.groupId] : [],
            });
            if (resultEl) resultEl.innerHTML = Components.renderAskResult(data);
        } catch (err) {
            if (resultEl) resultEl.innerHTML = `<div class="empty-state"><div class="empty-state-text">搜尋失敗: ${Components._esc(err.message)}</div></div>`;
        }
    },

    copyContext() {
        const el = document.getElementById('ask-context-text');
        if (!el) return;
        navigator.clipboard.writeText(el.textContent).then(() => {
            this._toast('已複製上下文', 'info');
        }).catch(() => {
            this._toast('複製失敗', 'error');
        });
    },

    // ============================================================
    // 快速範本
    // ============================================================

    applyTemplate() {
        const TEMPLATES = {
            decision: { name: '專案決策：', content: '決策內容：\n原因：\n影響範圍：\n決策日期：' },
            preference: { name: '技術偏好：', content: '偏好設定：\n原因：\n適用範圍：' },
            person: { name: '人員角色：', content: '姓名：\n角色：\n負責範圍：\n聯繫方式：' },
            process: { name: '流程步驟：', content: '步驟 1：\n步驟 2：\n步驟 3：\n注意事項：' },
            bug: { name: 'Bug：', content: '問題描述：\n重現步驟：\n預期行為：\n實際行為：\n解決方案：' },
        };
        const sel = document.getElementById('memory-template');
        if (!sel) return;
        const tpl = TEMPLATES[sel.value];
        if (tpl) {
            document.getElementById('memory-name').value = tpl.name;
            document.getElementById('memory-content').value = tpl.content;
        }
    },

    // ============================================================
    // 頁面說明關閉
    // ============================================================

    dismissDescription(page) {
        const key = `graphiti-desc-${page}`;
        localStorage.setItem(key, '1');
        const el = document.getElementById(`page-desc-${page}`);
        if (el) el.remove();
    },

    showDescription(page) {
        localStorage.removeItem(`graphiti-desc-${page}`);
        this._renderCurrentPage();
    },

    // ============================================================
    // 資料載入
    // ============================================================

    _groupList: [],

    async _loadGroups() {
        try {
            const data = await API.groups();
            this._groupList = data.groups || [];
            this._renderGroupFilter();
        } catch (err) {
            console.error('Load groups error:', err);
        }
    },

    _renderGroupFilter() {
        const container = document.getElementById('group-filter-container');
        if (!container) return;
        const groups = this._groupList;
        container.innerHTML = `
            <div class="group-filter-wrapper">
                <input type="text" class="group-search-input" id="group-search-input"
                       placeholder="搜尋群組..." value="${this.state.groupId || '全部群組'}"
                       onfocus="this.select(); App.toggleGroupDropdown()"
                       oninput="App.filterGroups()">
                <div class="group-dropdown">
                    <div class="group-dropdown-item${!this.state.groupId ? ' selected' : ''}"
                         onclick="App.selectGroup('')">全部群組</div>
                    ${groups.map(g => `<div class="group-dropdown-item${this.state.groupId === g ? ' selected' : ''}"
                         onclick="App.selectGroup('${g}')">${g}</div>`).join('')}
                    <div class="group-dropdown-empty" style="display:none">無匹配群組</div>
                </div>
            </div>
        `;
    },

    // ============================================================
    // 使用者操作
    // ============================================================

    toggleGroupDropdown() {
        const dd = document.querySelector('.group-dropdown');
        if (dd) dd.classList.toggle('open');
        const input = document.getElementById('group-search-input');
        if (input) input.focus();
    },

    filterGroups() {
        const input = document.getElementById('group-search-input');
        const dd = document.querySelector('.group-dropdown');
        if (!input || !dd) return;
        const q = input.value.toLowerCase();
        dd.classList.add('open');
        const items = dd.querySelectorAll('.group-dropdown-item');
        let visible = 0;
        items.forEach(item => {
            const match = item.textContent.toLowerCase().includes(q);
            item.style.display = match ? '' : 'none';
            if (match) visible++;
        });
        const empty = dd.querySelector('.group-dropdown-empty');
        if (empty) empty.style.display = visible === 0 ? '' : 'none';
    },

    selectGroup(groupId) {
        this.state.groupId = groupId;
        this.state.currentPage = 1;
        const input = document.getElementById('group-search-input');
        if (input) input.value = groupId || '全部群組';
        const dd = document.querySelector('.group-dropdown');
        if (dd) dd.classList.remove('open');
        // Show/hide delete button
        const deleteBtn = document.getElementById('delete-group-btn');
        if (deleteBtn) deleteBtn.style.display = groupId ? '' : 'none';
        this._renderCurrentPage();
    },

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

    jumpToPage(event) {
        if (event.key !== 'Enter') return;
        const page = parseInt(event.target.value);
        if (!isNaN(page) && page >= 1) {
            this.goPage(page);
        }
    },

    async deleteNode(uuid) {
        const ok = await this._confirm(`確定要刪除此實體節點？\n\nUUID: ${uuid}\n\n注意：相關的邊也會被一併刪除。`);
        if (!ok) return;
        try {
            await API.deleteNode(uuid);
            this._toast('實體節點已刪除', 'success');
            this._renderCurrentPage();
            this._loadGroups();
        } catch (err) {
            this._toast(`刪除失敗: ${err.message}`, 'error');
        }
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

    async deleteGroup() {
        if (!this.state.groupId) return;
        const ok = await this._confirm(`確定要刪除整個群組 "${this.state.groupId}" 嗎？\n\n此操作會清除該群組下的所有實體、事實和記憶片段。`);
        if (!ok) return;
        try {
            await API.deleteGroup(this.state.groupId);
            this._toast(`群組 ${this.state.groupId} 已清除`, 'success');
            this.state.groupId = '';
            const input = document.getElementById('group-search-input');
            if (input) input.value = '全部群組';
            const deleteBtn = document.getElementById('delete-group-btn');
            if (deleteBtn) deleteBtn.style.display = 'none';
            await this._loadGroups();
            this._renderCurrentPage();
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

    // ============================================================
    // 節點關係探索
    // ============================================================

    async loadNodeRelations(uuid) {
        const container = document.getElementById(`relations-${uuid}`);
        if (!container || container.dataset.loaded === 'true') return;
        container.innerHTML = '<div class="loading-spinner" style="font-size:12px;padding:8px 0">載入關係...</div>';
        try {
            const data = await API.nodeRelations(uuid);
            container.dataset.loaded = 'true';
            if (!data.relations.length) {
                container.innerHTML = '<div style="color:var(--text-muted);font-size:12px;padding:4px 0">無相關事實</div>';
                return;
            }
            container.innerHTML = data.relations.map(r => `
                <div class="relation-item">
                    <span class="relation-entities">${Components._esc(r.source_name)} → ${Components._esc(r.target_name)}</span>
                    <span class="relation-fact">${Components._esc(r.fact)}</span>
                </div>
            `).join('');
        } catch (err) {
            container.innerHTML = '<div style="color:var(--danger);font-size:12px">載入失敗</div>';
        }
    },

    // ============================================================
    // 新增記憶
    // ============================================================

    openAddMemory() {
        const dialog = document.getElementById('add-memory-dialog');
        const groupInput = document.getElementById('memory-group');
        if (groupInput && this.state.groupId) groupInput.value = this.state.groupId;
        dialog.showModal();
    },

    closeAddMemory() {
        document.getElementById('add-memory-dialog').close();
        document.getElementById('add-memory-form').reset();
    },

    // ============================================================
    // 批次選取刪除
    // ============================================================

    toggleBatchMode() {
        this.state.batchMode = !this.state.batchMode;
        this.state.selectedItems.clear();
        this._renderCurrentPage();
    },

    toggleSelectItem(uuid) {
        if (this.state.selectedItems.has(uuid)) {
            this.state.selectedItems.delete(uuid);
        } else {
            this.state.selectedItems.add(uuid);
        }
        // 更新 batch bar 計數
        const bar = document.querySelector('.batch-bar');
        if (bar) {
            bar.querySelector('span').textContent = `已選取 ${this.state.selectedItems.size} 個`;
            const deleteBtn = bar.querySelector('.btn-danger');
            if (deleteBtn) deleteBtn.disabled = this.state.selectedItems.size === 0;
        }
    },

    selectAll() {
        document.querySelectorAll('.batch-checkbox').forEach(cb => {
            const uuid = cb.getAttribute('onchange')?.match(/'([^']+)'/)?.[1];
            if (uuid) {
                this.state.selectedItems.add(uuid);
                cb.checked = true;
            }
        });
        const bar = document.querySelector('.batch-bar');
        if (bar) {
            bar.querySelector('span').textContent = `已選取 ${this.state.selectedItems.size} 個`;
            const deleteBtn = bar.querySelector('.btn-danger');
            if (deleteBtn) deleteBtn.disabled = false;
        }
    },

    deselectAll() {
        this.state.selectedItems.clear();
        document.querySelectorAll('.batch-checkbox').forEach(cb => { cb.checked = false; });
        const bar = document.querySelector('.batch-bar');
        if (bar) {
            bar.querySelector('span').textContent = '已選取 0 個';
            const deleteBtn = bar.querySelector('.btn-danger');
            if (deleteBtn) deleteBtn.disabled = true;
        }
    },

    async batchDelete() {
        const count = this.state.selectedItems.size;
        if (!count) return;
        const ok = await this._confirm(`確定要刪除選中的 ${count} 個項目？`);
        if (!ok) return;

        const page = this.state.page;
        const deleteFn = page === 'nodes' ? API.deleteNode.bind(API)
            : page === 'facts' ? API.deleteFact.bind(API)
            : API.deleteEpisode.bind(API);

        this._toast(`正在刪除 ${count} 個項目...`, 'info');

        const results = await Promise.allSettled(
            [...this.state.selectedItems].map(uuid => deleteFn(uuid))
        );

        const success = results.filter(r => r.status === 'fulfilled').length;
        const failed = results.filter(r => r.status === 'rejected').length;
        this._toast(
            `已刪除 ${success} 個` + (failed ? `，失敗 ${failed} 個` : ''),
            failed ? 'error' : 'success'
        );

        this.state.selectedItems.clear();
        this.state.batchMode = false;
        this._renderCurrentPage();
        this._loadGroups();
    },

    toggleDetail(uuid) {
        const el = document.getElementById(`detail-${uuid}`);
        if (el) el.classList.toggle('hidden');
    },

    toggleContent(id) {
        const shortEl = document.getElementById(`${id}-short`);
        const fullEl = document.getElementById(`${id}-full`);
        const btn = document.querySelector(`[onclick="App.toggleContent('${id}')"]`);
        if (!shortEl || !fullEl || !btn) return;

        const isCollapsed = btn.dataset.state === 'collapsed';
        if (isCollapsed) {
            shortEl.classList.add('hidden');
            fullEl.classList.add('visible');
            btn.textContent = '收合';
            btn.dataset.state = 'expanded';
        } else {
            shortEl.classList.remove('hidden');
            fullEl.classList.remove('visible');
            btn.textContent = '展開';
            btn.dataset.state = 'collapsed';
        }
    },

    // ============================================================
    // UI 工具
    // ============================================================

    toggleMenu() {
        const links = document.querySelector('.navbar-links');
        if (links) links.classList.toggle('open');
    },

    _confirm(message) {
        return new Promise(resolve => {
            this._confirmResolve = resolve;
            document.getElementById('confirm-message').textContent = message;
            document.getElementById('confirm-dialog').showModal();
        });
    },

    // ============================================================
    // 社群頁面
    // ============================================================

    async _renderCommunities(app) {
        const data = await API.communities({
            groupId: this.state.groupId,
            page: this.state.currentPage,
        });
        app.innerHTML = Components.renderCommunitiesPage(data, this.state.currentPage);
    },

    async goToCommunities(page) {
        this.state.currentPage = page;
        await this._renderCommunities(document.getElementById('app'));
    },

    async buildCommunities() {
        try {
            this._toast('正在建構社群...', 'info');
            const result = await API.buildCommunities({
                groupIds: this.state.groupId ? [this.state.groupId] : null,
            });
            this._toast(result.message || '社群建構完成', 'success');
            await this._renderCommunities(document.getElementById('app'));
        } catch (err) {
            this._toast('社群建構失敗: ' + err.message, 'error');
        }
    },

    // ============================================================
    // 三元組 Dialog
    // ============================================================

    openTripletDialog() {
        const dialog = document.getElementById('add-triplet-dialog');
        if (dialog) {
            document.getElementById('add-triplet-form').reset();
            const groupInput = document.getElementById('triplet-group');
            if (groupInput && this.state.groupId) groupInput.value = this.state.groupId;
            dialog.showModal();
        }
    },

    closeTripletDialog() {
        const dialog = document.getElementById('add-triplet-dialog');
        if (dialog) dialog.close();
    },

    _initTripletForm() {
        const form = document.getElementById('add-triplet-form');
        if (!form) return;
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const result = await API.addTriplet({
                    sourceName: document.getElementById('triplet-source').value.trim(),
                    relationName: document.getElementById('triplet-relation').value.trim(),
                    targetName: document.getElementById('triplet-target').value.trim(),
                    fact: document.getElementById('triplet-fact').value.trim(),
                    groupId: document.getElementById('triplet-group').value.trim() || 'default',
                });
                this._toast(result.message || '三元組已添加', 'success');
                this.closeTripletDialog();
                this._renderCurrentPage();
            } catch (err) {
                this._toast('添加三元組失敗: ' + err.message, 'error');
            }
        });
    },

    _toast(message, type = 'info') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        // Error messages show longer
        const duration = type === 'error' ? 6000 : 3000;
        toast.style.animationDuration = `0.3s, 0.3s`;
        toast.style.animationDelay = `0s, ${duration / 1000 - 0.3}s`;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), duration);
    },
};

// 啟動
document.addEventListener('DOMContentLoaded', () => App.init());
