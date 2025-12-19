const path = require('path');
const HOME = process.env.HOME;

module.exports = {
  apps: [
    {
      name: 'graphiti-mcp-sse',
      script: path.join(HOME, '.local/bin/uv'),
      args: 'run python graphiti_mcp_server.py --transport sse --host 0.0.0.0 --port 8000',
      cwd: path.join(HOME, 'MCP/graphiti'),
      interpreter: 'none',
      env: {
        // 繼承系統環境變數
        PATH: process.env.PATH,
        HOME: HOME,
        // 如果需要，可以在這裡添加其他環境變數
      },
      // 日誌設定
      out_file: './logs/pm2-out.log',
      error_file: './logs/pm2-error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true,
      // 進程管理
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      watch: false,
      // 資源限制
      max_memory_restart: '500M',
    }
  ]
};
