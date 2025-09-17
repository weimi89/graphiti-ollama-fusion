#!/usr/bin/env python3
"""
Graphiti MCP Server Configuration Management
基於原始官網版本的配置架構，提供結構化的配置管理
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Ollama LLM 配置"""
    model: str = "qwen2.5:7b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.1
    max_tokens: Optional[int] = None
    timeout: int = 120

    def validate(self) -> bool:
        """驗證 Ollama 配置"""
        if not self.model or not self.base_url:
            return False
        if not (0.0 <= self.temperature <= 2.0):
            return False
        return True


@dataclass
class OllamaEmbedderConfig:
    """Ollama 嵌入器配置"""
    model: str = "nomic-embed-text:v1.5"
    base_url: str = "http://localhost:11434"
    dimensions: int = 768
    batch_size: int = 10
    timeout: int = 60

    def validate(self) -> bool:
        """驗證嵌入器配置"""
        if not self.model or not self.base_url:
            return False
        if self.dimensions <= 0 or self.batch_size <= 0:
            return False
        return True


@dataclass
class Neo4jConfig:
    """Neo4j 資料庫配置"""
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = "password"
    database: str = "neo4j"
    max_connection_lifetime: int = 3600
    max_connection_pool_size: int = 50
    connection_timeout: int = 30

    def validate(self) -> bool:
        """驗證 Neo4j 配置"""
        if not self.uri or not self.user or not self.password:
            return False
        if not self.database:
            return False
        return True


@dataclass
class LoggingConfig:
    """日誌配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB (備用，現在使用時間輪轉)
    backup_count: int = 30  # 保留 30 天的日誌檔案
    console_output: bool = True
    rotation_type: str = "time"  # "time" 或 "size"
    rotation_interval: str = "midnight"  # 輪轉時間點

    def validate(self) -> bool:
        """驗證日誌配置"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        valid_rotation_types = ["time", "size"]
        valid_intervals = ["midnight", "H", "D", "W0", "W1", "W2", "W3", "W4", "W5", "W6"]

        if self.level.upper() not in valid_levels:
            return False
        if self.rotation_type not in valid_rotation_types:
            return False
        if self.rotation_type == "time" and self.rotation_interval not in valid_intervals:
            return False
        if self.backup_count < 1:
            return False

        return True


@dataclass
class ServerConfig:
    """MCP 伺服器配置"""
    host: str = "0.0.0.0"
    port: int = 8000
    transport: str = "sse"
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    max_request_size: int = 10 * 1024 * 1024  # 10MB

    def validate(self) -> bool:
        """驗證伺服器配置"""
        if not (1 <= self.port <= 65535):
            return False
        if self.transport not in ["sse", "stdio"]:
            return False
        return True


@dataclass
class GraphitiConfig:
    """完整的 Graphiti 配置"""
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    embedder: OllamaEmbedderConfig = field(default_factory=OllamaEmbedderConfig)
    neo4j: Neo4jConfig = field(default_factory=Neo4jConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    server: ServerConfig = field(default_factory=ServerConfig)

    # Graphiti 特定設定
    search_limit: int = 20
    enable_deduplication: bool = True
    pydantic_validation_fixes: bool = True
    cosine_similarity_threshold: float = 0.8

    @classmethod
    def from_env(cls) -> "GraphitiConfig":
        """從環境變數載入配置"""
        config = cls()

        # Ollama 配置
        config.ollama.model = os.getenv("OLLAMA_MODEL", config.ollama.model)
        config.ollama.base_url = os.getenv("OLLAMA_BASE_URL", config.ollama.base_url)
        config.ollama.temperature = float(os.getenv("OLLAMA_TEMPERATURE", config.ollama.temperature))

        # 嵌入器配置
        config.embedder.model = os.getenv("OLLAMA_EMBEDDING_MODEL", config.embedder.model)
        config.embedder.base_url = os.getenv("OLLAMA_EMBEDDING_BASE_URL", config.embedder.base_url)
        config.embedder.dimensions = int(os.getenv("OLLAMA_EMBEDDING_DIMENSIONS", config.embedder.dimensions))

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

        # Graphiti 特定設定
        if os.getenv("SEARCH_LIMIT"):
            config.search_limit = int(os.getenv("SEARCH_LIMIT"))
        if os.getenv("ENABLE_DEDUPLICATION"):
            config.enable_deduplication = os.getenv("ENABLE_DEDUPLICATION").lower() == "true"
        if os.getenv("PYDANTIC_VALIDATION_FIXES"):
            config.pydantic_validation_fixes = os.getenv("PYDANTIC_VALIDATION_FIXES").lower() == "true"
        if os.getenv("COSINE_SIMILARITY_THRESHOLD"):
            config.cosine_similarity_threshold = float(os.getenv("COSINE_SIMILARITY_THRESHOLD"))

        return config

    @classmethod
    def from_file(cls, config_path: str) -> "GraphitiConfig":
        """從配置檔案載入配置"""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"配置檔案不存在: {config_path}，使用預設配置")
            return cls()

        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            config = cls()

            # 載入各個配置區塊
            if "ollama" in config_data:
                for key, value in config_data["ollama"].items():
                    if hasattr(config.ollama, key):
                        setattr(config.ollama, key, value)

            if "embedder" in config_data:
                for key, value in config_data["embedder"].items():
                    if hasattr(config.embedder, key):
                        setattr(config.embedder, key, value)

            if "neo4j" in config_data:
                for key, value in config_data["neo4j"].items():
                    if hasattr(config.neo4j, key):
                        setattr(config.neo4j, key, value)

            if "logging" in config_data:
                for key, value in config_data["logging"].items():
                    if hasattr(config.logging, key):
                        setattr(config.logging, key, value)

            if "server" in config_data:
                for key, value in config_data["server"].items():
                    if hasattr(config.server, key):
                        setattr(config.server, key, value)

            # 載入 Graphiti 特定設定
            for key in ["search_limit", "enable_deduplication", "pydantic_validation_fixes", "cosine_similarity_threshold"]:
                if key in config_data:
                    setattr(config, key, config_data[key])

            logger.info(f"成功載入配置檔案: {config_path}")
            return config

        except Exception as e:
            logger.error(f"載入配置檔案失敗: {e}")
            return cls()

    def validate(self) -> bool:
        """驗證所有配置"""
        validations = [
            ("Ollama", self.ollama.validate()),
            ("Embedder", self.embedder.validate()),
            ("Neo4j", self.neo4j.validate()),
            ("Logging", self.logging.validate()),
            ("Server", self.server.validate())
        ]

        all_valid = True
        for name, is_valid in validations:
            if not is_valid:
                logger.error(f"配置驗證失敗: {name}")
                all_valid = False

        return all_valid

    def save_to_file(self, config_path: str) -> bool:
        """將配置保存到檔案"""
        try:
            config_data = {
                "ollama": {
                    "model": self.ollama.model,
                    "base_url": self.ollama.base_url,
                    "temperature": self.ollama.temperature,
                    "max_tokens": self.ollama.max_tokens,
                    "timeout": self.ollama.timeout
                },
                "embedder": {
                    "model": self.embedder.model,
                    "base_url": self.embedder.base_url,
                    "dimensions": self.embedder.dimensions,
                    "batch_size": self.embedder.batch_size,
                    "timeout": self.embedder.timeout
                },
                "neo4j": {
                    "uri": self.neo4j.uri,
                    "user": self.neo4j.user,
                    "password": "***",  # 不保存密碼
                    "database": self.neo4j.database,
                    "max_connection_lifetime": self.neo4j.max_connection_lifetime,
                    "max_connection_pool_size": self.neo4j.max_connection_pool_size,
                    "connection_timeout": self.neo4j.connection_timeout
                },
                "logging": {
                    "level": self.logging.level,
                    "format": self.logging.format,
                    "file_path": self.logging.file_path,
                    "max_file_size": self.logging.max_file_size,
                    "backup_count": self.logging.backup_count,
                    "console_output": self.logging.console_output
                },
                "server": {
                    "host": self.server.host,
                    "port": self.server.port,
                    "transport": self.server.transport,
                    "cors_origins": self.server.cors_origins,
                    "max_request_size": self.server.max_request_size
                },
                "search_limit": self.search_limit,
                "enable_deduplication": self.enable_deduplication,
                "pydantic_validation_fixes": self.pydantic_validation_fixes,
                "cosine_similarity_threshold": self.cosine_similarity_threshold
            }

            config_file = Path(config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"配置已保存至: {config_path}")
            return True

        except Exception as e:
            logger.error(f"保存配置檔案失敗: {e}")
            return False

    def get_summary(self) -> Dict[str, Any]:
        """獲取配置摘要（用於日誌記錄）"""
        return {
            "ollama_model": self.ollama.model,
            "embedder_model": self.embedder.model,
            "embedder_dimensions": self.embedder.dimensions,
            "neo4j_uri": self.neo4j.uri,
            "neo4j_database": self.neo4j.database,
            "server_port": self.server.port,
            "log_level": self.logging.level,
            "search_limit": self.search_limit,
            "deduplication_enabled": self.enable_deduplication,
            "pydantic_fixes_enabled": self.pydantic_validation_fixes
        }


def load_config(config_path: Optional[str] = None) -> GraphitiConfig:
    """載入配置的便利函數"""
    if config_path and Path(config_path).exists():
        config = GraphitiConfig.from_file(config_path)
    else:
        config = GraphitiConfig.from_env()

    if not config.validate():
        logger.warning("配置驗證失敗，某些功能可能無法正常運作")

    return config


# 預設配置實例
default_config = GraphitiConfig()