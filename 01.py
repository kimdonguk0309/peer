import asyncio
import threading
import json

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription

# 시그널링 서버 (aiohttp)
class SignalingServer:
    def __init__(self):
        self._app = web.Application()
        self._app.add_routes([web.post('/signal', self.on_signal)])
        self._messages = []  # 시그널링 메시지 임시 저장

    async def on_signal(self, request):
        data = await request.json()
        self._messages.append(data)
        return web.json_response({"status": "ok"})

    def run(self):
        web.run_app(self._app, port=8080)


# 메인 UI
class P2PBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.pc = None
        self.loop = asyncio.get_event_loop()

        self.status = Label(text='[상태 로그]')
        self.sdp_in = TextInput(hint_text='SDP 입력', multiline=True, size_hint_y=0.3)
        self.sdp_out = TextInput(hint_text='SDP 출력', multiline=True, readonly=True, size_hint_y=0.3)
        self.message_in = TextInput(hint_text='메시지 입력', multiline=False)
        self.chat_log = Label(text='채팅 로그', size_hint_y=0.3)

        self.add_widget(Button(text='호스트 시작', on_press=self.start_host))
        self.add_widget(Button(text='게스트 연결', on_press=self.start_guest))
        self.add_widget(self.sdp_in)
        self.add_widget(self.sdp_out)
        self.add_widget(self.message_in)
        self.add_widget(Button(text='메시지 전송', on_press=self.send_message))
        self.add_widget(self.status)
        self.add_widget(self.chat_log)

    def create_pc(self):
        self.pc = RTCPeerConnection()

        @self.pc.on("datachannel")
        def on_datachannel(channel):
            self.channel = channel

            @channel.on("message")
            def on_message(message):
                self.chat_log.text += f"\n[수신] {message}"

        self.channel = self.pc.createDataChannel("chat")

        @self.channel.on("open")
        def on_open():
            self.status.text += "\n채널 연결됨"

        @self.channel.on("close")
        def on_close():
            self.status.text += "\n채널 닫힘"

        @self.channel.on("error")
        def on_error(e):
            self.status.text += f"\n채널 에러: {e}"

    def send_message(self, _):
        if self.channel and self.channel.readyState == "open":
            msg = self.message_in.text
            self.channel.send(msg)
            self.chat_log.text += f"\n[송신] {msg}"
            self.message_in.text = ""
        else:
            self.status.text += "\n채널이 열려 있지 않습니다."

    def start_host(self, _):
        self.create_pc()
        asyncio.ensure_future(self.host_offer())

    def start_guest(self, _):
        self.create_pc()
        try:
            sdp_json = json.loads(self.sdp_in.text)
        except Exception as e:
            self.status.text += f"\nSDP 파싱 실패: {e}"
            return
        asyncio.ensure_future(self.guest_answer(sdp_json))

    async def host_offer(self):
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        self.sdp_out.text = json.dumps({
            "sdp": self.pc.localDescription.sdp,
            "type": self.pc.localDescription.type
        })

    async def guest_answer(self, offer_json):
        await self.pc.setRemoteDescription(
            RTCSessionDescription(offer_json["sdp"], offer_json["type"])
        )
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        self.sdp_out.text = json.dumps({
            "sdp": self.pc.localDescription.sdp,
            "type": self.pc.localDescription.type
        })

class P2PApp(App):
    def build(self):
        # 시그널링 서버 쓰레드로 실행 (로컬 8080)
        server = SignalingServer()
        t = threading.Thread(target=server.run, daemon=True)
        t.start()

        return P2PBox()

if __name__ == '__main__':
    P2PApp().run()
