#!/usr/bin/env python3
"""
Graphiti MCP Server 日誌設置模組
=================================

提供結構化的日誌記錄和錯誤追蹤系統。

此模組提供統一的日誌管理，支援多種輸出目標（控制台、檔案）
和多種輪轉策略（時間輪轉、大小輪轉）。

主要功能：
    - 自訂日誌格式器（錯誤級別顯示更多資訊）
    - 時間或大小輪轉的檔案日誌
    - 第三方庫日誌級別控制
    - 操作日誌記錄工具函數
    - 性能監控日誌記錄器

使用範例：
    >>> from src.logging_setup import setup_logging, log_operation_start
    >>> from src.config import LoggingConfig
    >>>
    >>> config = LoggingConfig(level="INFO", file_path="logs/app.log")
    >>> logger = setup_logging(config)
    >>> log_operation_start("search_nodes", query="TypeScript")
"""

import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .config import LoggingConfig


class GraphitiFormatter(logging.Formatter):
    """
    自訂日誌格式器。

    根據日誌級別選擇不同的格式：
    - 錯誤級別（ERROR、CRITICAL）：包含檔案路徑和行號
    - 其他級別：使用標準格式
    """

    DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ERROR_FORMAT = (
        "%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s"
    )

    def format(self, record: logging.LogRecord) -> str:
        """
        根據日誌級別格式化記錄。

        Args:
            record: 日誌記錄

        Returns:
            str: 格式化後的日誌字串
        """
        if record.levelno >= logging.ERROR:
            formatter = logging.Formatter(self.ERROR_FORMAT)
        else:
            formatter = logging.Formatter(self.DEFAULT_FORMAT)

        return formatter.format(record)


class GraphitiLogger:
    """
    Graphiti 專用日誌管理器。

    負責初始化和配置日誌系統，包括控制台輸出、
    檔案輸出和第三方庫日誌級別控制。

    Attributes:
        config: 日誌配置物件
    """

    def __init__(self, config: LoggingConfig):
        """
        初始化日誌管理器。

        Args:
            config: 日誌配置物件
        """
        self.config = config
        self._setup_logging()

    def _setup_logging(self) -> None:
        """設置日誌系統。"""
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.level.upper()))

        # 清除現有處理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        formatter = GraphitiFormatter()

        # 控制台輸出處理器
        if self.config.console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(getattr(logging, self.config.level.upper()))
            root_logger.addHandler(console_handler)

        # 檔案輸出處理器
        if self.config.file_path:
            self._setup_file_handler(formatter)

        # 設置特定模組的日誌級別
        self._setup_module_loggers()

    def _setup_file_handler(self, formatter: logging.Formatter) -> None:
        """
        設置檔案日誌處理器。

        支援時間輪轉和大小輪轉兩種策略。

        Args:
            formatter: 日誌格式器
        """
        try:
            log_path = Path(self.config.file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            if self.config.rotation_type == "time":
                file_handler = self._create_time_rotating_handler(log_path)
                rotation_info = (
                    f"時間輪轉: {self.config.rotation_interval}，"
                    f"保留 {self.config.backup_count} 個檔案"
                )
            else:
                file_handler = self._create_size_rotating_handler(log_path)
                size_mb = self.config.max_file_size / (1024 * 1024)
                rotation_info = (
                    f"大小輪轉: {size_mb:.1f}MB，"
                    f"保留 {self.config.backup_count} 個檔案"
                )

            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, self.config.level.upper()))

            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)

            logging.info(f"日誌檔案設置完成: {log_path}")
            logging.info(f"日誌輪轉設定: {rotation_info}")

        except Exception as e:
            logging.error(f"設置檔案日誌處理器失敗: {e}")

    def _create_time_rotating_handler(
        self, log_path: Path
    ) -> logging.handlers.TimedRotatingFileHandler:
        """建立時間輪轉處理器。

        注意：不在初始檔名中加入日期，讓 TimedRotatingFileHandler 自行管理
        輪轉後的檔案命名，避免產生雙日期格式（如 app_2026-02-28_2026-02-28.log）。
        """
        handler = logging.handlers.TimedRotatingFileHandler(
            filename=log_path,
            when=self.config.rotation_interval,
            interval=1,
            backupCount=self.config.backup_count,
            encoding="utf-8",
            delay=False,
            utc=False,
        )

        # 設定輪轉檔案的命名格式（由 handler 自動附加到基礎檔名）
        suffix_map = {
            "midnight": "_%Y-%m-%d",
            "H": "_%Y-%m-%d_%H",
        }
        handler.suffix = suffix_map.get(self.config.rotation_interval, "_%Y-%m-%d")

        return handler

    def _create_size_rotating_handler(
        self, log_path: Path
    ) -> logging.handlers.RotatingFileHandler:
        """建立大小輪轉處理器。"""
        return logging.handlers.RotatingFileHandler(
            filename=log_path,
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count,
            encoding="utf-8",
        )

    def _setup_module_loggers(self) -> None:
        """設置特定模組的日誌級別（從配置讀取）。"""
        # 從配置載入第三方日誌級別
        for logger_name, level_str in self.config.third_party_levels.items():
            level = getattr(logging, level_str.upper(), logging.WARNING)
            logging.getLogger(logger_name).setLevel(level)

        # Graphiti 相關模組
        graphiti_loggers = [
            "graphiti_core",
            "ollama_embedder",
            "ollama_graphiti_client",
        ]

        for logger_name in graphiti_loggers:
            logging.getLogger(logger_name).setLevel(logging.INFO)

    def get_logger(self, name: str) -> logging.Logger:
        """
        獲取指定名稱的日誌記錄器。

        Args:
            name: 日誌記錄器名稱

        Returns:
            logging.Logger: 日誌記錄器實例
        """
        return logging.getLogger(name)


def setup_logging(config: LoggingConfig) -> GraphitiLogger:
    """
    設置日誌系統的便利函數。

    Args:
        config: 日誌配置物件

    Returns:
        GraphitiLogger: 日誌管理器實例
    """
    return GraphitiLogger(config)


# =============================================================================
# 日誌記錄工具函數
# =============================================================================


def log_system_info() -> None:
    """記錄系統啟動資訊。"""
    logger = logging.getLogger("system")
    logger.info("=" * 50)
    logger.info("Graphiti MCP Server 啟動")
    logger.info(f"啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)


def log_config_summary(config_summary: dict) -> None:
    """
    記錄配置摘要。

    Args:
        config_summary: 配置摘要字典
    """
    logger = logging.getLogger("config")
    logger.info("系統配置摘要:")
    for key, value in config_summary.items():
        logger.info(f"  {key}: {value}")


def log_operation_start(operation: str, **kwargs: Any) -> None:
    """
    記錄操作開始。

    Args:
        operation: 操作名稱
        **kwargs: 額外的詳情
    """
    logger = logging.getLogger("operations")
    details = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    message = f"開始操作: {operation}"
    if details:
        message += f" | {details}"
    logger.info(message)


def log_operation_success(
    operation: str, duration: Optional[float] = None, **kwargs: Any
) -> None:
    """
    記錄操作成功。

    Args:
        operation: 操作名稱
        duration: 操作耗時（秒）
        **kwargs: 額外的詳情
    """
    logger = logging.getLogger("operations")
    details = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    duration_str = f" | 耗時: {duration:.2f}s" if duration else ""
    message = f"操作成功: {operation}{duration_str}"
    if details:
        message += f" | {details}"
    logger.info(message)


def log_operation_error(operation: str, error: Exception, **kwargs: Any) -> None:
    """
    記錄操作錯誤。

    Args:
        operation: 操作名稱
        error: 錯誤例外
        **kwargs: 額外的詳情
    """
    logger = logging.getLogger("operations")
    details = " | ".join(f"{k}={v}" for k, v in kwargs.items())
    message = f"操作失敗: {operation} | 錯誤: {error}"
    if details:
        message += f" | {details}"
    logger.error(message)


def log_cosine_similarity_debug(query_vector_info: dict, search_results: dict) -> None:
    """
    記錄 Cosine Similarity 調試資訊。

    Args:
        query_vector_info: 查詢向量資訊
        search_results: 搜索結果資訊
    """
    logger = logging.getLogger("cosine_debug")
    logger.debug("Cosine Similarity 調試資訊:")
    logger.debug(f"  查詢向量: {query_vector_info}")
    logger.debug(f"  搜索結果: {search_results}")


def log_pydantic_validation_fix(
    field_name: str, old_value: Any, new_value: Any
) -> None:
    """
    記錄 Pydantic 驗證修復。

    Args:
        field_name: 欄位名稱
        old_value: 原始值
        new_value: 修復後的值
    """
    logger = logging.getLogger("pydantic_fixes")
    logger.info(f"Pydantic 驗證修復: {field_name} | {old_value} -> {new_value}")


def log_memory_operation(operation: str, memory_id: str, details: dict) -> None:
    """
    記錄記憶操作。

    Args:
        operation: 操作類型
        memory_id: 記憶 ID
        details: 操作詳情
    """
    logger = logging.getLogger("memory")
    logger.info(f"記憶操作: {operation} | ID: {memory_id} | 詳情: {details}")


# =============================================================================
# 性能監控
# =============================================================================


class PerformanceLogger:
    """
    性能監控日誌記錄器。

    專門用於記錄各類操作的性能指標。
    """

    def __init__(self):
        """初始化性能監控記錄器。"""
        self.logger = logging.getLogger("performance")

    def log_embedding_performance(
        self, text_count: int, duration: float, model: str
    ) -> None:
        """
        記錄嵌入性能。

        Args:
            text_count: 處理的文本數量
            duration: 總耗時（秒）
            model: 使用的模型名稱
        """
        avg_time = duration / text_count if text_count > 0 else 0
        self.logger.info(
            f"嵌入性能 | 模型: {model} | 文本數: {text_count} | "
            f"總耗時: {duration:.2f}s | 平均: {avg_time:.3f}s/文本"
        )

    def log_neo4j_query_performance(
        self, query_type: str, duration: float, result_count: int
    ) -> None:
        """
        記錄 Neo4j 查詢性能。

        Args:
            query_type: 查詢類型
            duration: 耗時（秒）
            result_count: 結果數量
        """
        self.logger.info(
            f"Neo4j 查詢性能 | 類型: {query_type} | 耗時: {duration:.2f}s | "
            f"結果數: {result_count}"
        )

    def log_memory_add_performance(
        self, memory_size: int, duration: float, success: bool
    ) -> None:
        """
        記錄記憶添加性能。

        Args:
            memory_size: 記憶大小（字符數）
            duration: 耗時（秒）
            success: 是否成功
        """
        status = "成功" if success else "失敗"
        self.logger.info(
            f"記憶添加性能 | 大小: {memory_size} 字符 | 耗時: {duration:.2f}s | "
            f"狀態: {status}"
        )


# 全域性能監控實例
performance_logger = PerformanceLogger()
