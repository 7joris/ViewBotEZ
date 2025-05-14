import tkinter as tk
from tkinter import ttk, messagebox
import random
import threading
from curl_cffi import requests
from loguru import logger

class EzBioGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("EzBio View Sender")
        self.root.geometry("500x400")
        self.running = False
        self.threads = []
        self.create_widgets()
        
    def create_widgets(self):

        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="EzBio View Sender", font=('Helvetica', 16, 'bold')).grid(row=0, column=0, columnspan=2, pady=10)

        ttk.Label(main_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(main_frame, width=30)
        self.username_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)

        ttk.Label(main_frame, text="Threads:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.threads_entry = ttk.Entry(main_frame, width=30)
        self.threads_entry.grid(row=2, column=1, sticky=tk.EW, pady=5)

        ttk.Label(main_frame, text="Proxy File:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.proxy_file_entry = ttk.Entry(main_frame, width=30)
        self.proxy_file_entry.insert(0, "proxy.txt")
        self.proxy_file_entry.grid(row=3, column=1, sticky=tk.EW, pady=5)

        self.start_button = ttk.Button(main_frame, text="Start", command=self.start_sending)
        self.start_button.grid(row=4, column=0, pady=20, sticky=tk.W)
        
        self.stop_button = ttk.Button(main_frame, text="Stop", command=self.stop_sending, state=tk.DISABLED)
        self.stop_button.grid(row=4, column=1, pady=20, sticky=tk.E)

        ttk.Label(main_frame, text="Logs:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.log_text = tk.Text(main_frame, height=10, state=tk.DISABLED)
        self.log_text.grid(row=6, column=0, columnspan=2, sticky=tk.NSEW)

        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=6, column=2, sticky=tk.NS)
        self.log_text['yscrollcommand'] = scrollbar.set

        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        
    def log_message(self, message):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        
    def start_sending(self):
        username = self.username_entry.get()
        threads_count = self.threads_entry.get()
        proxy_file = self.proxy_file_entry.get()
        
        if not username or not threads_count:
            messagebox.showerror("Error", "Please fill all fields")
            return
            
        try:
            threads_count = int(threads_count)
        except ValueError:
            messagebox.showerror("Error", "Threads must be a number")
            return
            
        try:
            with open(proxy_file, 'r') as f:
                proxies = f.read().splitlines()
        except FileNotFoundError:
            messagebox.showerror("Error", f"Proxy file not found: {proxy_file}")
            return
            
        if not proxies:
            messagebox.showerror("Error", "No proxies found in the file")
            return
            
        self.running = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        
        self.log_message(f"Starting {threads_count} threads for username: {username}")
        
        self.ezbio = EzBio(proxies)
        
        for _ in range(threads_count):
            thread = threading.Thread(target=self.ezbio.start, args=(username,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)
            
    def stop_sending(self):
        self.running = False
        self.ezbio.running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.log_message("Stopping all threads...")
        
    def on_close(self):
        if self.running:
            self.stop_sending()
        self.root.destroy()

class EzBio:
    def __init__(self, proxies: list):
        self.session = requests.Session()
        self.proxies = proxies
        self.running = True

        self.session.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'pl-PL,pl;q=0.6',
            'origin': 'https://e-z.bio',
            'priority': 'u=1, i',
            'referer': 'https://e-z.bio/',
            'sec-ch-ua': '"Brave";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'sec-gpc': '1',
        }

    def get_random_proxy(self):
        return random.choice(self.proxies)
    
    def get_random_useragent(self):
        return f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.{random.randint(1000, 4000)}.0 Safari/537.36'

    def send_views(self, username: str):
        if not self.running:
            return
            
        useragent = self.get_random_useragent()

        self.session.headers['user-agent'] = useragent

        proxy = self.get_random_proxy()
        proxies = {
            'http': 'http://'+proxy,
            'https': 'http://'+proxy
        }

        try:
            response = self.session.put(f'https://api.e-z.bio/bio/view/{username}', impersonate="edge101", proxies=proxies)
            if not response.json()['success']:
                logger.error('Failed to send view')
                return
            
            logger.success(f'View sent successfully to {username}')
        except Exception as e:
            logger.error(f'Error sending view: {str(e)}')

    def start(self, username: str):
        while self.running:
            self.send_views(username)

if __name__ == "__main__":
    root = tk.Tk()
    app = EzBioGUI(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()