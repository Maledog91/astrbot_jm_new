<div align="center">
  <img src="./logo.png" width="160" alt="小祥找本 Logo" style="border-radius: 20px;">
  <h1>小祥找本 (AstrBot 插件)</h1>
  
  <p>基于 AstrBot 框架与 JMComic 官方底层库的搜本/下本插件。</p>
  <p>支持识图找本、临时会话防风控私发、多章节长图合并转发。</p>

  <br>

  <p>
    <a href="https://github.com/AstrBotDevs/AstrBot" target="_blank"><img src="https://img.shields.io/badge/AstrBot-Plugin-orange?style=flat-square" alt="AstrBot"></a>
    <a href="https://www.python.org/" target="_blank"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
    <a href="https://github.com/hect0x7/JMComic-Crawler-Python" target="_blank"><img src="https://img.shields.io/badge/Core-JMComic-red?style=flat-square" alt="JMComic"></a>
    <a href="https://github.com/Maledog91/astrbot_jm_new/releases" target="_blank"><img src="https://img.shields.io/badge/Version-v1.0.0-green?style=flat-square" alt="Version"></a>
    <a href="./LICENSE" target="_blank"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License"></a>
    <img src="https://img.shields.io/badge/Status-Beta-yellow?style=flat-square" alt="Status">
  </p>

  <br>

  <p>
    <a href="#-项目简介">项目简介</a> ·
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

市面上的插件往往因频繁发图导致机器人被封号，或者搜图结果混乱不堪。本项目深度依赖强大的 [JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python) 官方底层库，在保证搜本准确率的同时，创新性地引入了 **群聊触发与临时会话私发** 和 **本地路径直发** 机制，尽最大可能规避腾讯风控，保证机器人存活。

## ✨ 功能特性

- **智能识图搜本**：接入 Soutubot API，支持多重括号剥离、日文优先提取。自带 50% 相似度阈值拦截，低于该值不显示，防止污染结果。
- **文字精准搜本**：支持纯数字、JM号、关键词等模糊搜索，剔除严苛的相似度校验，繁简日文均可搜。
- **多章节全本私发下载**：
    - **群聊触发与私聊收取**：发送下本指令后，机器人自动拉取群临时会话（或私聊），将完整的本子以合并转发的形式发送。
    - **严格顺序**：完全遵循 API 的 `episode_list` 顺序，杜绝番外乱序；单章内图片按文件名数字自然排序。
    - **超长图拼接**：每 10 页垂直拼接为一张超长图，画质高清（1080p）且体积优化。
    - **本地路径直发**：绕过 Base64 转换，直接让协议端读取本地文件，极大降低因数据包过大被风控吞包的概率。
    - **会话预热机制**：群聊私发前自动发送文字预热，激活临时会话通道后再发合并转发。
- **全局拦截与权限**：
    - **全局白名单**：开启后，不在名单内的用户无法使用任何插件功能。
    - **全局禁用群**：群号在黑名单中时，搜本、识图、下本全部禁用。
    - **并发控制**：内置全局互斥锁，防止多人同时下本导致服务器 CPU 100% 或 QQ 风控。
- **深度结合 AI 人格**：
    - 拒绝提示不再硬编码，而是将场景描述发给大模型，完美配合你设置的专属人格。

## 🚀 安装与使用方法

### 1. 安装插件

在 AstrBot WebUI 的“插件管理”中，点击“从 URL 安装”，填入本仓库链接，等待拉取完成并重载即可：

```text
https://github.com/Maledog91/astrbot_jm_new
