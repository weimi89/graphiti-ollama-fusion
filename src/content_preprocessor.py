"""
內容預處理模組
==============

提供智慧內容切分功能，將長文本自動分割為適當大小的片段，
以減少每段的實體提取量，加速 add_episode 處理流程。

策略：
    - 以段落（\\n\\n）為基本切分單位，保持語意完整性
    - 相鄰短段自動合併，避免產生過於碎片化的片段
    - 可配置切分閾值和最大片段大小
"""

import logging
import re
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class ChunkResult:
    """切分結果。"""

    chunks: List[str]
    original_length: int
    was_chunked: bool


def should_chunk(text: str, threshold: int = 800) -> bool:
    """
    判斷文本是否需要切分。

    Args:
        text: 待判斷的文本
        threshold: 字元數閾值，超過此值返回 True

    Returns:
        bool: 是否需要切分
    """
    return len(text.strip()) > threshold


def smart_chunk(
    text: str,
    max_chunk_size: int = 600,
    threshold: int = 800,
) -> ChunkResult:
    """
    智慧切分文本為語意完整的片段。

    切分策略：
        1. 先按段落分隔符（\\n\\n）拆分
        2. 相鄰短段合併，直到超過 max_chunk_size
        3. 單一超長段落按句子邊界（。！？.!?\\n）再次拆分

    Args:
        text: 待切分的文本
        max_chunk_size: 每段最大字元數
        threshold: 觸發切分的字元數閾值

    Returns:
        ChunkResult: 切分結果，包含片段列表和元資訊
    """
    text = text.strip()
    original_length = len(text)

    if not should_chunk(text, threshold):
        return ChunkResult(
            chunks=[text] if text else [],
            original_length=original_length,
            was_chunked=False,
        )

    # Step 1: 按段落分割
    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    if not paragraphs:
        return ChunkResult(chunks=[], original_length=original_length, was_chunked=False)

    # Step 2: 合併短段落
    chunks: List[str] = []
    current_chunk = ""

    for para in paragraphs:
        # 如果段落本身超過 max_chunk_size，需要進一步拆分
        if len(para) > max_chunk_size:
            # 先把當前累積的 chunk 存入
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            # 拆分超長段落
            sub_chunks = _split_long_paragraph(para, max_chunk_size)
            chunks.extend(sub_chunks)
            continue

        # 嘗試合併到當前 chunk
        if current_chunk:
            merged = current_chunk + "\n\n" + para
            if len(merged) <= max_chunk_size:
                current_chunk = merged
            else:
                chunks.append(current_chunk)
                current_chunk = para
        else:
            current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    # 過濾空片段
    chunks = [c for c in chunks if c.strip()]

    logger.info(
        f"內容切分完成: {original_length} 字元 -> {len(chunks)} 段"
        f" (平均 {original_length // max(len(chunks), 1)} 字元/段)"
    )

    return ChunkResult(
        chunks=chunks,
        original_length=original_length,
        was_chunked=len(chunks) > 1,
    )


def _split_long_paragraph(text: str, max_size: int) -> List[str]:
    """
    按句子邊界拆分超長段落。

    Args:
        text: 超長段落文本
        max_size: 最大片段大小

    Returns:
        List[str]: 拆分後的片段列表
    """
    # 按句子邊界拆分（中英文句號、問號、感嘆號、換行）
    sentences = re.split(r"(?<=[。！？.!?\n])\s*", text)
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [text]

    chunks: List[str] = []
    current = ""

    for sentence in sentences:
        if current:
            merged = current + " " + sentence
            if len(merged) <= max_size:
                current = merged
            else:
                chunks.append(current)
                current = sentence
        else:
            current = sentence

    if current:
        chunks.append(current)

    # 如果切完還有超長的（句子本身超長），硬切
    final_chunks: List[str] = []
    for chunk in chunks:
        if len(chunk) <= max_size:
            final_chunks.append(chunk)
        else:
            # 硬切：按 max_size 分割，盡量在空白處斷開
            final_chunks.extend(_hard_split(chunk, max_size))

    return final_chunks


def _hard_split(text: str, max_size: int) -> List[str]:
    """
    硬性切割超長文本，盡量在空白字元處斷開。

    Args:
        text: 超長文本
        max_size: 最大片段大小

    Returns:
        List[str]: 切割後的片段列表
    """
    chunks: List[str] = []
    while len(text) > max_size:
        # 在 max_size 位置附近找最近的空白字元
        split_pos = text.rfind(" ", 0, max_size)
        if split_pos <= max_size // 2:
            # 找不到合適的空白位置，直接硬切
            split_pos = max_size
        chunks.append(text[:split_pos].strip())
        text = text[split_pos:].strip()
    if text:
        chunks.append(text)
    return chunks
