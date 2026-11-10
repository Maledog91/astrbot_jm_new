<div align="center">
  <img src="./logo.png" width="180" alt="小祥找本 Logo" style="border-radius: 20px;">
  <h1>小祥找本 (AstrBot 插件)</h1>
  
  <!-- 小徽章区域 -->
  <p>
    <a href="https://github.com/Maledog91/astrbot_jm_new/stargazers"><img src="https://img.shields.io/github/stars/Maledog91/astrbot_jm_new?style=for-the-badge&logo=github&color=gold" alt="Stars"></a>
    <a href="https://github.com/Maledog91/astrbot_jm_new/network/members"><img src="https://img.shields.io/github/forks/Maledog91/astrbot_jm_new?style=for-the-badge&logo=github" alt="Forks"></a>
    <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
    <a href="./LICENSE"><img src="https://img.shields.io/github/license/Maledog91/astrbot_jm_new?style=for-the-badge" alt="License"></a>
    <img src="https://img.shields.io/badge/AstrBot-Plugin-orange?style=for-the-badge" alt="AstrBot">
  </p>

  <p><strong>版本：v1.0.0</strong></p>
</div>

**小祥找本** 是一款基于 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 框架，并**深度依赖 [JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python) 官方底层库**开发的禁漫（JM）搜本、下本插件。

支持深度定制的人格拒绝提示、防封控发送、多章节合并转发以及精准的识图搜本。

## ✨ 功能特性

- **🔍 智能识图搜本**：支持多重括号剥离、日文优先提取。自带 50% 相似度阈值拦截，低于该值不显示，防止污染结果。
- **📝 文字精准搜本**：支持纯数字、JM号、关键词等模糊搜索，剔除严苛的相似度校验，繁简日文均可搜。
- **📥 多章节全本私发下载**：
  - **群聊触发，私聊收取**：在群聊中发送下本指令后，机器人会自动拉取**群临时会话**（或私聊），将完整的本子以**合并转发（聊天记录）**的形式发送到你的私人聊天框中。
  - **严格顺序**：完全遵循 API 的 `episode_list` 顺序，杜绝“番外”乱序；单章内图片按文件名数字自然排序。
  - **超长图拼接**：每 10 页垂直拼接为一张超长图，画质高清（1080p）且体积优化。
  - **本地路径直发**：绕过 Base64 转换，直接让协议端读取本地文件，极大降低因数据包过大被风控吞包的概率。
  - **会话预热机制**：群聊私发前自动发送文字预热（“正在发送聊天记录...”），激活临时会话通道后再发合并转发，防止被腾讯静默拦截。
- **🛡️ 全局拦截与权限**：
  - **全局白名单**：开启后，不在名单内的用户无法使用任何插件功能（群聊和私聊均拦截）。
  - **全局禁用群**：群号在黑名单中时，搜本、识图、下本全部禁用。
  - **并发控制**：内置全局互斥锁，防止多人同时下本导致服务器 CPU 100% 或 QQ 风控。
- **🤖 深度结合 AI 人格**：
  - 拒绝提示不再硬编码“高傲”语气，而是将“场景描述”直接发给大模型。
  - 完美配合用户在 AstrBot WebUI 中配置的专属人格设定，让 AI 以该人格演绎拒绝。

## 🚀 安装与使用方法

1. **安装插件**：
   在 AstrBot WebUI 的“插件管理”中，点击“从 URL 安装”，填入本仓库链接：`https://github.com/Maledog91/astrbot_jm_new`，等待拉取完成并重载插件即可。
2. **配置设置**：
   在 AstrBot WebUI 的“插件管理”中找到“小祥找本”，点击配置，根据自身需求设置指令别名、白名单、禁用群以及 AI 拒绝场景。
3. **使用指令**：
   - **文字搜本**：发送 `小祥搜本 <关键词>` （可搜名称或 JM 号）。
   - **识图搜本**：引用一张图片，发送 `小祥找本`。
   - **下载本子**：引用机器人返回的搜本结果，发送 `小祥下本`；或直接发送 `小祥下本 <JM号>`。

## ⚙️ 配置说明 (WebUI)

- **基础设置**：指令别名设置、下本功能开关、超时时间设置。
- **权限拦截**：
  - `启用私聊白名单`：开启后，不在名单内的用户将被直接拦截（不走大模型，直接文字提示）。
  - `私聊白名单`：填写允许使用的 QQ 号。
  - `禁用群号`：在此群中所有功能失效，并通过大模型进行拒绝。
- **AI 场景提示词**：
  - 包含：禁用群搜本、禁用群识图、禁用群下本、下载功能被关闭。
  - 注意事项：此处只需客观描述“发生了什么”，AI 会**自动套用你当前在 AstrBot 中配置的人格（Persona）**进行回复。

## ⚠️ 重要注意事项（必读）

1. **为什么本子不直接发在群聊，而是发私聊/临时会话？**
   - **规避腾讯极高强度的群聊风控**。短时间内发送大量图片极易触发拦截，导致机器人被禁言甚至封号，通过私发/临时会话能最大程度保证机器人的存活与消息送达率。

2. **临时会话限制**：下本功能采用的是**“群聊触发 -> 拉取群临时会话私发”**的模式。**机器人所在的群聊必须允许开启临时会话权限**，且你最好没有关闭接收陌生人消息。如果群主/管理员限制了临时会话，或者你屏蔽了群临时消息，机器人将无法把本子私发给你。

3. **协议端防吞**：临时会话（非好友私聊）受腾讯风控极严。本插件已通过“文字预热 + 本地路径读取 + 合并转发”尽最大努力防吞包。但强烈建议**将机器人添加为好友**，好友私聊的稳定性和风控容忍度远高于临时会话。

4. **识图搜本**：若 Soutubot 识图接口不可用，识图功能会提示失败，文字搜本和下本不受影响。

## 🔗 核心依赖与资源

| 资源 | 说明 |
| :--- | :--- |
| **[JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)** | **本项目核心依赖库，所有 JM 接口、下载与解析功能的上游** |
| [AstrBot 官方文档](https://astrbot.soulter.top/) | 机器人框架使用与配置指南 |
| [Soutubot](https://soutubot.moe/) | 提供免费的图片搜索接口 |

## 🙏 致谢

- 感谢 **路过的复读姬** 和 **谷Eileen** 提供的技术与灵感。
- **特别感谢 [JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python) 提供的极其强大且稳定的底层 API 支持，没有这个库，本插件根本无法运行。**

## 📝 更新日志

### v1.0.0 (初版发布)
- 实现基础的识图与文字搜本功能。
- 实现多章节严格排序、长图垂直拼接与合并转发发送。
- 引入本地路径直发与会话预热机制，大幅降低临时会话被吞包的概率。
- 引入全局白名单与禁用群机制。
- 支持向 AI 大模型传递自定义场景，完美结合 AstrBot 人格设定。

## 📄 开源协议

[MIT License](./LICENSE) 

> ⚠️ **免责声明与使用限制**
> 
> 1. 本插件**仅供小范围个人学习与娱乐享受**，严禁用于任何商业用途、倒卖或大规模公开滥用。
> 2. 使用本插件产生的一切**法律后果**与连带责任（包括但不限于因滥用导致的法律纠纷、以及 QQ 账号被风控、封禁、群聊被解散等），均由使用者自行承担。作者不对任何因使用或滥用本插件而引起的任何直接或间接的损失负责。

*PS：以上部分内容由 DeepSeek 生成，我又懒得拢了。*
