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

    /** 新增記憶 */
    async addMemory({ name, content, groupId, source }) {
        return this._post('/api/memory/add', {
            name, content, group_id: groupId, source,
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
