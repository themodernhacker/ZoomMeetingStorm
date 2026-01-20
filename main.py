import customtkinter as ctk
import threading
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs

# Selenium Imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ZoomBotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Zoom Meeting Storm Tool (Ultimate Edition)")
        self.geometry("900x750") # Made taller for new inputs
        self.resizable(False, False)

        self.running = False
        self.executor = None

        # --- LAYOUT ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.title_label = ctk.CTkLabel(self, text="Zoom Mass Load Tester", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Controls Frame
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        # --- INPUT OPTION 1: LINK ---
        self.lbl_or = ctk.CTkLabel(self.controls_frame, text="--- OPTION 1: Direct Link ---", text_color="gray")
        self.lbl_or.grid(row=0, column=0, columnspan=2, pady=(10, 5))

        self.link_label = ctk.CTkLabel(self.controls_frame, text="Meeting Link:")
        self.link_label.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.link_entry = ctk.CTkEntry(self.controls_frame, width=450, placeholder_text="Paste full Invite Link here...")
        self.link_entry.grid(row=1, column=1, padx=10, pady=5)

        # --- INPUT OPTION 2: ID & PASS ---
        self.lbl_or2 = ctk.CTkLabel(self.controls_frame, text="--- OPTION 2: ID & Password ---", text_color="gray")
        self.lbl_or2.grid(row=2, column=0, columnspan=2, pady=(15, 5))

        self.id_label = ctk.CTkLabel(self.controls_frame, text="Meeting ID:")
        self.id_label.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        self.id_entry = ctk.CTkEntry(self.controls_frame, width=450, placeholder_text="e.g. 850 3072 2159")
        self.id_entry.grid(row=3, column=1, padx=10, pady=5)

        self.pwd_label = ctk.CTkLabel(self.controls_frame, text="Password:")
        self.pwd_label.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        
        self.pwd_entry = ctk.CTkEntry(self.controls_frame, width=450, placeholder_text="e.g. 123456 (Leave empty if none)")
        self.pwd_entry.grid(row=4, column=1, padx=10, pady=5)

        # --- SLIDER ---
        self.sep = ctk.CTkLabel(self.controls_frame, text="------------------------------------------------", text_color="gray")
        self.sep.grid(row=5, column=0, columnspan=2, pady=(10, 0))

        self.slider_label = ctk.CTkLabel(self.controls_frame, text="Bots: 5")
        self.slider_label.grid(row=6, column=0, padx=10, pady=10, sticky="w")
        
        self.slider = ctk.CTkSlider(self.controls_frame, from_=1, to=350, number_of_steps=349, command=self.update_slider)
        self.slider.set(5)
        self.slider.grid(row=6, column=1, padx=10, pady=10, sticky="ew")

        # Buttons
        self.btn_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.btn_frame.grid(row=7, column=0, columnspan=2, pady=10)

        self.start_btn = ctk.CTkButton(self.btn_frame, text="START MASS LOAD", command=self.start_process, fg_color="red", hover_color="darkred", height=50, width=200)
        self.start_btn.pack(side="left", padx=10)

        self.stop_btn = ctk.CTkButton(self.btn_frame, text="STOP ALL", command=self.stop_process, fg_color="gray", height=50, state="disabled")
        self.stop_btn.pack(side="left", padx=10)

        # Log
        self.log_box = ctk.CTkTextbox(self, state="disabled", font=("Consolas", 10))
        self.log_box.grid(row=2, column=0, padx=20, pady=(0, 20), sticky="nsew")

    def update_slider(self, value):
        self.slider_label.configure(text=f"Bots: {int(value)}")

    def log(self, message):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def start_process(self):
        # 1. Get Inputs
        raw_link = self.link_entry.get().strip()
        raw_id = self.id_entry.get().strip()
        raw_pass = self.pwd_entry.get().strip()
        count = int(self.slider.get())

        final_url = ""

        # 2. Logic to build URL
        if raw_link:
            # Use Link if provided
            final_url = self.clean_link(raw_link)
        elif raw_id:
            # Construct from ID + Pass
            # Remove spaces from ID
            clean_id = raw_id.replace(" ", "").replace("-", "")
            final_url = f"https://zoom.us/wc/join/{clean_id}"
            if raw_pass:
                final_url += f"?pwd={raw_pass}"
        else:
            self.log("Error: Please provide a Link OR Meeting ID!")
            return

        # 3. Create Names File
        if not os.path.exists("names.txt") or len(open("names.txt").readlines()) < count:
            with open("names.txt", "w") as f:
                for i in range(1, 401): f.write(f"Participant_{i}\n")
        
        self.running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        # 4. Start Thread
        threading.Thread(target=self.run_automation, args=(final_url, count), daemon=True).start()

    def stop_process(self):
        self.running = False
        self.log("Stopping...")
        if self.executor: self.executor.shutdown(wait=False)
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")

    def clean_link(self, link):
        """Standardizes Zoom Links to Web Client Format"""
        if link.isdigit(): return f"https://zoom.us/wc/join/{link}"
        try:
            parsed = urlparse(link)
            path_parts = parsed.path.split('/')
            mid = next((p for p in path_parts if p.isdigit()), None)
            pwd = parse_qs(parsed.query).get('pwd', [None])[0]
            clean_url = f"https://zoom.us/wc/join/{mid}"
            if pwd: clean_url += f"?pwd={pwd}"
            return clean_url
        except: 
            return link

    def find_any_input(self, driver):
        selectors = [
            (By.CSS_SELECTOR, "input[placeholder='Your Name']"),
            (By.ID, "input-for-name"),
            (By.ID, "input-user-name"),
            (By.CSS_SELECTOR, "input[type='text']")
        ]
        # Check current frame
        for sel in selectors:
            try: return driver.find_element(*sel)
            except: pass
        
        # Check iframes
        frames = driver.find_elements(By.TAG_NAME, "iframe")
        for frame in frames:
            try:
                driver.switch_to.frame(frame)
                for sel in selectors:
                    try: return driver.find_element(*sel)
                    except: pass
                driver.switch_to.parent_frame()
            except:
                driver.switch_to.default_content()
        return None

    def bot_task(self, name, url):
        if not self.running: return

        options = Options()
        
        # --- HEADLESS STEALTH (PROVEN) ---
        options.add_argument("--headless=new") 
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--blink-settings=imagesEnabled=false") 
        
        prefs = {"profile.default_content_setting_values.media_stream_mic": 2, 
                 "profile.default_content_setting_values.media_stream_camera": 2,
                 "profile.default_content_setting_values.notifications": 2}
        options.add_experimental_option("prefs", prefs)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        driver = None
        try:
            self.log(f"Queue: {name} starting...")
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            driver.get(url)
            wait = WebDriverWait(driver, 40)

            # 1. Redirect
            try:
                browser_link = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Join from Your Browser")))
                browser_link.click()
            except: pass

            # 2. Cookie
            try:
                driver.find_element(By.ID, "onetrust-accept-btn-handler").click()
            except: pass

            # 3. TYPE & ENTER (The Fix)
            time.sleep(3)
            name_box = self.find_any_input(driver)

            if name_box:
                # TYPE NAME
                try:
                    name_box.click()
                    name_box.clear()
                    name_box.send_keys(name)
                    time.sleep(1)
                    
                    # FORCE VALIDATION (TAB)
                    name_box.send_keys(Keys.TAB)
                    time.sleep(0.5)
                    
                    # PRESS ENTER (Bypasses finding the button)
                    name_box.send_keys(Keys.RETURN)
                    self.log(f"SUCCESS: {name} submitted via ENTER key!")
                    
                except Exception as e:
                    self.log(f"Error typing/entering: {str(e)[:30]}")

                # Backup: Try clicking button if Enter didn't work
                time.sleep(2)
                try:
                    join_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Join')]")
                    driver.execute_script("arguments[0].click();", join_btn)
                except:
                    pass 

            else:
                self.log(f"Fail: {name} no input found.")
                driver.save_screenshot(f"debug_no_input_{name}.png")

            # STAY ALIVE
            while self.running:
                time.sleep(10)

        except Exception as e:
            pass
        finally:
            if driver and not self.running: 
                driver.quit()

    def run_automation(self, url, count):
        with open("names.txt", "r") as f:
            names = [line.strip() for line in f if line.strip()]
        
        self.log(f"Target: {url}")
        self.executor = ThreadPoolExecutor(max_workers=count)
        
        for i, name in enumerate(names[:count]):
            if not self.running: break
            self.executor.submit(self.bot_task, name, url)
            time.sleep(3) 
            if i > 0 and i % 10 == 0:
                self.log(f"--- {i} Bots Active ---")

if __name__ == "__main__":
    app = ZoomBotApp()
    app.mainloop()