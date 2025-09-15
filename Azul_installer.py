import os
import socket
import subprocess
import tempfile
import shutil
import requests
import tarfile
import zipfile
import platform

AZUL_METADATA_BASE = "https://api.azul.com/metadata/v1" # Azul's metadata API base URL


# Normalize OS and architecture
def normalize_os_arch():
    system = platform.system().lower()
    machine = platform.machine().lower()

    if "windows" in system:
        os_name = "windows"
    elif "linux" in system:
        os_name = "linux"
    elif "darwin" in system or "mac" in system:
        os_name = "macos"
    else:
        raise ValueError(f"Unsupported OS: {system}")
    
    # Mapping the architecture

    if machine in ["x86_64", "amd64"]:
        arch = "x86_64"
    elif machine in ["aarch64", "arm64"]:
        arch = "aarch64"
    else:
        raise ValueError(f"Unsupported architecture: {machine}")
    
    return os_name, arch


def get_latest_zulu(java_major=21, os_name=None, arch=None):

    if not os_name or not arch:
        os_name, arch = normalize_os_arch()

    params = {
        "java_version": java_major,
        "os": os_name,
        "arch": arch,
        "java_package_type": "jdk",
        "release_status": "ga",
        "availability_types": "CA",
        "latest": "true",
        "page_size": 20
    }

    url = f"{AZUL_METADATA_BASE}/zulu/packages/"
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    if not data:
        raise ValueError("No matching Zulu JDK found.")
    
    def pick(suffix):
        for pkg in data:
            name = pkg["name"].lower()
            if "-crac-" in name:
                continue
            if any(name.endswith(suf) for suf in suffix):
                return pkg["download_url"], pkg["name"]
        return None
    
    if os_name == "windows":

        found = pick([".msi"]) or pick([".zip"])
    
    elif os_name == "macos":
        found = pick([".tar.gz", ".tgz"]) or pick([".zip"])
    else: # For Linux distros
        found = pick([".tar.gz", ".tgz"]) or pick([".zip"])
    
    if not found:
        raise ValueError("No suitable package found for the specified OS and architecture.")
    return found


def download_file(url,dest):

    print (f"Downloading {url}...")

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print (f"Saved: {dest}")

def extract_archive(archive_path, extract_to):
    if archive_path.endswith(".zip"):
        with zipfile.ZipFile(archive_path, 'r') as z:
            z.extractall(extract_to)
    elif archive_path.endswith((".tar.gz", ".tgz")):
        with tarfile.open(archive_path, 'r:gz') as t:
            t.extractall(extract_to)
    else:
        raise ValueError("Unsupported archive format.")
    print(f"Extracted to: {extract_to}")

def ensure_java_installed():
    try:
        out = subprocess.run(["java", "-version"], capture_output=True, text=True)
        return out.returncode == 0
    except FileNotFoundError:
        return False

def install_zulu_msi(msi_path):
    print ("Running MSI installer (requires Administrator access)...")
    subprocess.run([
        "msiexec", "/i", msi_path,
        "/qn",
        "ADDLOCAL=FeatureJavaHome,FeatureEnvironment"
    ], check=True)
    print("✅ Azul JDK installed via MSI.")

def setup_java(java_major=21):
    if ensure_java_installed():
        print("✅ Java is already installed.")
        return
        
    os_name, arch = normalize_os_arch()
    url, fname = get_latest_zulu(java_major, os_name, arch)

    print(f"Found Azul JDK package: {fname}")

    tmpdir = tempfile.mkdtemp()
    try:
        file_path = os.path.join(tmpdir, fname)
        download_file(url, file_path)

        if os_name == "windows":
            install_zulu_msi(file_path)
            java_bin = "java"
        else:
            install_dir = os.path.join(os.getcwd(), "zulu-jdk")
            os.makedirs(install_dir, exist_ok=True)
            extract_archive(file_path, install_dir)
            print(f"✅ OpenJDK extracted to:", install_dir)

            jdk_contents = os.listdir(install_dir)
            if not jdk_contents:
                raise RuntimeError("Extraction failed, no contents found.")
            jdk_root = os.path.join(install_dir, jdk_contents[0])
            java_bin = os.path.join(jdk_root, "bin", "java")
                # subprocess.run([java_bin, "-version"])
    finally: 
        shutil.rmtree(tmpdir, ignore_errors=True) 

    # Verify installation       
    try:
        out = subprocess.run([java_bin, "-version"], capture_output=True, text=True)
        print("Java version:\n", out.stderr.strip() or out.stdout.strip())
    except Exception as e:
        print("⚠️ Java check failed:", e)

        

        # ============================= Turned off to test the new part=========================
        # if os_name in ("linux", "macos"):
        #     extract_archive(file_path, install_dir)
        # elif os_name == "windows":
        #     extract_archive(file_path, install_dir)
        # else:
        #     raise ValueError(f"Unsupported OS for extraction: {os_name}")
        # print(f"✅ Azul JDK installed at:", install_dir)
        #  ============================= Turned off to test the new part=========================
        
        
    # Verify installation
    # try:
    #     out = subprocess.run(["java", "-version"], capture_output=True, text=True)
    #     print("Java version: \n", out.stderr.strip())

    # except Exception as e:
    #     print("⚠️ Java installation failed:", e)

if __name__ == "__main__":
    setup_java(java_major=21)

    





