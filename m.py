import os
import sys
import json
import socket
import threading
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
import subprocess
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.recycleview import RecycleView
from kivy.lang import Builder

# --- 핵심 통신 모듈 ---
class P2PNetwork:
    def __init__(self):
        self.key_pair = ec.generate_private_key(ec.SECP384R1())
        self.peers = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind(('0.0.0.0', 5555))
        threading.Thread(target=self.listen, daemon=True).start()

    def get_public_key_str(self):
        return self.key_pair.public_key().public_bytes(
            Encoding.PEM, PublicFormat.SubjectPublicKeyInfo
        ).decode()

    def listen(self):
        while True:
            data, addr = self.socket.recvfrom(1024)
            self.handle_message(data.decode(), addr)

    def send(self, message, peer_ip):
        self.socket.sendto(message.encode(), (peer_ip, 5555))

    def handle_message(self, message, addr):
        try:
            msg = json.loads(message)
            if msg['type'] == 'discover':
                response = {
                    'type': 'discover_response',
                    'pub_key': self.get_public_key_str(),
                    'ip': addr[0]
                }
                self.send(json.dumps(response), addr[0])
        except Exception as e:
            print(f"메시지 처리 오류: {e}")

# --- RecycleView 구현 ---
Builder.load_string('''
<RV>:
    viewclass: 'Label'
    RecycleBoxLayout:
        default_size: None, dp(56)
        default_size_hint: 1, None
        size_hint_y: None
        height: self.minimum_height
        orientation: 'vertical'
''')

class RV(RecycleView):
    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.data = []

# --- Kivy UI 앱 ---
class DecentralChatApp(App):
    def build(self):
        self.network = P2PNetwork()
        self.setup_ui()
        return self.layout

    def setup_ui(self):
        self.layout = BoxLayout(orientation='vertical')
        
        # 디바이스 탐색 버튼
        self.scan_btn = Button(text='근처 사용자 탐색', size_hint=(1, 0.1))
        self.scan_btn.bind(on_press=self.scan_devices)
        
        # 디바이스 목록 (RecycleView 사용)
        self.devices_rv = RV()
        self.devices_rv.data = [{'text': "디바이스 목록이 여기에 표시됩니다"}]
        
        # 채팅 메시지 영역
        self.chat_rv = RV()
        self.chat_rv.data = [{'text': "채팅 메시지가 여기에 표시됩니다"}]
        
        # 메시지 입력
        self.msg_input = TextInput(hint_text='메시지 입력', size_hint=(1, 0.1))
        send_btn = Button(text='전송', size_hint=(0.2, 0.1))
        send_btn.bind(on_press=self.send_message)
        
        # UI 배치
        input_layout = BoxLayout(size_hint=(1, 0.1))
        input_layout.add_widget(self.msg_input)
        input_layout.add_widget(send_btn)
        
        self.layout.add_widget(self.scan_btn)
        self.layout.add_widget(Label(text='연결 가능한 디바이스:'))
        self.layout.add_widget(self.devices_rv)
        self.layout.add_widget(Label(text='채팅 메시지:'))
        self.layout.add_widget(self.chat_rv)
        self.layout.add_widget(input_layout)

    def scan_devices(self, instance):
        """로컬 네트워크에서 디바이스 검색"""
        self.devices_rv.data = [{'text': f"디바이스 {i}"} for i in range(1, 4)]

    def send_message(self, instance):
        """메시지 전송"""
        msg = self.msg_input.text
        if msg:
            self.chat_rv.data.append({'text': f"나: {msg}"})
            self.msg_input.text = ''

if __name__ == '__main__':
    DecentralChatApp().run()
