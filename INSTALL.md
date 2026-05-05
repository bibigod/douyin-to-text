# 零基础 10 分钟上手指南

> 这份是写给**完全不懂编程**的朋友的。如果你看到 "pip"、"PowerShell" 这些词就头大，按下面一步一步来就行。
> 全程鼠标点 + 复制粘贴，**不需要写代码**。

---

## 你需要准备的

- 一台 Windows 10/11 电脑（Mac 也行，命令略有差别）
- 一个能上网的浏览器
- 一张能扫支付宝/微信的支付二维码（去阿里云开免费账号用）

预计耗时：**首次配置 10 分钟，之后每次用只要 30 秒**。

---

## 第一步：装 Python（5 分钟，**只要装一次**）

1. 打开浏览器，访问 https://www.python.org/downloads/
2. 点中间那个大大的 "Download Python 3.x.x" 按钮，下载安装包
3. **重要**：双击安装包后，**先勾选最下面那个 "Add Python to PATH"**，再点 Install Now

   ![](https://docs.python.org/3/_images/win_installer.png)

4. 等它装完，关掉窗口

**怎么验证装好了？** 按 `Win + R`，输入 `powershell` 回车，在弹出的蓝色窗口里输入：

```powershell
python --version
```

如果显示类似 `Python 3.12.x` 就说明 OK。

---

## 第二步：装 douyin-to-text（2 分钟）

继续在那个蓝色 PowerShell 窗口里，**复制下面这行**，粘贴进去回车：

```powershell
pip install "git+https://github.com/bibigod/douyin-to-text.git#egg=douyin-to-text[ui]"
```

> 💡 后面 `git+https://...` 那一长串是因为我们还没发布到 PyPI。等正式发布之后，命令会简化成 `pip install "douyin-to-text[ui]"`。复制粘贴就行，不用懂语法。

等它跑完（屏幕会刷一堆字，正常）。

接着再粘贴这一行回车：

```powershell
playwright install chromium
```

这是装一个隐形浏览器，工具用它去抖音抓视频。

---

## 第三步：装 ffmpeg（1 分钟，**只要装一次**）

ffmpeg 是用来从视频里抽音频的小工具。最简单的装法——继续在 PowerShell 里：

```powershell
winget install Gyan.FFmpeg
```

回车后会让你按 `Y` 同意协议，按一次就行。

> Mac 用户：`brew install ffmpeg`

---

## 第四步：申请阿里云 API Key（5 分钟，**只要申请一次**）

工具用阿里云的 Qwen Paraformer 做语音识别，有免费额度（够你用很久）。

1. 浏览器打开 https://dashscope.aliyun.com/
2. 用支付宝/手机号注册登录
3. 登录后，点右上角头像 → **API-KEY 管理** → **创建新的 API-KEY**
4. 把生成的那串 `sk-xxxxxxxxxxxx` **复制下来**（很长，全选复制）

⚠️ 这串 key 像密码，别给别人看，也别贴到聊天群里。

---

## 第五步：开跑！（30 秒）

回到 PowerShell 窗口，输入：

```powershell
douyin-to-text-ui
```

回车之后：

- 浏览器会自动打开 http://127.0.0.1:7860/
- 看到一个干净的页面：① API Key  ② 抖音链接  ③ 开始转写

操作：

1. ① 处粘贴你的 `sk-xxx` key（**只填这一次**，之后会自动记住）
2. ② 处粘贴抖音视频链接：抖音 App 里打开视频 → 右下角分享 → 复制链接
3. ③ 点开始转写

**等 30~90 秒**（按视频长度）：
- 转写完成的中文文本会出现在"转写文本"标签页
- 一句话总结 + 核心要点会出现在"LLM 总结"标签页
- 同时会保存两份文件到 `transcripts/` 文件夹（在 PowerShell 当前目录下）

---

## 之后每次怎么用

PowerShell 输入一行：

```powershell
douyin-to-text-ui
```

浏览器自动打开，**API Key 已记住**，直接粘链接 → 点按钮即可。

要关掉的话：在 PowerShell 窗口按 `Ctrl + C`。

---

## 常见问题

### Q: PowerShell 里 `python` 提示"不是内部命令"

第一步装 Python 时**没勾选** "Add to PATH"。卸载重装，记得勾上那个选项。

### Q: 报错 "No mp4 URL captured"

抖音视频可能用了新的反爬手段。换一条视频试试；如果都不行，去
[GitHub Issues](https://github.com/bibigod/douyin-to-text/issues) 提 bug 并附上失败的链接。

### Q: 报错 "DashScope ... 401 / Invalid API Key"

API Key 输错了，回 https://dashscope.aliyun.com/ 控制台重新复制粘贴。

### Q: 想换 API Key

UI 顶部 ① 处直接覆盖填入新 key 即可，新 key 会替换旧的。

或者删掉 `C:\Users\你的用户名\.douyin-to-text\config.json` 这个文件，下次启动就清空了。

### Q: 转写文本里中文识别错了几个字

短视频里的方言、流行语、专业术语 ASR 都会偶尔出错。**LLM 总结那一栏**通常能根据上下文修正大部分。要彻底改正只能手动。

### Q: 想批量转写一堆视频

工具**故意不支持批量**——这是为了合规。你可以在 PowerShell 里写个简单的循环自己跑，但请遵守
[免责声明](README.md#%EF%B8%8F-免责声明--disclaimer)。

---

## 完整工作流截图（待补）

> TODO: 等首批用户用了之后，补一组安装 + 使用的截图，把"装"和"用"都讲明白。

---

回到主文档：[README.md](README.md)
