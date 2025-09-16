#!/usr/bin/env python3
"""
專案整理後的快速驗證測試
"""
import sys
import asyncio
from pathlib import Path

# 添加項目根目錄到路徑
sys.path.append(str(Path(__file__).parent))

async def test_project_structure():
    """測試專案結構和基本功能"""
    print("🔍 驗證專案結構...")

    # 檢查核心文件
    required_files = [
        "graphiti_mcp_server.py",
        "ollama_embedder.py",
        "ollama_graphiti_client.py",
        ".env.example",
        "pyproject.toml"
    ]

    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)

    if missing_files:
        print(f"❌ 缺少核心文件: {missing_files}")
        return False
    else:
        print("✅ 核心文件檢查通過")

    # 檢查目錄結構
    required_dirs = ["docs", "tests", "tools"]
    missing_dirs = []
    for dir_name in required_dirs:
        if not Path(dir_name).is_dir():
            missing_dirs.append(dir_name)

    if missing_dirs:
        print(f"❌ 缺少目錄: {missing_dirs}")
        return False
    else:
        print("✅ 目錄結構檢查通過")

    # 測試導入
    try:
        from graphiti_mcp_server import initialize_graphiti, test_connection
        from ollama_embedder import OllamaEmbedder
        print("✅ 模組導入檢查通過")
    except ImportError as e:
        print(f"❌ 模組導入失敗: {e}")
        return False

    # 測試基本連接（不要求所有服務都在線）
    try:
        print("🔗 測試基本連接...")
        connection_result = await test_connection()
        print(f"   連接結果: {connection_result}")

        if connection_result.get('neo4j') == 'OK':
            print("✅ Neo4j 連接正常")
        else:
            print("⚠️ Neo4j 未連接（這在開發環境中是正常的）")

        if connection_result.get('ollama_llm') == 'OK':
            print("✅ Ollama LLM 連接正常")
        else:
            print("⚠️ Ollama LLM 未連接（這在開發環境中是正常的）")

    except Exception as e:
        print(f"⚠️ 連接測試異常（這在開發環境中是正常的）: {e}")

    print("\n🎉 專案結構驗證完成！")
    print("📝 使用說明請參閱:")
    print("   - README.md - 專案總覽")
    print("   - docs/USAGE.md - 詳細使用指南")
    print("   - docs/CLAUDE.md - 開發記錄")

    return True

if __name__ == "__main__":
    success = asyncio.run(test_project_structure())
    sys.exit(0 if success else 1)