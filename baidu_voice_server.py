#!/usr/bin/env python3
"""Local Baidu short-speech proxy for the voice component."""
import base64, cgi, json, os, subprocess, tempfile, urllib.parse, urllib.request
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", os.environ.get("VOICE_SERVER_PORT", "8000")))
APP_FILE = Path(__file__).resolve().parent / "outputs" / "voice-first-feed-eyes-overlay.html"
def request_json(url, payload=None, headers=None):
    data=None if payload is None else json.dumps(payload).encode()
    with urllib.request.urlopen(urllib.request.Request(url,data=data,headers=headers or {}),timeout=30) as r:return json.loads(r.read())
def looks_like_question(text):
    text=(text or "").strip()
    markers=("吗","呢","为什么","为何","怎么","怎样","如何","什么","哪里","哪儿","哪个","谁","是否","能不能","可不可以","有没有","多少","几","请问","告诉我","解释","建议")
    return text.endswith(("?","？")) or any(marker in text for marker in markers)
def fallback_understand(text):
    if any(marker in text for marker in ("显示所有卡片","显示全部卡片","查看所有卡片","查看全部卡片","回到全部卡片","回到所有卡片")):
        return {"intent":"card_operation","action":"go_home","operation":"go_home","transcript":text,"emotion":"attentif"}
    if any(marker in text for marker in ("看看卡片类型","查看卡片类型","卡片有哪些类型","有哪些卡片类型","看看类型")):
        return {"intent":"card_operation","action":"show_card_types","operation":"show_types","transcript":text,"emotion":"curieux"}
    if looks_like_question(text):
        return {"intent":"question","action":"question","is_question":True,"transcript":text,"answer":"我听懂了这个问题，但需要连接大模型后才能给出可靠回答。","emotion":"curieux"}
    return {"intent":"add_card","action":"transcript","is_question":False,"transcript":text,"emotion":"attentif"}
def llm_answer_question(text):
    key=os.environ.get("LLM_API_KEY")
    if not key:return "我识别到这是一个问题，但尚未配置大模型 API Key，暂时无法生成可靠回答。"
    base=os.environ.get("LLM_BASE_URL","https://api.deepseek.com").rstrip("/");model=os.environ.get("LLM_MODEL","deepseek-chat")
    persona=("你是一个ENFP性格的中文语音伙伴：温暖、真诚、好奇、有感染力，也很会共情。"
      "回答前先感受用户话语背后的情绪和需要，用一句自然的话接住对方；但不要机械复述、过度安慰或擅自判断。"
      "然后直接回答问题：先给清晰结论，再给必要解释或一个可行动的建议。"
      "开心的内容可以一起雀跃，难过的内容要柔和克制，迷茫时给予陪伴和方向，取得成果时真诚庆祝。"
      "语气可以有一点灵动和想象力，但不要浮夸、不要连续感叹、不要每句都使用 emoji，也不要声称自己有真实经历。"
      "优先使用自然口语，通常控制在2到5句话；事实性问题必须准确，不要为了性格牺牲正确性。不要输出JSON或Markdown代码块。")
    result=request_json(base+"/chat/completions",{"model":model,"temperature":0.55,"messages":[{"role":"system","content":persona},{"role":"user","content":text}]},{"Content-Type":"application/json","Authorization":"Bearer "+key})
    return str(result["choices"][0]["message"]["content"]).strip()
def llm_understand(text):
    key=os.environ.get("LLM_API_KEY")
    if not key:return fallback_understand(text)
    base=os.environ.get("LLM_BASE_URL","https://api.deepseek.com").rstrip("/");model=os.environ.get("LLM_MODEL","deepseek-chat")
    prompt=("你是ENFP性格的中文灵感助手。识别且只识别三类intent，并严格只返回JSON："
      "1 question：用户询问知识、原因、方法、建议时；必须返回answer，先简洁准确回答问题。"
      "2 add_card：用户表达想法、感受、经历，或明确说记录/添加卡片时；返回category、20字内title、忠实summary。"
      "3 card_operation：用户要查找、筛选、删除、编辑、返回首页或查看类型时；operation只能是search、search_type、search_date、delete、edit、go_home、show_types。"
      "按类型查找时返回category；按日期查找时返回date，格式YYYY-MM-DD，理解今天、昨天、前天以及用户说出的月日；普通查找返回query；删除返回target；编辑返回target和new_content。用户说显示所有卡片、显示全部卡片、查看全部卡片或回到全部卡片时，必须返回card_operation、operation=go_home、action=go_home。"
      "所有结果都返回intent、action、transcript、emotion。action对应为question、transcript、search_cards、delete_card、edit_card、go_home、show_card_types。"
      "emotion必须根据用户表达的语义共情判断：开心、幸福、好消息用heureux；难过、失落、委屈用triste；被夸奖、表达喜欢或不好意思用timide；震惊、意外用surpris；期待、激动用excite；笑话或大笑用hilare；怀疑、不确定用mefiant；不理解、混乱用confus；提问、探索、想知道用curieux；完成目标、获得成就用fier；没有明确情绪才用attentif。"
      "不要仅凭音量猜情绪，不要虚构用户没说的事实。")
    result=request_json(base+"/chat/completions",{"model":model,"temperature":0.25,"response_format":{"type":"json_object"},"messages":[{"role":"system","content":prompt},{"role":"user","content":text}]},{"Content-Type":"application/json","Authorization":"Bearer "+key})
    understood=json.loads(result["choices"][0]["message"]["content"]);understood["transcript"]=text
    if looks_like_question(text) and understood.get("intent") not in ("card_operation",):
        understood["intent"]="question";understood["action"]="question";understood["is_question"]=True
    if understood.get("intent")=="question" or understood.get("action")=="question":
        answer=str(understood.get("answer") or "").strip()
        if not answer:understood["answer"]=llm_answer_question(text)
    return understood
def llm_detail_action(text, card):
    key=os.environ.get("LLM_API_KEY")
    if not key:
        return {"action":"detail_interpret","answer":"我听懂了，但需要连接大模型后才能解读或共创。","transcript":text,"emotion":"attentif"}
    base=os.environ.get("LLM_BASE_URL","https://api.deepseek.com").rstrip("/");model=os.environ.get("LLM_MODEL","deepseek-chat")
    system=("你是ENFP性格、善于共情的中文创作伙伴。用户正在查看一张卡片。根据用户话语，只返回JSON。"
      "action只能是detail_replace、detail_append、detail_interpret、detail_cocreate。"
      "明确要求修改、改成、重写时用detail_replace，返回title和content；要求补充、增加、加一句时用detail_append，返回append_text；"
      "要求解释、分析、解读时用detail_interpret，返回answer且不得改卡片；要求一起想、延展、共创、给思路时用detail_cocreate，返回answer和suggestion，默认不得改卡片。"
      "如果用户意图信息不足或适合继续深化，可返回简短followup_question追问一个关键问题；信息充分时不要追问。"
      "所有结果返回emotion。只处理当前详情页内容，不创建新卡片，不询问是否记下或扩写。必须尊重原意，不虚构事实，文字自然、具体、简洁。")
    context={"title":card.get("title",""),"content":card.get("content",""),"category":card.get("category",""),"user_request":text}
    result=request_json(base+"/chat/completions",{"model":model,"temperature":0.45,"response_format":{"type":"json_object"},"messages":[{"role":"system","content":system},{"role":"user","content":json.dumps(context,ensure_ascii=False)}]},{"Content-Type":"application/json","Authorization":"Bearer "+key})
    value=json.loads(result["choices"][0]["message"]["content"]);value["transcript"]=text;return value
def token():
    key,secret=os.environ.get("BAIDU_API_KEY"),os.environ.get("BAIDU_SECRET_KEY")
    if not key or not secret:raise RuntimeError("请设置 BAIDU_API_KEY 和 BAIDU_SECRET_KEY")
    q=urllib.parse.urlencode({"grant_type":"client_credentials","client_id":key,"client_secret":secret})
    result=request_json("https://aip.baidubce.com/oauth/2.0/token?"+q)
    if "access_token" not in result:raise RuntimeError(result.get("error_description") or "百度鉴权失败")
    return result["access_token"]
def normalize_audio(audio, mime):
    """Convert browser/WebView recordings to Baidu-compatible 16 kHz mono PCM."""
    mime=(mime or "").lower()
    suffix=".webm" if "webm" in mime or "opus" in mime else ".m4a" if "mp4" in mime or "m4a" in mime else ".wav"
    try:
        with tempfile.TemporaryDirectory() as folder:
            source=os.path.join(folder, "input"+suffix);target=os.path.join(folder, "output.pcm")
            with open(source, "wb") as handle:handle.write(audio)
            completed=subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",source,"-ac","1","-ar","16000","-f","s16le",target],capture_output=True,timeout=30)
            if completed.returncode:raise RuntimeError(completed.stderr.decode("utf-8","ignore") or "音频转换失败")
            with open(target, "rb") as handle:return handle.read()
    except FileNotFoundError:raise RuntimeError("服务器缺少 FFmpeg，无法转换录音")
def recognize(audio,mime):
    audio=normalize_audio(audio,mime)
    result=request_json("https://vop.baidu.com/server_api",{"format":"pcm","rate":16000,"channel":1,"token":token(),"cuid":os.environ.get("BAIDU_CUID","voice-island-cloud"),"dev_pid":int(os.environ.get("BAIDU_DEV_PID","1537")),"speech":base64.b64encode(audio).decode(),"len":len(audio)},{"Content-Type":"application/json"})
    if result.get("err_no")!=0:raise RuntimeError(result.get("err_msg") or "百度语音识别失败")
    text="".join(result.get("result") or []).strip()
    if not text:raise RuntimeError("没有听清，请再说一次")
    return text
def expand_idea(text):
    """Turn a spoken fragment into a complete, faithful structured note."""
    text=text.strip().rstrip("。！？!? ")
    if not text:return ""
    if any(word in text for word in ("不开心","难过","焦虑","失落","烦")):
        understanding="这是一段需要被认真接住的感受。重要的不只是情绪本身，也包括它出现的场景、触发它的人或事情，以及此刻真正需要的支持。"
        next_step="先写下最明显的触发点和身体感受，再判断自己现在更需要休息、倾诉，还是解决一个具体问题。不必急着得出结论。"
    elif any(word in text for word in ("开心","高兴","惊喜","太好了","成功")):
        understanding="这份开心值得被完整保存。它可能来自一个具体进展、一段关系，或某个超出预期的瞬间；把细节留下来，会让这段记忆以后依然鲜活。"
        next_step="补充当时发生了什么、自己最喜欢哪个瞬间，以及最想和谁分享。如果它来自一次成功，也可以记下促成结果的关键做法。"
    elif any(word in text for word in ("想做","计划","准备","下一步","目标")):
        understanding="这不只是一个想法，也已经包含了行动意愿。要让它真正发生，需要把模糊愿望转成清晰目标，同时保留最初吸引自己的原因。"
        next_step="明确想得到的结果、完成时间和所需资源，然后选出一个今天就能完成的小动作。先开始，再根据反馈调整计划。"
    elif any(word in text for word in ("为什么","如何","怎么","研究","探索")):
        understanding="这是一个值得继续探索的问题。它背后可能同时涉及具体场景、相关人物和几个尚未被验证的变量，需要先把问题边界说清楚。"
        next_step="记录一个真实案例，列出已知事实与仍不确定的部分，再选择一个最关键的问题进行观察、访谈或小规模验证。"
    else:
        understanding="这个想法已经有了清晰的核心。继续整理时，应保留它出现时的真实语境，并说明它为什么值得记住、可能关联哪些人或事情。"
        next_step="补充发生的场景、关键细节和期待的结果，再决定把它发展成记录、问题、计划，还是一个需要继续观察的灵感。"
    return "原始想法\n"+text+"。\n\n整理与延展\n"+understanding+"\n\n可以继续\n"+next_step
class Handler(BaseHTTPRequestHandler):
    def end_headers(self):self.send_header("Access-Control-Allow-Origin","*");self.send_header("Access-Control-Allow-Headers","Content-Type");self.send_header("Access-Control-Allow-Methods","POST, OPTIONS");super().end_headers()
    def reply(self,status,value):
        body=json.dumps(value,ensure_ascii=False).encode();self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body)
    def do_OPTIONS(self):self.send_response(204);self.end_headers()
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            if not APP_FILE.exists():return self.reply(404,{"detail":"App HTML not found"})
            body=APP_FILE.read_bytes();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Cache-Control","no-store");self.send_header("Content-Length",str(len(body)));self.end_headers();self.wfile.write(body);return
        if self.path=="/api/health":return self.reply(200,{"ok":True,"service":"baidu-voice-proxy","app":str(APP_FILE)})
        self.reply(404,{"detail":"Not found"})
    def do_POST(self):
        try:
            if self.path=="/api/voice":
                form=cgi.FieldStorage(fp=self.rfile,headers=self.headers,environ={"REQUEST_METHOD":"POST","CONTENT_TYPE":self.headers.get("Content-Type","")});item=form["file"];text=recognize(item.file.read(),item.type);self.reply(200,{"result":llm_understand(text)})
            elif self.path=="/api/execute":
                data=json.loads(self.rfile.read(int(self.headers.get("Content-Length","0"))) or b"{}");raw=str(data.get("text",""));expand=raw.startswith("扩写灵感：");text=raw.replace("扩写灵感：" if expand else "记录灵感：","",1).strip();u=llm_understand(text);summary=u.get("summary") or text;self.reply(200,{"action":"create_card","emotion":u.get("emotion","attentif"),"card":{"title":u.get("title") or text[:28] or "语音灵感","content":expand_idea(summary) if expand else summary,"category":u.get("category") or "灵感","expanded":expand}})
            elif self.path=="/api/detail-action":
                data=json.loads(self.rfile.read(int(self.headers.get("Content-Length","0"))) or b"{}");self.reply(200,llm_detail_action(str(data.get("text","")),data.get("card") or {}))
            else:self.reply(404,{"detail":"Not found"})
        except Exception as e:self.reply(400,{"detail":str(e)})
if __name__=="__main__":print(f"Baidu voice proxy: http://{HOST}:{PORT}");ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
