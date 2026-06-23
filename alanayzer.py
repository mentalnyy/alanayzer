import customtkinter as ctk
import re
import requests
import webbrowser
import json
import os
from urllib.parse import urlparse
from datetime import datetime
from tkinter import messagebox

# ===== НАСТРОЙКИ =====
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ===== ФАЙЛ С ДОМЕНАМИ =====
DOMAINS_FILE = "domains.json"
HISTORY_FILE = "history.json"

def load_domains():
    default = {
        "suspicious": [
            "bit.ly", "goo.gl", "tinyurl.com", "cutt.ly",
            "short.link", "shorturl.at", "is.gd", "ow.ly",
            "rb.gy", "t.co", "lnkd.in", "buff.ly",
            "adf.ly", "shorte.st", "bc.vc", "bit.do"
        ],
        "dangerous_words": [
            "login", "verify", "update", "security", "confirm",
            "reset", "wallet", "paypal", "steam", "roblox",
            "bank", "password", "account", "validate"
        ]
    }
    if os.path.exists(DOMAINS_FILE):
        try:
            with open(DOMAINS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data
        except:
            return default
    else:
        save_domains(default)
        return default

def save_domains(data):
    try:
        with open(DOMAINS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except:
        pass

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
    except:
        pass

domain_data = load_domains()
suspicious_domains = domain_data.get("suspicious", [])
dangerous_words = domain_data.get("dangerous_words", [])
history = load_history()

# ===== ФУНКЦИИ =====
def expand_url(url):
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.url
    except:
        return url

def check_typo(url):
    typo_patterns = [
        (r'g00gle', 'google'),
        (r'g0ogle', 'google'),
        (r'faceb00k', 'facebook'),
        (r'fac3book', 'facebook'),
        (r'y0utube', 'youtube'),
        (r'y0u tube', 'youtube'),
        (r'tw1tter', 'twitter'),
        (r'twitt3r', 'twitter'),
        (r'instagr4m', 'instagram'),
        (r'instagrаm', 'instagram'),
        (r'steаm', 'steam'),
        (r'rоblox', 'roblox'),
    ]
    found = []
    url_lower = url.lower()
    for pattern, original in typo_patterns:
        if re.search(pattern, url_lower):
            found.append(f"возможно, вы имели в виду {original} (опечатка)")
    return found

last_url = ""

def analyze_url():
    global last_url
    url = entry.get().strip()
    if not url:
        result_textbox.delete("1.0", "end")
        result_textbox.insert("1.0", "❌ введите ссылку")
        return
    
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    
    result = f"🔗 ссылка: {url}\n"
    color = "green"
    warnings = []
    
    expanded = expand_url(url)
    if expanded != url:
        result += f"📎 раскрытая ссылка: {expanded}\n"
        url = expanded
    
    if not url.startswith("https://"):
        result += "⚠️ http (не защищено)\n"
        color = "orange"
        warnings.append("http")
    else:
        result += "✅ https\n"
    
    try:
        domain = urlparse(url).netloc
        if domain:
            result += f"🌐 домен: {domain}\n"
            for sus in suspicious_domains:
                if sus in domain:
                    result += f"⚠️ подозрительный домен: {sus}\n"
                    color = "orange"
                    warnings.append("подозрительный домен")
    except:
        pass
    
    typos = check_typo(url)
    for typo in typos:
        result += f"⚠️ {typo}\n"
        color = "orange"
        warnings.append("опечатка")
    
    for word in dangerous_words:
        if word in url.lower():
            result += f"⚠️ подозрительное слово: {word}\n"
            color = "orange"
            warnings.append("опасное слово")
    
    if re.search(r'[^a-zA-Z0-9/:._-]', url):
        result += "⚠️ странные символы в ссылке\n"
        color = "orange"
        warnings.append("странные символы")
    
    if color == "green":
        status = "✅ безопасно"
        result += "\n✅ ссылка выглядит безопасной."
    elif color == "orange":
        status = "⚠️ подозрительно"
        result += "\n⚠️ ссылка подозрительная. будьте осторожны!"
    else:
        status = "❌ опасно"
        result += "\n❌ ссылка выглядит ОПАСНОЙ. не переходите!"
    
    result_textbox.delete("1.0", "end")
    result_textbox.insert("1.0", result)
    
    if color == "green":
        result_textbox.configure(fg_color="#1a2b1a")
    elif color == "orange":
        result_textbox.configure(fg_color="#2b2b1a")
    else:
        result_textbox.configure(fg_color="#2b1a1a")
    
    last_url = url
    
    # сохраняем в историю
    entry_history = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "url": url,
        "status": status,
        "warnings": ", ".join(warnings) if warnings else "нет"
    }
    history.insert(0, entry_history)
    save_history(history)
    update_history_list()

def copy_result():
    content = result_textbox.get("1.0", "end-1c")
    root.clipboard_clear()
    root.clipboard_append(content)
    copy_btn.configure(text="✅ скопировано")
    root.after(2000, lambda: copy_btn.configure(text="📋 копировать"))

def open_url():
    if last_url:
        webbrowser.open(last_url)

def add_domain():
    new_domain = domain_entry.get().strip()
    if not new_domain:
        status_label.configure(text="❌ введите домен", text_color="red")
        return
    if new_domain in suspicious_domains:
        status_label.configure(text="⚠️ домен уже есть", text_color="orange")
        return
    suspicious_domains.append(new_domain)
    domain_data["suspicious"] = suspicious_domains
    save_domains(domain_data)
    status_label.configure(text=f"✅ домен {new_domain} добавлен", text_color="green")
    domain_entry.delete(0, "end")
    update_domain_list()

def remove_domain(domain):
    if domain in suspicious_domains:
        suspicious_domains.remove(domain)
        domain_data["suspicious"] = suspicious_domains
        save_domains(domain_data)
        update_domain_list()
        status_label.configure(text=f"✅ домен {domain} удалён", text_color="green")

def update_domain_list():
    for widget in domain_list_frame.winfo_children():
        widget.destroy()
    
    for domain in suspicious_domains:
        row = ctk.CTkFrame(domain_list_frame, fg_color="transparent")
        row.pack(fill="x", pady=1)
        
        label = ctk.CTkLabel(row, text=domain, anchor="w", font=("Arial", 12))
        label.pack(side="left", fill="x", expand=True, padx=5)
        
        del_btn = ctk.CTkButton(row, text="✕", width=30, height=25, fg_color="#6b2a2a", hover_color="#8b3a3a",
                               command=lambda d=domain: remove_domain(d))
        del_btn.pack(side="right", padx=5)

def update_history_list():
    for widget in history_frame.winfo_children():
        widget.destroy()
    
    if not history:
        empty = ctk.CTkLabel(history_frame, text="история пуста", font=("Arial", 12), text_color="gray")
        empty.pack(pady=10)
        return
    
    for i, entry in enumerate(history):
        row = ctk.CTkFrame(history_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        time_label = ctk.CTkLabel(row, text=entry.get("time", ""), font=("Arial", 10), width=150)
        time_label.pack(side="left", padx=5)
        
        url_label = ctk.CTkLabel(row, text=entry.get("url", "")[:40] + "...", font=("Arial", 11), anchor="w")
        url_label.pack(side="left", fill="x", expand=True, padx=5)
        
        status_color = "#1a6b1a" if "безопасно" in entry.get("status", "") else "#6b6b1a" if "подозрительно" in entry.get("status", "") else "#6b1a1a"
        status_label = ctk.CTkLabel(row, text=entry.get("status", ""), font=("Arial", 10), text_color=status_color, width=120)
        status_label.pack(side="left", padx=5)
        
        del_btn = ctk.CTkButton(row, text="✕", width=25, height=20, fg_color="#4a1a1a", hover_color="#6b2a2a",
                               command=lambda idx=i: delete_history_entry(idx))
        del_btn.pack(side="right", padx=5)

def delete_history_entry(idx):
    if 0 <= idx < len(history):
        del history[idx]
        save_history(history)
        update_history_list()

def clear_history():
    if not history:
        return
    if messagebox.askyesno("очистка", "удалить всю историю?"):
        history.clear()
        save_history(history)
        update_history_list()

def export_history():
    if not history:
        return
    with open("history_export.txt", "w", encoding="utf-8") as f:
        f.write("===== история проверок =====\n\n")
        for entry in history:
            f.write(f"[{entry.get('time', '')}] {entry.get('url', '')} → {entry.get('status', '')}\n")
            f.write(f"  предупреждения: {entry.get('warnings', 'нет')}\n\n")
        messagebox.showinfo("экспорт", "история сохранена в history_export.txt")

# ===== GUI =====
root = ctk.CTk()
root.title("анализатор ссылок")
root.geometry("700x900")
root.minsize(600, 700)

# заголовок
title = ctk.CTkLabel(root, text="🔍 анализатор ссылок", font=("Arial", 20, "bold"))
title.pack(pady=10)

# поле ввода
entry = ctk.CTkEntry(root, placeholder_text="вставьте ссылку для проверки", height=40, font=("Arial", 14))
entry.pack(pady=5, padx=20, fill="x")
entry.bind("<Return>", lambda e: analyze_url())

# кнопки
btn_frame = ctk.CTkFrame(root, fg_color="transparent")
btn_frame.pack(pady=5, padx=20, fill="x")

check_btn = ctk.CTkButton(btn_frame, text="🔍 проверить", command=analyze_url, height=35)
check_btn.pack(side="left", padx=3, expand=True, fill="x")

open_btn = ctk.CTkButton(btn_frame, text="🌐 открыть", command=open_url, height=35, fg_color="#2a6b2a", hover_color="#1f4f1f")
open_btn.pack(side="left", padx=3, expand=True, fill="x")

copy_btn = ctk.CTkButton(btn_frame, text="📋 копировать", command=copy_result, height=35, fg_color="#2a2a6b", hover_color="#1f1f4f")
copy_btn.pack(side="left", padx=3, expand=True, fill="x")

# результат
result_textbox = ctk.CTkTextbox(root, font=("Courier New", 12), wrap="word", height=200)
result_textbox.pack(pady=10, padx=20, fill="x")
result_textbox.insert("1.0", "вставьте ссылку и нажмите 'проверить'")
result_textbox.configure(fg_color="#1a1a1a")

# ===== РАЗДЕЛ ДОМЕНОВ =====
domain_section = ctk.CTkFrame(root, fg_color="transparent")
domain_section.pack(pady=5, padx=20, fill="x")

ctk.CTkLabel(domain_section, text="➕ управление доменами", font=("Arial", 14, "bold")).pack(anchor="w")

domain_entry = ctk.CTkEntry(domain_section, placeholder_text="введите домен для добавления", height=30)
domain_entry.pack(fill="x", pady=3)

domain_btn_frame = ctk.CTkFrame(domain_section, fg_color="transparent")
domain_btn_frame.pack(fill="x", pady=2)

add_domain_btn = ctk.CTkButton(domain_btn_frame, text="➕ добавить", command=add_domain, height=30, fg_color="#2a6b2a", hover_color="#1f4f1f")
add_domain_btn.pack(side="left", padx=3, expand=True, fill="x")

refresh_btn = ctk.CTkButton(domain_btn_frame, text="🔄 обновить", command=update_domain_list, height=30, fg_color="#2a2a4a", hover_color="#1f1f3f")
refresh_btn.pack(side="left", padx=3, expand=True, fill="x")

status_label = ctk.CTkLabel(domain_section, text="", font=("Arial", 10))
status_label.pack(anchor="w", pady=2)

domain_list_frame = ctk.CTkScrollableFrame(domain_section, fg_color="transparent", height=120)
domain_list_frame.pack(fill="x", pady=5)
update_domain_list()

# ===== РАЗДЕЛ ИСТОРИИ =====
history_section = ctk.CTkFrame(root, fg_color="transparent")
history_section.pack(pady=5, padx=20, fill="both", expand=True)

history_header = ctk.CTkFrame(history_section, fg_color="transparent")
history_header.pack(fill="x")

ctk.CTkLabel(history_header, text="📜 история проверок", font=("Arial", 14, "bold")).pack(side="left")

clear_history_btn = ctk.CTkButton(history_header, text="🗑 очистить", command=clear_history, height=25, width=80, fg_color="#4a1a1a", hover_color="#6b2a2a")
clear_history_btn.pack(side="right", padx=3)

export_history_btn = ctk.CTkButton(history_header, text="💾 экспорт", command=export_history, height=25, width=80, fg_color="#2a2a4a", hover_color="#1f1f4f")
export_history_btn.pack(side="right", padx=3)

history_frame = ctk.CTkScrollableFrame(history_section, fg_color="transparent", height=200)
history_frame.pack(fill="both", expand=True, pady=5)
update_history_list()

# подсказка
tip = ctk.CTkLabel(root, text="💡 результат можно скопировать или открыть ссылку в браузере", font=("Arial", 10), text_color="gray")
tip.pack(pady=3)

root.mainloop()
