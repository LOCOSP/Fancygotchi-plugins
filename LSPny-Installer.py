import os
import subprocess
import shutil

# Function to download files from the repository
def download_files():
    repo_url = "https://github.com/LOCOSP/Fancygotchi-plugins.git"
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Path to the folder where the script is located
    target_dir = os.path.join(current_dir, "custom-plugins")  # Target folder in the same location

    # Cloning the repository
    subprocess.run(["sudo", "git", "clone", repo_url, target_dir, "--depth", "1"], check=True)

    # Moving files from folders to appropriate locations
    oled_plugins_src = os.path.join(target_dir, "OLED-plugins")

    # Moving files from OLED-plugins
    for item in os.listdir(oled_plugins_src):
        s = os.path.join(oled_plugins_src, item)
        d = os.path.join(target_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

    # Removing the cloned repository
    shutil.rmtree(target_dir)

# Function to edit the config.toml file
def edit_config(bt_mac, wpa_api_key, discord_webhook):
    config_path = "/etc/pwnagotchi/config.toml"

    # Reading the config.toml file
    with open(config_path, 'r') as file:
        config_lines = file.readlines()

    # Editing the appropriate lines
    for i, line in enumerate(config_lines):
        if 'main.plugins.bt-tether.devices.ios-phone.mac' in line:
            config_lines[i] = f'main.plugins.bt-tether.devices.ios-phone.mac = "{bt_mac}" #BT Mac Address of iPhone\n'
        elif 'main.plugins.wpa-sec.api_key' in line:
            config_lines[i] = f'main.plugins.wpa-sec.api_key = "{wpa_api_key}" #wpa-sec API Key\n'
        elif 'main.plugins.discord-info.webhook_url' in line:
            config_lines[i] = f'main.plugins.discord-info.webhook_url = "{discord_webhook}" #Discord Webhook URL\n'

    # Saving the modified file
    with open(config_path, 'w') as file:
        file.writelines(config_lines)

def main():
    # Language selection
    language = input("Choose your language / Wybierz swój język (en/pl): ").strip().lower()
    
    if language == "pl":
        # Polish prompts
        bt_tether_prompt = "Czy korzystasz z BT-Tether? (tak/nie): "
        bt_mac_prompt = "Podaj MAC adres BT iPhone: "
        wpa_sec_prompt = "Czy korzystasz z wpa-sec? (tak/nie): "
        wpa_api_key_prompt = "Podaj klucz API wpa-sec: "
        discord_webhook_prompt = "Czy korzystasz z Discord Webhook? (tak/nie): "
        discord_url_prompt = "Podaj URL webhooka Discord: "
    else:
        # English prompts
        bt_tether_prompt = "Are you using BT-Tether? (yes/no): "
        bt_mac_prompt = "Please provide the BT iPhone MAC address: "
        wpa_sec_prompt = "Are you using wpa-sec? (yes/no): "
        wpa_api_key_prompt = "Please provide the wpa-sec API key: "
        discord_webhook_prompt = "Are you using Discord Webhook? (yes/no): "
        discord_url_prompt = "Please provide the Discord webhook URL: "

    download_files()

    # Asking the user for data
    bt_tether = input(bt_tether_prompt).strip().lower()
    bt_mac = ""
    if (language == "pl" and bt_tether == "tak") or (language != "pl" and bt_tether == "yes"):
        bt_mac = input(bt_mac_prompt).strip()

    wpa_sec = input(wpa_sec_prompt).strip().lower()
    wpa_api_key = ""
    if (language == "pl" and wpa_sec == "tak") or (language != "pl" and wpa_sec == "yes"):
        wpa_api_key = input(wpa_api_key_prompt).strip()

    discord_webhook = input(discord_webhook_prompt).strip().lower()
    discord_url = ""
    if (language == "pl" and discord_webhook == "tak") or (language != "pl" and discord_webhook == "yes"):
        discord_url = input(discord_url_prompt).strip()

    # Editing the config.toml file
    edit_config(bt_mac, wpa_api_key, discord_url)

if __name__ == "__main__":
    main() 