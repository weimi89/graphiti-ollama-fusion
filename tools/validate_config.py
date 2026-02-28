#!/usr/bin/env python3
"""
Graphiti MCP Server 配置驗證工具
================================

一鍵驗證配置檔 + 連線測試，快速診斷部署問題。

用法：
    uv run python tools/validate_config.py
    uv run python tools/validate_config.py --json
    uv run python tools/validate_config.py --skip-ollama
    uv run python tools/validate_config.py --skip-neo4j
    uv run python tools/validate_config.py --config config.json
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from src.config import load_config

logging.basicConfig(level=logging.WARNING)


class ValidationResult:
    """單項驗證結果。"""

    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.message = ""
        self.duration = 0.0
        self.details: dict = {}

    def to_dict(self) -> dict:
        d = {
            "name": self.name,
            "passed": self.passed,
            "message": self.message,
            "duration_ms": round(self.duration * 1000, 1),
        }
        if self.details:
            d["details"] = self.details
        return d


async def validate_config_file(config_path: str | None) -> ValidationResult:
    """驗證配置檔載入和格式。"""
    result = ValidationResult("配置驗證")
    start = time.time()
    try:
        config = load_config(config_path)
        valid = config.validate()
        result.duration = time.time() - start
        if valid:
            result.passed = True
            result.message = "配置載入並驗證成功"
            result.details = config.get_summary()
        else:
            result.message = "配置格式有誤，請檢查各欄位"
            result.details = config.get_summary()
    except Exception as e:
        result.duration = time.time() - start
        result.message = f"配置載入失敗: {e}"
    return result


async def validate_neo4j(config) -> ValidationResult:
    """測試 Neo4j 連線。"""
    result = ValidationResult("Neo4j 連線")
    start = time.time()
    try:
        from graphiti_core import Graphiti

        graphiti = Graphiti(
            uri=config.neo4j.uri,
            user=config.neo4j.user,
            password=config.neo4j.password,
        )

        records, _, _ = await graphiti.driver.execute_query("RETURN 1 AS ok")
        result.duration = time.time() - start
        if records and records[0]["ok"] == 1:
            result.passed = True
            result.message = f"連線成功 ({config.neo4j.uri})"
        else:
            result.message = "連線成功但回應異常"

        # 取得節點數作為額外資訊
        try:
            count_records, _, _ = await graphiti.driver.execute_query(
                "MATCH (n) RETURN count(n) AS total"
            )
            result.details["total_nodes"] = count_records[0]["total"] if count_records else 0
        except Exception:
            pass

        await graphiti.driver.close()
    except Exception as e:
        result.duration = time.time() - start
        result.message = f"連線失敗: {e}"
    return result


async def validate_neo4j_indices(config) -> ValidationResult:
    """驗證 Neo4j 索引是否已建立。"""
    result = ValidationResult("Neo4j 索引")
    start = time.time()
    try:
        from graphiti_core import Graphiti

        graphiti = Graphiti(
            uri=config.neo4j.uri,
            user=config.neo4j.user,
            password=config.neo4j.password,
        )

        records, _, _ = await graphiti.driver.execute_query("SHOW INDEXES")
        result.duration = time.time() - start

        index_names = [r.get("name", "") for r in records]
        total = len(index_names)
        result.passed = total > 0
        result.message = f"找到 {total} 個索引"
        result.details["index_count"] = total
        result.details["index_names"] = sorted(index_names)

        await graphiti.driver.close()
    except Exception as e:
        result.duration = time.time() - start
        result.message = f"索引檢查失敗: {e}"
    return result


async def validate_ollama_llm(config) -> ValidationResult:
    """測試 Ollama LLM 服務。"""
    result = ValidationResult("Ollama LLM")
    start = time.time()
    try:
        from src.ollama_graphiti_client import OptimizedOllamaClient
        from graphiti_core.llm_client.config import LLMConfig

        llm_config = LLMConfig(
            base_url=config.ollama.base_url,
            model=config.ollama.model,
            temperature=config.ollama.temperature,
        )
        client = OptimizedOllamaClient(config=llm_config)
        response = await client.generate_response(
            [{"role": "user", "content": "回答：1+1=?"}]
        )
        result.duration = time.time() - start

        if response:
            result.passed = True
            result.message = f"模型 {config.ollama.model} 回應正常"
            result.details["response_preview"] = str(response)[:100]
        else:
            result.message = "模型回應為空"
    except Exception as e:
        result.duration = time.time() - start
        result.message = f"LLM 測試失敗: {e}"
    return result


async def validate_ollama_embedder(config) -> ValidationResult:
    """測試 Ollama 嵌入器。"""
    result = ValidationResult("Ollama 嵌入器")
    start = time.time()
    try:
        from src.ollama_embedder import OllamaEmbedder

        embedder = OllamaEmbedder(
            model=config.embedder.model,
            base_url=config.embedder.base_url,
            dimensions=config.embedder.dimensions,
        )
        embeddings = await embedder.create([{"text": "測試嵌入"}])
        result.duration = time.time() - start

        if embeddings and len(embeddings) > 0:
            # create() 單個文本回傳扁平 float 列表
            if isinstance(embeddings[0], float):
                dim = len(embeddings)
            else:
                dim = len(embeddings[0]) if embeddings[0] else 0
            result.passed = True
            result.message = f"模型 {config.embedder.model} 嵌入正常"
            result.details["actual_dimensions"] = dim
            result.details["expected_dimensions"] = config.embedder.dimensions
            if dim != config.embedder.dimensions:
                result.message += f"（警告: 實際維度 {dim} != 配置 {config.embedder.dimensions}）"
        else:
            result.message = "嵌入回應為空"
    except Exception as e:
        result.duration = time.time() - start
        result.message = f"嵌入器測試失敗: {e}"
    return result


async def run_validation(config_path: str | None, skip_neo4j: bool, skip_ollama: bool) -> list[ValidationResult]:
    """執行所有驗證。"""
    config = load_config(config_path)

    results = []

    # 配置驗證（必做）
    results.append(await validate_config_file(config_path))

    # Neo4j
    if not skip_neo4j:
        results.append(await validate_neo4j(config))
        results.append(await validate_neo4j_indices(config))

    # Ollama
    if not skip_ollama:
        results.append(await validate_ollama_llm(config))
        results.append(await validate_ollama_embedder(config))

    return results


def print_results(results: list[ValidationResult]) -> None:
    """彩色格式輸出驗證結果。"""
    print("=" * 60)
    print("Graphiti MCP Server 配置驗證")
    print("=" * 60)

    all_passed = True
    for r in results:
        icon = "\033[32m✓\033[0m" if r.passed else "\033[31m✗\033[0m"
        time_str = f"({r.duration * 1000:.0f}ms)"
        print(f"  {icon} {r.name}: {r.message} {time_str}")
        if not r.passed:
            all_passed = False

    print()
    total_time = sum(r.duration for r in results)
    if all_passed:
        print(f"\033[32m所有驗證通過\033[0m（總耗時: {total_time:.2f}s）")
    else:
        failed = sum(1 for r in results if not r.passed)
        print(f"\033[31m{failed} 項驗證失敗\033[0m（總耗時: {total_time:.2f}s）")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Graphiti MCP Server 配置驗證工具")
    parser.add_argument("--config", help="配置檔案路徑（預設使用 .env）")
    parser.add_argument("--json", action="store_true", help="JSON 格式輸出")
    parser.add_argument("--skip-ollama", action="store_true", help="跳過 Ollama 測試")
    parser.add_argument("--skip-neo4j", action="store_true", help="跳過 Neo4j 測試")
    args = parser.parse_args()

    results = asyncio.run(
        run_validation(args.config, skip_neo4j=args.skip_neo4j, skip_ollama=args.skip_ollama)
    )

    if args.json:
        output = {
            "results": [r.to_dict() for r in results],
            "all_passed": all(r.passed for r in results),
            "total_duration_ms": round(sum(r.duration for r in results) * 1000, 1),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_results(results)

    sys.exit(0 if all(r.passed for r in results) else 1)


if __name__ == "__main__":
    main()
