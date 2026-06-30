import os
import subprocess
import sys
import venv

def main():
    print("--- SMART IoT WASTE CLASSIFICATION - SETUP ---")
    
    # 1. Create images directory (for saving captured photos)
    images_dir = "images"
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
        print(f"[OK] Created directory: {images_dir}")
    else:
        print(f"[INFO] Directory '{images_dir}' already exists.")

    # 2. Auto-generate .env file with default configurations
    env_file = ".env"
    if not os.path.exists(env_file):
        print(f"\n[..] Creating {env_file} file with default configurations...")
        with open(env_file, "w") as f:
            f.write("# --- DATABASE CONFIGURATION ---\n")
            f.write('MONGO_URI="mongodb://localhost:27017/waste_management"\n')
            f.write('DB_NAME="WasteManagementDB"\n')
            f.write('COLLECTION_NAME="WasteRecords"\n\n')
            f.write("# --- WEB SERVER CONFIGURATION ---\n")
            f.write('WEB_PORT=5000\n')
        print(f"[OK] {env_file} created successfully.")
    else:
        print(f"\n[INFO] {env_file} already exists. Skipping creation.")

    # 3. Create virtual environment (.venv)
    venv_dir = ".venv"
    if not os.path.exists(venv_dir):
        print("\n[..] Creating virtual environment (.venv)...")
        venv.create(venv_dir, with_pip=True)
        print(f"[OK] Virtual environment created at: {venv_dir}")
    else:
        print(f"\n[INFO] Virtual environment '{venv_dir}' already exists.")

    # 4. Determine pip path based on OS
    if sys.platform == "win32":
        pip_exe = os.path.join(venv_dir, "Scripts", "pip")
    else:
        pip_exe = os.path.join(venv_dir, "bin", "pip")

    # 5. Install required libraries
    packages = [
        "tensorflow",
        "opencv-python",
        "numpy",
        "pillow",
        "pymongo",
        "flask",
        "flask-cors",
        "rich",
        "requests",
        "python-dotenv"
    ]
    
    if sys.platform == "win32":
        packages.append("winsdk")

    print("\n[..] Installing required libraries. This may take a few minutes...")
    try:
        subprocess.check_call([pip_exe, "install", "--upgrade", "pip"])
        subprocess.check_call([pip_exe, "install"] + packages)
        print("[OK] All libraries installed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install libraries: {e}")
        return

    print("\n--- SETUP COMPLETE ---")
    if sys.platform == "win32":
        print(f"To start using the environment, run: .venv\\Scripts\\activate")
    else:
        print(f"To start using the environment, run: source .venv/bin/activate")

if __name__ == "__main__":
    main()