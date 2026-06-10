/**
 * Graphiti Web UI 組件渲染
 */
const Components = {

    // ============================================================
    // 頁面說明常數
    // ============================================================

    PAGE_DESCRIPTIONS: {
        dashboard: '儀表板顯示知識圖譜的總體統計和最近活動，快速掌握記憶庫的現況。',
        nodes: '實體節點是知識圖譜中的核心概念，如人物、專案、技術等。支援關鍵字篩選和向量語意搜尋。',
        facts: '事實關係描述實體之間的連結，如「使用」「負責」「依賴」。這是 AI 理解上下文的關鍵。',
        episodes: '記憶片段是原始的輸入資料，AI 從中提取實體和事實。可以全文搜尋。',
        overview: '知識總覽提供各群組的健康度指標、品質分析和影響力排行，幫助你了解知識庫的完整度。',
        timeline: '時間線顯示知識圖譜隨時間的成長趨勢，了解 AI 何時學到了什麼。',
        graph: '知識圖譜視覺化以互動式力導向圖呈現實體和關係，直觀探索知識結構。',
        ask: '知識問答讓你測試 AI 對特定問題能取得哪些上下文，驗證知識庫的覆蓋度。',
        communities: '社群頁面顯示知識圖譜中自動檢測到的社群聚類，了解實體之間的緊密關聯群組。',
        tasks: '背景任務頁面列出所有 add_memory / add_episode_bulk / build_communities 的非同步處理進度，重啟後仍可查詢歷史狀態。',
        quality: '品質維護頁面整合過時記憶分析、清理操作和知識品質指標，幫助保持知識圖譜的健康度。',
        import: '匯入頁面支援將 JSON 格式的記憶片段批量導入知識圖譜，可貼上 JSON 或上傳檔案。',
        config: '設定頁面允許在不重啟的情況下調整部分運行參數（本次進程生效）。',
    },

    renderPageDescription(page) {
        const desc = this.PAGE_DESCRIPTIONS[page];
        if (!desc) return '';
        if (localStorage.getItem(`graphiti-desc-${page}`) === '1') {
            return `<button class="page-help-btn" onclick="App.showDescription('${page}')" title="${desc}">? 說明</button>`;
        }
        return `
            <div class="page-description" id="page-desc-${page}">
                <span class="page-description-text">${desc}</span>
                <button class="page-description-close" onclick="App.dismissDescription('${page}')" title="關閉說明">&#10005;</button>
            </div>
        `;
    },

    // ============================================================
    // 儀表板
    // ============================================================

    renderDashboard(stats, recentNodes, recentFacts, recentEpisodes) {
        return `
            ${this.renderPageDescription('dashboard')}
            <div class="stats-grid">
                <div class="stat-card nodes" onclick="location.hash='#/nodes'" title="查看所有實體節點">
                    <div class="stat-number">${stats.nodes ?? 0}</div>
                    <div class="stat-label">實體節點</div>
                </div>
                <div class="stat-card facts" onclick="location.hash='#/facts'" title="查看所有事實關係">
                    <div class="stat-number">${stats.facts ?? 0}</div>
                    <div class="stat-label">事實關係</div>
                </div>
                <div class="stat-card episodes" onclick="location.hash='#/episodes'" title="查看所有記憶片段">
                    <div class="stat-number">${stats.episodes ?? 0}</div>
                    <div class="stat-label">記憶片段</div>
                </div>
            </div>
            <div class="dashboard-actions">
                <button class="btn btn-primary" onclick="App.openAddMemory()" aria-label="新增記憶">新增記憶</button>
                <button class="btn btn-secondary" onclick="App.exportJSON()" aria-label="匯出知識圖譜資料為 JSON">匯出 JSON</button>
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

    renderNodesPage(data, searchValue, searchMode, searchMeta) {
        return `
            ${this.renderPageDescription('nodes')}
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
                        title="依關鍵字過濾結果"
                        onclick="App.setSearchMode('filter')">篩選</button>
                <button class="search-mode-tab ${searchMode === 'vector' ? 'active' : ''}"
                        role="tab" aria-selected="${searchMode === 'vector'}"
                        title="使用語意相似度匹配"
                        onclick="App.setSearchMode('vector')">向量搜尋</button>
                <button class="btn btn-sm btn-secondary" style="margin-left:auto"
                        onclick="App.toggleBatchMode()">
                    ${App.state.batchMode ? '取消選取' : '批次選取'}
                </button>
            </div>
            ${this.renderSearchResultSummary(searchValue, searchMode, data.total, searchMeta)}
            <div class="card-list">
                ${data.nodes && data.nodes.length
                    ? data.nodes.map(n => this.renderNodeCard(n)).join('')
                    : this._empty('沒有找到實體節點')
                }
            </div>
            ${data.pages > 1 ? this.renderPagination(data.page, data.pages, data.total) : ''}
            ${this._batchBar()}
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
                        <div class="relations-section">
                            <button class="btn btn-sm btn-secondary" onclick="App.loadNodeRelations('${safeId}')">查看關係</button>
                            <button class="btn btn-sm btn-secondary" onclick="App.viewInGraph('${safeId}')" style="margin-left:4px">在圖譜中查看</button>
                            <div id="relations-${safeId}" class="relations-container"></div>
                        </div>
                    </div>
                </div>
                <div class="card-footer">
                    ${App.state.batchMode ? `<input type="checkbox" class="batch-checkbox"
                        ${App.state.selectedItems.has(node.uuid) ? 'checked' : ''}
                        onchange="App.toggleSelectItem('${safeId}')" onclick="event.stopPropagation()">` : ''}
                    <button class="btn-uuid" title="${node.uuid}" onclick="App.copyText('${safeId}')">
                        ${this._shortUuid(node.uuid)}
                    </button>
                    <span title="建立時間">${this._time(node.created_at)}</span>
                    <span class="card-actions">
                        <button class="btn-delete" onclick="App.deleteNode('${safeId}')" title="刪除節點">刪除</button>
                    </span>
                </div>
            </div>
        `;
    },

    // ============================================================
    // 事實頁面
    // ============================================================

    renderFactsPage(data, searchValue, searchMode, searchMeta) {
        return `
            ${this.renderPageDescription('facts')}
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
                        title="依關鍵字過濾結果"
                        onclick="App.setSearchMode('filter')">篩選</button>
                <button class="search-mode-tab ${searchMode === 'vector' ? 'active' : ''}"
                        role="tab" aria-selected="${searchMode === 'vector'}"
                        title="使用語意相似度匹配"
                        onclick="App.setSearchMode('vector')">向量搜尋</button>
                <button class="btn btn-sm btn-secondary" style="margin-left:auto"
                        onclick="App.toggleBatchMode()">
                    ${App.state.batchMode ? '取消選取' : '批次選取'}
                </button>
            </div>
            ${this.renderSearchResultSummary(searchValue, searchMode, data.total, searchMeta)}
            <div class="card-list">
                ${data.facts && data.facts.length
                    ? data.facts.map(f => this.renderFactCard(f)).join('')
                    : this._empty('沒有找到事實關係')
                }
            </div>
            ${data.pages > 1 ? this.renderPagination(data.page, data.pages, data.total) : ''}
            ${this._batchBar()}
        `;
    },

    renderFactCard(fact) {
        const safeId = this._safeUuid(fact.uuid);
        const isSelfRef = fact.source_name && fact.target_name && fact.source_name === fact.target_name;
        return `
            <div class="card card-fact">
                <div class="card-tags">
                    <span class="card-tag fact">Fact</span>
                    ${fact.name ? `<span class="card-tag fact-type" title="關係類型">${this._esc(fact.name)}</span>` : ''}
                    <span class="card-tags-right">
                        <span class="card-tag group">${this._esc(fact.group_id)}</span>
                    </span>
                </div>
                ${fact.fact ? `<div class="card-body-primary">${this._esc(fact.fact)}</div>` : ''}
                <div class="fact-entities${isSelfRef ? ' fact-self-ref' : ''}">
                    <span class="fact-source fact-entity-path" title="${this._esc(fact.source_name || '?')}">${this._esc(fact.source_name || '?')}</span>
                    <span class="fact-arrow">&#8594;</span>
                    <span class="fact-target fact-entity-path" title="${this._esc(fact.target_name || '?')}">${this._esc(fact.target_name || '?')}</span>
                </div>
                <div class="card-footer">
                    ${App.state.batchMode ? `<input type="checkbox" class="batch-checkbox"
                        ${App.state.selectedItems.has(fact.uuid) ? 'checked' : ''}
                        onchange="App.toggleSelectItem('${safeId}')" onclick="event.stopPropagation()">` : ''}
                    <button class="btn-uuid" title="${fact.uuid}" onclick="App.copyText('${safeId}')">
                        ${this._shortUuid(fact.uuid)}
                    </button>
                    <span title="建立時間">${this._time(fact.created_at)}</span>
                    <span class="card-actions">
                        <button class="btn-delete" onclick="App.deleteFact('${safeId}')" title="刪除">刪除</button>
                    </span>
                </div>
            </div>
        `;
    },

    // ============================================================
    // 記憶片段頁面
    // ============================================================

    renderEpisodesPage(data, searchValue, searchMode, searchMeta) {
        return `
            ${this.renderPageDescription('episodes')}
            <div class="page-header">
                <h1 class="page-title">記憶片段</h1>
                <div class="search-box">
                    <input type="text" class="search-input" id="search-input"
                           placeholder="${searchMode === 'vector' ? '全文搜尋...' : '關鍵字篩選...'}"
                           value="${this._esc(searchValue || '')}"
                           aria-label="搜尋關鍵字">
                    <button class="btn btn-primary" onclick="App.doSearch()" aria-label="執行搜尋">搜尋</button>
                </div>
            </div>
            <div class="search-mode-tabs" role="tablist" aria-label="搜尋模式">
                <button class="search-mode-tab ${searchMode === 'filter' ? 'active' : ''}"
                        role="tab" aria-selected="${searchMode === 'filter'}"
                        title="依關鍵字過濾結果"
                        onclick="App.setSearchMode('filter')">關鍵字</button>
                <button class="search-mode-tab ${searchMode === 'vector' ? 'active' : ''}"
                        role="tab" aria-selected="${searchMode === 'vector'}"
                        title="BM25 全文檢索匹配"
                        onclick="App.setSearchMode('vector')">全文搜尋</button>
                <button class="btn btn-sm btn-secondary" style="margin-left:auto"
                        onclick="App.toggleBatchMode()">
                    ${App.state.batchMode ? '取消選取' : '批次選取'}
                </button>
            </div>
            ${this.renderSearchResultSummary(searchValue, searchMode, data.total, searchMeta)}
            <div class="card-list">
                ${data.episodes && data.episodes.length
                    ? data.episodes.map(e => this.renderEpisodeCard(e)).join('')
                    : this._empty('沒有找到記憶片段')
                }
            </div>
            ${data.pages > 1 ? this.renderPagination(data.page, data.pages, data.total) : ''}
            ${this._batchBar()}
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
                    ${App.state.batchMode ? `<input type="checkbox" class="batch-checkbox"
                        ${App.state.selectedItems.has(ep.uuid) ? 'checked' : ''}
                        onchange="App.toggleSelectItem('${safeId}')" onclick="event.stopPropagation()">` : ''}
                    <button class="btn-uuid" title="${ep.uuid}" onclick="App.copyText('${safeId}')">
                        ${this._shortUuid(ep.uuid)}
                    </button>
                    <span title="建立時間">${this._time(ep.created_at)}</span>
                    <span class="card-actions">
                        <button class="btn-delete" onclick="App.deleteEpisode('${safeId}')" title="刪除">刪除</button>
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

        const jumpInput = total > 5 ? `<span class="pagination-jump">跳至 <input type="number" min="1" max="${total}" placeholder="#" onkeydown="App.jumpToPage(event)"> 頁</span>` : '';

        return `
            <div class="pagination" role="navigation" aria-label="分頁導航">
                ${buttons}
                <span class="pagination-info" aria-live="polite">共 ${totalItems} 筆</span>
                ${jumpInput}
            </div>
        `;
    },

    // ============================================================
    // 搜尋結果摘要
    // ============================================================

    renderSearchResultSummary(query, searchMode, total, meta) {
        if (!query) return '';
        const escapedQuery = this._esc(query);
        const isVector = searchMode === 'vector';
        const label = isVector ? '搜尋' : '篩選';
        const duration = meta && meta.duration != null
            ? `<span class="search-separator">&middot;</span><span class="search-duration">${meta.duration}s</span>`
            : '';
        return `
            <div class="search-result-summary" role="status" aria-live="polite">
                ${label} <span class="search-query">&ldquo;${escapedQuery}&rdquo;</span>
                <span class="search-separator">&mdash;</span>
                ${isVector ? '找到' : '共'} <span class="search-count">${total ?? 0}</span> 筆${isVector ? '結果' : ''}
                ${duration}
            </div>
        `;
    },

    // ============================================================
    // 知識總覽頁面
    // ============================================================

    renderOverviewPage(groupsData, quality, topNodes) {
        const groups = groupsData.groups || [];
        return `
            ${this.renderPageDescription('overview')}
            <div class="page-header">
                <h1 class="page-title">知識總覽</h1>
            </div>

            ${this.renderQualityMetrics(quality)}

            <div class="dashboard-section">
                <div class="section-title">影響力排行 TOP 10</div>
                ${topNodes.nodes && topNodes.nodes.length
                    ? `<div class="top-nodes-list">
                        ${topNodes.nodes.map((n, i) => `
                            <div class="top-node-item" onclick="App.viewInGraph('${this._safeUuid(n.uuid)}')">
                                <span class="top-node-rank">#${i + 1}</span>
                                <span class="top-node-name">${this._esc(n.name)}</span>
                                <span class="top-node-degree" title="關係數量">${n.degree} 條關係</span>
                                <span class="card-tag group">${this._esc(n.group_id)}</span>
                            </div>
                        `).join('')}
                       </div>`
                    : this._empty('尚無實體節點')
                }
            </div>

            <div class="dashboard-section">
                <div class="section-title" style="display:flex;align-items:center;gap:12px;">
                    群組健康度（${groups.length} 個群組）
                    ${groups.length ? `
                        <button class="btn btn-sm btn-secondary" onclick="App.toggleGroupBatch()" id="group-batch-toggle">批量刪除</button>
                        <span id="group-batch-bar" style="display:none;font-size:13px;color:var(--text-muted);">
                            已選取 <span id="group-batch-count">0</span> 個
                            <button class="btn btn-sm btn-danger" onclick="App.batchDeleteGroups()" style="margin-left:8px;">刪除選取</button>
                            <button class="btn btn-sm btn-secondary" onclick="App.toggleGroupBatch()" style="margin-left:4px;">取消</button>
                        </span>
                    ` : ''}
                </div>
                ${groups.length
                    ? `<div class="groups-grid" id="groups-grid">
                        ${groups.map(g => this.renderGroupCard(g)).join('')}
                       </div>`
                    : this._empty('尚無群組資料')
                }
            </div>
        `;
    },

    renderGroupCard(group) {
        const total = group.nodes + group.facts + group.episodes;
        const gid = this._esc(group.group_id);
        return `
            <div class="group-card" data-group-id="${gid}">
                <div class="group-card-header">
                    <label class="group-batch-cb" style="display:none;">
                        <input type="checkbox" onchange="App.toggleGroupSelect('${gid}')">
                    </label>
                    <span class="group-card-name">${gid}</span>
                    <span class="group-card-total">${total} 筆</span>
                </div>
                <div class="group-card-stats">
                    <div class="group-stat">
                        <span class="group-stat-num entity-color">${group.nodes}</span>
                        <span class="group-stat-label">節點</span>
                    </div>
                    <div class="group-stat">
                        <span class="group-stat-num fact-color">${group.facts}</span>
                        <span class="group-stat-label">事實</span>
                    </div>
                    <div class="group-stat">
                        <span class="group-stat-num episode-color">${group.episodes}</span>
                        <span class="group-stat-label">片段</span>
                    </div>
                </div>
                ${group.top_entities && group.top_entities.length ? `
                    <div class="group-card-top">
                        <span class="group-card-top-label">核心實體</span>
                        ${group.top_entities.map(e => `
                            <span class="group-top-entity" onclick="App.viewInGraph('${this._safeUuid(e.uuid)}')" title="度數: ${e.degree}">
                                ${this._esc(e.name)}
                            </span>
                        `).join('')}
                    </div>
                ` : ''}
                ${group.last_updated ? `<div class="group-card-updated">最後更新: ${this._time(group.last_updated)}</div>` : ''}
            </div>
        `;
    },

    renderQualityMetrics(quality) {
        if (!quality) return '';
        const orphans = quality.orphan_nodes || { count: 0, items: [] };
        const empty = quality.empty_summaries || { count: 0, items: [] };
        const dups = quality.duplicate_names || { count: 0, items: [] };

        const severity = (count) => {
            if (quality.total_nodes && quality.total_nodes > 0) {
                const pct = count / quality.total_nodes * 100;
                return pct === 0 ? 'good' : pct <= 5 ? 'warn' : 'bad';
            }
            return count === 0 ? 'good' : count <= 5 ? 'warn' : 'bad';
        };

        return `
            <div class="quality-section">
                <div class="section-title">知識品質指標</div>
                <div class="quality-grid">
                    <div class="quality-card quality-${severity(orphans.count)}" onclick="this.querySelector('.quality-detail').classList.toggle('hidden')">
                        <div class="quality-num">${orphans.count}</div>
                        <div class="quality-label">孤立節點</div>
                        <div class="quality-hint">無任何關係連結的實體${quality.total_nodes ? ` (${(orphans.count / quality.total_nodes * 100).toFixed(1)}%)` : ''}</div>
                        ${orphans.items.length ? `<div class="quality-detail hidden">
                            ${orphans.items.slice(0, 10).map(n => `<div class="quality-item">${this._esc(n.name || n.uuid)}</div>`).join('')}
                            ${orphans.count > 10 ? `<div class="quality-item-more">還有 ${orphans.count - 10} 個...</div>` : ''}
                        </div>` : ''}
                    </div>
                    <div class="quality-card quality-${severity(empty.count)}" onclick="this.querySelector('.quality-detail').classList.toggle('hidden')">
                        <div class="quality-num">${empty.count}</div>
                        <div class="quality-label">空摘要</div>
                        <div class="quality-hint">缺少摘要描述的實體${quality.total_nodes ? ` (${(empty.count / quality.total_nodes * 100).toFixed(1)}%)` : ''}</div>
                        ${empty.items.length ? `<div class="quality-detail hidden">
                            ${empty.items.slice(0, 10).map(n => `<div class="quality-item">${this._esc(n.name || n.uuid)}</div>`).join('')}
                            ${empty.count > 10 ? `<div class="quality-item-more">還有 ${empty.count - 10} 個...</div>` : ''}
                        </div>` : ''}
                    </div>
                    <div class="quality-card quality-${severity(dups.count)}" onclick="this.querySelector('.quality-detail').classList.toggle('hidden')">
                        <div class="quality-num">${dups.count}</div>
                        <div class="quality-label">重複名稱</div>
                        <div class="quality-hint">名稱相同的實體組${quality.total_nodes ? ` (${(dups.count / quality.total_nodes * 100).toFixed(1)}%)` : ''}</div>
                        ${dups.items.length ? `<div class="quality-detail hidden">
                            ${dups.items.map(d => `<div class="quality-item">${this._esc(d.name)} (${d.count} 個)</div>`).join('')}
                        </div>` : ''}
                    </div>
                </div>
            </div>
        `;
    },

    // ============================================================
    // 時間線頁面
    // ============================================================

    renderTimelinePage(data, currentDays) {
        const timeline = data.timeline || [];
        const dayOptions = [7, 14, 30, 90];

        // 計算最大值以決定柱狀圖比例
        let maxVal = 1;
        timeline.forEach(d => {
            const total = d.nodes + d.facts + d.episodes;
            if (total > maxVal) maxVal = total;
        });

        return `
            ${this.renderPageDescription('timeline')}
            <div class="page-header">
                <h1 class="page-title">時間線</h1>
                <div class="timeline-days">
                    ${dayOptions.map(d => `
                        <button class="btn btn-sm ${d === currentDays ? 'btn-primary' : 'btn-secondary'}"
                                onclick="App.setTimelineDays(${d})">${d} 天</button>
                    `).join('')}
                </div>
            </div>

            ${timeline.length === 0
                ? this._empty('選定時間範圍內無資料')
                : `<div class="timeline-chart">
                    ${timeline.map(d => {
                        const total = d.nodes + d.facts + d.episodes;
                        const sqrtScale = (val) => (Math.sqrt(val) / Math.sqrt(maxVal) * 100).toFixed(1);
                        const pctNodes = sqrtScale(d.nodes);
                        const pctFacts = sqrtScale(d.facts);
                        const pctEps = sqrtScale(d.episodes);
                        return `
                            <div class="timeline-row">
                                <span class="timeline-date">${d.date.slice(5)}</span>
                                <div class="timeline-bars">
                                    ${d.nodes ? `<div class="timeline-bar bar-entity" style="width:${pctNodes}%" title="節點: ${d.nodes}"></div>` : ''}
                                    ${d.facts ? `<div class="timeline-bar bar-fact" style="width:${pctFacts}%" title="事實: ${d.facts}"></div>` : ''}
                                    ${d.episodes ? `<div class="timeline-bar bar-episode" style="width:${pctEps}%" title="片段: ${d.episodes}"></div>` : ''}
                                </div>
                                <span class="timeline-total">${total}</span>
                            </div>
                        `;
                    }).join('')}
                    <div class="timeline-legend">
                        <span class="legend-item"><span class="legend-dot bar-entity"></span>節點</span>
                        <span class="legend-item"><span class="legend-dot bar-fact"></span>事實</span>
                        <span class="legend-item"><span class="legend-dot bar-episode"></span>片段</span>
                    </div>
                  </div>`
            }
        `;
    },

    // ============================================================
    // 圖譜頁面
    // ============================================================

    renderGraphPage(data, centerUuid) {
        return `
            ${this.renderPageDescription('graph')}
            <div class="page-header">
                <h1 class="page-title">知識圖譜</h1>
                <div class="search-box">
                    <input type="text" class="search-input" id="graph-search-input"
                           placeholder="搜尋節點名稱..."
                           value="${this._esc(centerUuid ? '' : '')}"
                           onkeydown="if(event.key==='Enter')App.searchGraph()"
                           aria-label="搜尋節點">
                    <button class="btn btn-primary" onclick="App.searchGraph()">探索</button>
                </div>
            </div>
            <div id="graph-container" class="graph-container">
                ${centerUuid
                    ? '<div class="loading-spinner">載入圖譜...</div>'
                    : '<div class="empty-state"><div class="empty-state-icon">&#9670;</div><div class="empty-state-text">正在載入最具影響力的節點...</div></div>'
                }
            </div>
        `;
    },

    renderD3Graph(container, data, centerUuid) {
        if (!data.nodes || !data.nodes.length) {
            container.innerHTML = '<div class="empty-state"><div class="empty-state-text">此節點無相關連結</div></div>';
            return;
        }

        container.innerHTML = '';
        const width = container.clientWidth || 800;
        const height = 600;

        // Group 顏色映射
        const groups = [...new Set(data.nodes.map(n => n.group_id || 'default'))];
        const colorScale = d3.scaleOrdinal(d3.schemeTableau10).domain(groups);

        // 節點統計
        const statsHtml = `<div style="padding:6px 12px;font-size:12px;color:var(--text-muted);display:flex;gap:16px;flex-wrap:wrap;">
            <span>${data.nodes.length} 個節點</span>
            <span>${data.edges.length} 條關係</span>
            <span>${groups.length} 個群組</span>
            ${groups.map(g => `<span style="color:${colorScale(g)}">● ${g}</span>`).join('')}
        </div>`;
        container.insertAdjacentHTML('beforeend', statsHtml);

        const svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height)
            .attr('viewBox', [0, 0, width, height]);

        const g = svg.append('g');

        // Zoom
        svg.call(d3.zoom()
            .scaleExtent([0.1, 8])
            .on('zoom', (event) => g.attr('transform', event.transform))
        );

        const nodes = data.nodes.map(n => ({ ...n, id: n.uuid }));
        const edges = data.edges.map(e => ({ ...e, source: e.source, target: e.target }));

        // 根據節點數調整力學參數
        const nodeCount = nodes.length;
        const chargeStrength = nodeCount > 200 ? -100 : nodeCount > 50 ? -200 : -300;
        const linkDistance = nodeCount > 200 ? 50 : nodeCount > 50 ? 80 : 100;

        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(edges).id(d => d.id).distance(linkDistance))
            .force('charge', d3.forceManyBody().strength(chargeStrength))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(nodeCount > 100 ? 15 : 30))
            .force('x', d3.forceX(width / 2).strength(0.05))
            .force('y', d3.forceY(height / 2).strength(0.05));

        // Edges
        const link = g.append('g')
            .selectAll('line')
            .data(edges)
            .join('line')
            .attr('class', 'graph-link')
            .attr('stroke', 'var(--border-color)')
            .attr('stroke-width', 1.5)
            .attr('stroke-opacity', 0.6);

        // Edge labels（節點多時隱藏）
        let linkLabel;
        if (nodeCount <= 100) {

            linkLabel = g.append('g')
                .selectAll('text')
                .data(edges)
                .join('text')
                .attr('class', 'graph-link-label')
                .attr('text-anchor', 'middle')
                .attr('font-size', '9px')
                .attr('fill', 'var(--text-muted)')
                .text(d => d.name ? d.name.slice(0, 15) : '');

        }

        // Nodes
        const node = g.append('g')
            .selectAll('g')
            .data(nodes)
            .join('g')
            .attr('class', 'graph-node')
            .call(d3.drag()
                .on('start', (event, d) => {
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x; d.fy = d.y;
                })
                .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
                .on('end', (event, d) => {
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null; d.fy = null;
                })
            );

        const nodeRadius = nodeCount > 200 ? 5 : nodeCount > 50 ? 8 : 10;

        node.append('circle')
            .attr('r', d => d.uuid === centerUuid ? 14 : nodeRadius)
            .attr('fill', d => d.uuid === centerUuid ? 'var(--accent)' : colorScale(d.group_id || 'default'))
            .attr('stroke', d => d.uuid === centerUuid ? 'var(--accent-hover)' : 'rgba(255,255,255,0.3)')
            .attr('stroke-width', d => d.uuid === centerUuid ? 3 : 1)
            .style('cursor', 'pointer');

        // 標籤（節點多時只顯示較短文字）
        const maxLabelLen = nodeCount > 200 ? 8 : nodeCount > 50 ? 12 : 20;

        node.append('text')
            .attr('dy', '0.35em')
            .attr('x', nodeRadius + 4)
            .attr('font-size', nodeCount > 200 ? '9px' : '12px')
            .attr('fill', 'var(--text-primary)')
            .text(d => d.name ? d.name.slice(0, maxLabelLen) : '');

        // Tooltip
        node.append('title')
            .text(d => `${d.name}\n群組: ${d.group_id}\n${d.uuid}`);

        // Click to expand
        node.on('click', (event, d) => {
            App.expandGraphNode(d.uuid);
        });

        simulation.on('tick', () => {

            link
                .attr('x1', d => d.source.x).attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x).attr('y2', d => d.target.y);

            if (linkLabel) {

                linkLabel
                    .attr('x', d => (d.source.x + d.target.x) / 2)
                    .attr('y', d => (d.source.y + d.target.y) / 2);

            }

            node.attr('transform', d => `translate(${d.x},${d.y})`);

        });
    },

    // ============================================================
    // AI 問答頁面
    // ============================================================

    renderAskPage(data) {
        return `
            ${this.renderPageDescription('ask')}
            <div class="page-header">
                <h1 class="page-title">知識問答</h1>
            </div>
            <div class="ask-panel">
                <div class="ask-input-row">
                    <input type="text" class="search-input ask-input" id="ask-input"
                           placeholder="問一個問題，看看 AI 能取得哪些上下文..."
                           onkeydown="if(event.key==='Enter')App.doAsk()"
                           aria-label="問題輸入">
                    <button class="btn btn-primary" onclick="App.doAsk()">查詢</button>
                </div>
                <div id="ask-result">
                    <div class="empty-state">
                        <div class="empty-state-icon">&#9889;</div>
                        <div class="empty-state-text">輸入問題後，系統將同時搜尋實體和事實，展示 AI 會看到的上下文</div>
                    </div>
                </div>
            </div>
        `;
    },

    renderAskResult(data) {
        if (!data) return '';
        const hasErrors = (data.errors?.nodes || data.errors?.facts);
        return `
            <div class="ask-duration">搜尋耗時 ${data.duration}s
                <button class="btn btn-sm btn-secondary" onclick="App.copyContext()" style="margin-left:8px">複製上下文</button>
            </div>
            ${hasErrors ? `<div class="ask-errors">
                ${data.errors.nodes ? `<div class="toast error" style="position:static;animation:none">節點搜尋錯誤: ${this._esc(data.errors.nodes)}</div>` : ''}
                ${data.errors.facts ? `<div class="toast error" style="position:static;animation:none">事實搜尋錯誤: ${this._esc(data.errors.facts)}</div>` : ''}
            </div>` : ''}
            <div class="ask-context">
                <div class="ask-context-label">AI 會看到的上下文</div>
                <pre class="ask-context-text" id="ask-context-text">${this._esc(data.context)}</pre>
            </div>
            <div class="ask-raw-results">
                ${data.nodes && data.nodes.length ? `
                    <div class="section-title">相關實體 (${data.nodes.length})</div>
                    <div class="card-list">
                        ${data.nodes.map(n => `
                            <div class="card card-entity" style="padding:12px 16px">
                                <div class="card-tags">
                                    <span class="card-tag entity">Entity</span>
                                    <span class="card-tags-right"><span class="card-tag group">${this._esc(n.group_id)}</span></span>
                                </div>
                                <div class="card-title-row" onclick="App.viewInGraph('${this._safeUuid(n.uuid)}')">${this._esc(n.name)}</div>
                                ${n.summary ? `<div class="card-body">${this._esc(n.summary)}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                ${data.facts && data.facts.length ? `
                    <div class="section-title" style="margin-top:16px">相關事實 (${data.facts.length})</div>
                    <div class="card-list">
                        ${data.facts.map(f => `
                            <div class="card card-fact" style="padding:12px 16px">
                                <div class="card-tags">
                                    <span class="card-tag fact">Fact</span>
                                    ${f.name ? `<span class="card-tag fact-type">${this._esc(f.name)}</span>` : ''}
                                </div>
                                ${f.fact ? `<div class="card-body-primary">${this._esc(f.fact)}</div>` : ''}
                                <div class="fact-entities">
                                    <span class="fact-source">${this._esc(f.source_name || '?')}</span>
                                    <span class="fact-arrow">&#8594;</span>
                                    <span class="fact-target">${this._esc(f.target_name || '?')}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
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

    /** 批次操作浮動列 */
    _batchBar() {
        if (!App.state.batchMode) return '';
        const count = App.state.selectedItems.size;
        return `
            <div class="batch-bar">
                <span>已選取 ${count} 個</span>
                <button class="btn btn-sm btn-secondary" onclick="App.selectAll()">全選</button>
                <button class="btn btn-sm btn-secondary" onclick="App.deselectAll()">取消全選</button>
                <button class="btn btn-sm btn-danger" onclick="App.batchDelete()" ${count === 0 ? 'disabled' : ''}>刪除選取</button>
                <button class="btn btn-sm btn-secondary" onclick="App.toggleBatchMode()">退出</button>
            </div>
        `;
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

    /** 渲染社群頁面 */
    renderCommunitiesPage(data = {}, page = 1) {
        const communities = data.communities || [];
        const total = data.total || 0;
        const pages = data.pages || 1;

        let html = this.renderPageDescription('communities');

        html += `
            <div class="page-header">
                <h2>社群 (${total})</h2>
                <div class="header-actions">
                    <button class="btn btn-primary" onclick="App.buildCommunities()">重新建構社群</button>
                </div>
            </div>
        `;

        if (!communities.length) {
            html += '<div class="empty-state">尚無社群資料。點擊「重新建構社群」開始社群檢測。</div>';
            return html;
        }

        html += '<div class="card-grid">';
        for (const c of communities) {
            html += `
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">${this._esc(c.name || '未命名社群')}</span>
                        <span class="card-meta">${c.uuid ? c.uuid.substring(0, 8) : ''}</span>
                    </div>
                    <div class="card-body">
                        <p class="card-summary">${this._esc(c.summary || '無摘要')}</p>
                        ${c.group_id ? `<span class="tag">${this._esc(c.group_id)}</span>` : ''}
                    </div>
                    <div class="card-footer">
                        <span class="card-date">${c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}</span>
                    </div>
                </div>
            `;
        }
        html += '</div>';

        if (pages > 1) {
            html += this.renderPagination(page, pages, 'App.goToCommunities');
        }

        return html;
    },

    /** 渲染背景任務頁面 */
    renderTasks(data) {
        const { tasks = [], total = 0, status_filter = '' } = data;
        const STATUS_LABELS = { pending: '待處理', processing: '進行中', completed: '完成', failed: '失敗' };
        const STATUS_COLORS = { pending: 'tag-yellow', processing: 'tag-blue', completed: 'tag-green', failed: 'tag-red' };

        let html = `<div class="page-header">
                <h2 class="page-title">背景任務</h2>
                <p class="page-description">${this.PAGE_DESCRIPTIONS.tasks}</p>
            </div>
            <div class="filter-bar">
                <label>狀態篩選：</label>
                ${['', 'pending', 'processing', 'completed', 'failed'].map(s =>
                    `<button class="btn btn-sm ${status_filter === s ? 'btn-primary' : 'btn-secondary'}"
                        onclick="App.loadTasks('${s}')">${s ? STATUS_LABELS[s] : '全部'}</button>`
                ).join('')}
                <button class="btn btn-secondary btn-sm" onclick="App.loadTasks()">&#x21bb; 重新整理</button>
            </div>`;

        if (tasks.length === 0) {
            return html + '<div class="empty-state"><p>目前沒有背景任務記錄。</p></div>';
        }

        html += `<div class="result-count">共 ${total} 筆</div><div class="task-list">`;

        for (const task of tasks) {
            const statusLabel = STATUS_LABELS[task.status] || task.status;
            const statusClass = STATUS_COLORS[task.status] || 'tag';
            const createdAt = task.created_at ? new Date(task.created_at).toLocaleString() : '';
            const completedAt = task.completed_at ? new Date(task.completed_at).toLocaleString() : '';
            const progress = task.chunks_total > 0
                ? `<div class="task-progress"><progress max="${task.chunks_total}" value="${task.chunks_done}"></progress> ${task.chunks_done}/${task.chunks_total}</div>`
                : '';
            const errorHtml = task.error
                ? `<div class="task-error">錯誤：${this._esc(task.error)}</div>` : '';

            html += `<div class="task-card task-${task.status}">
                <div class="task-header">
                    <span class="task-id">#${this._esc(task.task_id)}</span>
                    <span class="tag ${statusClass}">${statusLabel}</span>
                    <span class="task-name">${this._esc(task.name)}</span>
                    <span class="task-group tag">${this._esc(task.group_id)}</span>
                </div>
                ${progress}
                ${errorHtml}
                <div class="task-footer">
                    <span>建立：${createdAt}</span>
                    ${completedAt ? `<span>完成：${completedAt}</span>` : ''}
                    ${task.status === 'processing'
                        ? `<button class="btn btn-sm btn-secondary" onclick="App.pollTask('${task.task_id}')">查詢進度</button>` : ''}
                </div>
            </div>`;
        }

        html += '</div>';
        return html;
    },

    /** 渲染品質維護頁面（#6） */
    renderQuality(quality, stale) {
        let html = `<div class="page-header">
            <div class="page-header-top">
                <h2 class="page-title">品質維護</h2>
                <div style="display:flex;gap:8px">
                    <button class="btn btn-secondary btn-sm" onclick="App._renderQuality(document.getElementById('app'))">&#x21bb; 重新整理</button>
                    <button class="btn btn-secondary btn-sm" onclick="App.cleanupStale(true)">預覽清理</button>
                    <button class="btn btn-danger btn-sm" onclick="App.cleanupStale(false)">執行清理</button>
                </div>
            </div>
            <p class="page-description">${this.PAGE_DESCRIPTIONS.quality}</p>
        </div>`;

        if (quality && !quality.error) {
            const orphanCnt = quality.orphan_nodes?.count ?? 0;
            const emptyCnt = quality.empty_summaries?.count ?? 0;
            const dupCnt = quality.duplicate_names?.count ?? 0;
            html += `<div class="quality-grid">
                <div class="quality-card"><div class="quality-label">節點總數</div><div class="quality-value">${quality.total_nodes ?? '-'}</div></div>
                <div class="quality-card"><div class="quality-label">孤立節點</div><div class="quality-value ${orphanCnt > 0 ? 'quality-warn' : ''}">${orphanCnt}</div></div>
                <div class="quality-card"><div class="quality-label">空摘要</div><div class="quality-value ${emptyCnt > 0 ? 'quality-warn' : ''}">${emptyCnt}</div></div>
                <div class="quality-card"><div class="quality-label">重複名稱</div><div class="quality-value ${dupCnt > 0 ? 'quality-warn' : ''}">${dupCnt}</div></div>
            </div>`;
        }

        if (stale && stale.memories?.length > 0) {
            html += `<h3 class="section-title">過時記憶（低存取量）</h3><div class="task-list">`;
            for (const m of stale.memories.slice(0, 20)) {
                html += `<div class="task-card task-pending">
                    <div class="task-header">
                        <span class="task-name">${this._esc(m.name || m.uuid || '未命名')}</span>
                        <span class="tag">${this._esc(m.group_id || '')}</span>
                        <span class="tag-yellow tag">存取 ${m.access_count ?? 0} 次</span>
                    </div>
                    <div class="task-footer">
                        <span>最後存取：${m.last_accessed ? new Date(m.last_accessed).toLocaleDateString() : '從未'}</span>
                        <span>建立：${m.created_at ? new Date(m.created_at).toLocaleDateString() : ''}</span>
                    </div>
                </div>`;
            }
            html += '</div>';
        } else if (stale) {
            html += '<div class="empty-state"><p>沒有過時記憶，知識庫狀態良好。</p></div>';
        }

        return html;
    },

    /** 渲染匯入頁面（#8） */
    renderImport() {
        return `<div class="page-header">
            <h2 class="page-title">批量匯入</h2>
            <p class="page-description">${this.PAGE_DESCRIPTIONS.import}</p>
        </div>
        <div class="config-section">
            <form id="import-form" class="memory-form">
                <div class="form-group">
                    <label>JSON 格式（陣列或單一物件）</label>
                    <textarea id="import-json" rows="12" placeholder='[
  {"name": "記憶名稱", "content": "記憶內容", "group_id": "my-group", "source": "text"},
  ...
]'></textarea>
                </div>
                <div class="form-group">
                    <label>上傳 JSON 檔案</label>
                    <input type="file" id="import-file" accept=".json">
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label for="import-group">預設群組</label>
                        <input type="text" id="import-group" placeholder="default" value="default">
                    </div>
                    <div class="form-group" style="display:flex;align-items:flex-end">
                        <label class="checkbox-label">
                            <input type="checkbox" id="import-background" checked>
                            背景處理
                        </label>
                    </div>
                </div>
                <div class="dialog-actions" style="justify-content:flex-start">
                    <button type="submit" class="btn btn-primary">開始匯入</button>
                </div>
            </form>
            <div class="import-hint">
                <strong>欄位說明：</strong>
                <code>name</code>（必填）、<code>content</code>（必填）、
                <code>group_id</code>（選填，覆蓋上方預設）、
                <code>source</code>（text/json/message）、
                <code>source_description</code>（來源說明）
            </div>
        </div>`;
    },

    /** 渲染設定頁面（#5） */
    renderConfig(cfg) {
        if (cfg.error) {
            return `<div class="empty-state"><p>無法載入設定：${this._esc(cfg.error)}</p></div>`;
        }
        const mp = cfg.memory_performance || {};
        const field = (name, label, value, type = 'text', extra = '') =>
            `<div class="form-group">
                <label for="${name}">${label}</label>
                <input type="${type}" id="${name}" name="${name}" value="${this._esc(String(value ?? ''))}" ${extra}>
            </div>`;
        const check = (name, label, checked) =>
            `<div class="form-group">
                <label class="checkbox-label">
                    <input type="checkbox" id="${name}" name="${name}" ${checked ? 'checked' : ''}>
                    ${label}
                </label>
            </div>`;

        return `<div class="page-header">
            <h2 class="page-title">運行設定</h2>
            <p class="page-description">${this.PAGE_DESCRIPTIONS.config}</p>
            <div class="config-readonly">
                <span>LLM：<strong>${this._esc(cfg.llm_provider || '')}</strong></span>
                <span>模型：<strong>${this._esc(cfg.active_model || '')}</strong></span>
                <span>Embedding：<strong>${this._esc(cfg.embedding_provider || '')}</strong></span>
            </div>
        </div>
        <div class="config-section">
            <form id="config-form" class="memory-form">
                <h3 class="section-title">伺服器</h3>
                <div class="form-row">
                    ${field('server_lang', 'MCP 回應語言', cfg.server_lang)}
                    ${field('display_timezone', '顯示時區（IANA）', cfg.display_timezone)}
                </div>
                <h3 class="section-title">搜尋</h3>
                <div class="form-row">
                    ${field('search_limit', '搜尋結果上限', cfg.search_limit, 'number', 'min="1" max="100"')}
                    ${field('cosine_similarity_threshold', '去重相似度閾值', cfg.cosine_similarity_threshold, 'number', 'min="0" max="1" step="0.01"')}
                </div>
                <div class="form-row form-checkboxes">
                    ${check('enable_deduplication', '啟用去重', cfg.enable_deduplication)}
                </div>
                <h3 class="section-title">重要性追蹤</h3>
                <div class="form-row">
                    ${field('importance_weight', '重要性權重', cfg.importance_weight, 'number', 'min="0" max="1" step="0.01"')}
                    ${field('stale_days_threshold', '過時天數閾值', cfg.stale_days_threshold, 'number', 'min="1"')}
                    ${field('stale_min_access_count', '最低存取次數', cfg.stale_min_access_count, 'number', 'min="0"')}
                </div>
                <div class="form-row form-checkboxes">
                    ${check('enable_importance_tracking', '啟用存取追蹤', cfg.enable_importance_tracking)}
                </div>
                <h3 class="section-title">記憶處理效能</h3>
                <div class="form-row">
                    ${field('chunk_threshold', '觸發切分閾值（字元）', mp.chunk_threshold, 'number', 'min="100"')}
                    ${field('max_chunk_size', '每段最大字元數', mp.max_chunk_size, 'number', 'min="100"')}
                    ${field('max_coroutines', '最大並行協程', mp.max_coroutines, 'number', 'min="1" max="20"')}
                </div>
                <div class="form-row form-checkboxes">
                    ${check('default_background', '預設使用背景處理', mp.default_background)}
                </div>
                <div class="dialog-actions" style="justify-content:flex-start;margin-top:16px">
                    <button type="submit" class="btn btn-primary">套用設定</button>
                    <small style="color:var(--text-muted);margin-left:8px">僅本次進程生效，重啟後恢復配置檔設定</small>
                </div>
            </form>
        </div>`;
    },

    /** 渲染三元組新增按鈕（用於事實頁面） */
    renderTripletButton() {
        return '<button class="btn btn-secondary" onclick="App.openTripletDialog()">+ 新增三元組</button>';
    },
};
