# 本地视频/音频文件支持 — 设计文档

> 日期：2026-06-28 | 版本：v0.5.0

## 概述

当前 `douyin-to-text` 只接受抖音分享链接，管道固定为：抓取 → 语音识别 → 摘要。本次改动新增**本地文件模式**，用户可传入本地的 `.mp4` / `.mov` / `.mp3` / `.wav` 等音视频文件，跳过网络抓取阶段，直接从文件提取音频做语音识别，并可选择生成摘要。

## 设计决策总结

| 决策 | 选择 |
|---|---|
| CLI 接口 | 子命令：`url` 和 `file` |
| 输出文件命名 | 取输入文件 stem + `_sanitize()` 清洗 |
| `--title` 覆盖 | 可选，不传就用文件名 |
| 音频格式支持 | 视频 + 纯音频都支持（ffmpeg 统一处理） |
| 工作目录 | 和 URL 模式一致：`.raw/<uuid>/` |
| 临时文件清理 | 默认清理提取的 mp3；原始文件永远不动 |
| Web UI | 本次不做，后续迭代 |
| 元数据记录 | `.raw/source_file.txt` 记录原文件绝对路径 |

## CLI 接口

```
douyin-to-text url  <url>   [--out ...] [--summary] [--keep-media]
douyin-to-text file <path>  [--out ...] [--summary] [--keep-media] [--title ...]
```

- `url` 子命令：行为与现有 CLI 完全一致（向后兼容）
- `file` 子命令：
  - `<path>`：本地音视频文件路径
  - `--title`：可选，手动指定输出文件标题；不传则取文件 stem 经 `_sanitize()` 清洗
  - `--keep-media`：保留提取出的临时 mp3（原始文件永远不动）
  - 进度打印从 `[2/3]` 开始（无 fetching 阶段）

## 架构改动

### 管道层 (`pipeline.py`)

新增内部函数 `_transcribe_media()`，作为 URL 和本地模式的共享核心：

```
transcribe_url(url, ...)          # 公开 API，向后兼容
├── fetch_mp4(url)                → mp4, page_title
└── _transcribe_media(            # 共享核心
        mp4, title, out_dir,
        keep_media, on_sentence,
        on_stage, summarize)
    ├── mp4_to_mp3(mp4)          → mp3
    ├── transcribe_mp3(mp3)      → text
    ├── 写元数据到 .raw/
    ├── 清理媒体（除非 keep_media）
    └── summarize_transcript     → summary（可选）

transcribe_file(path, ...)        # 新增公开 API
├── 校验 path 存在
└── _transcribe_media(            # 复用同一核心
        path, title_from_stem,
        out_dir, ...)
```

- `transcribe_url()` 签名和行为**完全不变**，内部重构为调用 `_transcribe_media()`
- `transcribe_file()` 新增，接收本地路径
- `_transcribe_media()`：接收一个已就绪的媒体文件路径 + 元数据，执行提取→转写→摘要→清理

### ASR 层 (`asr.py`)

**无需改动。** 现有 `mp4_to_mp3()` 使用 `ffmpeg -vn`，对视频和纯音频都有效：

```bash
ffmpeg -y -i <source> -vn -ar 16000 -ac 1 -codec:a libmp3lame -q:a 5 <output>.mp3
```

- `-vn`：不处理视频流（对纯音频无害，ffmpeg 自动忽略）
- 支持格式：`.mp4` `.mov` `.avi` `.mkv` `.webm` `.mp3` `.wav` `.m4a` `.aac` `.flac` `.ogg` `.opus` `.wma` 等

### 输出目录结构

```
transcripts/
├── 2026-06-28_会议录制.txt
├── 2026-06-28_会议录制.md          # --summary 时生成
├── .raw/
│   └── <uuid>/
│       ├── transcript.txt
│       ├── source_file.txt         # 本地模式：记录原文件绝对路径
│       │                           # URL 模式：仍是 source_url.txt + page_title.txt
│       └── video.mp3               # 仅 --keep-media
```

### 公共 API (`__init__.py`)

```python
from douyin_to_text.pipeline import transcribe_url, transcribe_file
__all__ = ["transcribe_url", "transcribe_file", "__version__"]
```

### Web UI (`web.py`)

本次不修改。`_run()` 生成器仍只处理 URL 输入。

## 错误处理矩阵

| 场景 | 行为 |
|---|---|
| 文件不存在 | 立即报错 `FileNotFoundError`，不创建工作目录 |
| 文件无音频轨道 | ffmpeg 报错 → 包装为可读错误信息 |
| 不支持的文件格式 | ffmpeg 报错 → 透出原始错误 |
| 传入目录 | 立即报错，提示应传文件路径 |
| DASHSCOPE_API_KEY 未配置 | 和 URL 模式一致：检查环境变量，打印友好提示 |
| ASR 转写失败 | 保留 mp3（即使未传 --keep-media），方便重试 |
| 总结失败 | 非致命，转写文本仍成功保存 |

## 测试

### 新增单元测试 (`tests/test_smoke.py`)

- `test_transcribe_file_importable` — 验证新公开 API 可导入
- `test_sanitize_with_file_stems` — 常见文件名清洗（空格、特殊字符、中文）
- `test_mp4_to_mp3_accepts_audio` — 纯音频输入也能生成 mp3（需 ffmpeg）

### 手动端到端 (`tests/manual_e2e.py`)

- 新增 `test_transcribe_file()` — 传入本地测试 mp4/mp3 文件验证全管道

## 明确拒绝的特性

- 批量文件处理（和批量抓取一样，项目范围外）
- 递归目录扫描
- 文件扩展名白名单校验（ffmpeg 自己判断）
- 音频长度/大小预检
- Web UI 本地上传（后续迭代考虑）
