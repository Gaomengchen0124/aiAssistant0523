# 临时演示指南（Cloudflare Tunnel）

通过 Cloudflare Tunnel 将本地 Flask 服务暴露到公网，生成临时 HTTPS 域名供演示使用。

---

## 前置准备

### 1. 安装依赖

```bash
cd aiAssistant0523
pip install -r requirements.txt
```

### 2. 配置 API Key

复制模板并填入你的 DeepSeek API Key：

```bash
cp .env.example .env
```

编辑 `.env`：

```
LLM_API_KEY=sk-your-api-key-here
```

> API Key 申请：https://platform.deepseek.com/

### 3. 下载 cloudflared

**方法一：PowerShell（推荐）**

```powershell
cd aiAssistant0523
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "cloudflared.exe"
```

**方法二：浏览器下载**

1. 访问：https://github.com/cloudflare/cloudflared/releases/latest
2. 下载 `cloudflared-windows-amd64.exe`
3. 重命名为 `cloudflared.exe` 放到 `aiAssistant0523/` 目录下

---

## 启动演示

双击运行：

```
start-demo.bat
```

脚本会：
1. 检查环境和依赖
2. 启动 Flask 服务（端口 5000）
3. 启动 Cloudflare Tunnel
4. 在终端显示公网访问地址，例如：

```
Your quick Tunnel has been created! Visit it at:
https://kol-demo-xxxxx.trycloudflare.com
```

将 `https://kol-demo-xxxxx.trycloudflare.com` 分享给观众即可。

---

## 演示注意事项

- **settings 页面已隐藏 API Key 输入框**，观众无法看到或修改你的 API Key
- 演示期间保持 `start-demo.bat` 窗口运行，关闭窗口即断开公网访问
- 生成的 `*.trycloudflare.com` 域名是临时的，每次启动都会不同

---

## 演示结束后

### 1. 关闭服务

直接关闭 `start-demo.bat` 窗口，或按 `Ctrl + C` 停止 Tunnel。

Flask 服务窗口需要单独关闭。

### 2. 清理 API Key（重要）

登录 [DeepSeek 平台](https://platform.deepseek.com/)，删除或轮转演示使用的 API Key。

### 3. 恢复 settings 页面（如需继续开发）

如需恢复 API Key 输入框，编辑 `web/settings.html`，将 API Key 区域的 `style="display: none;"` 去掉。

---

## 常见问题

**Q: 启动后访问不了？**
A: 检查 Flask 服务是否正常启动（看 Flask Server 窗口是否有报错），确认 `cloudflared.exe` 没有被防火墙拦截。

**Q: 生成的域名打不开？**
A: Cloudflare Tunnel 需要几秒钟建立连接，请稍等片刻再试。

**Q: 演示很卡？**
A: Tunnel 走的是 Cloudflare 海外节点，访问速度取决于网络状况。如需国内快速访问，建议购买域名 + 服务器部署。
