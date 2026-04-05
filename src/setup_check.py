import sys
import shutil
import subprocess


def check_python_version():
    v = sys.version_info
    ok = v >= (3, 10)
    ver = f"{v.major}.{v.minor}.{v.micro}"
    return ok, f"Python {ver}", "" if ok else "Install Python 3.10+ from python.org"


def check_package(name):
    try:
        __import__(name)
        return True, f"{name} installed", ""
    except ImportError:
        return False, f"{name} MISSING", f"Run: pip install {name}"


def check_microphone():
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d["max_input_channels"] > 0]
        if input_devices:
            default = sd.query_devices(kind="input")
            return True, f"Microphone: {default['name']}", ""
        return False, "No microphone found", "Connect a microphone and retry"
    except Exception as e:
        return False, f"Microphone error: {e}", "Check audio drivers"


def check_cuda():
    try:
        import ctypes
        ctypes.cdll.LoadLibrary("cudart64_12.dll")
        return True, "CUDA available — will use 'medium' model", ""
    except OSError:
        return False, "CUDA not available — will use 'small' model (CPU)", (
            "Optional: Install CUDA toolkit + cuDNN for faster transcription"
        )


def check_whisper_model():
    try:
        from faster_whisper.utils import download_model
        import os
        cache_dir = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
        # Just check if faster_whisper can be imported; model downloads on first use
        return True, "faster-whisper ready (model downloads on first run)", ""
    except ImportError:
        return False, "faster-whisper not installed", "Run: pip install faster-whisper"


def run_checks():
    checks = [
        check_python_version(),
        check_package("faster_whisper"),
        check_package("sounddevice"),
        check_package("pynput"),
        check_package("pystray"),
        check_package("PIL"),
        check_package("pyperclip"),
        check_microphone(),
        check_cuda(),
        check_whisper_model(),
    ]

    print("=" * 50)
    print("  Speech-to-Text Setup Check")
    print("=" * 50)
    print()

    all_ok = True
    for ok, message, fix in checks:
        status = "[OK]  " if ok else "[FAIL]"
        print(f"  {status} {message}")
        if not ok and fix:
            print(f"         -> {fix}")
            all_ok = False

    print()
    if all_ok:
        print("  All checks passed! Run start.bat to launch.")
    else:
        print("  Some checks failed. Fix the issues above and re-run.")
    print()
    return all_ok


if __name__ == "__main__":
    success = run_checks()
    sys.exit(0 if success else 1)
