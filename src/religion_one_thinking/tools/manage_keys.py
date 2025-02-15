import asyncio
import argparse
from ..utils.key_manager import KeyManager

async def manage_keys(action: str, key: str = None):
    km = KeyManager()
    await km.initialize()
    
    if action == "add" and key:
        success = await km.add_key(key)
        print(f"Add key: {'success' if success else 'failed'}")
    
    elif action == "remove" and key:
        success = km.remove_key(key)
        print(f"Remove key: {'success' if success else 'failed'}")
    
    elif action == "list":
        status = km.get_key_status()
        print("\nKey Status:")
        print(f"Valid keys ({len(status['valid'])}):")
        for key in status['valid']:
            print(f"  {key[-8:]}")  # 只显示最后8位
        print(f"\nInvalid keys ({len(status['invalid'])}):")
        for key in status['invalid']:
            print(f"  {key[-8:]}")
        print(f"\nUnused keys ({len(status['unused'])}):")
        for key in status['unused']:
            print(f"  {key[-8:]}")
        if status['current']:
            print(f"\nCurrent key: {status['current'][-8:]}")

def main():
    parser = argparse.ArgumentParser(description="Manage OpenRouter API keys")
    parser.add_argument("action", choices=["add", "remove", "list"], help="Action to perform")
    parser.add_argument("--key", help="API key for add/remove actions")
    
    args = parser.parse_args()
    asyncio.run(manage_keys(args.action, args.key))

if __name__ == "__main__":
    main() 