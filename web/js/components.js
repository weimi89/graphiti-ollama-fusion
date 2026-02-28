/**
 * Graphiti Web UI 組件渲染
 */
const Components = {

    // ============================================================
    // 儀表板
    // ============================================================

    renderDashboard(stats, recentNodes, recentFacts, recentEpisodes) {
        return `
            <div class="stats-grid">
                <div class="stat-card nodes">
                    <div class="stat-number">${stats.nodes ?? 0}</div>
                    <div class="stat-label">實體節點</div>
                </div>
                <div class="stat-card facts">
                    <div class="stat-number">${stats.facts ?? 0}</div>
                    <div class="stat-label">事實關係</div>
                </div>
                <div class="stat-card episodes">
                    <div class="stat-number">${stats.episodes ?? 0}</div>
                    <div class="stat-label">記憶片段</div>
                </div>
            </div>
            <div style="text-align:right;margin-bottom:1rem">
                <button class="btn btn-primary" onclick="App.exportJSON()" aria-label="匯出知識圖譜資料為 JSON">匯出 JSON</button>
            </div>

            <div class="dashboard-section">
                <div class="section-title">最近的實體節點</div>
                <div class="card-list">
                    ${recentNodes.length
                        ? recentNodes.map(n => this.renderNodeCard(n)).join('')
                        : this._empty('尚無實體節點')
                    }
                </div>
            </div>

            <div class="dashboard-section">
                <div class="section-title">最近的事實關係</div>
                <div class="card-list">
                    ${recentFacts.length
                        ? recentFacts.map(f => this.renderFactCard(f)).join('')
                        : this._empty('尚無事實關係')
                    }
                </div>
            </div>

            <div class="dashboard-section">
                <div class="section-title">最近的記憶片段</div>
                <div class="card-list">
                    ${recentEpisodes.length
                        ? recentEpisodes.map(e => this.renderEpisodeCard(e)).join('')
                        : this._empty('尚無記憶片段')
                    }
                </div>
            </div>
        `;
    },

    // ============================================================
    // 節點頁面
    // ============================================================

    renderNodesPage(data, searchValue, searchMode) {
        return `
            <div class="page-header">
                <h1 class="page-title">實體節點</h1>
                <div class="search-box">
                    <input type="text" class="search-input" id="search-input"
                           placeholder="${searchMode === 'vector' ? '向量語意搜尋...' : '關鍵字篩選...'}"
                           value="${this._esc(searchValue)}"
                           aria-label="搜尋關鍵字">
                    <button class="btn btn-primary" onclick="App.doSearch()" aria-label="執行搜尋">搜尋</button>
                </div>
            </div>
            <div class="search-mode-tabs" role="tablist" aria-label="搜尋模式">
                <button class="search-mode-tab ${searchMode === 'filter' ? 'active' : ''}"
                        role="tab" aria-selected="${searchMode === 'filter'}"
                        onclick="App.setSearchMode('filter')">篩選</button>
                <button class="search-mode-tab ${searchMode === 'vector' ? 'active' : ''}"
                        role="tab" aria-selected="${searchMode === 'vector'}"
                        onclick="App.setSearchMode('vector')">向量搜尋</button>
            </div>
            <div class="card-list">
                ${data.nodes && data.nodes.length
                    ? data.nodes.map(n => this.renderNodeCard(n)).join('')
                    : this._empty('沒有找到實體節點')
                }
            </div>
            ${data.pages > 1 ? this.renderPagination(data.page, data.pages, data.total) : ''}
        `;
    },

    renderNodeCard(node) {
        const labels = (node.labels || []).filter(l => l !== 'Entity' && l !== '__Entity__');
        return `
            <div class="card card-entity">
                <div class="card-header">
                    <div class="card-title" style="cursor:pointer" onclick="App.toggleDetail('${this._safeUuid(node.uuid)}')">${this._esc(node.name || '(unnamed)')}</div>
                    <span class="card-tag entity">Entity${labels.length ? ' / ' + labels.join(', ') : ''}</span>
                </div>
                ${node.summary ? `<div class="card-body">${this._esc(node.summary)}</div>` : ''}
                <div id="detail-${this._safeUuid(node.uuid)}" class="card-detail hidden">
                    <div class="card-body" style="opacity:0.7;font-size:0.85em">
                        <strong>UUID:</strong> ${node.uuid}<br>
                        <strong>Group:</strong> ${this._esc(node.group_id)}<br>
                        <strong>Labels:</strong> ${(node.labels || []).join(', ')}<br>
                        <strong>Created:</strong> ${this._time(node.created_at)}
                    </div>
                </div>
                <div class="card-meta">
                    <span title="Group ID">${this._esc(node.group_id)}</span>
                    <span title="建立時間">${this._time(node.created_at)}</span>
                    <span class="card-actions">
                        <button class="btn-delete" title="UUID" onclick="App.copyText('${this._safeUuid(node.uuid)}')">
                            ${this._shortUuid(node.uuid)}
                        </button>
                        <button class="btn-delete" onclick="App.deleteNode('${this._safeUuid(node.uuid)}')" title="刪除節點">&#10005;</button>
                    </span>
                </div>
            </div>
        `;
    },

    // ============================================================
    // 事實頁面
    // ============================================================

    renderFactsPage(data, searchValue, searchMode) {
        return `
            <div class="page-header">
                <h1 class="page-title">事實關係</h1>
                <div class="search-box">
                    <input type="text" class="search-input" id="search-input"
                           placeholder="${searchMode === 'vector' ? '向量語意搜尋...' : '關鍵字篩選...'}"
                           value="${this._esc(searchValue)}"
                           aria-label="搜尋關鍵字">
                    <button class="btn btn-primary" onclick="App.doSearch()" aria-label="執行搜尋">搜尋</button>
                </div>
            </div>
            <div class="search-mode-tabs" role="tablist" aria-label="搜尋模式">
                <button class="search-mode-tab ${searchMode === 'filter' ? 'active' : ''}"
                        role="tab" aria-selected="${searchMode === 'filter'}"
                        onclick="App.setSearchMode('filter')">篩選</button>
                <button class="search-mode-tab ${searchMode === 'vector' ? 'active' : ''}"
                        role="tab" aria-selected="${searchMode === 'vector'}"
                        onclick="App.setSearchMode('vector')">向量搜尋</button>
            </div>
            <div class="card-list">
                ${data.facts && data.facts.length
                    ? data.facts.map(f => this.renderFactCard(f)).join('')
                    : this._empty('沒有找到事實關係')
                }
            </div>
            ${data.pages > 1 ? this.renderPagination(data.page, data.pages, data.total) : ''}
        `;
    },

    renderFactCard(fact) {
        return `
            <div class="card card-fact">
                <div class="card-header">
                    <div>
                        <div class="fact-relation">
                            <span class="fact-source">${this._esc(fact.source_name || '?')}</span>
                            <span class="fact-arrow">&#8594;</span>
                            <span class="card-title" style="display:inline">${this._esc(fact.name || '')}</span>
                            <span class="fact-arrow">&#8594;</span>
                            <span class="fact-target">${this._esc(fact.target_name || '?')}</span>
                        </div>
                    </div>
                    <span class="card-tag fact">Fact</span>
                </div>
                ${fact.fact ? `<div class="card-body">${this._esc(fact.fact)}</div>` : ''}
                <div class="card-meta">
                    <span title="Group ID">${this._esc(fact.group_id)}</span>
                    <span title="建立時間">${this._time(fact.created_at)}</span>
                    <span class="card-actions">
                        <button class="btn-delete" onclick="App.deleteFact('${this._safeUuid(fact.uuid)}')" title="刪除">&#10005;</button>
                    </span>
                </div>
            </div>
        `;
    },

    // ============================================================
    // 記憶片段頁面
    // ============================================================

    renderEpisodesPage(data, searchValue) {
        return `
            <div class="page-header">
                <h1 class="page-title">記憶片段</h1>
                <div class="search-box">
                    <input type="text" class="search-input" id="search-input"
                           placeholder="關鍵字篩選..."
                           value="${this._esc(searchValue || '')}"
                           aria-label="搜尋關鍵字">
                    <button class="btn btn-primary" onclick="App.doSearch()" aria-label="執行搜尋">搜尋</button>
                </div>
            </div>
            <div class="card-list">
                ${data.episodes && data.episodes.length
                    ? data.episodes.map(e => this.renderEpisodeCard(e)).join('')
                    : this._empty('沒有找到記憶片段')
                }
            </div>
            ${data.pages > 1 ? this.renderPagination(data.page, data.pages, data.total) : ''}
        `;
    },

    renderEpisodeCard(ep) {
        return `
            <div class="card card-episode">
                <div class="card-header">
                    <div class="card-title">${this._esc(ep.name || '(unnamed)')}</div>
                    <span class="card-tag episode">Episode</span>
                </div>
                ${ep.content ? `<div class="card-body">${this._esc(ep.content)}</div>` : ''}
                <div class="card-meta">
                    <span title="Group ID">${this._esc(ep.group_id)}</span>
                    <span title="建立時間">${this._time(ep.created_at)}</span>
                    ${ep.source_description ? `<span>${this._esc(ep.source_description)}</span>` : ''}
                    <span class="card-actions">
                        <button class="btn-delete" onclick="App.deleteEpisode('${this._safeUuid(ep.uuid)}')" title="刪除">&#10005;</button>
                    </span>
                </div>
            </div>
        `;
    },

    // ============================================================
    // 分頁
    // ============================================================

    renderPagination(current, total, totalItems) {
        let buttons = '';

        buttons += `<button ${current <= 1 ? 'disabled' : ''} onclick="App.goPage(${current - 1})" aria-label="上一頁">&#8249;</button>`;

        const start = Math.max(1, current - 2);
        const end = Math.min(total, current + 2);

        if (start > 1) {
            buttons += `<button onclick="App.goPage(1)">1</button>`;
            if (start > 2) buttons += `<span class="pagination-info">...</span>`;
        }

        for (let i = start; i <= end; i++) {
            buttons += `<button class="${i === current ? 'active' : ''}" onclick="App.goPage(${i})">${i}</button>`;
        }

        if (end < total) {
            if (end < total - 1) buttons += `<span class="pagination-info">...</span>`;
            buttons += `<button onclick="App.goPage(${total})">${total}</button>`;
        }

        buttons += `<button ${current >= total ? 'disabled' : ''} onclick="App.goPage(${current + 1})" aria-label="下一頁">&#8250;</button>`;

        return `
            <div class="pagination" role="navigation" aria-label="分頁導航">
                ${buttons}
                <span class="pagination-info" aria-live="polite">共 ${totalItems} 筆</span>
            </div>
        `;
    },

    // ============================================================
    // Helpers
    // ============================================================

    _empty(text) {
        return `
            <div class="empty-state">
                <div class="empty-state-icon">&#9671;</div>
                <div class="empty-state-text">${text}</div>
            </div>
        `;
    },

    _esc(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = String(str);
        return div.innerHTML;
    },

    _time(str) {
        if (!str) return '';
        try {
            const d = new Date(str);
            if (isNaN(d.getTime())) return str;
            return d.toLocaleString('zh-TW', {
                year: 'numeric', month: '2-digit', day: '2-digit',
                hour: '2-digit', minute: '2-digit',
            });
        } catch {
            return str;
        }
    },

    _shortUuid(uuid) {
        if (!uuid) return '';
        return uuid.length > 8 ? uuid.slice(0, 8) + '...' : uuid;
    },

    /** 驗證並清理 UUID（防止 XSS 注入）。只允許 hex 字元和連字符。 */
    _safeUuid(uuid) {
        if (!uuid) return '';
        return String(uuid).replace(/[^a-fA-F0-9\-]/g, '');
    },
};
