#!/usr/bin/env python3
"""
Graphiti MCP Server Exception Classes
提供結構化的異常處理和錯誤分類
"""

from typing import Optional, Dict, Any
import traceback


class GraphitiMCPError(Exception):
    """Graphiti MCP 基礎異常類"""

    def __init__(
        self,
        message: str,
        error_code: str = "GRAPHITI_ERROR",
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause
        self.traceback_str = traceback.format_exc() if cause else None

    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式（用於 JSON 響應）"""
        error_dict = {
            "error": True,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details
        }

        if self.cause:
            error_dict["cause"] = str(self.cause)
            error_dict["cause_type"] = type(self.cause).__name__

        if self.traceback_str:
            error_dict["traceback"] = self.traceback_str

        return error_dict

    def __str__(self):
        base = f"[{self.error_code}] {self.message}"
        if self.details:
            base += f" | Details: {self.details}"
        if self.cause:
            base += f" | Caused by: {self.cause}"
        return base


class ConfigurationError(GraphitiMCPError):
    """配置相關錯誤"""

    def __init__(self, message: str, config_field: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            error_code="CONFIG_ERROR",
            details={"config_field": config_field} if config_field else {},
            **kwargs
        )


class ConnectionError(GraphitiMCPError):
    """連接相關錯誤"""

    def __init__(self, message: str, service: str, endpoint: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            error_code="CONNECTION_ERROR",
            details={"service": service, "endpoint": endpoint},
            **kwargs
        )


class OllamaError(GraphitiMCPError):
    """Ollama 服務相關錯誤"""

    def __init__(self, message: str, model: Optional[str] = None, operation: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            error_code="OLLAMA_ERROR",
            details={"model": model, "operation": operation},
            **kwargs
        )


class EmbeddingError(GraphitiMCPError):
    """嵌入向量相關錯誤"""

    def __init__(self, message: str, text_length: Optional[int] = None, vector_dim: Optional[int] = None, **kwargs):
        super().__init__(
            message,
            error_code="EMBEDDING_ERROR",
            details={"text_length": text_length, "vector_dim": vector_dim},
            **kwargs
        )


class CosineSimilarityError(GraphitiMCPError):
    """Cosine Similarity 計算錯誤"""

    def __init__(
        self,
        message: str,
        search_vector_type: Optional[str] = None,
        search_vector_shape: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            error_code="COSINE_SIMILARITY_ERROR",
            details={
                "search_vector_type": search_vector_type,
                "search_vector_shape": search_vector_shape
            },
            **kwargs
        )


class Neo4jError(GraphitiMCPError):
    """Neo4j 資料庫相關錯誤"""

    def __init__(self, message: str, query: Optional[str] = None, parameters: Optional[Dict] = None, **kwargs):
        super().__init__(
            message,
            error_code="NEO4J_ERROR",
            details={"query": query, "parameters": parameters},
            **kwargs
        )


class GraphitiAPIError(GraphitiMCPError):
    """Graphiti API 相關錯誤"""

    def __init__(self, message: str, operation: str, episode_id: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            error_code="GRAPHITI_API_ERROR",
            details={"operation": operation, "episode_id": episode_id},
            **kwargs
        )


class ValidationError(GraphitiMCPError):
    """數據驗證錯誤"""

    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, **kwargs):
        super().__init__(
            message,
            error_code="VALIDATION_ERROR",
            details={"field": field, "value": str(value) if value is not None else None},
            **kwargs
        )


class PydanticValidationError(ValidationError):
    """Pydantic 驗證錯誤"""

    def __init__(self, message: str, validation_errors: Optional[list] = None, **kwargs):
        super().__init__(
            message,
            field="pydantic_validation",
            **kwargs
        )
        if validation_errors:
            self.details["validation_errors"] = validation_errors
        self.error_code = "PYDANTIC_VALIDATION_ERROR"


class MemoryError(GraphitiMCPError):
    """記憶處理相關錯誤"""

    def __init__(self, message: str, memory_type: str, memory_id: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            error_code="MEMORY_ERROR",
            details={"memory_type": memory_type, "memory_id": memory_id},
            **kwargs
        )


class SearchError(GraphitiMCPError):
    """搜索相關錯誤"""

    def __init__(self, message: str, search_type: str, search_query: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            error_code="SEARCH_ERROR",
            details={"search_type": search_type, "search_query": search_query},
            **kwargs
        )


# 異常處理工具函數
def handle_exception(exc: Exception, context: str = "") -> GraphitiMCPError:
    """將一般異常轉換為 Graphiti 異常"""
    if isinstance(exc, GraphitiMCPError):
        return exc

    # 根據異常類型進行分類
    if "neo4j" in str(exc).lower() or "bolt" in str(exc).lower():
        return Neo4jError(
            f"Neo4j 操作失敗: {str(exc)}",
            cause=exc
        )

    if "ollama" in str(exc).lower():
        return OllamaError(
            f"Ollama 服務錯誤: {str(exc)}",
            cause=exc
        )

    if "embed" in str(exc).lower() or "vector" in str(exc).lower():
        return EmbeddingError(
            f"嵌入向量錯誤: {str(exc)}",
            cause=exc
        )

    if "cosine" in str(exc).lower() or "similarity" in str(exc).lower():
        return CosineSimilarityError(
            f"Cosine Similarity 錯誤: {str(exc)}",
            cause=exc
        )

    if "validation" in str(exc).lower() or "pydantic" in str(exc).lower():
        return PydanticValidationError(
            f"驗證錯誤: {str(exc)}",
            cause=exc
        )

    # 預設處理
    return GraphitiMCPError(
        f"{context}: {str(exc)}" if context else str(exc),
        error_code="UNKNOWN_ERROR",
        cause=exc
    )


def create_error_response(exc: Exception, context: str = "") -> Dict[str, Any]:
    """創建標準化的錯誤響應"""
    graphiti_error = handle_exception(exc, context)
    return graphiti_error.to_dict()


# 預定義的常見錯誤
class CommonErrors:
    """常見錯誤的預定義類"""

    @staticmethod
    def ollama_connection_failed(base_url: str) -> OllamaError:
        return OllamaError(
            f"無法連接到 Ollama 服務",
            details={"base_url": base_url, "suggestion": "請確認 Ollama 服務正在運行"}
        )

    @staticmethod
    def neo4j_connection_failed(uri: str) -> Neo4jError:
        return Neo4jError(
            f"無法連接到 Neo4j 資料庫",
            details={"uri": uri, "suggestion": "請確認 Neo4j 服務正在運行並檢查連接參數"}
        )

    @staticmethod
    def model_not_found(model_name: str) -> OllamaError:
        return OllamaError(
            f"模型 '{model_name}' 未找到",
            model=model_name,
            details={"suggestion": f"請使用 'ollama pull {model_name}' 下載模型"}
        )

    @staticmethod
    def invalid_vector_format(vector_type: str, expected: str) -> CosineSimilarityError:
        return CosineSimilarityError(
            f"無效的向量格式",
            search_vector_type=vector_type,
            details={
                "expected": expected,
                "suggestion": "檢查嵌入器接口返回的向量格式"
            }
        )

    @staticmethod
    def pydantic_field_missing(field_name: str, model_class: str) -> PydanticValidationError:
        return PydanticValidationError(
            f"必需欄位 '{field_name}' 缺失",
            details={
                "field": field_name,
                "model_class": model_class,
                "suggestion": "檢查數據結構或啟用自動修復功能"
            }
        )