#!/usr/bin/env python3
"""
Graphiti MCP Server 配置管理模組
================================

提供結構化的配置管理，支援從環境變數和配置檔案載入設定。

主要功能：
    - 各組件配置類別（Ollama、Neo4j、日誌、伺服器）
    - 配置驗證機制
    - 環境變數與檔案載入
    - 配置序列化與反序列化

使用範例：
    >>> from src.config import load_config
    >>> config = load_config()  # 從環境變數載入
    >>> config = load_config("config.json")  # 從檔案載入
"""

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================================
# 配置資料類別
# ============================================================================


@dataclass
class OllamaConfig:
    """
    Ollama LLM 服務配置。

    Attributes:
        model: 使用的主模型名稱（用於複雜任務如實體提取）
        small_model: 用於簡單任務的小模型名稱（如去重判斷、摘要生成）
        base_url: Ollama API 端點
        temperature: 生成溫度（0.0-2.0）
        max_tokens: 最大輸出 token 數
        timeout: 請求超時時間（秒）
        target_language: 強制 LLM 輸出使用的語言（如 "Traditional Chinese"）
    """

    model: str = "qwen2.5:7b"
    small_model: Optional[str] = None
    base_url: str = "http://localhost:11434"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    timeout: int = 120
    target_language: Optional[str] = None

    def validate(self) -> bool:
        """驗證配置是否有效。"""
        return not self.get_errors()

    def get_errors(self) -> list[str]:
        """返回配置中的具體錯誤列表。"""
        errors = []
        if not self.model:
            errors.append("ollama.model 不能為空")
        if not self.base_url:
            errors.append("ollama.base_url 不能為空")
        elif not self.base_url.startswith(("http://", "https://")):
            errors.append(f"ollama.base_url 格式無效: {self.base_url}")
        if not 0.0 <= self.temperature <= 2.0:
            errors.append(f"ollama.temperature 超出範圍 (0.0-2.0): {self.temperature}")
        return errors


@dataclass
class OllamaEmbedderConfig:
    """
    Ollama 嵌入器配置。

    Attributes:
        model: 嵌入模型名稱
        base_url: Ollama API 端點
        dimensions: 嵌入向量維度
        batch_size: 批次處理大小
        timeout: 請求超時時間（秒）
    """

    model: str = "nomic-embed-text:v1.5"
    base_url: str = "http://localhost:11434"
    dimensions: int = 768
    batch_size: int = 10
    timeout: int = 60

    def validate(self) -> bool:
        """驗證配置是否有效。"""
        return not self.get_errors()

    def get_errors(self) -> list[str]:
        """返回配置中的具體錯誤列表。"""
        errors = []
        if not self.model:
            errors.append("embedder.model 不能為空")
        if not self.base_url:
            errors.append("embedder.base_url 不能為空")
        elif not self.base_url.startswith(("http://", "https://")):
            errors.append(f"embedder.base_url 格式無效: {self.base_url}")
        if self.dimensions <= 0:
            errors.append(f"embedder.dimensions 必須 > 0: {self.dimensions}")
        if self.batch_size <= 0:
            errors.append(f"embedder.batch_size 必須 > 0: {self.batch_size}")
        return errors


@dataclass
class Neo4jConfig:
    """
    Neo4j 資料庫配置。

    Attributes:
        uri: 資料庫連接 URI
        user: 使用者名稱
        password: 密碼
        database: 資料庫名稱
        max_connection_lifetime: 連接最大存活時間（秒）
        max_connection_pool_size: 連接池最大大小
        connection_timeout: 連接超時時間（秒）
    """

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_timeout: int = 30

    def validate(self) -> bool:
        """驗證配置是否有效。"""
        return not self.get_errors()

    def get_errors(self) -> list[str]:
        """返回配置中的具體錯誤列表。"""
        errors = []
        if not self.uri:
            errors.append("neo4j.uri 不能為空")
        elif not self.uri.startswith(("bolt://", "neo4j://", "bolt+s://", "neo4j+s://")):
            errors.append(f"neo4j.uri 格式無效: {self.uri}")
        if not self.user:
            errors.append("neo4j.user 不能為空")
        if not self.password:
            errors.append("neo4j.password 不能為空")
        if not self.database:
            errors.append("neo4j.database 不能為空")
        return errors


@dataclass
class LoggingConfig:
    """
    日誌配置。

    Attributes:
        level: 日誌級別
        format: 日誌格式
        file_path: 日誌檔案路徑
        max_file_size: 檔案大小輪轉閾值（位元組）
        backup_count: 保留的備份檔案數量
        console_output: 是否輸出到控制台
        rotation_type: 輪轉類型（"time" 或 "size"）
        rotation_interval: 時間輪轉間隔
    """

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 30
    console_output: bool = True
    rotation_type: str = "time"
    rotation_interval: str = "midnight"
    third_party_levels: Dict[str, str] = field(default_factory=lambda: {
        "httpx": "WARNING",
        "httpcore": "WARNING",
        "urllib3": "WARNING",
        "asyncio": "WARNING",
        "neo4j": "INFO",
    })

    # 有效的配置選項
    VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    VALID_ROTATION_TYPES = {"time", "size"}
    VALID_INTERVALS = {"midnight", "H", "D", "W0", "W1", "W2", "W3", "W4", "W5", "W6"}

    def validate(self) -> bool:
        """驗證配置是否有效。"""
        return not self.get_errors()

    def get_errors(self) -> list[str]:
        """返回配置中的具體錯誤列表。"""
        errors = []
        if self.level.upper() not in self.VALID_LEVELS:
            errors.append(f"logging.level 無效: {self.level}（有效值: {', '.join(self.VALID_LEVELS)}）")
        if self.rotation_type not in self.VALID_ROTATION_TYPES:
            errors.append(f"logging.rotation_type 無效: {self.rotation_type}")
        if self.rotation_type == "time" and self.rotation_interval not in self.VALID_INTERVALS:
            errors.append(f"logging.rotation_interval 無效: {self.rotation_interval}")
        if self.backup_count < 1:
            errors.append(f"logging.backup_count 必須 >= 1: {self.backup_count}")
        return errors


@dataclass
class ServerConfig:
    """
    MCP 伺服器配置。

    Attributes:
        host: 綁定的主機地址
        port: 監聽端口
        transport: 傳輸模式（sse, stdio, http）
        cors_origins: CORS 允許的來源
        max_request_size: 最大請求大小（位元組）
    """

    host: str = "0.0.0.0"
    port: int = 8000
    transport: str = "sse"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    max_request_size: int = 10 * 1024 * 1024  # 10MB

    VALID_TRANSPORTS = {"sse", "stdio", "http"}

    def validate(self) -> bool:
        """驗證配置是否有效。"""
        return not self.get_errors()

    def get_errors(self) -> list[str]:
        """返回配置中的具體錯誤列表。"""
        errors = []
        if not 1 <= self.port <= 65535:
            errors.append(f"server.port 超出範圍 (1-65535): {self.port}")
        if self.transport not in self.VALID_TRANSPORTS:
            errors.append(f"server.transport 無效: {self.transport}（有效值: {', '.join(self.VALID_TRANSPORTS)}）")
        return errors


@dataclass
class MemoryPerformanceConfig:
    """
    記憶添加效能配置。

    Attributes:
        chunk_threshold: 觸發智慧切分的字元數閾值
        max_chunk_size: 每段最大字元數
        max_coroutines: Graphiti 內部最大並行協程數
        default_background: 是否預設使用背景處理模式
    """

    chunk_threshold: int = 800
    max_chunk_size: int = 600
    max_coroutines: int = 5
    default_background: bool = False

    def validate(self) -> bool:
        """驗證配置是否有效。"""
        return not self.get_errors()

    def get_errors(self) -> list[str]:
        """返回配置中的具體錯誤列表。"""
        errors = []
        if self.chunk_threshold < 100:
            errors.append(f"memory_performance.chunk_threshold 過小 (最小 100): {self.chunk_threshold}")
        if self.max_chunk_size < 100:
            errors.append(f"memory_performance.max_chunk_size 過小 (最小 100): {self.max_chunk_size}")
        if self.max_coroutines < 1 or self.max_coroutines > 20:
            errors.append(f"memory_performance.max_coroutines 超出範圍 (1-20): {self.max_coroutines}")
        return errors


@dataclass
class GraphitiConfig:
    """
    完整的 Graphiti 應用程式配置。

    整合所有子配置模組，提供統一的配置管理介面。

    Attributes:
        ollama: Ollama LLM 配置
        embedder: 嵌入器配置
        neo4j: Neo4j 資料庫配置
        logging: 日誌配置
        server: 伺服器配置
        memory_performance: 記憶添加效能配置
        search_limit: 搜索結果上限
        enable_deduplication: 是否啟用去重
        pydantic_validation_fixes: 是否啟用 Pydantic 驗證修復
        cosine_similarity_threshold: 餘弦相似度閾值
    """

    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    embedder: OllamaEmbedderConfig = field(default_factory=OllamaEmbedderConfig)
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    memory_performance: MemoryPerformanceConfig = field(default_factory=MemoryPerformanceConfig)

    # Graphiti 特定設定
    search_limit: int = 20
    enable_deduplication: bool = True
    pydantic_validation_fixes: bool = True
    cosine_similarity_threshold: float = 0.8

    # 重要性追蹤設定
    enable_importance_tracking: bool = True
    importance_weight: float = 0.1

    # 智慧遺忘設定
    stale_days_threshold: int = 30
    stale_min_access_count: int = 2

    # 顯示時區（API 回傳時間戳轉換用）
    display_timezone: str = "UTC"

    @classmethod
    def from_env(cls) -> "GraphitiConfig":
        """
        從環境變數載入配置。

        環境變數對應關係：
            - OLLAMA_MODEL, OLLAMA_SMALL_MODEL, OLLAMA_BASE_URL, OLLAMA_TEMPERATURE
            - OLLAMA_EMBEDDING_MODEL, OLLAMA_EMBEDDING_BASE_URL, OLLAMA_EMBEDDING_DIMENSIONS
            - NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, NEO4J_DATABASE
            - SERVER_HOST, SERVER_PORT, SERVER_TRANSPORT
            - LOG_LEVEL, LOG_FILE, LOG_ROTATION_TYPE, LOG_ROTATION_INTERVAL

        Returns:
            GraphitiConfig: 載入的配置實例
        """
        config = cls()

        # Ollama 配置
        config.ollama.model = os.getenv("OLLAMA_MODEL", config.ollama.model)
        config.ollama.small_model = os.getenv("OLLAMA_SMALL_MODEL", config.ollama.small_model)
        config.ollama.base_url = os.getenv("OLLAMA_BASE_URL", config.ollama.base_url)
        config.ollama.temperature = float(
            os.getenv("OLLAMA_TEMPERATURE", config.ollama.temperature)
        )
        config.ollama.target_language = os.getenv(
            "OLLAMA_TARGET_LANGUAGE", config.ollama.target_language
        )

        # 嵌入器配置
        config.embedder.model = os.getenv("OLLAMA_EMBEDDING_MODEL", config.embedder.model)
        config.embedder.base_url = os.getenv(
            "OLLAMA_EMBEDDING_BASE_URL", config.embedder.base_url
        )
        config.embedder.dimensions = int(
            os.getenv("OLLAMA_EMBEDDING_DIMENSIONS", config.embedder.dimensions)
        )

        # Neo4j 配置
        config.neo4j.uri = os.getenv("NEO4J_URI", config.neo4j.uri)
        config.neo4j.user = os.getenv("NEO4J_USER", config.neo4j.user)
        config.neo4j.password = os.getenv("NEO4J_PASSWORD", config.neo4j.password)
        config.neo4j.database = os.getenv("NEO4J_DATABASE", config.neo4j.database)

        # 伺服器配置
        config.server.host = os.getenv("SERVER_HOST", config.server.host)
        config.server.port = int(os.getenv("SERVER_PORT", config.server.port))
        config.server.transport = os.getenv("SERVER_TRANSPORT", config.server.transport)

        # 日誌配置
        config.logging.level = os.getenv("LOG_LEVEL", config.logging.level)
        config.logging.file_path = os.getenv("LOG_FILE", config.logging.file_path)
        config.logging.rotation_type = os.getenv(
            "LOG_ROTATION_TYPE", config.logging.rotation_type
        )
        config.logging.rotation_interval = os.getenv(
            "LOG_ROTATION_INTERVAL", config.logging.rotation_interval
        )

        if os.getenv("LOG_BACKUP_COUNT"):
            config.logging.backup_count = int(os.getenv("LOG_BACKUP_COUNT"))

        # 第三方日誌級別覆蓋（JSON 格式）
        third_party_env = os.getenv("GRAPHITI_LOG_THIRD_PARTY_LEVELS")
        if third_party_env:
            try:
                overrides = json.loads(third_party_env)
                config.logging.third_party_levels.update(overrides)
            except json.JSONDecodeError:
                logger.warning("GRAPHITI_LOG_THIRD_PARTY_LEVELS 格式無效（需 JSON），已忽略")

        # 顯示時區
        config.display_timezone = os.getenv(
            "GRAPHITI_DISPLAY_TIMEZONE", config.display_timezone
        )

        # 記憶效能配置
        _load_memory_performance_settings(config)

        # Graphiti 特定設定
        _load_graphiti_settings(config)

        return config

    @classmethod
    def from_file(cls, config_path: str) -> "GraphitiConfig":
        """
        從 JSON 配置檔案載入配置。

        Args:
            config_path: 配置檔案路徑

        Returns:
            GraphitiConfig: 載入的配置實例（檔案不存在時返回預設配置）
        """
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"配置檔案不存在: {config_path}，使用預設配置")
            return cls()

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            config = cls()
            _apply_config_section(config.ollama, config_data.get("ollama", {}))
            _apply_config_section(config.embedder, config_data.get("embedder", {}))
            _apply_config_section(config.neo4j, config_data.get("neo4j", {}))
            _apply_config_section(config.logging, config_data.get("logging", {}))
            _apply_config_section(config.server, config_data.get("server", {}))
            _apply_config_section(config.memory_performance, config_data.get("memory_performance", {}))

            # 載入 Graphiti 特定設定
            for key in [
                "search_limit",
                "enable_deduplication",
                "pydantic_validation_fixes",
                "cosine_similarity_threshold",
                "enable_importance_tracking",
                "importance_weight",
                "stale_days_threshold",
                "stale_min_access_count",
                "display_timezone",
            ]:
                if key in config_data:
                    setattr(config, key, config_data[key])

            logger.info(f"成功載入配置檔案: {config_path}")
            return config

        except Exception as e:
            logger.error(f"載入配置檔案失敗: {e}")
            return cls()

    def validate(self) -> bool:
        """驗證所有配置。"""
        return not self.get_errors()

    def get_errors(self) -> list[str]:
        """
        收集所有子配置的具體錯誤列表。

        Returns:
            list[str]: 錯誤訊息列表，空列表表示全部通過
        """
        errors = []
        for sub in [self.ollama, self.embedder, self.neo4j, self.logging, self.server, self.memory_performance]:
            errors.extend(sub.get_errors())
        return errors

    def save_to_file(self, config_path: str) -> bool:
        """
        將配置保存到 JSON 檔案。

        Args:
            config_path: 目標檔案路徑

        Returns:
            bool: 保存成功返回 True

        Note:
            密碼欄位會被遮蔽為 "***"
        """
        try:
            config_data = {
                "ollama": {
                    "model": self.ollama.model,
                    "small_model": self.ollama.small_model,
                    "base_url": self.ollama.base_url,
                    "temperature": self.ollama.temperature,
                    "max_tokens": self.ollama.max_tokens,
                    "timeout": self.ollama.timeout,
                },
                "embedder": {
                    "model": self.embedder.model,
                    "base_url": self.embedder.base_url,
                    "dimensions": self.embedder.dimensions,
                    "batch_size": self.embedder.batch_size,
                    "timeout": self.embedder.timeout,
                },
                "neo4j": {
                    "uri": self.neo4j.uri,
                    "user": self.neo4j.user,
                    "password": "***",  # 不保存密碼
                    "database": self.neo4j.database,
                    "max_connection_lifetime": self.neo4j.max_connection_lifetime,
                    "max_connection_pool_size": self.neo4j.max_connection_pool_size,
                    "connection_timeout": self.neo4j.connection_timeout,
                },
                "logging": {
                    "level": self.logging.level,
                    "format": self.logging.format,
                    "file_path": self.logging.file_path,
                    "max_file_size": self.logging.max_file_size,
                    "backup_count": self.logging.backup_count,
                    "console_output": self.logging.console_output,
                },
                "server": {
                    "host": self.server.host,
                    "port": self.server.port,
                    "transport": self.server.transport,
                    "cors_origins": self.server.cors_origins,
                    "max_request_size": self.server.max_request_size,
                },
                "search_limit": self.search_limit,
                "enable_deduplication": self.enable_deduplication,
                "pydantic_validation_fixes": self.pydantic_validation_fixes,
                "cosine_similarity_threshold": self.cosine_similarity_threshold,
                "enable_importance_tracking": self.enable_importance_tracking,
                "importance_weight": self.importance_weight,
                "stale_days_threshold": self.stale_days_threshold,
                "stale_min_access_count": self.stale_min_access_count,
                "display_timezone": self.display_timezone,
            }

            config_file = Path(config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"配置已保存至: {config_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置檔案失敗: {e}")
            return False

    def apply_env_overrides(self) -> None:
        """
        用環境變數覆蓋現有配置（只覆蓋有設定的環境變數）。

        適用於 JSON 配置為基礎、環境變數為覆蓋的部署場景（如 Docker）。
        """
        # Ollama 配置
        if os.getenv("OLLAMA_MODEL"):
            self.ollama.model = os.getenv("OLLAMA_MODEL")
        if os.getenv("OLLAMA_SMALL_MODEL"):
            self.ollama.small_model = os.getenv("OLLAMA_SMALL_MODEL")
        if os.getenv("OLLAMA_BASE_URL"):
            self.ollama.base_url = os.getenv("OLLAMA_BASE_URL")
        if os.getenv("OLLAMA_TEMPERATURE"):
            self.ollama.temperature = float(os.getenv("OLLAMA_TEMPERATURE"))
        if os.getenv("OLLAMA_TARGET_LANGUAGE"):
            self.ollama.target_language = os.getenv("OLLAMA_TARGET_LANGUAGE")

        # 嵌入器配置
        if os.getenv("OLLAMA_EMBEDDING_MODEL"):
            self.embedder.model = os.getenv("OLLAMA_EMBEDDING_MODEL")
        if os.getenv("OLLAMA_EMBEDDING_BASE_URL"):
            self.embedder.base_url = os.getenv("OLLAMA_EMBEDDING_BASE_URL")
        if os.getenv("OLLAMA_EMBEDDING_DIMENSIONS"):
            self.embedder.dimensions = int(os.getenv("OLLAMA_EMBEDDING_DIMENSIONS"))

        # Neo4j 配置
        if os.getenv("NEO4J_URI"):
            self.neo4j.uri = os.getenv("NEO4J_URI")
        if os.getenv("NEO4J_USER"):
            self.neo4j.user = os.getenv("NEO4J_USER")
        if os.getenv("NEO4J_PASSWORD"):
            self.neo4j.password = os.getenv("NEO4J_PASSWORD")
        if os.getenv("NEO4J_DATABASE"):
            self.neo4j.database = os.getenv("NEO4J_DATABASE")

        # 伺服器配置
        if os.getenv("SERVER_HOST"):
            self.server.host = os.getenv("SERVER_HOST")
        if os.getenv("SERVER_PORT"):
            self.server.port = int(os.getenv("SERVER_PORT"))
        if os.getenv("SERVER_TRANSPORT"):
            self.server.transport = os.getenv("SERVER_TRANSPORT")

        # 日誌配置
        if os.getenv("LOG_LEVEL"):
            self.logging.level = os.getenv("LOG_LEVEL")
        if os.getenv("LOG_FILE"):
            self.logging.file_path = os.getenv("LOG_FILE")
        if os.getenv("LOG_ROTATION_TYPE"):
            self.logging.rotation_type = os.getenv("LOG_ROTATION_TYPE")
        if os.getenv("LOG_ROTATION_INTERVAL"):
            self.logging.rotation_interval = os.getenv("LOG_ROTATION_INTERVAL")
        if os.getenv("LOG_BACKUP_COUNT"):
            self.logging.backup_count = int(os.getenv("LOG_BACKUP_COUNT"))

        # 第三方日誌級別覆蓋
        third_party_env = os.getenv("GRAPHITI_LOG_THIRD_PARTY_LEVELS")
        if third_party_env:
            try:
                overrides = json.loads(third_party_env)
                self.logging.third_party_levels.update(overrides)
            except json.JSONDecodeError:
                logger.warning("GRAPHITI_LOG_THIRD_PARTY_LEVELS 格式無效（需 JSON），已忽略")

        # 顯示時區
        if os.getenv("GRAPHITI_DISPLAY_TIMEZONE"):
            self.display_timezone = os.getenv("GRAPHITI_DISPLAY_TIMEZONE")

        # 記憶效能配置
        _load_memory_performance_settings(self)

        # Graphiti 特定設定
        _load_graphiti_settings(self)

    def get_summary(self) -> Dict[str, Any]:
        """
        獲取配置摘要（用於日誌記錄）。

        Returns:
            dict: 不含敏感資訊的配置摘要
        """
        return {
            "ollama_model": self.ollama.model,
            "ollama_small_model": self.ollama.small_model or self.ollama.model,
            "ollama_target_language": self.ollama.target_language,
            "embedder_model": self.embedder.model,
            "embedder_dimensions": self.embedder.dimensions,
            "neo4j_uri": self.neo4j.uri,
            "neo4j_database": self.neo4j.database,
            "server_port": self.server.port,
            "log_level": self.logging.level,
            "search_limit": self.search_limit,
            "deduplication_enabled": self.enable_deduplication,
            "pydantic_fixes_enabled": self.pydantic_validation_fixes,
            "max_coroutines": self.memory_performance.max_coroutines,
            "chunk_threshold": self.memory_performance.chunk_threshold,
            "importance_tracking": self.enable_importance_tracking,
            "display_timezone": self.display_timezone,
        }


# ============================================================================
# 輔助函數
# ============================================================================


def _apply_config_section(target: Any, source: Dict[str, Any]) -> None:
    """
    將配置字典套用到目標物件。

    Args:
        target: 目標配置物件
        source: 來源配置字典
    """
    for key, value in source.items():
        if hasattr(target, key):
            setattr(target, key, value)


def _load_memory_performance_settings(config: GraphitiConfig) -> None:
    """
    從環境變數載入記憶效能設定。

    Args:
        config: 配置物件
    """
    mp = config.memory_performance
    if os.getenv("GRAPHITI_CHUNK_THRESHOLD"):
        mp.chunk_threshold = int(os.getenv("GRAPHITI_CHUNK_THRESHOLD"))
    if os.getenv("GRAPHITI_MAX_CHUNK_SIZE"):
        mp.max_chunk_size = int(os.getenv("GRAPHITI_MAX_CHUNK_SIZE"))
    if os.getenv("GRAPHITI_MAX_COROUTINES"):
        mp.max_coroutines = int(os.getenv("GRAPHITI_MAX_COROUTINES"))
    if os.getenv("GRAPHITI_DEFAULT_BACKGROUND"):
        mp.default_background = os.getenv("GRAPHITI_DEFAULT_BACKGROUND").lower() == "true"


def _load_graphiti_settings(config: GraphitiConfig) -> None:
    """
    從環境變數載入 Graphiti 特定設定。

    Args:
        config: 配置物件
    """
    if os.getenv("SEARCH_LIMIT"):
        config.search_limit = int(os.getenv("SEARCH_LIMIT"))

    if os.getenv("ENABLE_DEDUPLICATION"):
        config.enable_deduplication = os.getenv("ENABLE_DEDUPLICATION").lower() == "true"

    if os.getenv("PYDANTIC_VALIDATION_FIXES"):
        config.pydantic_validation_fixes = (
            os.getenv("PYDANTIC_VALIDATION_FIXES").lower() == "true"
        )

    if os.getenv("COSINE_SIMILARITY_THRESHOLD"):
        config.cosine_similarity_threshold = float(os.getenv("COSINE_SIMILARITY_THRESHOLD"))

    if os.getenv("ENABLE_IMPORTANCE_TRACKING"):
        config.enable_importance_tracking = os.getenv("ENABLE_IMPORTANCE_TRACKING").lower() == "true"

    if os.getenv("IMPORTANCE_WEIGHT"):
        config.importance_weight = float(os.getenv("IMPORTANCE_WEIGHT"))

    if os.getenv("STALE_DAYS_THRESHOLD"):
        config.stale_days_threshold = int(os.getenv("STALE_DAYS_THRESHOLD"))

    if os.getenv("STALE_MIN_ACCESS_COUNT"):
        config.stale_min_access_count = int(os.getenv("STALE_MIN_ACCESS_COUNT"))


def load_config(config_path: Optional[str] = None) -> GraphitiConfig:
    """
    載入配置的便利函數。

    支援配置層疊：JSON 檔案為基礎配置，環境變數覆蓋個別值。
    這在 Docker/K8s 部署中特別有用，可以用 JSON 做基礎配置，
    再用環境變數覆蓋密碼、端口等敏感或環境特定的值。

    載入順序：
        1. 有 config_path 且檔案存在 → 從 JSON 載入基礎 + 環境變數覆蓋
        2. 無 config_path 或檔案不存在 → 純環境變數載入

    Args:
        config_path: 可選的配置檔案路徑

    Returns:
        GraphitiConfig: 載入並驗證的配置實例
    """
    if config_path and Path(config_path).exists():
        config = GraphitiConfig.from_file(config_path)
        # 層疊：用環境變數覆蓋 JSON 中的值
        config.apply_env_overrides()
    else:
        config = GraphitiConfig.from_env()

    errors = config.get_errors()
    if errors:
        for err in errors:
            logger.warning(f"配置問題: {err}")
        logger.warning("配置驗證失敗，某些功能可能無法正常運作")

    return config


# 預設配置實例（供模組直接使用）
default_config = GraphitiConfig()
