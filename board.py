import tkinter as tk
from tkinter import scrolledtext
import webbrowser
import re
from datetime import datetime

class BoardApp:
    
    def __init__(self, frame, width, height):
        self.num = 1
        self.board_data = []
        self.board_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, width=width, height=height)
        self.board_text.pack(padx=10, pady=10)

    def update_board(self, address, source):
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_info = f"[{self.num}]\n{current_time}\n{address}\n{source}\n\n"
        self.num = self.num + 1
        self.board_data.insert(0, new_info)
        self.board_text.delete(1.0, tk.END)
        for info in self.board_data:
            self.insert_with_hyperlinks(info)

    def insert_with_hyperlinks(self, text):
        urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        parts = re.split(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)

        for i in range(len(parts)):
            if i < len(urls):
                tag_name = f"url_{i}"
                self.board_text.tag_config(tag_name, foreground="blue", underline=True)  # 새로운 태그 정의 및 스타일 설정
                self.board_text.insert(tk.END, parts[i], tag_name)
                self.board_text.tag_add(tag_name, f"{tk.END}-{len(parts[i])}c", tk.END)
                self.board_text.tag_bind(tag_name, "<Button-1>", lambda e, url=urls[i]: self.open_url(url))
            else:
                self.board_text.insert(tk.END, parts[i])

        self.board_text.insert(tk.END, "\n")

    def open_url(self, url):
        webbrowser.open(url)