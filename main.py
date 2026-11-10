import base64
import json
import time
import asyncio
import aiohttp
import os
import re
import random
import traceback
import shutil
import io
import uuid
import unicodedata
from pathlib import Path
from astrbot.api import logger
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api.message_components import Node, Nodes, Image, Plain, At

try:
    from PIL import Image as PILImage
except ImportError:
    PILImage = None

CACHE_DIR = Path(__file__).parent / "cache"

@register("astrbot_jm_new", "X", "小祥找本", "v1.0.5")
class XiaoXiangJM(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        cfg = config or {}
        self.image_cmd = str(cfg.get("image_cmd", "小祥找本")).strip()
        self.text_cmd = str(cfg.get("text_cmd", "小祥搜本")).strip()
        self.download_cmd = str(cfg.get("download_cmd", "小祥下本")).strip()
        self.enable_download = cfg.get("enable_download", True)
        
        self.enable_private_whitelist = cfg.get("enable_private_whitelist", True)
        self.private_whitelist = [str(q).strip() for q in cfg.get("private_whitelist", []) if str(q).strip()]
        self.search_disabled = [str(g).strip() for g in cfg.get("search_disabled_groups", []) if str(g).strip()]
        
        self.whitelist_blocked_msg = ["您不在私聊白名单中，无法使用该功能。"]
        self.disabled_msg = ["此群已禁用。"]
        self.download_disabled_msg = ["下载功能已关闭。"]
        
        self.scene_group_disabled_search = str(cfg.get("scene_group_disabled_search", "有人试图在禁用的群聊里进行搜本，请拒绝他。"))
        self.scene_group_disabled_image = str(cfg.get("scene_group_disabled_image", "有人试图在禁用的群聊里进行识图找本，请拒绝他。"))
        self.scene_group_disabled_download = str(cfg.get("scene_group_disabled_download", "有人试图在禁用的群聊里进行下载，请拒绝他。"))
        self.scene_download_disabled = str(cfg.get("scene_download_disabled", "有人试图使用下载功能，但该功能已被管理员关闭，请拒绝他。"))
        
        self.ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        self.timeout = int(cfg.get("timeout", 30))
        self.download_lock = asyncio.Lock()
        
        CACHE_DIR.mkdir(exist_ok=True)
        self.clean_all_cache_now()
        asyncio.create_task(self.clean_garbage_cache_task())

    async def get_persona_reply(self, event: AstrMessageEvent, scene: str, fallback_msgs: list):
        try:
            umo = event.unified_msg_origin
            provider_id = await self.context.get_current_chat_provider_id(umo=umo)
            if not provider_id: raise ValueError("未配置对话模型")
            llm_resp = await self.context.llm_generate(chat_provider_id=provider_id, prompt=scene)
            reply = llm_resp.completion_text.strip()
            if reply: 
                return reply.replace('"', '').replace('“', '').replace('”', '')
        except Exception as e:
            logger.warning(f"LLM 生成语录失败，使用本地兜底: {e}")
        return random.choice(fallback_msgs)

    def clean_all_cache_now(self):
        for item in CACHE_DIR.iterdir():
            if item.name == '.gitkeep': continue
            try:
                if item.is_dir(): shutil.rmtree(item, ignore_errors=True)
                else: item.unlink(missing_ok=True)
            except Exception: pass

    async def clean_garbage_cache_task(self):
        while True:
            try:
                now = time.time()
                for item in CACHE_DIR.iterdir():
                    if item.name == '.gitkeep': continue
                    if now - item.stat().st_mtime > 300:
                        if item.is_dir(): shutil.rmtree(item, ignore_errors=True)
                        else: item.unlink(missing_ok=True)
            except Exception: pass
            await asyncio.sleep(600)

    def deep_find(self, obj, target_keys):
        results = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in target_keys and v: results.append(v)
                results.extend(self.deep_find(v, target_keys))
        elif isinstance(obj, list):
            for item in obj: results.extend(self.deep_find(item, target_keys))
        return results

    def get_similarity(self, item):
        score = item.get("score") or item.get("similarity")
        if score is not None:
            try:
                val = float(str(score).replace("%", ""))
                if val <= 1.0 and val > 0: val *= 100
                return val
            except: pass
        scores = self.deep_find(item, ["score", "similarity", "best_similarity", "work_best_similarity"])
        for s in scores:
            try:
                val = float(str(s).replace("%", ""))
                if val <= 1.0 and val > 0: val *= 100
                if val > 0: return val
            except: pass
        return 0.0

    def extract_all_texts(self, obj, results):
        if isinstance(obj, str):
            s = obj.strip()
            if len(s) > 1 and not s.isdigit():
                lower_s = s.lower()
                if not any(x in lower_s for x in [".webp", ".jpg", ".png", ".gif", "http", "www.", "nhentai", "soutubot"]):
                    results.append(s)
        elif isinstance(obj, dict):
            for v in obj.values(): self.extract_all_texts(v, results)
        elif isinstance(obj, list):
            for item in obj: self.extract_all_texts(item, results)

    def extract_candidates(self, raw_strings):
        if not raw_strings: return []
        candidates = []
        jp_lines = [s for s in raw_strings if re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', s)]
        for line in (jp_lines if jp_lines else raw_strings):
            text = re.sub(r'\[[^\]]*\]|【[^】]*】', ' ', line)
            text = re.sub(r'[\(（]\s*C\d+\s*[\)）]|\bC\d{2,3}\b', ' ', text)
            text = re.sub(r'[\(（][^\)）]*(?:COMIC|Vol\.\d+|雑誌|\d{4}[-年]\d{1,2}[月号]|DL版|Digital|中国翻訳|汉化|漢化|無修正|英訳|Chinese|ZH|Translation)[^\)）]*[\)）]', ' ', text, flags=re.I)
            pure = re.sub(r'[\(（][^\)）]*[\)）]', ' ', text)
            pure = re.split(r'[~～]', re.sub(r'\s+', ' ', pure).strip())[0].strip()
            if len(pure) >= 2: candidates.append(pure)
            keep = re.split(r'[~～]', re.sub(r'\s+', ' ', text).strip())[0].strip()
            if len(keep) >= 2: candidates.append(keep)
            
        kill_words = ["english", "chinese", "japanese", "language", "translation", "original"]
        final_candidates = []
        for c in candidates:
            cl = c.lower()
            if cl in kill_words: continue
            if c.isdigit(): continue
            if c not in final_candidates:
                final_candidates.append(c)
                
        return final_candidates

    def search_jm(self, keyword):
        if len(keyword) < 2: return False, "❌ 词太短"
        try:
            from jmcomic import JmOption
            client = JmOption.default().new_jm_client()
            page = client.search_site(search_query=keyword, page=1)
            if page.total == 0: return False, "❌ 无结果"
            for aid, title in page.iter_id_title():
                album = client.get_album_detail(aid)
                authors = ", ".join(album.author) if isinstance(album.author, list) else str(album.author)
                return True, (aid, title, authors, 1.0)
            return False, "❌ 无结果"
        except Exception as e: 
            return False, f"❌ 报错: {str(e)}"

    def create_long_image(self, img_paths, out_path):
        if not PILImage: return False
        try:
            images = [PILImage.open(p) for p in img_paths]
            target_width, resized_images, total_height = 1080, [], 0
            for img in images:
                w, h = img.size
                if w != target_width:
                    new_h = int(h * (target_width / w))
                    img = img.resize((target_width, new_h), PILImage.Resampling.LANCZOS)
                resized_images.append(img)
                total_height += img.size[1]
            long_img = PILImage.new("RGB", (target_width, total_height), (255, 255, 255))
            y_offset = 0
            for img in resized_images:
                long_img.paste(img, (0, y_offset))
                y_offset += img.size[1]
            long_img.save(out_path, format="JPEG", quality=90, optimize=True)
            return True
        except Exception as e: 
            logger.error(f"拼接长图失败: {e}")
            return False

    def download_single_chapter(self, option, photo_id, temp_dir):
        option.dir_rule.base_dir = str(temp_dir)
        try: 
            option.download_photo(photo_id)
        except Exception as e: 
            logger.error(f"底层下载单章 {photo_id} 失败: {e}")
            return False
        
        img_exts = {'.jpg', '.jpeg', '.png', '.webp'}
        all_files = [f for f in temp_dir.rglob('*') if f.suffix.lower() in img_exts and f.is_file()]
        
        def extract_num(f):
            m = re.search(r'(\d+)', f.name)
            return int(m.group(1)) if m else 999999
            
        all_files.sort(key=extract_num)
        
        temp_pics = []
        for idx, f in enumerate(all_files):
            new_name = temp_dir / f"temp_{uuid.uuid4().hex}_{idx:04d}.jpg"
            if PILImage:
                try:
                    img = PILImage.open(f).convert("RGB")
                    img.thumbnail((1080, 1080))
                    img.save(new_name, format="JPEG", quality=90, optimize=True)
                    temp_pics.append(str(new_name))
                except Exception: 
                    temp_pics.append(str(f))
            else: 
                temp_pics.append(str(f))
        return temp_pics

    @filter.regex(r".+")
    async def on_message(self, event: AstrMessageEvent):
        message_str = event.message_str.strip()
        group_id = event.get_group_id()
        sender_id = str(event.get_sender_id())
        is_dl_cmd = message_str.startswith(self.download_cmd)
        is_txt_cmd = message_str.startswith(self.text_cmd)
        is_img_cmd = (message_str == self.image_cmd)
        is_plugin_cmd = is_dl_cmd or is_txt_cmd or is_img_cmd

        if is_plugin_cmd and self.enable_private_whitelist and len(self.private_whitelist) > 0:
            if sender_id not in self.private_whitelist:
                msg = random.choice(self.whitelist_blocked_msg)
                if not group_id: yield event.plain_result(msg)
                else: yield event.chain_result([At(qq=sender_id), Plain(f" {msg}")])
                return

        if is_plugin_cmd and group_id and str(group_id) in self.search_disabled:
            if is_dl_cmd: 
                msg = await self.get_persona_reply(event, self.scene_group_disabled_download, self.disabled_msg)
            elif is_txt_cmd: 
                msg = await self.get_persona_reply(event, self.scene_group_disabled_search, self.disabled_msg)
            else: 
                msg = await self.get_persona_reply(event, self.scene_group_disabled_image, self.disabled_msg)
            yield event.plain_result(msg)
            return

        if is_dl_cmd:
            if not self.enable_download:
                msg = await self.get_persona_reply(event, self.scene_download_disabled, self.download_disabled_msg)
                if not group_id: yield event.plain_result(msg)
                else: yield event.chain_result([At(qq=sender_id), Plain(f" {msg}")])
                return
                
            keyword = message_str[len(self.download_cmd):].strip()
            album_id = ""
            raw_msg = event.message_obj.raw_message.get("message", [])
            segs = json.loads(raw_msg) if isinstance(raw_msg, str) else raw_msg
            reply_id = next((x.get("data", {}).get("id") for x in segs if isinstance(x, dict) and x.get("type") == "reply"), None)
            if reply_id:
                msg_data = await event.bot.call_action("get_msg", message_id=int(reply_id))
                raw_text = ""
                def walk_text(obj):
                    nonlocal raw_text
                    if isinstance(obj, dict):
                        if obj.get("type") == "text": raw_text += obj.get("data", {}).get("text", "")
                        for v in obj.values(): walk_text(v)
                    elif isinstance(obj, list):
                        for it in obj: walk_text(it)
                walk_text(msg_data)
                match = re.search(r'JM号[:：]\s*(\d+)', raw_text) or re.search(r'JM(\d+)', raw_text, re.IGNORECASE)
                if match: album_id = match.group(1)
                
            if not album_id and keyword:
                kw_norm = unicodedata.normalize('NFKC', keyword)
                match = re.search(r'(\d+)', kw_norm)
                if match: album_id = match.group(1)
                
            if not album_id:
                msg = "⚠️ 未从你的输入中提取到有效的 JM号，请发送纯数字或带JM前缀的数字。"
                if not group_id: yield event.plain_result(msg)
                else: yield event.chain_result([At(qq=sender_id), Plain(f" {msg}")])
                return

            if self.download_lock.locked():
                msg = "⚠️ 当前有其他人在下载中，已为你加入队列，请耐心等待前面的人下载完..."
                if not group_id: yield event.plain_result(msg)
                else: yield event.chain_result([At(qq=sender_id), Plain(f" {msg}")])

            async with self.download_lock:
                if not group_id: 
                    yield event.plain_result(f"正在后台准备，即将按序逐章下载并发送 JM{album_id}...")
                else: 
                    yield event.plain_result(f"正在后台准备，即将按序逐章下载并私发给你...")
                
                try:
                    from jmcomic import JmOption
                    option = JmOption.default()
                    client = option.new_jm_client()
                    
                    album_detail = client.get_album_detail(album_id)
                    episodes = album_detail.episode_list
                    
                    if not episodes:
                        episodes = [None] 
                        
                    target_user_id = int(sender_id)
                    risk_blocked = False     
                    no_permission = False    
                    sent_count = 0
                    
                    album_title = getattr(album_detail, 'title', '') or getattr(album_detail, 'name', '') or ""
                    
                    try:
                        bot_info = await event.bot.call_action("get_login_info")
                        self_id = int(bot_info.get("user_id"))
                        bot_name = bot_info.get("nickname", "小祥找本")
                    except Exception:
                        self_id = getattr(event, 'self_id', 10000)
                        if isinstance(self_id, str) and self_id.isdigit(): self_id = int(self_id)
                        bot_name = "小祥找本"

                    for i, ep in enumerate(episodes):
                        photo_id = album_id
                        ep_index = i + 1
                        ep_raw_name = ""
                        
                        if ep:
                            photo_id = getattr(ep, 'photo_id', None) or getattr(ep, 'id', None)
                            ep_raw_name = getattr(ep, 'name', None) or getattr(ep, 'title', None) or ""
                            ep_index = getattr(ep, 'index', None) or getattr(ep, 'sort', None) or (i + 1)
                            
                            if not photo_id:
                                if isinstance(ep, (tuple, list)):
                                    photo_id = str(ep[0]) if len(ep) > 0 else None
                                    ep_index = ep[1] if len(ep) > 1 else i + 1
                                    ep_raw_name = str(ep[2]).strip() if len(ep) > 2 and ep[2] else ""
                                elif isinstance(ep, dict):
                                    photo_id = ep.get('photo_id') or ep.get('id')
                                    ep_raw_name = ep.get('name') or ep.get('title') or ""
                                    ep_index = ep.get('index') or ep.get('sort') or (i + 1)
                                    
                            if not ep_raw_name:
                                ep_raw_name = album_title
                                
                        if not photo_id:
                            logger.error(f"【小祥排查】无法从 {ep} 提取 photo_id")
                            continue
                            
                        temp_dir = CACHE_DIR / f"JM_{album_id}_{i}_{uuid.uuid4().hex}"
                        if temp_dir.exists(): shutil.rmtree(temp_dir)
                        temp_dir.mkdir(parents=True, exist_ok=True)
                        
                        logger.info(f"【小祥排查】开始下载单章：第{ep_index}话 {ep_raw_name}，ID：{photo_id}")
                        temp_pics = await asyncio.to_thread(self.download_single_chapter, option, photo_id, temp_dir)
                        
                        if not temp_pics:
                            logger.error(f"【小祥排查】章节 {ep_index} 没有下载到图片")
                            continue
                            
                        idx_str = str(ep_index)
                        clean_name = re.sub(r'\s+', ' ', ep_raw_name).strip()
                        clean_album = re.sub(r'\s+', ' ', album_title).strip()
                        
                        if clean_name and (idx_str in clean_name or f"第{idx_str}话" in clean_name or f"第{idx_str}章" in clean_name):
                            text_header = clean_name
                        elif clean_name:
                            text_header = f"第{idx_str}话 {clean_name}"
                        else:
                            text_header = f"第{idx_str}话"
                            
                        if clean_album and clean_album not in text_header:
                            text_header += f" - {clean_album}"
                            
                        text_header = text_header.replace('\n', '').replace('\r', '').strip()

                        long_pics = []
                        for k in range(0, len(temp_pics), 10):
                            sub_chunk = temp_pics[k:k+10]
                            out_path = str(temp_dir / f"long_{uuid.uuid4().hex}.jpg")
                            if self.create_long_image(sub_chunk, out_path):
                                long_pics.append(out_path)
                            else:
                                long_pics.extend(sub_chunk)
                                
                        nodes_data = []
                        nodes_data.append({
                            "type": "node",
                            "data": {
                                "user_id": self_id,
                                "nickname": bot_name,
                                "content": [{"type": "text", "data": {"text": text_header}}]
                            }
                        })
                        
                        for p in long_pics:
                            content = [
                                {"type": "image", "data": {"file": f"file://{p}"}}
                            ]
                            nodes_data.append({
                                "type": "node",
                                "data": {
                                    "user_id": self_id,
                                    "nickname": bot_name,
                                    "content": content
                                }
                            })
                                
                        try:
                            if group_id:
                                await event.bot.call_action(
                                    "send_private_msg",
                                    user_id=target_user_id,
                                    group_id=int(group_id),
                                    message=[{"type": "text", "data": {"text": f"正在发送【{text_header}】的聊天记录，请稍候..."}}]
                                )
                                await asyncio.sleep(1.5)
                                await event.bot.call_action(
                                    "send_private_forward_msg",
                                    user_id=target_user_id,
                                    group_id=int(group_id),
                                    messages=nodes_data
                                )
                            else:
                                await event.bot.call_action("send_private_forward_msg", user_id=target_user_id, messages=nodes_data)

                            logger.info(f"【小祥排查】{text_header} 合并转发发送成功")
                            sent_count += 1
                            await asyncio.sleep(2)
                        except Exception as e:
                            logger.error(f"【小祥排查】{text_header} 私聊发图失败: {e}")
                            if not risk_blocked and not no_permission:
                                try:
                                    await event.bot.call_action(
                                        "send_private_msg",
                                        user_id=target_user_id,
                                        group_id=int(group_id) if group_id else None,
                                        message=[{"type": "text", "data": {"text": "（探测消息，请忽略）"}}]
                                    )
                                    risk_blocked = True
                                except Exception:
                                    no_permission = True
                                    
                        if temp_dir.exists(): shutil.rmtree(temp_dir, ignore_errors=True)
                        if no_permission:
                            break
                            
                    if no_permission:
                        if group_id:
                            yield event.chain_result([At(qq=sender_id), Plain(" ⚠️ 私发失败。本群可能禁止临时会话或未加好友，请添加小祥后私聊获取。")])
                        else:
                            yield event.plain_result("⚠️ 私聊发图失败。请确认是否已添加小祥为好友。")
                    elif risk_blocked:
                        if group_id:
                            yield event.chain_result([At(qq=sender_id), Plain(" ❌ 图片被风控拦截，部分章节发送失败。")])
                        else:
                            yield event.plain_result("❌ 图片被风控拦截，请稍后重试。")
                    elif sent_count > 0 and group_id:
                        yield event.chain_result([At(qq=sender_id), Plain(" ✅ 本子已全部私聊发送，请查收。")])
                        
                except Exception as e:
                    logger.error(f"【小祥排查】串行任务崩溃: {traceback.format_exc()}")
                    yield event.plain_result(f"❌ 下载出错：{e}")
            return

        if is_txt_cmd:
            keyword = message_str[len(self.text_cmd):].strip()
            if not keyword:
                yield event.plain_result(f"请带上要搜的名字哦，比如：{self.text_cmd} 催眠手机")
                return
            yield event.plain_result("正在检索...")
            
            success, msg = await asyncio.to_thread(self.search_jm, keyword)
            if success:
                album_id, album_title, authors, ratio = msg
                download_tip = f"\n\n💡 提示：引用本条消息并发送「{self.download_cmd}」就可以下载哦。" if self.enable_download else ""
                final_output = f"🎯匹配成功！\nJM号： {album_id}\n作品名：{album_title}\n作者： {authors}\n\n⚠️注意：文字检索可能存在误差。{download_tip}"
                yield event.plain_result(final_output)
            else: 
                yield event.plain_result(f"💔 尝试搜索「{keyword}」，但是 {msg}")
            return

        if not is_img_cmd: return
        raw_msg = event.message_obj.raw_message.get("message", [])
        segs = json.loads(raw_msg) if isinstance(raw_msg, str) else raw_msg
        reply_id = next((x.get("data", {}).get("id") for x in segs if isinstance(x, dict) and x.get("type") == "reply"), None)
        if not reply_id: return
        try:
            msg_data = await event.bot.call_action("get_msg", message_id=int(reply_id))
            img_data = None
            def walk_img(obj):
                nonlocal img_data
                if img_data: return
                if isinstance(obj, dict):
                    if obj.get("type") == "image": img_data = obj.get("data", {}); return
                    for v in obj.values(): walk_img(v)
                elif isinstance(obj, list):
                    for it in obj: walk_img(it)
            walk_img(msg_data)
            if not img_data: 
                yield event.plain_result("引用的消息没有图片呢。")
                return
            img_bytes = None
            url = img_data.get("url")
            file_name = img_data.get("file")
            yield event.plain_result("正在检索...")
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                if url and str(url).startswith("http"):
                    try:
                        async with session.get(url, headers={"User-Agent": self.ua}) as resp:
                            if resp.status == 200: img_bytes = await resp.read()
                    except Exception: pass
                if not img_bytes and file_name:
                    if file_name.startswith("base64://"): img_bytes = base64.b64decode(file_name.replace("base64://", ""))
                    elif os.path.exists(file_name):
                        with open(file_name, "rb") as f: img_bytes = f.read()
                if not img_bytes: 
                    yield event.plain_result("❌ 无法读取图片数据。")
                    return
                ts = int(time.time())
                api_key = base64.b64encode(str(ts * ts + len(self.ua) ** 2 + 3331358690401).encode()).decode()[::-1].replace("=", "")
                res_json = None
                for attempt in range(3):
                    try:
                        form = aiohttp.FormData()
                        form.add_field("file", img_bytes, filename="image.jpg", content_type="image/jpeg")
                        form.add_field("factor", "1.2")
                        headers = {"User-Agent": self.ua, "X-API-KEY": api_key, "Referer": "https://soutubot.moe/"}
                        async with session.post("https://soutubot.moe/api/search", data=form, headers=headers) as resp:
                            res_json = await resp.json(content_type=None); break
                    except Exception as e:
                        if attempt == 2: 
                            yield event.plain_result("❌ 连接识图服务器失败，请检查网络。")
                            return
                        await asyncio.sleep(2)
            result_id = res_json.get("result_id") if res_json else None
            if not result_id: 
                yield event.plain_result("❌ 识图接口未返回任务ID。")
                return
            await asyncio.sleep(2.5)
            res_headers = {"User-Agent": self.ua, "Referer": f"https://soutubot.moe/results/{result_id}"}
            raw_text = None
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                for attempt in range(3):
                    try:
                        async with session.get(f"https://soutubot.moe/api/results/{result_id}", headers=res_headers) as resp:
                            raw_text = await resp.text(); break
                    except Exception as e:
                        if attempt == 2: 
                            yield event.plain_result("❌ 获取识图结果时网络断开。")
                            return
                        await asyncio.sleep(2)
            data = json.loads(raw_text)
            data_list = data.get("data", []) or data.get("results", [])
            if not data_list: 
                yield event.plain_result("❌ 没有搜到相似的图呢。")
                return
            
            data_list.sort(key=self.get_similarity, reverse=True)
            
            highest_score = self.get_similarity(data_list[0]) if data_list else 0
            if highest_score < 50:
                yield event.plain_result(f"💔 Soutubot 未找到高置信度结果（最高相似度仅 {int(highest_score)}%），已自动拦截。\n如果你确定有这本，请尝试手动发送：小祥搜本 关键词")
                return

            all_jp_zh_words = []
            all_en_words = []
            debug_titles = []
            
            for item_idx, best_item in enumerate(data_list[:3]):
                score = self.get_similarity(best_item)
                if score < 50: continue
                
                raw_strings = []
                self.extract_all_texts(best_item, raw_strings)
                
                if not raw_strings:
                    debug_titles.append("【无有效字符串】")
                    continue
                    
                debug_titles.append(f"捕获词：{raw_strings[0][:20]}...")

                candidates = self.extract_candidates(raw_strings)

                for kw in candidates:
                    if re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', kw):
                        if (score, kw) not in all_jp_zh_words:
                            all_jp_zh_words.append((score, kw))
                    else:
                        if (score, kw) not in all_en_words:
                            all_en_words.append((score, kw))
                            
            all_jp_zh_words.sort(key=lambda x: x[0], reverse=True)
            all_en_words.sort(key=lambda x: x[0], reverse=True)

            found = False
            tried_info = []
            
            for score, kw in all_jp_zh_words:
                success, msg = await asyncio.to_thread(self.search_jm, kw)
                if success:
                    album_id, album_title, authors, jm_ratio = msg
                    download_tip = f"\n\n💡 提示：引用本条消息并发送「{self.download_cmd}」就可以下载哦。" if self.enable_download else ""
                    low_conf_warn = "⚠️注意：识图相似度较低，请自行核对。" if score < 75 else "⚠️注意：识图可能存在误差，请自行核对。"
                    final_output = (
                        f"🎯匹配成功！\n"
                        f"JM号： {album_id}\n"
                        f"作品名：{album_title}\n"
                        f"作者： {authors}\n\n"
                        f"🔍 识图匹配：{int(score)}%\n"
                        f"🔍 命中词：{kw}\n"
                        f"{low_conf_warn}"
                        f"{download_tip}"
                    )
                    yield event.plain_result(final_output)
                    found = True
                    break
                else: 
                    tried_info.append(kw)
                    
            if not found:
                for score, kw in all_en_words:
                    success, msg = await asyncio.to_thread(self.search_jm, kw)
                    if success:
                        album_id, album_title, authors, jm_ratio = msg
                        download_tip = f"\n\n💡 提示：引用本条消息并发送「{self.download_cmd}」就可以下载哦。" if self.enable_download else ""
                        low_conf_warn = "⚠️注意：识图相似度较低，请自行核对。" if score < 75 else "⚠️注意：识图可能存在误差，请自行核对。"
                        final_output = (
                            f"🎯匹配成功！\n"
                            f"JM号： {album_id}\n"
                            f"作品名：{album_title}\n"
                            f"作者： {authors}\n\n"
                            f"🔍 识图匹配：{int(score)}%\n"
                            f"🔍 命中词：{kw}\n"
                            f"{low_conf_warn}"
                            f"{download_tip}"
                        )
                        yield event.plain_result(final_output)
                        found = True
                        break
                    else: 
                        tried_info.append(kw)
                    
            if not found:
                info_str = "\n".join(debug_titles[:3]) if debug_titles else "无"
                yield event.plain_result(
                    f"💔 Soutubot 找出的高置信度结果在 JM 中未通过校验。\n"
                    f"提取词：{info_str}\n"
                    f"已尝试词：{', '.join(tried_info[:5])} 等...\n"
                    f"如果你确定这是你要的本子，请尝试手动发送：小祥搜本 关键词"
                )
                
        except Exception as e:
            logger.error(f"报错: {traceback.format_exc()}")
            yield event.plain_result(f"❌ 主流程出错啦：{e}")
        finally:
            async def clean_cache_delayed():
                await asyncio.sleep(10)
                for f in CACHE_DIR.iterdir():
                    try:
                        if time.time() - f.stat().st_mtime > 10:
                            if f.is_dir(): shutil.rmtree(f, ignore_errors=True)
                            else: f.unlink(missing_ok=True)
                    except: pass
            asyncio.create_task(clean_cache_delayed())
