#!/usr/bin/env python3
"""
Graphiti MCP Server Logging Setup
提供結構化的日誌記錄和錯誤追蹤系統
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from .config import LoggingConfig


class GraphitiFormatter(logging.Formatter):
    """自定義日誌格式器"""

    def __init__(self):
        super().__init__()
        self.default_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.error_format = "%(asctime)s - %(name)s - %(levelname)s - [%(pathname)s:%(lineno)d] - %(message)s"

    def format(self, record):
        """根據日誌級別選擇格式"""
        if record.levelno >= logging.ERROR:
            formatter = logging.Formatter(self.error_format)
        else:
            formatter = logging.Formatter(self.default_format)
        return formatter.format(record)


class GraphitiLogger:
    """Graphiti 專用日誌管理器"""

    def __init__(self, config: LoggingConfig):
        self.config = config
        self._setup_logging()

    def _setup_logging(self):
        """設置日誌系統"""
        # 獲取根日誌記錄器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.level.upper()))

        # 清除現有處理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # 創建格式器
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

    def _setup_file_handler(self, formatter):
        """設置檔案日誌處理器（支援時間和大小輪轉）"""
        try:
            log_path = Path(self.config.file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # 根據配置選擇輪轉方式
            if self.config.rotation_type == "time":
                # 時間輪轉處理器（每天一個新檔案）
                file_handler = logging.handlers.TimedRotatingFileHandler(
                    filename=log_path,
                    when=self.config.rotation_interval,  # 輪轉時間點
                    interval=1,                          # 間隔
                    backupCount=self.config.backup_count,
                    encoding='utf-8',
                    delay=False,
                    utc=False
                )

                # 設定輪轉檔案的命名格式
                if self.config.rotation_interval == "midnight":
                    file_handler.suffix = "_%Y-%m-%d.log"
                elif self.config.rotation_interval == "H":
                    file_handler.suffix = "_%Y-%m-%d_%H.log"
                else:
                    file_handler.suffix = "_%Y-%m-%d.log"

                rotation_info = f"時間輪轉: {self.config.rotation_interval}，保留 {self.config.backup_count} 個檔案"

            else:
                # 大小輪轉處理器（檔案大小達到限制時輪轉）
                file_handler = logging.handlers.RotatingFileHandler(
                    filename=log_path,
                    maxBytes=self.config.max_file_size,
                    backupCount=self.config.backup_count,
                    encoding='utf-8'
                )

                size_mb = self.config.max_file_size / (1024 * 1024)
                rotation_info = f"大小輪轉: {size_mb:.1f}MB，保留 {self.config.backup_count} 個檔案"

            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, self.config.level.upper()))

            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)

            # 顯示日誌檔案資訊
            if self.config.rotation_type == "time":
                today = datetime.now().strftime("%Y-%m-%d")
                log_dir = log_path.parent
                base_name = log_path.stem
                extension = log_path.suffix
                current_log_file = log_dir / f"{base_name}_{today}{extension}"
                logging.info(f"日誌檔案設置完成: {current_log_file}")
            else:
                logging.info(f"日誌檔案設置完成: {log_path}")

            logging.info(f"日誌輪轉設定: {rotation_info}")

        except Exception as e:
            logging.error(f"設置檔案日誌處理器失敗: {e}")

    def _setup_module_loggers(self):
        """設置特定模組的日誌級別"""
        # 抑制過於詳細的第三方庫日誌
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("neo4j").setLevel(logging.INFO)
        logging.getLogger("asyncio").setLevel(logging.WARNING)

        # 設置 Graphiti 相關模組的日誌級別
        logging.getLogger("graphiti_core").setLevel(logging.INFO)
        logging.getLogger("ollama_embedder").setLevel(logging.INFO)
        logging.getLogger("ollama_graphiti_client").setLevel(logging.INFO)

    def get_logger(self, name: str) -> logging.Logger:
        """獲取指定名稱的日誌記錄器"""
        return logging.getLogger(name)


def setup_logging(config: LoggingConfig) -> GraphitiLogger:
    """設置日誌系統的便利函數"""
    return GraphitiLogger(config)


# 日誌記錄工具函數
def log_system_info():
    """記錄系統信息"""
    logger = logging.getLogger("system")
    logger.info("=" * 50)
    logger.info("Graphiti MCP Server 啟動")
    logger.info(f"啟動時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 50)


def log_config_summary(config_summary: dict):
    """記錄配置摘要"""
    logger = logging.getLogger("config")
    logger.info("系統配置摘要:")
    for key, value in config_summary.items():
        logger.info(f"  {key}: {value}")


def log_operation_start(operation: str, **kwargs):
    """記錄操作開始"""
    logger = logging.getLogger("operations")
    details = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.info(f"開始操作: {operation}" + (f" | {details}" if details else ""))


def log_operation_success(operation: str, duration: Optional[float] = None, **kwargs):
    """記錄操作成功"""
    logger = logging.getLogger("operations")
    details = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    duration_str = f" | 耗時: {duration:.2f}s" if duration else ""
    logger.info(f"操作成功: {operation}{duration_str}" + (f" | {details}" if details else ""))


def log_operation_error(operation: str, error: Exception, **kwargs):
    """記錄操作錯誤"""
    logger = logging.getLogger("operations")
    details = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    logger.error(f"操作失敗: {operation} | 錯誤: {error}" + (f" | {details}" if details else ""))


def log_cosine_similarity_debug(query_vector_info: dict, search_results: dict):
    """記錄 Cosine Similarity 調試信息"""
    logger = logging.getLogger("cosine_debug")
    logger.debug("Cosine Similarity 調試信息:")
    logger.debug(f"  查詢向量: {query_vector_info}")
    logger.debug(f"  搜索結果: {search_results}")


def log_pydantic_validation_fix(field_name: str, old_value: any, new_value: any):
    """記錄 Pydantic 驗證修復"""
    logger = logging.getLogger("pydantic_fixes")
    logger.info(f"Pydantic 驗證修復: {field_name} | {old_value} -> {new_value}")


def log_memory_operation(operation: str, memory_id: str, details: dict):
    """記錄記憶操作"""
    logger = logging.getLogger("memory")
    logger.info(f"記憶操作: {operation} | ID: {memory_id} | 詳情: {details}")


# 性能監控相關
class PerformanceLogger:
    """性能監控日誌記錄器"""

    def __init__(self):
        self.logger = logging.getLogger("performance")

    def log_embedding_performance(self, text_count: int, duration: float, model: str):
        """記錄嵌入性能"""
        avg_time = duration / text_count if text_count > 0 else 0
        self.logger.info(
            f"嵌入性能 | 模型: {model} | 文本數: {text_count} | "
            f"總耗時: {duration:.2f}s | 平均: {avg_time:.3f}s/文本"
        )

    def log_neo4j_query_performance(self, query_type: str, duration: float, result_count: int):
        """記錄 Neo4j 查詢性能"""
        self.logger.info(
            f"Neo4j 查詢性能 | 類型: {query_type} | 耗時: {duration:.2f}s | 結果數: {result_count}"
        )

    def log_memory_add_performance(self, memory_size: int, duration: float, success: bool):
        """記錄記憶添加性能"""
        status = "成功" if success else "失敗"
        self.logger.info(
            f"記憶添加性能 | 大小: {memory_size} 字符 | 耗時: {duration:.2f}s | 狀態: {status}"
        )


# 創建全局性能監控實例
performance_logger = PerformanceLogger()