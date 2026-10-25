# 当前测试：HTML 音频 → Twitch B 与 Raid Handshake

> 前期中文操作记录。新版入口为 Settings → Audio 与 Start listening；当前英文版本见[OBS audio setup](OBS_AUDIO_SETUP.md)。

适用于你现在的组合：手机 A `thisisraida` 正在直播；电脑 OBS 以 B `thisisraidb` 直播 `tmp/index.html`。不需要对着麦克风讲话。

2026-10-25 已读取本机保存的配置：OBS 32.2.2；HTML 浏览器来源的“通过 OBS 控制音频”未勾选；桌面音频采集 EDIFIER 扬声器；Windows 默认播放设备也是 EDIFIER。控制台支持回录这个播放设备。

## 1. 让两个程序取得同一份声音

| 位置 | 选择 / 操作 |
| --- | --- |
| Windows 声音输出 | `扬声器 (EDIFIER Halo Soundbar)` |
| OBS → 设置 → 音频 → 桌面音频 | 同一个 EDIFIER 设备；已选好时保持现状 |
| OBS → 混音器 → 桌面音频 | 保持输出未静音，播放语音时应有电平跳动 |
| OBS → 混音器 → 麦克风/辅助音频 | 点击扬声器图标，将物理麦克风静音 |
| HTML 浏览器来源 → 属性 | “通过 OBS 控制音频 / Control audio via OBS”保持未勾选 |
| Raid Handshake → Audio input | `扬声器 (EDIFIER Halo Soundbar) · system playback` |

这条路径让 HTML 先把 MP3 播放到 Windows 输出设备；OBS 通过桌面音频把它推给 Twitch；Raid Handshake 从同一设备回录并转录。控制台里的 `system playback` 表示系统播放回录，虽然它出现在 Audio input 菜单里，但不要求物理麦克风。

当前路径无需开启 OBS 音频监听，也无需添加虚拟声卡。不要同时启用另一套音频路由，否则可能出现重复声音。

依据：[OBS 浏览器音频路由源码](https://github.com/obsproject/obs-browser/blob/master/browser-client.cpp)、[OBS 音频混音器说明](https://obsproject.com/kb/audio-mixer-guide)。

## 2. 确认 HTML 的声音确实播放了

1. OBS 保持当前 `浏览器` 来源可见。文件路径是 `E:/Projects/Musabika/Codex_TwitchCon/tmp/index.html`。
2. 它引用的 `raid-b-test.mp3` 已确认存在于同目录，页面设置为自动循环播放。
3. 你应能从 EDIFIER 听到“Hi, This is Raid B Test”；同时 OBS 的“桌面音频”电平应跳动。
4. 如果没有声音，在 OBS 右键该浏览器来源 → **交互 / Interact**。若出现“点击开启循环语音”，点击它；也可以点击页面空白处，页面会再次尝试播放。
5. 仍无声音时检查 Windows 输出设备、音量混合器中 OBS/浏览器音频的音量，以及 OBS 桌面音频是否静音。保持 Windows 和应用音量可听见。

只需要 OBS 中这一份 HTML 播放。电脑上其他打开同一 HTML 的浏览器标签页应暂停或关闭，避免同一句话叠加。

## 3. 在本地控制台启动回录

1. 打开 [本地控制台](http://127.0.0.1:8765)。
2. 在右侧 **02 · Live context with OpenAI** 找到 **Audio input**。
3. 点击旁边的 **↻** 刷新设备，然后选择：

   **扬声器 (EDIFIER Halo Soundbar) · system playback**

4. 点击 **Start audio**。如果当前按钮是 **Stop audio**，先停止，重新选择设备，再启动。
5. 保持 HTML 持续播放，观察控制台小音量条是否有变化。程序按 8 秒处理有声片段，随后调用 OpenAI。
6. 展开 **Recent transcript**，应看到与 MP3 相符的英文；再等待 **OPENAI CONTEXT → Summary ready**。已有转录但摘要尚未出现时，可点一次 **Refresh summary**。

只重复一句话时，摘要也应很简单，不能期待生成并未出现在音频里的活动内容。该音频确实由 B 直播出去，就可以验证当前真实音频链路。

## 4. Twitch 端的设置

Twitch 不需要再选择电脑麦克风；B 的直播音轨由 OBS 推送。A 的手机直播继续保持。

电脑上 A、B 的 Twitch 网页播放器保持静音，聊天仍然可以使用。否则播放器中延迟回来的直播音频也会进入桌面音频和系统回录，形成重复或回声。可用独立设备或请真实测试参与者确认 B 的直播声音；不要为此中断手机 A 的直播。

## 5. 给 OBS 加入第二个浏览器来源

当前 HTML 是 B 的直播内容。来客小抄需要独立的 overlay 来源：

1. 控制台右上角 **Copy OBS URL**。
2. OBS → 来源 → **＋ → 浏览器 → 新建**，命名 `Raid Handshake Overlay`。
3. 这个新来源的“本地文件”不勾选，在 URL 中粘贴复制的地址。不要覆盖原来播放 `index.html` 的来源。
4. 宽高填 **1920 × 1080**；如需铺满当前画布，右键新来源 → 变换 → 适配屏幕。
5. 将 overlay 排在原 HTML 来源上方。等待 raid 时显示待机状态属于正常情况。

## 6. 什么时候可以 raid

确认 OBS 桌面音频电平正常、控制台已有对应转录、摘要显示 **Summary ready**，并且 Twitch Events 和 Chatters Baseline 正常后，再按[第一次真实 raid 指南](FIRST_REAL_RAID.zh-CN.md#7-发起第一次真实-raid)从 A 发起 `/raid thisisraidb`。

落地卡须在控制台查看最终文字后，用 **Send to Twitch chat** 或 **Ctrl+Shift+Enter** 确认发送。首次连通继续使用默认的手动确认模式。

## 7. 按症状排查

| 现象 | 排查位置 |
| --- | --- |
| OBS 桌面音频电平不动 | HTML 是否播放、Windows/OBS 是否静音、桌面音频是否指向 EDIFIER |
| OBS 有电平，控制台无电平 | 是否选了 EDIFIER 的 `system playback`，并点击 Start audio |
| 控制台有电平，尚无转录 | 等待完整片段；检查 Audio 下方的错误，特别是 API 额度/模型访问错误 |
| 有转录，无摘要 | 等待摘要更新或点一次 Refresh summary；查看摘要区域的错误 |
| 语音重复或延迟回声 | 关闭额外 HTML 播放，静音电脑 Twitch 播放器，保持当前单一路由 |

若有错误，只需提供控制台错误文字；无需发送 API key、登录验证码或 stream key。
