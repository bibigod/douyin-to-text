# douyin-to-text

> 把抖音视频一键转成中文文本。基于阿里云 Qwen Paraformer 流式 ASR，比 Whisper 更快、更准、更便宜。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## 这个工具是什么

```
抖音链接  ──Playwright──▶ mp4  ──ffmpeg──▶ mp3  ──Paraformer──▶ 文本.txt
```

一行命令：

```bash
douyin-to-text "https://v.douyin.com/xxxxxx/"
```

输出一份逐句换行的转写稿，丢给 LLM 做二次总结/改写都很方便。

## 为什么不用 Whisper

| | Whisper-large | Paraformer-realtime-v2 |
|---|---|---|
| 中文准确率（短视频） | 一般，方言糊 | **更准**（阿里训练数据偏中文） |
| 速度 | 本地慢，云端贵 | **流式，几乎实时** |
| 成本 | 自己部署要 GPU | **阿里云有免费额度** |
| 标点 | 弱 | 自带 |

短视频场景下 Paraformer 是更优解，Whisper 仍然是英文/多语种之王。

## 输出长这样

```text
$ douyin-to-text "https://v.douyin.com/xxxxxx/"
[1/3] fetching mp4 from https://v.douyin.com/xxxxxx/ ...
[2/3] extracting audio + streaming to Paraformer ...
  · 大家好，今天我们来聊一个特别有意思的话题。
  · 就是关于人工智能在日常生活中的应用。
  · 你看现在很多人都在用各种 AI 工具来提高效率。
  ...
[3/3] done. transcript -> ./transcripts/2026-05-05_某视频标题.txt
```

完整示例见 [`examples/sample_transcript.txt`](examples/sample_transcript.txt)。

## 安装

```bash
pip install douyin-to-text
playwright install chromium
```

需要：
- Python 3.10+
- ffmpeg 在 PATH 里（[安装指引](https://ffmpeg.org/download.html)）
- 阿里云 DashScope API Key（[免费申请](https://dashscope.aliyun.com/) → 控制台拿 key）

设置 API Key：

```bash
# Linux/Mac
export DASHSCOPE_API_KEY=sk-xxxx
# Windows PowerShell
$env:DASHSCOPE_API_KEY="sk-xxxx"
```

## 使用

```bash
# 仅转写
douyin-to-text "https://v.douyin.com/xxxxxx/"

# 转写 + LLM 总结成 Markdown（复用同一个 DASHSCOPE_API_KEY，调 qwen-plus）
douyin-to-text "https://v.douyin.com/xxxxxx/" --summary

# 指定输出目录
douyin-to-text "https://v.douyin.com/xxxxxx/" --out ./transcripts
```

输出：

```
./transcripts/2026-05-05_视频标题.txt   # 逐句转写
./transcripts/2026-05-05_视频标题.md    # （加 --summary 时）一句话概括 + 核心要点 + 实用信息
```

总结失败不会影响转写——txt 一定会落地，md 才可能跳过。

## 设计边界（明确不做的事）

为了把工具的合规风险压到最低，下面这些功能**不会**被加进来，issue/PR 也不会被接受：

- ❌ 批量抓取（用户主页扒全部、关键词搜索批量抓）
- ❌ 模拟登录、绕过验证码、抓取私密/会员视频
- ❌ 内置任何形式的"自动重发布"（到博客/公众号/小红书）
- ❌ 提供 SaaS 部署（HuggingFace Spaces、Docker Hub 公共镜像）
- ❌ 视频持久化存储（默认转写完立即删除 mp4/mp3）

会做的：
- [x] ~~一键 LLM 总结（接 Qwen / Claude / 本地模型可选）~~ ✅ v0.2.0 已加入 `--summary`
- [ ] 本地 Gradio UI（仅供本机使用）
- [ ] 其他平台 fetcher（B 站、小红书），同样遵守上述边界

## ⚠️ 免责声明 / Disclaimer

**中文：**

本工具仅供**个人学习、研究和合理使用**。使用前请确认：

1. 视频著作权归原作者所有，**禁止**将转写文本用于商业用途、再分发或任何侵犯原作者著作权的场景；
2. 使用本工具时须遵守抖音平台的《用户服务协议》及中华人民共和国相关法律法规（包括但不限于《著作权法》《反不正当竞争法》《数据安全法》《个人信息保护法》）；
3. **禁止**使用本工具进行批量抓取、绕过技术保护措施、爬取非公开内容或任何可能构成不正当竞争的行为；
4. 转写所产生的文本由用户自行掌握和处置，**作者不存储、不托管、不传输**任何视频或文本内容；
5. 因使用本工具产生的任何法律责任**由使用者自行承担**，作者不对任何滥用行为或下游使用结果承担连带责任。

**English (non-binding summary):**

This tool is provided for personal study and research only. Users are solely responsible for compliance with Douyin's Terms of Service and all applicable copyright/data laws. The authors do not host or distribute video or transcribed content, and disclaim all liability for misuse. Bulk scraping, login bypass, and SaaS deployment of this tool are outside its intended use.

如果你是视频原作者，本仓库不持有也不分发你的内容；请直接联系下载该视频的具体用户。

立场参考 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 与 [youtube-dl 案 (EFF, 2020)](https://www.eff.org/deeplinks/2020/11/github-reinstates-youtube-dl-after-riaa-abuse-dmca)：工具中立，责任在使用者。

## License

[MIT](LICENSE)

## 相关项目

- [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) — 上游：抖音/TikTok 下载
- [jianchang512/pyvideotrans](https://github.com/jianchang512/pyvideotrans) — 大而全：ASR+翻译+TTS 全流水线
