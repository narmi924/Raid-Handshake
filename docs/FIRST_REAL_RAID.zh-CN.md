# Raid Handshake：从零准备第一次真实 A → B raid

本指南按 2026-10-25 的官方资料编写。你需要亲自完成注册、验证码、2FA 和授权；密码、验证码、stream key 和 OpenAI key 都不用发给 Codex。

## 先认识三个名字

| 角色 | 用途 | 是否必须新建 |
| --- | --- | --- |
| 来源频道 A | 集合观众，发起 raid | 你现在没有账号，需要创建 |
| 接收频道 B | 开播、运行 Raid Handshake、接收 raid | 创建第二个账号 |
| 真实参与者 | 在 A 看直播、跟随 raid 到 B、发言 | 可邀请朋友使用自己的账号；首轮建议几位 |

注册 Twitch 账号后就有对应的频道地址，不需要另外申请 Affiliate、Partner 或付费开通频道。两个主播账号和两个直播间用于演示；参与者越少，差分指标就越容易受平台延迟影响。

## 1. 创建 A 和 B

1. 打开 [Twitch 注册页](https://www.twitch.tv/signup)，选择可用用户名，使用真实出生日期和你能接收验证码的邮箱或手机，完成注册与验证。
2. 账号 A 登录后，打开头像 → Settings（设置）→ Security and Privacy（安全与隐私），确认邮箱已验证，并开启 Two-Factor Authentication（双重验证）。按提示用手机及验证器完成。
3. 为 B 重复操作。建议两个浏览器资料分别登录 A 和 B，并把浏览器资料命名为“来源 A”和“接收 B”，避免从错误频道发起 raid 或授权。
4. 若要复用邮箱或手机号，先阅读当前的额外账号规则；遇到提示时，在原账号设置开启额外账号创建。不要为此虚构个人资料。
5. 把两个登录名记在下面。频道 URL 是 `https://www.twitch.tv/登录名`，登录名可能与显示名大小写不同。

```
A 登录名：thisisraida
A 频道 URL：https://www.twitch.tv/thisisraida
B 登录名：thisisraidb
B 频道 URL：https://www.twitch.tv/thisisraidb
```

依据：[官方注册指南](https://help.twitch.tv/s/article/creating-an-account-with-twitch)、[开发者账号验证要求](https://dev.twitch.tv/docs/authentication/register-app/)。

## 2. 让两个频道同时真实开播

最省事的组合是：B 用电脑 OBS，A 用第二台电脑或手机 Twitch App。只运行 OBS bandwidth test 不算开播。

**接收 B（电脑）：**

1. 从 [OBS 官方网站](https://obsproject.com/download) 安装 OBS Studio。
2. OBS → Settings → Stream，选 Twitch 并连接 **B**。若使用 stream key，请从 B 的 Creator Dashboard 获取并保密。
3. 新建场景，加入你有权直播的画面、麦克风和清晰可见的频道名。先用 720p/30fps 等保守设置跑通。
4. 在 B 的 Creator Dashboard → Stream Manager 编辑标题、分类和语言。标题应描述实际内容。
5. 点击 OBS 的 Start Streaming。用另一浏览器打开 B，确认有 LIVE 标记、能听到麦克风、能发聊天；使用耳机避免回声。
6. 在 Twitch/OBS 里关闭额外的人为 stream delay；可用时启用低延迟，方便验证30秒目标。

**来源 A（手机或另一台电脑）：**

1. 在设备上确认登录的是 A，选择 Go Live / 开播，并按当前提示允许摄像头、麦克风等所需权限。
2. 直播你自己的讲解或其他授权内容；填好真实标题和分类。
3. 从浏览器打开 A，确认它和 B **同时 LIVE**。首次开播若被账号验证步骤拦截，先按页面提示完成。

单台电脑也能用隔离的 OBS 实例/独立配置推两路，但不建议把首次成功建立在双实例配置上。用电脑 B＋手机 A 更容易排错。

依据：[Twitch 开播概述](https://dev.twitch.tv/docs/video-broadcast/)、[OBS Quick Start](https://obsproject.com/kb/quick-start-guide)。

## 3. 放行测试 raid 和聊天

在 B 的 Creator Dashboard → Settings → Stream 中找到 Raids / Incoming Raids：

1. 测试阶段允许 A 发起 raid。对于新账号，尤其要检查最低账号年龄、最低人数和额外群组限制。
2. 官方给出的允许所有来源配置是：最低观众1、最高不设上限、账号年龄0，不勾选额外群组。请根据你自己的频道情况选择，测试后可恢复偏好。
3. 确认没有临时启用“停止接收 raid 1小时”。
4. 检查 B 的聊天限制，避免订阅者模式、关注时长、邮箱/手机验证门槛阻止测试者发言；如果保留验证门槛，请让参与者先完成验证。

依据：[官方 raid 设置与操作](https://help.twitch.tv/s/article/how-to-use-raids?language=en_US&langage=en_US)。

## 4. 注册 Twitch Public Client

应用注册一次，A 发 raid 不需要安装应用；Raid Handshake 主要由 B 授权。

1. 用你拥有的、邮箱已验证且已开启2FA的账号进入 [Developer Console](https://dev.twitch.tv/console/apps)。
2. Applications → Register Your Application。名称须唯一，可用 `Raid Handshake + 你的后缀`。
3. OAuth Redirect URL 按控制台要求填写。若要求至少一项，可填 `http://localhost:8765`；Device Code Flow 本身不通过此地址接收 OAuth 回调。
4. 类别选择与聊天工具相符的一项；Client Type 选择 **Public**。若界面将该选项放在注册后的 Manage 页面，则在那里确认。
5. 保存后复制 **Client ID**，在 Raid Handshake 控制台填入。Public DCF 不需要 Client Secret；不要为了填应用而公开 secret。
6. 在应用点“Connect Twitch”，取得激活码；打开 Twitch 返回的官方激活页面，先确认当前登录的是 **B**，再输入码、检查权限并授权。
7. 回到控制台，确认显示 B 的头像/登录名和 EventSub 已连接。授权到 A 了就断开并重新登录 B。

首发需要：`user:read:chat`、`user:write:chat`、`moderator:read:chatters`、`moderator:read:followers`。主播本人 token 用于读取自己频道的聊天连接者和关注事件。Shoutout 是可选权限。

依据：[注册应用](https://dev.twitch.tv/docs/authentication/register-app/)、[Public Device Code Flow](https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#device-code-grant-flow)。

## 5. 准备 OpenAI API

1. 打开 [OpenAI API 平台](https://platform.openai.com/)，登录并创建/选择自己的项目。
2. 在项目中创建 API key，并确认项目已具备可用额度/计费和所选模型访问权限。API 的额度与 ChatGPT/Codex 的订阅使用量分别管理。
3. 把 key 直接粘贴到 Raid Handshake 本地控制台的密码输入框，点击保存。不要粘贴到聊天、仓库、截图或演示视频。
4. 控制台会显示“已配置”而不回显 key。默认使用 OpenAI 的转录和结构化摘要接口；模型名称可以在高级设置调整。
5. 选择 B 实际使用的麦克风/授权音频设备，开始采集。音频片段会发送给 OpenAI，聊天上下文也用于生成摘要。若 B 正在直播本地 HTML 中的语音，可选择对应扬声器的 `system playback`，操作见[当前 HTML 音频设置指南](OBS_AUDIO_SETUP.zh-CN.md)。
6. 让所选设备持续收到 B 实际直播的语音，等待转录和摘要；使用系统回录时无需对麦克风讲话。先确认摘要与实际内容一致，再发起正式测试。

依据：[OpenAI API Quickstart](https://developers.openai.com/api/docs/quickstart)、[转录](https://developers.openai.com/api/docs/guides/speech-to-text)、[结构化输出](https://developers.openai.com/api/docs/guides/structured-outputs)。

## 6. 在 B 的 OBS 加入 overlay

1. 启动项目，打开 `http://127.0.0.1:8765`。
2. 在控制台点 Copy OBS URL。
3. B 的 OBS → Sources → + → Browser → 新建 `Raid Handshake`。
4. 把刚复制的 URL 填入，画布尺寸设置为1920×1080；背景透明。确认需要时能看到卡片。
5. 控制台检查 EventSub、Chatters baseline、OpenAI、Audio 状态。**先等至少一次完整的 Chatters 基线采样成功。**

## 7. 发起第一次真实 raid

1. 邀请朋友登录并进入 A 的聊天室和直播，暂时不要进入 B；已在 B 的账号会属于 S0，不会进入差分群体 R。
2. 让 B 持续开播并提供真实语音内容（主播讲话或正在直播的授权音频）；确保近3分钟已有转录和可用摘要。首轮保持“预批模板自动发送”关闭。
3. 在 **A 的 Twitch 聊天框**输入 `/raid B的实际登录名`。不要写显示名中的空格或示例占位符。
4. Twitch 出现倒计时后，等 Raid Now 可用（官方说明约10秒），点击完成。参与者不要退出 raid。
5. 到 B 确认有 Twitch 自带的 raid 通知。应用5秒目标显示基础来客卡；控制台出现落地卡后，查看最终文字并点击发送或使用 `Ctrl+Shift+Enter`。
6. 录下 Twitch 通知、OBS 卡片、B 的真实聊天消息与时间。参与者可以发送真实的欢迎词、口头禅、表情。
7. 60秒后检查“浪潮学习”：来源原生表情按 owner_id 识别；其他重复文本只标为学习到的 token。缺少多人样本时显示“样本不足”。
8. 90秒后差分群体固定。让 B 继续开播至少5分钟，查看实际聊天连接和最近5分钟发言人数；完整测试继续到15/30分钟。

新账号可能没有来源专属原生表情，也可能没有 clips，出现“样本不足/暂无 clips”是正确结果。已有真实 clips 时可以测试标题展示，但不是首次连通的前置条件。

## 8. 如何理解统计

- S0：raid 到达时采用的最近一次完整的 raid 前采样；应用显示它离到达时刻有多旧。
- R：到达后90秒内，后续采样中新出现、且不在 S0 中的账号的并集。
- 5/15/30分钟的连接人数：R 与该时刻实际 Chatters 采样的交集。
- 发言人数：R 中在采样前5分钟发过普通消息的独立账号数。
- 新增关注：该 raid 后对应窗口内，全频道的 `channel.follow` 事件数，不能归因到 R。
- 平台有列表更新延迟；聊天已连接也不代表正在看视频。自然进台的人、机器人、同时发生的其他 raid 都可能混入 R。界面只称“估计新增聊天连接者”，不称“已识别 raid 观众”或“观看留存”。

## 9. 常见卡点

| 现象 | 先检查 |
| --- | --- |
| 无法开播或注册应用 | 邮箱验证、2FA及当前账号是否正确 |
| Public Client 认证失败 | Client Type 是否为 Public、Client ID 是否复制完整 |
| raid 被拒绝 | B 的账号年龄/人数/群组门槛、禁用 raid 状态、是否互相屏蔽 |
| 没有应用事件 | B 是否授权、EventSub 是否在线、Twitch 聊天是否出现原生 raid 通知 |
| 统计未知 | 是否在 raid 前就有完整基线、采样是否报错；不要把未知当成0 |
| 发不出消息 | token 的身份、scope、聊天限制及落地卡是否已预览 |
| 没有转录 | 设备选择、麦克风音量、API key/额度/模型访问、Windows 录音权限 |
| 有声音但内容错误 | 是否选到了系统回放/回声，改用主播本人麦克风并使用耳机 |

## 10. 预批模式与提交素材

默认热键确认模式先跑通。可选预批模式会在主播确认模板结构和固定措辞后，将当前摘要自动填入并发送；这意味着最终文本仍会变化。比赛联合主办不能单独证明第三方数据授权或发布条款已获豁免，须保留对此的准确说明。

正式演示只拍真实 Twitch raid，不使用模拟按钮或 CLI 事件。完整录制保留真实5分钟等待，剪成少于3分钟时标注时间跳转；包括 Codex 使用过程。公开素材应使用你有权展示的频道内容及自愿参与者，隐藏密钥与验证码。
