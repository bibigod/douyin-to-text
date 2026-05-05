<div align="center">

# 🎬 douyin-to-text

**抖音视频 → 中文文字稿，30 秒搞定。**

中文短视频专用的本地化转写工具。基于阿里云 Qwen Paraformer，自带 LLM 一键总结。

[![PyPI](https://img.shields.io/pypi/v/douyin-to-text?color=%237c3aed&label=pypi)](https://pypi.org/project/douyin-to-text/)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-22c55e)](LICENSE)
[![Stars](https://img.shields.io/github/stars/bibigod/douyin-to-text?style=flat&color=f59e0b)](https://github.com/bibigod/douyin-to-text/stargazers)

[**🚀 快速开始**](#-30-秒上手) · [**📖 零基础指南**](INSTALL.md) · [**🐛 反馈**](https://github.com/bibigod/douyin-to-text/issues)

</div>

<br />

```bash
$ douyin-to-text "https://v.douyin.com/xxx/" --summary

📥 [1/3] 抓取视频...
🎙️ [2/3] 流式转写中...
  · 一分钟看完一周AI大事，OpenAI解除与微软绑定的情侣关系
  · Google io大会剧透，下一代大模型Gemini 4即将登场
  · ...
🧠 [3/3] LLM 总结中...
✅ 完成 → 2026-05-05_xxx.txt + 2026-05-05_xxx.md
```

<br />

## ✨ 为什么用它

```
🎯 中文最准    ·  阿里 Paraformer 训练数据本来就偏中文，方言、流行语都比 Whisper 强
⚡  几乎实时    ·  流式 API，30 秒转完一条 1 分钟视频
💰 几乎免费    ·  阿里云 DashScope 有免费额度，正常用一个月也用不完
🧠 自带总结    ·  --summary 一键出 Markdown 笔记：一句话概括 + 核心要点
🪶 没有 GPU 也行 ·  本地不跑模型，云端流式调用
🌐 还有 Web UI  ·  不想敲命令？douyin-to-text-ui 起本地浏览器界面
```

<br />

## 🚀 30 秒上手

```bash
# 1. 装包（带 Web UI）
pip install "douyin-to-text[ui]"
playwright install chromium

# 2. 拿一个免费 API Key：https://dashscope.aliyun.com/
export DASHSCOPE_API_KEY=sk-xxxx       # macOS / Linux
$env:DASHSCOPE_API_KEY="sk-xxxx"       # Windows PowerShell

# 3. 跑！
douyin-to-text "https://v.douyin.com/xxx/" --summary
```

> 🤓 **完全不懂编程？** 看这份手把手图文教程 → [INSTALL.md](INSTALL.md)

<br />

## 🖥 两种用法

### A. 命令行（极客喜欢）

```bash
douyin-to-text "https://v.douyin.com/xxx/"               # 仅转写
douyin-to-text "https://v.douyin.com/xxx/" --summary     # 转写 + LLM 总结
douyin-to-text "https://v.douyin.com/xxx/" --out ~/notes # 自选目录
```

### B. 本地 Web UI（普通人）

```bash
douyin-to-text-ui
```

浏览器自动打开 http://127.0.0.1:7860/ → 粘贴链接 → 点开始 → 喝杯水回来就好了。

API Key 填一次自动记住，下次免输。

<br />

## 📂 输出长什么样

```
~/transcripts/
├── 2026-05-05_盘点一周AI大事.txt   # 逐句转写（一句一行，方便复制）
└── 2026-05-05_盘点一周AI大事.md    # 一句话概括 + 核心要点 + 实用信息
```

完整示例 → [`examples/sample_transcript.txt`](examples/sample_transcript.txt)

<br />

<details>
<summary>📊 <b>对比 Whisper / 其他工具</b></summary>

<br />

|  | Whisper-large | **Paraformer-realtime-v2** |
|---|---|---|
| 中文短视频准确率 | 一般，方言糊 | **更准**（阿里训练数据偏中文） |
| 速度 | 本地慢，云端贵 | **流式，几乎实时** |
| 成本 | 自己部署要 GPU | **阿里云有免费额度** |
| 标点 | 弱 | 自带 |

短视频场景 Paraformer 更优。Whisper 仍然是英文 / 多语种之王——这两条路线互补。

</details>

<details>
<summary>🛣 <b>路线图 / 已完成</b></summary>

<br />

- ✅ v0.2.0 — `--summary` 一键 LLM 总结
- ✅ v0.3.0 — 本地 Gradio Web UI
- ✅ v0.4.0 — API Key 持久化、实时进度、排版优化、傻瓜式安装指南
- ⏳ 其他平台 fetcher（B 站、小红书）——同样遵守"不批量、不绕登录"边界

</details>

<details>
<summary>🚫 <b>不会做的事（设计边界）</b></summary>

<br />

为把合规风险压到最低，下面这些功能 **不会** 被加进来，issue/PR 也不会被接受：

- ❌ 批量抓取（用户主页扒全部、关键词搜索批量抓）
- ❌ 模拟登录、绕过验证码、抓取私密/会员视频
- ❌ 内置自动重发布（到博客 / 公众号 / 小红书）
- ❌ SaaS 公开部署（HuggingFace Spaces、Docker Hub 公共镜像）
- ❌ 视频持久化存储（默认转写完立即删除 mp4/mp3）

</details>

<details>
<summary>⚠️ <b>免责声明 / Disclaimer</b></summary>

<br />

**中文：**

本工具仅供 **个人学习、研究和合理使用**。使用前请确认：

1. 视频著作权归原作者所有，**禁止** 将转写文本用于商业用途、再分发或任何侵犯原作者著作权的场景；
2. 使用本工具时须遵守抖音平台的《用户服务协议》及中华人民共和国相关法律法规（《著作权法》《反不正当竞争法》《数据安全法》《个人信息保护法》等）；
3. **禁止** 使用本工具进行批量抓取、绕过技术保护措施、爬取非公开内容或任何可能构成不正当竞争的行为；
4. 转写所产生的文本由用户自行掌握和处置，**作者不存储、不托管、不传输** 任何视频或文本内容；
5. 因使用本工具产生的任何法律责任 **由使用者自行承担**，作者不对任何滥用行为或下游使用结果承担连带责任。

**English (non-binding summary):**

This tool is provided for personal study and research only. Users are solely responsible for compliance with Douyin's Terms of Service and all applicable copyright/data laws. The authors do not host or distribute video or transcribed content, and disclaim all liability for misuse. Bulk scraping, login bypass, and SaaS deployment of this tool are outside its intended use.

立场参考 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 与 [youtube-dl 案 (EFF, 2020)](https://www.eff.org/deeplinks/2020/11/github-reinstates-youtube-dl-after-riaa-abuse-dmca)：工具中立，责任在使用者。

</details>

<br />

## 🤝 相关项目

- [Evil0ctal/Douyin_TikTok_Download_API](https://github.com/Evil0ctal/Douyin_TikTok_Download_API) — 上游：抖音/TikTok 下载 API
- [jianchang512/pyvideotrans](https://github.com/jianchang512/pyvideotrans) — 大而全：ASR + 翻译 + TTS 全流水线

<br />

<div align="center">

**MIT License** · Built with ❤️ for the Chinese short-video community

如果觉得有用，给个 ⭐ Star 是最大的鼓励。

</div>
