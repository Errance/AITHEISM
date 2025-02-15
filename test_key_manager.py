import asyncio
from src.religion_one_thinking.utils.key_manager import KeyManager

async def test_key_manager():
    print("\n=== 开始测试 Key Manager ===\n")
    
    km = KeyManager()
    
    # 1. 测试初始化
    print("1. 初始化 Key Manager...")
    await km.initialize()
    status = km.get_key_status()
    print("初始状态:", status)
    
    # 2. 测试添加新 key
    print("\n2. 测试添加新 key...")
    new_key = "test_key_06"
    result = await km.add_key(new_key)
    print(f"添加 key {new_key}: {'成功' if result else '失败'}")
    print("添加后状态:", km.get_key_status())
    
    # 3. 测试移除 key
    print("\n3. 测试移除 key...")
    remove_key = "test_key_01"
    result = km.remove_key(remove_key)
    print(f"移除 key {remove_key}: {'成功' if result else '失败'}")
    print("移除后状态:", km.get_key_status())
    
    # 4. 测试当前 key 信息
    print("\n4. 测试当前 key 信息...")
    current_info = km.get_current_key_info()
    print("当前 key 信息:", current_info)
    
    # 5. 测试 key 切换
    print("\n5. 测试 key 切换...")
    next_key = km.switch_to_next_key()
    print(f"切换到下一个 key: {next_key}")
    print("切换后状态:", km.get_key_status())

    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_key_manager()) 