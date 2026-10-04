#!/usr/bin/env python3
import cgi,json,os,re,urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
PORT=int(os.environ.get('BUSINESS_VOICE_PORT','8010'))
def call_llm(text):
 key=os.environ.get('LLM_API_KEY')
 if not key:return fallback(text)
 base=os.environ.get('LLM_BASE_URL','https://api.deepseek.com').rstrip('/');model=os.environ.get('LLM_MODEL','deepseek-chat')
 prompt=('你是商务语音工作台。只返回JSON。识别intent：meeting_summary、voice_memo、tool_call、business_question。'
 'meeting_summary返回title、summary、decisions数组、action_items数组（含owner、deadline）、risks数组；voice_memo返回title、summary、tags；'
 'tool_call返回tool、operation、parameters、requires_confirmation=true，绝不声称已执行；business_question返回answer。'
 '所有结果返回title、body、actions数组、output对象。内容专业、简洁，不虚构未提供的人名日期。')
 data=json.dumps({'model':model,'temperature':.2,'response_format':{'type':'json_object'},'messages':[{'role':'system','content':prompt},{'role':'user','content':text}]}).encode()
 req=urllib.request.Request(base+'/chat/completions',data=data,headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
 with urllib.request.urlopen(req,timeout=40) as r: result=json.loads(r.read())
 return json.loads(result['choices'][0]['message']['content'])
def fallback(text):
 if re.search('会议|纪要|决策|待办',text):return {'intent':'meeting_summary','title':'会议内容已整理','body':'已生成会议摘要，并提取决策与待办。','actions':['查看纪要','创建任务','取消'],'output':{'title':'会议纪要','type':'MEETING','summary':text}}
 if re.search('发邮件|日历|会议邀请|创建任务|提醒',text):return {'intent':'tool_call','title':'准备调用工具','body':'已整理执行参数，确认后才能执行外部操作。','actions':['确认执行','取消']}
 return {'intent':'voice_memo','title':'语音备忘已整理','body':text,'actions':['保存备忘','取消'],'output':{'title':text[:20] or '语音备忘','type':'MEMO','summary':text}}
class H(BaseHTTPRequestHandler):
 def end_headers(self):self.send_header('Access-Control-Allow-Origin','*');super().end_headers()
 def reply(self,n,v):
  b=json.dumps(v,ensure_ascii=False).encode();self.send_response(n);self.send_header('Content-Type','application/json;charset=utf-8');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def do_POST(self):
  try:
   if self.path!='/api/voice':return self.reply(404,{'detail':'Not found'})
   form=cgi.FieldStorage(fp=self.rfile,headers=self.headers,environ={'REQUEST_METHOD':'POST','CONTENT_TYPE':self.headers.get('Content-Type','')});item=form['file']
   # Demo hook: plug production ASR here. For now accept a transcript field or use a safe placeholder.
   text=form.getfirst('transcript','').strip() or os.environ.get('BUSINESS_DEMO_TRANSCRIPT','请总结刚才的会议，并提取待办。')
   self.reply(200,call_llm(text))
  except Exception as e:self.reply(400,{'detail':str(e)})
if __name__=='__main__':print(f'Business voice server: http://127.0.0.1:{PORT}');ThreadingHTTPServer(('127.0.0.1',PORT),H).serve_forever()
