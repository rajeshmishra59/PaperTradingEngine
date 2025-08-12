# select_broker.py
import yaml
from pathlib import Path

CFG = Path("config.yml")

def set_broker(name: str):
    name = (name or "").strip().lower()
    if name not in {"zerodha", "angelone"}:
        raise SystemExit("Use broker as 'zerodha' or 'angelone'")
    data = yaml.safe_load(CFG.read_text(encoding="utf-8"))
    data["broker"] = name
    CFG.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    print(f"✅ broker set to: {name}")

if __name__ == "__main__":
    try:
        choice = input("Select broker [zerodha/angelone]: ").strip().lower()
        set_broker(choice)
    except Exception as e:
        print(f"❌ {e}")
