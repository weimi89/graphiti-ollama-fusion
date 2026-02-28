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
        const safeId = this._safeUuid(node.uuid);
        const cleanedSummary = this._cleanSummary(node.summary);
        return `
            <div class="card card-entity">
                <div class="card-tags">
                    <span class="card-tag entity">Entity</span>
                    ${labels.map(l => `<span class="card-tag entity-label">${this._esc(l)}</span>`).join('')}
                    <span class="card-tags-right">
                        <span class="card-tag group">${this._esc(node.group_id)}</span>
                    </span>
                </div>
                <div class="card-title-row" onclick="App.toggleDetail('${safeId}')">
                    ${this._esc(node.name || '(unnamed)')}
                </div>
                ${cleanedSummary ? `<div class="card-body">${this._esc(cleanedSummary)}</div>` : ''}
                <div id="detail-${safeId}" class="card-detail hidden">
                    <div class="card-detail-content">
                        <div class="detail-row">
                            <span class="detail-label">UUID</span>
                            <span class="detail-value">${node.uuid}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Group</span>
                            <span class="detail-value">${this._esc(node.group_id)}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Labels</span>
                            <span class="detail-value">${(node.labels || []).join(', ')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Created</span>
                            <span class="detail-value">${this._time(node.created_at)}</span>
                        </div>
                        ${node.summary ? `<div class="detail-raw">${this._esc(node.summary)}</div>` : ''}
                    </div>
                </div>
                <div class="card-footer">
                    <button class="btn-uuid" title="點擊複製 UUID" onclick="App.copyText('${safeId}')">
                        ${this._shortUuid(node.uuid)}
                    </button>
                    <span title="建立時間">${this._time(node.created_at)}</span>
                    <span class="card-actions">
                        <button class="btn-delete" onclick="App.deleteNode('${safeId}')" title="刪除節點">&#10005;</button>
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
        const safeId = this._safeUuid(fact.uuid);
        return `
            <div class="card card-fact">
                <div class="card-tags">
                    <span class="card-tag fact">Fact</span>
                    ${fact.name ? `<span class="card-tag fact-type">${this._esc(fact.name)}</span>` : ''}
                    <span class="card-tags-right">
                        <span class="card-tag group">${this._esc(fact.group_id)}</span>
                    </span>
                </div>
                ${fact.fact ? `<div class="card-body-primary">${this._esc(fact.fact)}</div>` : ''}
                <div class="fact-entities">
                    <span class="fact-source">${this._esc(fact.source_name || '?')}</span>
                    <span class="fact-arrow">&#8594;</span>
                    <span class="fact-target">${this._esc(fact.target_name || '?')}</span>
                </div>
                <div class="card-footer">
                    <button class="btn-uuid" title="點擊複製 UUID" onclick="App.copyText('${safeId}')">
                        ${this._shortUuid(fact.uuid)}
                    </button>
                    <span title="建立時間">${this._time(fact.created_at)}</span>
                    <span class="card-actions">
                        <button class="btn-delete" onclick="App.deleteFact('${safeId}')" title="刪除">&#10005;</button>
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
        const safeId = this._safeUuid(ep.uuid);
        const contentId = `ep-content-${safeId}`;
        return `
            <div class="card card-episode">
                <div class="card-tags">
                    <span class="card-tag episode">Episode</span>
                    ${ep.source_description ? `<span class="card-tag source-desc">${this._esc(ep.source_description)}</span>` : ''}
                    <span class="card-tags-right">
                        <span class="card-tag group">${this._esc(ep.group_id)}</span>
                    </span>
                </div>
                <div class="card-title-row" onclick="App.toggleDetail('${safeId}')">
                    ${this._esc(ep.name || '(unnamed)')}
                </div>
                ${ep.content ? this._contentPreview(ep.content, contentId, 200) : ''}
                <div id="detail-${safeId}" class="card-detail hidden">
                    <div class="card-detail-content">
                        <div class="detail-row">
                            <span class="detail-label">UUID</span>
                            <span class="detail-value">${ep.uuid}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-label">Group</span>
                            <span class="detail-value">${this._esc(ep.group_id)}</span>
                        </div>
                        ${ep.source_description ? `<div class="detail-row">
                            <span class="detail-label">Source</span>
                            <span class="detail-value">${this._esc(ep.source_description)}</span>
                        </div>` : ''}
                        <div class="detail-row">
                            <span class="detail-label">Created</span>
                            <span class="detail-value">${this._time(ep.created_at)}</span>
                        </div>
                    </div>
                </div>
                <div class="card-footer">
                    <button class="btn-uuid" title="點擊複製 UUID" onclick="App.copyText('${safeId}')">
                        ${this._shortUuid(ep.uuid)}
                    </button>
                    <span title="建立時間">${this._time(ep.created_at)}</span>
                    <span class="card-actions">
                        <button class="btn-delete" onclick="App.deleteEpisode('${safeId}')" title="刪除">&#10005;</button>
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
        return uuid.length > 7 ? uuid.slice(0, 7) + '…' : uuid;
    },

    /** 驗證並清理 UUID（防止 XSS 注入）。只允許 hex 字元和連字符。 */
    _safeUuid(uuid) {
        if (!uuid) return '';
        return String(uuid).replace(/[^a-fA-F0-9\-]/g, '');
    },

    /** 截斷長文字 */
    _truncate(str, maxLen = 150) {
        if (!str) return '';
        const s = String(str);
        if (s.length <= maxLen) return s;
        return s.slice(0, maxLen) + '…';
    },

    /** 清理 summary：偵測 Python dict / JSON 格式並提取有意義文字 */
    _cleanSummary(raw) {
        if (!raw) return '';
        const s = String(raw).trim();

        // 偵測是否為 dict/JSON 類格式（以 { 開頭，包含引號和冒號）
        const looksLikeDict = s.startsWith('{') && /['"].*['"]?\s*:/.test(s);

        if (looksLikeDict) {
            // 先嘗試正則提取有意義欄位（即使字串被截斷也能工作）
            const allNames = [];
            const re = /['"](?:name|summary|description|title|text)['"]\s*:\s*['"]([^'"]+)['"]/gi;
            let m;
            while ((m = re.exec(s)) !== null) {
                const val = m[1].trim();
                if (val.length > 2 && !/^[\d.]+$/.test(val)) {
                    allNames.push(val);
                }
            }
            if (allNames.length) {
                // 去重並組合
                const unique = [...new Set(allNames)];
                return this._truncate(unique.join(' · '), 150);
            }

            // 正則提取所有有意義的字串值（非 key 名稱）
            const strVals = [];
            const strRe = /['"]([^'"]{4,})['"]/g;
            while ((m = strRe.exec(s)) !== null) {
                const val = m[1].trim();
                // 過濾掉看起來像 key 名稱的值
                if (!/^(entity\d*|type|name|observations|summary|description|title|text|uuid|group_id|labels|created_at)$/i.test(val)) {
                    strVals.push(val);
                }
            }
            if (strVals.length) {
                const unique = [...new Set(strVals)];
                return this._truncate(unique.slice(0, 5).join(' · '), 150);
            }

            // 嘗試完整解析（如果字串完整）
            if (s.endsWith('}') || s.endsWith(']')) {
                try {
                    const jsonStr = s
                        .replace(/'/g, '"')
                        .replace(/True/g, 'true')
                        .replace(/False/g, 'false')
                        .replace(/None/g, 'null');
                    const obj = JSON.parse(jsonStr);
                    const extracted = this._extractFromParsed(obj);
                    if (extracted) return this._truncate(extracted, 150);
                } catch {
                    // 解析失敗
                }
            }

            // Dict 格式但無法提取，返回空讓展開區顯示原始資料
            return '';
        }

        // 嘗試解析為 JSON
        if (s.startsWith('[')) {
            try {
                const obj = JSON.parse(s);
                const extracted = this._extractFromParsed(obj);
                if (extracted) return this._truncate(extracted, 150);
            } catch {
                // 非有效 JSON
            }
        }

        // 純文字直接截斷
        return this._truncate(s, 150);
    },

    /** 從已解析的物件遞迴提取有意義欄位（name, summary, description） */
    _extractFromParsed(obj) {
        if (!obj || typeof obj !== 'object') return '';

        // 優先欄位名稱
        const priorityKeys = ['summary', 'description', 'name', 'title', 'content', 'text'];

        // 直接在頂層查找
        for (const key of priorityKeys) {
            if (obj[key] && typeof obj[key] === 'string') {
                return obj[key];
            }
        }

        // 遞迴查找第一層子物件
        for (const val of Object.values(obj)) {
            if (val && typeof val === 'object' && !Array.isArray(val)) {
                for (const key of priorityKeys) {
                    if (val[key] && typeof val[key] === 'string') {
                        return val[key];
                    }
                }
            }
        }

        // 收集所有字串值
        const strings = [];
        for (const val of Object.values(obj)) {
            if (typeof val === 'string' && val.length > 3) {
                strings.push(val);
            }
        }
        return strings.join(' · ') || '';
    },

    /** 帶展開/收合的內容預覽 */
    _contentPreview(content, id, maxLen = 200) {
        if (!content) return '';
        const s = String(content);
        if (s.length <= maxLen) {
            return `<div class="content-preview">${this._esc(s)}</div>`;
        }
        const short = s.slice(0, maxLen) + '…';
        return `
            <div class="content-preview">
                <span id="${id}-short" class="content-short">${this._esc(short)}</span>
                <span id="${id}-full" class="content-full">${this._esc(s)}</span>
                <button class="btn-expand" onclick="App.toggleContent('${id}')" data-state="collapsed">展開</button>
            </div>
        `;
    },
};
