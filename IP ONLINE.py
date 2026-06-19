import os
import subprocess
import sys
import requests

def get_public_ip():
    try:
        # Fetch public IP safely using requests
        response = requests.get("https://api.ipify.org", timeout=5)
        if response.status_code == 200:
            return response.text.strip()
    except requests.RequestException:
        pass
    return None

def find_tshark():
    # Common paths for Windows
    paths = [
        r"C:\Program Files\Wireshark\tshark.exe",
        r"C:\Program Files (x86)\Wireshark\tshark.exe"
    ]
    for path in paths:
        if os.path.exists(path):
            return path
    return None

def main():
    # Set console title (Windows only)
    if os.name == 'nt':
        os.system('title Ebola Puller')
        # Simple trick to change text color to green on Windows
        os.system('color A')

    print("Retrieving public IP...")
    public_ip = get_public_ip()
    if not public_ip:
        print("Failed to retrieve public IP.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    tshark_path = find_tshark()
    if not tshark_path:
        print("Wireshark (tshark.exe) not found.")
        print("Opening Wireshark download page...")
        import webbrowser
        webbrowser.open("https://www.wireshark.org/download.html")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print(f"tshark.exe Found! ({tshark_path})\n")

    # List interfaces
    try:
        subprocess.run([tshark_path, "-D"], check=True)
    except subprocess.CalledProcessError:
        print("Error listing interfaces.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    print("")
    interface = input("Interface #: ")

    # Clear screen (cls for Windows, clear for Unix)
    os.system('cls' if os.name == 'nt' else 'clear')

    print("\nIP Dump")
    print("-------\n")

    # Construct the tshark command exactly like the original script
    # Filters out your own public IP from STUN/UDP traffic responses
    display_filter = f"stun.type == 0x0101 && stun.att.type == 0x0020 && stun.att.ipv4 != {public_ip}"
    
    tshark_cmd = [
        tshark_path,
        "-i", interface,
        "-f", "udp",
        "-Y", display_filter,
        "-T", "fields",
        "-e", "stun.att.ipv4"
    ]

    try:
        # Run tshark and let it stream outputs to the console
        subprocess.run(tshark_cmd)
    except KeyboardInterrupt:
        print("\nCapture stopped by user.")
    except Exception as e:
        print(f"\nAn error occurred while running tshark: {e}")

if __name__ == "__main__":
    main()