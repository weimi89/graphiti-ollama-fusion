#!/usr/bin/env python3
"""
測試複雜記憶添加來復現 cosine similarity 錯誤
"""

import asyncio
import sys
from tests.test_mcp_complete import test_all_tools

async def test_complex_scenario():
    """測試複雜場景來嘗試復現錯誤"""

    print("🧪 測試複雜記憶場景...")

    try:
        # 運行完整的 MCP 測試
        success = await test_all_tools()

        if success:
            print("✅ 複雜測試通過，沒有發現 cosine similarity 錯誤")
            return False
        else:
            print("❌ 測試失敗，可能發現了問題")
            return True

    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {str(e)}")

        if "cosine" in str(e).lower():
            print("🎯 發現 cosine similarity 錯誤！")
            print(f"錯誤詳情: {str(e)}")
            return True
        else:
            print("❌ 這不是 cosine similarity 錯誤")
            return False

if __name__ == "__main__":
    found_error = asyncio.run(test_complex_scenario())

    if found_error:
        print("\n🎯 成功復現 cosine similarity 錯誤！")
        sys.exit(1)
    else:
        print("\n✅ 沒有復現錯誤")
        sys.exit(0)