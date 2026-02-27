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
    async episodes({ groupId = '', page = 1, limit = 20 } = {}) {
        const params = new URLSearchParams();
        if (groupId) params.set('group_id', groupId);
        if (page > 1) params.set('page', page);
        if (limit !== 20) params.set('limit', limit);
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

    // 內部方法
    async _get(url) {
        const res = await fetch(url);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    },

    async _delete(url) {
        const res = await fetch(url, { method: 'DELETE' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
    },
};
