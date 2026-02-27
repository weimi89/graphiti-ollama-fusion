#!/usr/bin/env python3
"""
Graphiti MCP Server 異常處理模組
=================================

提供結構化的異常類別和錯誤處理工具。

此模組定義了 Graphiti MCP Server 專用的異常階層，
支援錯誤分類、詳細資訊追蹤和 JSON 序列化。

異常階層：
    GraphitiMCPError（基礎類別）
    ├── ConfigurationError   - 配置錯誤
    ├── ConnectionError      - 連接錯誤
    ├── OllamaError          - Ollama 服務錯誤
    ├── EmbeddingError       - 嵌入向量錯誤
    ├── CosineSimilarityError - 餘弦相似度計算錯誤
    ├── Neo4jError           - Neo4j 資料庫錯誤
    ├── GraphitiAPIError     - Graphiti API 錯誤
    ├── ValidationError      - 資料驗證錯誤
    │   └── PydanticValidationError - Pydantic 驗證錯誤
    ├── MemoryError          - 記憶處理錯誤
    └── SearchError          - 搜索錯誤
"""

import traceback
from typing import Any, Dict, Optional


class GraphitiMCPError(Exception):
    """
    Graphiti MCP 基礎異常類別。

    所有 Graphiti MCP 相關的異常都繼承自此類別，
    提供統一的錯誤資訊格式和序列化功能。

    Attributes:
        message: 錯誤訊息
        error_code: 錯誤代碼
        details: 額外的錯誤詳情
        cause: 原始異常（如有）
        traceback_str: 堆疊追蹤字串
    """

    def __init__(
        self,
        message: str,
        error_code: str = "GRAPHITI_ERROR",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
    ):
        """
        初始化異常。

        Args:
            message: 錯誤訊息
            error_code: 錯誤代碼
            details: 額外的錯誤詳情
            cause: 原始異常
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        self.traceback_str = traceback.format_exc() if cause else None

    def to_dict(self) -> Dict[str, Any]:
        """
        轉換為字典格式（用於 JSON 響應）。

        Returns:
            dict: 包含錯誤資訊的字典
        """
        error_dict = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }

        if self.cause:
            error_dict["cause"] = str(self.cause)
            error_dict["cause_type"] = type(self.cause).__name__

        if self.traceback_str:
            # 限制 traceback 長度，避免回應過大
            tb = self.traceback_str
            error_dict["traceback"] = tb[:1000] + "..." if len(tb) > 1000 else tb

        return error_dict

    def __str__(self) -> str:
        """返回格式化的錯誤字串。"""
        parts = [f"[{self.error_code}] {self.message}"]

        if self.details:
            parts.append(f"Details: {self.details}")

        if self.cause:
            parts.append(f"Caused by: {self.cause}")

        return " | ".join(parts)


# =============================================================================
# 特定異常類別
# =============================================================================


class ConfigurationError(GraphitiMCPError):
    """
    配置相關錯誤。

    當配置檔案無效、缺少必要設定或設定值不正確時拋出。
    """

    def __init__(
        self,
        message: str,
        config_field: Optional[str] = None,
        **kwargs,
    ):
        details = {"config_field": config_field} if config_field else {}
        super().__init__(message, error_code="CONFIG_ERROR", details=details, **kwargs)


class ConnectionError(GraphitiMCPError):
    """
    連接相關錯誤。

    當無法建立與外部服務的連接時拋出。
    """

    def __init__(
        self,
        message: str,
        service: str,
        endpoint: Optional[str] = None,
        **kwargs,
    ):
        details = {"service": service, "endpoint": endpoint}
        super().__init__(message, error_code="CONNECTION_ERROR", details=details, **kwargs)


class OllamaError(GraphitiMCPError):
    """
    Ollama 服務相關錯誤。

    當 Ollama API 請求失敗或模型不可用時拋出。
    """

    def __init__(
        self,
        message: str,
        model: Optional[str] = None,
        operation: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        details.update({"model": model, "operation": operation})
        super().__init__(message, error_code="OLLAMA_ERROR", details=details, **kwargs)


class EmbeddingError(GraphitiMCPError):
    """
    嵌入向量相關錯誤。

    當嵌入向量生成失敗或向量格式不正確時拋出。
    """

    def __init__(
        self,
        message: str,
        text_length: Optional[int] = None,
        vector_dim: Optional[int] = None,
        **kwargs,
    ):
        details = {"text_length": text_length, "vector_dim": vector_dim}
        super().__init__(message, error_code="EMBEDDING_ERROR", details=details, **kwargs)


class CosineSimilarityError(GraphitiMCPError):
    """
    Cosine Similarity 計算錯誤。

    當向量格式不正確導致相似度計算失敗時拋出。
    """

    def __init__(
        self,
        message: str,
        search_vector_type: Optional[str] = None,
        search_vector_shape: Optional[str] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        details.update(
            {
                "search_vector_type": search_vector_type,
                "search_vector_shape": search_vector_shape,
            }
        )
        super().__init__(
            message, error_code="COSINE_SIMILARITY_ERROR", details=details, **kwargs
        )


class Neo4jError(GraphitiMCPError):
    """
    Neo4j 資料庫相關錯誤。

    當資料庫連接失敗或查詢執行錯誤時拋出。
    """

    def __init__(
        self,
        message: str,
        query: Optional[str] = None,
        parameters: Optional[Dict] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        details.update({"query": query, "parameters": parameters})
        super().__init__(message, error_code="NEO4J_ERROR", details=details, **kwargs)


class GraphitiAPIError(GraphitiMCPError):
    """
    Graphiti API 相關錯誤。

    當 Graphiti 核心 API 呼叫失敗時拋出。
    """

    def __init__(
        self,
        message: str,
        operation: str,
        episode_id: Optional[str] = None,
        **kwargs,
    ):
        details = {"operation": operation, "episode_id": episode_id}
        super().__init__(message, error_code="GRAPHITI_API_ERROR", details=details, **kwargs)


class ValidationError(GraphitiMCPError):
    """
    資料驗證錯誤。

    當輸入資料不符合預期格式時拋出。
    """

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs,
    ):
        details = {
            "field": field,
            "value": str(value) if value is not None else None,
        }
        super().__init__(message, error_code="VALIDATION_ERROR", details=details, **kwargs)


class PydanticValidationError(ValidationError):
    """
    Pydantic 驗證錯誤。

    當 Pydantic 模型驗證失敗時拋出。
    """

    def __init__(
        self,
        message: str,
        validation_errors: Optional[list] = None,
        **kwargs,
    ):
        super().__init__(message, field="pydantic_validation", **kwargs)
        self.error_code = "PYDANTIC_VALIDATION_ERROR"

        if validation_errors:
            self.details["validation_errors"] = validation_errors


class MemoryError(GraphitiMCPError):
    """
    記憶處理相關錯誤。

    當記憶添加、檢索或刪除操作失敗時拋出。
    """

    def __init__(
        self,
        message: str,
        memory_type: str,
        memory_id: Optional[str] = None,
        **kwargs,
    ):
        details = {"memory_type": memory_type, "memory_id": memory_id}
        super().__init__(message, error_code="MEMORY_ERROR", details=details, **kwargs)


class SearchError(GraphitiMCPError):
    """
    搜索相關錯誤。

    當搜索操作失敗時拋出。
    """

    def __init__(
        self,
        message: str,
        search_type: str,
        search_query: Optional[str] = None,
        **kwargs,
    ):
        details = {"search_type": search_type, "search_query": search_query}
        super().__init__(message, error_code="SEARCH_ERROR", details=details, **kwargs)


# =============================================================================
# 異常處理工具函數
# =============================================================================


def handle_exception(exc: Exception, context: str = "") -> GraphitiMCPError:
    """
    將一般異常轉換為 Graphiti 異常。

    優先透過異常類型分類，其次透過異常訊息內容分類。

    Args:
        exc: 原始異常
        context: 額外的上下文資訊

    Returns:
        GraphitiMCPError: 對應類型的 Graphiti 異常
    """
    if isinstance(exc, GraphitiMCPError):
        return exc

    # 1. 優先透過異常類型分類
    exc_type_name = type(exc).__module__ + "." + type(exc).__qualname__

    # Neo4j 驅動異常
    if "neo4j" in exc_type_name.lower():
        return Neo4jError(f"Neo4j 操作失敗: {exc}", cause=exc)

    # aiohttp / 連接異常（使用 builtins.ConnectionError 判斷）
    import builtins
    if isinstance(exc, (builtins.ConnectionError, OSError)):
        return OllamaError(f"連接錯誤: {exc}", cause=exc)

    # Pydantic 驗證異常
    if "pydantic" in exc_type_name.lower() or "ValidationError" in type(exc).__name__:
        return PydanticValidationError(f"驗證錯誤: {exc}", cause=exc)

    # asyncio 超時
    if isinstance(exc, TimeoutError):
        return OllamaError(f"操作超時: {exc}", cause=exc)

    # 2. 回退到訊息文字分類（僅在類型無法判定時）
    exc_str = str(exc).lower()

    if "neo4j" in exc_str or "bolt" in exc_str:
        return Neo4jError(f"Neo4j 操作失敗: {exc}", cause=exc)

    if "ollama" in exc_str:
        return OllamaError(f"Ollama 服務錯誤: {exc}", cause=exc)

    if "cosine" in exc_str or "similarity" in exc_str:
        return CosineSimilarityError(f"Cosine Similarity 錯誤: {exc}", cause=exc)

    # 注意：只有明確的嵌入錯誤場景才歸類，避免 "embedding 已完成" 被誤判
    if ("embed" in exc_str and "error" in exc_str) or "vector" in exc_str:
        return EmbeddingError(f"嵌入向量錯誤: {exc}", cause=exc)

    # 預設處理
    message = f"{context}: {exc}" if context else str(exc)
    return GraphitiMCPError(message, error_code="UNKNOWN_ERROR", cause=exc)


def create_error_response(exc: Exception, context: str = "") -> Dict[str, Any]:
    """
    建立標準化的錯誤響應。

    Args:
        exc: 異常物件
        context: 額外的上下文資訊

    Returns:
        dict: 標準化的錯誤響應字典
    """
    graphiti_error = handle_exception(exc, context)
    return graphiti_error.to_dict()


# =============================================================================
# 預定義的常見錯誤
# =============================================================================


class CommonErrors:
    """
    常見錯誤的工廠類別。

    提供建立常見錯誤的便利方法。
    """

    @staticmethod
    def ollama_connection_failed(base_url: str) -> OllamaError:
        """建立 Ollama 連接失敗錯誤。"""
        return OllamaError(
            "無法連接到 Ollama 服務",
            details={"base_url": base_url, "suggestion": "請確認 Ollama 服務正在運行"},
        )

    @staticmethod
    def neo4j_connection_failed(uri: str) -> Neo4jError:
        """建立 Neo4j 連接失敗錯誤。"""
        return Neo4jError(
            "無法連接到 Neo4j 資料庫",
            details={"uri": uri, "suggestion": "請確認 Neo4j 服務正在運行並檢查連接參數"},
        )

    @staticmethod
    def model_not_found(model_name: str) -> OllamaError:
        """建立模型未找到錯誤。"""
        return OllamaError(
            f"模型 '{model_name}' 未找到",
            model=model_name,
            details={"suggestion": f"請使用 'ollama pull {model_name}' 下載模型"},
        )

    @staticmethod
    def invalid_vector_format(vector_type: str, expected: str) -> CosineSimilarityError:
        """建立無效向量格式錯誤。"""
        return CosineSimilarityError(
            "無效的向量格式",
            search_vector_type=vector_type,
            details={"expected": expected, "suggestion": "檢查嵌入器接口返回的向量格式"},
        )

    @staticmethod
    def pydantic_field_missing(field_name: str, model_class: str) -> PydanticValidationError:
        """建立 Pydantic 欄位缺失錯誤。"""
        return PydanticValidationError(
            f"必需欄位 '{field_name}' 缺失",
            details={
                "field": field_name,
                "model_class": model_class,
                "suggestion": "檢查數據結構或啟用自動修復功能",
            },
        )

    @staticmethod
    def operation_failed(operation: str, reason: str) -> GraphitiMCPError:
        """建立操作失敗錯誤。"""
        return GraphitiMCPError(
            f"操作 '{operation}' 失敗: {reason}",
            error_code="OPERATION_FAILED",
            details={
                "operation": operation,
                "reason": reason,
                "suggestion": "檢查操作參數或系統狀態",
            },
        )
