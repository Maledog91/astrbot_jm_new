<div align="center">
  <img src="./logo.png" width="160" alt="小祥找本 Logo" style="border-radius: 20px;">
  <h1>小祥找本 (AstrBot 插件)</h1>
  
  <p>基于 AstrBot 框架与 JMComic 官方底层库的搜本/下本插件。</p>
  <p>支持识图找本、临时会话防风控私发、多章节长图合并转发。</p>

  <br>

  <!-- 徽章墙 -->
  <p>
    <a href="https://github.com/AstrBotDevs/AstrBot" target="_blank"><img src="https://img.shields.io/badge/AstrBot-Plugin-orange?style=flat-square" alt="AstrBot"></a>
    <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
    <a href="https://github.com/hect0x7/JMComic-Crawler-Python" target="_blank"><img src="https://img.shields.io/badge/Core-JMComic-red?style=flat-square" alt="JMComic"></a>
    <a href="https://github.com/Maledog91/astrbot_jm_new/releases" target="_blank"><img src="https://img.shields.io/badge/Version-v1.0.0-green?style=flat-square" alt="Version"></a>
    <a href="./LICENSE" target="_blank"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License"></a>
    <img src="https://img.shields.io/badge/Status-Beta-yellow?style=flat-square" alt="Status">
  </p>

  <br>

  <!-- 快捷导航 -->
  <p>
    <a href="#-功能特性">功能特性</a> ·
    <a href="#-安装与使用方法">安装与使用方法</a> ·
    <a href="#-核心依赖与资源">核心依赖</a> ·
    <a href="#-重要注意事项">注意事项</a> ·
    <a href="#-开源协议">开源协议</a>
  </p>
</div>

---

## 📖 项目简介

**小祥找本** 是一个运行在 AstrBot 框架上的禁漫（JM）搜本与下本插件。

市面上的插件往往因频繁发图导致机器人被封号，或者搜图结果混乱不堪。本项目深度依赖强大的 **[JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)** 官方底层库，在保证搜本准确率的同时，创新性地引入了 **群聊触发与临时会话私发** 和 **本地路径直发** 机制，尽最大可能规避腾讯风控，保证机器人存活。

## ✨ 功能特性

- 🔍 **智能识图搜本**：接入 Soutubot API，支持多重括号剥离、日文优先提取。自带 50% 相似度阈值拦截，低于该值不显示，防止污染结果。
- 📝 **文字精准搜本**：支持纯数字、JM号、关键词等模糊搜索，剔除严苛的相似度校验，繁简日文均可搜。
- 📥 **多章节全本私发下载**：
    - **群聊触发与私聊收取**：发送下本指令后，机器人自动拉取群临时会话（或私聊），将完整的本子以合并转发的形式发送。
    - **严格顺序**：完全遵循 API 的 `episode_list` 顺序，杜绝番外乱序；单章内图片按文件名数字自然排序。
    - **超长图拼接**：每 10 页垂直拼接为一张超长图，画质高清（1080p）且体积优化。
    - **本地路径直发**：绕过 Base64 转换，直接让协议端读取本地文件，极大降低因数据包过大被风控吞包的概率。
    - **会话预热机制**：群聊私发前自动发送文字预热，激活临时会话通道后再发合并转发。
- 🛡️ **全局拦截与权限**：
    - **全局白名单**：开启后，不在名单内的用户无法使用任何插件功能。
    - **全局禁用群**：群号在黑名单中时，搜本、识图、下本全部禁用。
    - **并发控制**：内置全局互斥锁，防止多人同时下本导致服务器 CPU 100% 或 QQ 风控。
- 🤖 **深度结合 AI 人格**：
    - 拒绝提示不再硬编码，而是将场景描述发给大模型，完美配合你设置的专属人格。

## 🚀 安装与使用方法

1. **安装插件**：在 AstrBot WebUI 的“插件管理”中，点击“从 URL 安装”，填入本仓库链接：`https://github.com/Maledog91/astrbot_jm_new`，等待拉取完成并重载。
2. **配置设置**：在 AstrBot WebUI 中点击“小祥找本”的配置，根据需求设置指令别名、白名单、禁用群以及 AI 拒绝场景。
3. **使用指令**：
    - **文字搜本**：发送 `小祥搜本 <关键词>`
    - **识图搜本**：引用一张图片，发送 `小祥找本`
    - **下载本子**：引用搜本结果发送 `小祥下本`；或直接发送 `小祥下本 <JM号>`

## ⚠️ 重要注意事项

1. **为什么本子不直接发在群聊，而是发私聊/临时会话？**
   为了规避腾讯极高强度的群聊风控。短时间内发送大量图片极易触发拦截，导致机器人被禁言甚至封号。同时也能防止刷屏。
2. **临时会话限制**：下本功能采用“群聊触发 -> 拉取群临时会话私发”模式。**机器人所在的群聊必须允许开启临时会话权限**，否则将无法发送。
3. **协议端防吞**：临时会话受腾讯风控极严。强烈建议 **将机器人添加为好友**，好友私聊的稳定性和风控容忍度远高于临时会话。
4. **识图接口**：若 Soutubot 接口不可用，识图功能会提示失败，文字搜本和下本不受影响。

## 🔗 核心依赖与资源

| 资源 | 说明 |
| :--- | :--- |
| **[JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)** | **本项目核心依赖库，所有 JM 接口、下载与解析功能的上游** |
| [AstrBot 官方文档](https://docs.astrbot.app) | 机器人框架使用与配置指南 |
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
> 1. 本插件 **仅供小范围个人学习与娱乐享受**，严禁用于任何商业用途、倒卖或大规模公开滥用。
> 2. 使用本插件产生的一切 **法律后果** 与连带责任（包括但不限于因滥用导致的法律纠纷、以及 QQ 账号被风控、封禁、群聊被解散等），均由使用者自行承担。作者不对任何因使用或滥用本插件而引起的任何直接或间接的损失负责。

*PS：以上部分内容由 DeepSeek 生成，我又懒得拢了。*
