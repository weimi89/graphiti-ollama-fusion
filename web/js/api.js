/**
 * Graphiti Web API 封裝
 */
const API = {
    /** 取得儀表板統計 */
    async stats(groupId = '') {
        const params = groupId ? `?group_id=${encodeURIComponent(groupId)}` : '';
        return this._get(`/api/stats${params}`);
    },

    /** 取得所有 group_id */
    async groups() {
        return this._get('/api/groups');
    },

    /** 瀏覽實體節點 */
    async nodes({ groupId = '', page = 1, limit = 20, search = '' } = {}) {
        const params = new URLSearchParams();
        if (groupId) params.set('group_id', groupId);
        if (page > 1) params.set('page', page);
        if (limit !== 20) params.set('limit', limit);
        if (search) params.set('search', search);
        return this._get(`/api/nodes?${params}`);
    },

    /** 瀏覽事實 */
    async facts({ groupId = '', page = 1, limit = 20, search = '' } = {}) {
        const params = new URLSearchParams();
        if (groupId) params.set('group_id', groupId);
        if (page > 1) params.set('page', page);
        if (limit !== 20) params.set('limit', limit);
        if (search) params.set('search', search);
        return this._get(`/api/facts?${params}`);
    },

    /** 瀏覽記憶片段 */
    async episodes({ groupId = '', page = 1, limit = 20, search = '' } = {}) {
        const params = new URLSearchParams();
        if (groupId) params.set('group_id', groupId);
        if (page > 1) params.set('page', page);
        if (limit !== 20) params.set('limit', limit);
        if (search) params.set('search', search);
        return this._get(`/api/episodes?${params}`);
    },

    /** 向量搜尋節點 */
    async searchNodes(q, { groupIds = [], limit = 10 } = {}) {
        const params = new URLSearchParams({ q });
        if (groupIds.length) params.set('group_ids', groupIds.join(','));
        if (limit !== 10) params.set('limit', limit);
        return this._get(`/api/search/nodes?${params}`);
    },

    /** 向量搜尋事實 */
    async searchFacts(q, { groupIds = [], limit = 10 } = {}) {
        const params = new URLSearchParams({ q });
        if (groupIds.length) params.set('group_ids', groupIds.join(','));
        if (limit !== 10) params.set('limit', limit);
        return this._get(`/api/search/facts?${params}`);
    },

    /** 全文搜尋記憶片段（BM25） */
    async searchEpisodes(q, { groupIds = [], limit = 10 } = {}) {
        const params = new URLSearchParams({ q });
        if (groupIds.length) params.set('group_ids', groupIds.join(','));
        if (limit !== 10) params.set('limit', limit);
        return this._get(`/api/search/episodes?${params}`);
    },

    /** 取得節點關係 */
    async nodeRelations(uuid) {
        return this._get(`/api/nodes/${uuid}/relations`);
    },

    /** 取得各 Group 統計 */
    async groupsStats() {
        return this._get('/api/groups/stats');
    },

    /** 取得時間線資料 */
    async timeline({ groupId = '', days = 30 } = {}) {
        const params = new URLSearchParams();
        if (groupId) params.set('group_id', groupId);
        if (days !== 30) params.set('days', days);
        return this._get(`/api/timeline?${params}`);
    },

    /** 取得影響力排行 */
    async topNodes({ groupId = '', limit = 20 } = {}) {
        const params = new URLSearchParams();
        if (groupId) params.set('group_id', groupId);
        if (limit !== 20) params.set('limit', limit);
        return this._get(`/api/analytics/top-nodes?${params}`);
    },

    /** 取得知識品質指標 */
    async quality({ groupId = '' } = {}) {
        const params = groupId ? `?group_id=${encodeURIComponent(groupId)}` : '';
        return this._get(`/api/analytics/quality${params}`);
    },

    /** 取得子圖資料 */
    async subgraph({ uuid, depth = 2, limit = 50 } = {}) {
        const params = new URLSearchParams({ uuid });
        if (depth !== 2) params.set('depth', depth);
        if (limit !== 50) params.set('limit', limit);
        return this._get(`/api/graph/subgraph?${params}`);
    },

    /** AI 問答測試 */
    async ask({ q, groupIds = [] } = {}) {
        const params = new URLSearchParams({ q });
        if (groupIds.length) params.set('group_ids', groupIds.join(','));
        return this._get(`/api/ask?${params}`);
    },

    /** 新增記憶 */
    async addMemory({ name, content, groupId, source }) {
        return this._post('/api/memory/add', {
            name, content, group_id: groupId, source,
        });
    },

    /** 批量新增記憶 */
    async addBulk({ episodes, groupId }) {
        return this._post('/api/memory/add-bulk', {
            episodes, group_id: groupId,
        });
    },

    /** 新增三元組 */
    async addTriplet({ sourceName, relationName, targetName, fact, groupId, sourceLabels, targetLabels }) {
        return this._post('/api/memory/add-triplet', {
            source_name: sourceName,
            relation_name: relationName,
            target_name: targetName,
            fact,
            group_id: groupId,
            source_labels: sourceLabels || [],
            target_labels: targetLabels || [],
        });
    },

    /** 瀏覽社群節點 */
    async communities({ groupId = '', page = 1, limit = 20 } = {}) {
        const params = new URLSearchParams();
        if (groupId) params.set('group_id', groupId);
        if (page > 1) params.set('page', page);
        if (limit !== 20) params.set('limit', limit);
        return this._get(`/api/communities?${params}`);
    },

    /** 觸發社群建構 */
    async buildCommunities({ groupIds } = {}) {
        return this._post('/api/communities/build', {
            group_ids: groupIds || null,
        });
    },

    /** 進階搜尋 */
    async advancedSearch(q, { recipe = 'combined_cross_encoder', groupIds = [], limit = 10 } = {}) {
        const params = new URLSearchParams({ q, recipe });
        if (groupIds.length) params.set('group_ids', groupIds.join(','));
        if (limit !== 10) params.set('limit', limit);
        return this._get(`/api/search/advanced?${params}`);
    },

    /** 過時記憶分析 */
    async staleAnalysis({ days = 30, minCount = 2, groupId = '', limit = 50 } = {}) {
        const params = new URLSearchParams();
        if (days !== 30) params.set('days', days);
        if (minCount !== 2) params.set('min_count', minCount);
        if (groupId) params.set('group_id', groupId);
        if (limit !== 50) params.set('limit', limit);
        return this._get(`/api/analytics/stale?${params}`);
    },

    /** 清理過時記憶 */
    async cleanupStale({ daysThreshold = 30, minAccessCount = 2, groupId = '', limit = 50, dryRun = true } = {}) {
        return this._post('/api/analytics/cleanup', {
            days_threshold: daysThreshold,
            min_access_count: minAccessCount,
            group_id: groupId,
            limit,
            dry_run: dryRun,
        });
    },

    /** 刪除實體節點 */
    async deleteNode(uuid) {
        return this._delete(`/api/nodes/${uuid}`);
    },

    /** 刪除記憶片段 */
    async deleteEpisode(uuid) {
        return this._delete(`/api/episodes/${uuid}`);
    },

    /** 刪除事實 */
    async deleteFact(uuid) {
        return this._delete(`/api/facts/${uuid}`);
    },

    /** 刪除群組 */
    async deleteGroup(groupId) {
        return this._delete(`/api/groups/${encodeURIComponent(groupId)}`);
    },

    /** 導出所有資料為 JSON（分頁拉取直到取完） */
    async exportData({ groupId = '' } = {}) {
        const fetchAll = async (fetcher) => {
            const allItems = [];
            let page = 1;
            while (true) {
                const data = await fetcher(page);
                const items = data.nodes || data.facts || data.episodes || [];
                allItems.push(...items);
                if (page >= (data.pages || 1)) break;
                page++;
            }
            return allItems;
        };

        const [nodes, facts, episodes] = await Promise.all([
            fetchAll(p => this.nodes({ groupId, page: p, limit: 100 })),
            fetchAll(p => this.facts({ groupId, page: p, limit: 100 })),
            fetchAll(p => this.episodes({ groupId, page: p, limit: 100 })),
        ]);
        return { nodes, facts, episodes };
    },

    // 內部方法（含重試）
    async _get(url, retries = 2) {
        for (let i = 0; i <= retries; i++) {
            try {
                const res = await fetch(url);
                if (res.status === 429) {
                    await new Promise(r => setTimeout(r, 2000 * (i + 1)));
                    continue;
                }
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return await res.json();
            } catch (err) {
                if (i === retries) throw err;
                await new Promise(r => setTimeout(r, 1000 * (i + 1)));
            }
        }
    },

    async _post(url, data) {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `HTTP ${res.status}`);
        }
        return res.json();
    },

    async _delete(url) {
        const res = await fetch(url, { method: 'DELETE' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    },
};
