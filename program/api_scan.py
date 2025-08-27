import os
import json
import requests
from config import SCAN_API_INFO, moralis_api
from web3 import Web3
from moralis import evm_api


erc20_abi = [
    {
        "constant": True,
        "inputs": [
            {"name": "_owner", "type": "address"}
        ],
        "name": "balanceOf",
        "outputs": [
            {"name": "balance", "type": "uint256"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [
            {"name": "decimals", "type": "uint8"}
        ],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

def get_erc20_price(info):
    # 检查必填项
    required_fields = ["block", "network", "token_address"]
    if not all(field in info for field in required_fields):
        raise ValueError("block, network 和 token_address 是必填项！")
    
    # 获取参数
    block = info.get("block")
    network = info.get("network")
    token_address = Web3.to_checksum_address(info.get("token_address"))

    # 定义保存路径（分级目录形式）
    save_dir = f"./prices/{network}/{token_address}"
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{block}.txt")

    # 检查本地文件是否存在
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            price = file.read()
            return price
            # if int(price) != 0:
            #     return price
        
    # 构造 API 请求参数
    params = {
        "chain": network,
        "to_block": block,
        "address": token_address
    }

    # 调用 Moralis API 获取代币价格
    try:
        result = evm_api.token.get_token_price(
            api_key=moralis_api, # Moralis API Key
            params=params,
        )
        price = result.get("usdPrice")
        # 将价格保存到本地文件
        with open(file_path, "w") as file:
            file.write(str(price))
            return float(price)
    except Exception as e:
        if 'free-plan-daily total included usage has been consumed' in str(e):
            exit()

def get_erc20_decimals(info):
    # 检查必填项
    required_fields = ["network", "token_address"]
    if not all(field in info for field in required_fields):
        raise ValueError("network 和 token_address 是必填项！")
    
    # 获取参数
    network = info.get("network")
    token_address = Web3.to_checksum_address(info.get("token_address"))
    if token_address == '0xc19b6a4ac7c7cc24459f08984bbd09664af17bd1':
        return 0
    elif token_address in ['0x7e9c15c43f0d6c4a12e6bdff7c7d55d0f80e3e23']:
        return 100

    # 获取对应网络的节点地址
    node_url = SCAN_API_INFO[network]['node_url']

    # 初始化Web3连接
    w3 = Web3(Web3.HTTPProvider(node_url))

    # 定义保存路径（分级目录形式）
    save_dir = f"./decimals/"
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{token_address}.txt")

    # 检查本地文件是否存在
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            decimals = file.read()
            decimals = int(decimals)
            # if decimals != 30:
            #     return decimals
            return decimals
    try:
        # 通过Web3初始化ERC20合约
        contract = w3.eth.contract(address=token_address, abi=erc20_abi)
        
        # 获取代币的精度
        decimals = contract.functions.decimals().call()

        # 将精度保存到本地文件
        with open(file_path, "w") as file:
            file.write(str(decimals))
    except:
        decimals = 100
    return int(decimals)

def get_erc20_balance_at_block(info):
    # 检查必填项
    required_fields = ["network", "block_number", "token_address", "eoa_address"]
    if not all(field in info for field in required_fields):
        raise ValueError("network, block_number, token_address 和 eoa_address 是必填项！")
    
    # 获取参数
    network = info.get("network")
    block_number = info.get("block_number")
    token_address = Web3.to_checksum_address(info.get("token_address"))
    eoa_address = Web3.to_checksum_address(info.get("eoa_address"))

    # 获取对应网络的节点地址
    node_url = SCAN_API_INFO[network]['node_url']

    # 初始化Web3连接
    w3 = Web3(Web3.HTTPProvider(node_url))

    # 定义保存路径（分级目录形式）
    save_dir = f"./balances/{eoa_address}/{token_address}"
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{block_number}.txt")

    # 检查本地文件是否存在
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            balance = file.read()
            return int(balance)
    else:
        # 通过Web3初始化ERC20合约
        contract = w3.eth.contract(address=token_address, abi=erc20_abi)
        
        # 获取指定区块的代币余额
        balance = contract.functions.balanceOf(eoa_address).call(block_identifier=block_number)

        # 将余额保存到本地文件
        with open(file_path, "w") as file:
            file.write(str(balance))
        return int(balance)

def get_transactions_by_address(filter_info, is_update=False):
    """
    获取指定地址的所有交易哈希。
    如果本地文件存在，则直接从本地文件加载数据；
    如果本地文件不存在，则按区块范围发起网络请求并保存数据到本地文件。
    
    参数:
        address (str): 要查询的地址。
    
    返回:
        list: 包含交易哈希的列表。
    """
    # 检查必填项
    if "address" not in filter_info:
        raise ValueError("address 和 topic0 是必填项！")
    address = filter_info.get("address")
    # 初始化区块范围
    from_block = filter_info.get("fromBlock", 0) # 从区块 0 开始
    to_block = filter_info.get("toBlock", 9999999999)  # 默认一个很大的值，表示查询到最新区块

    # 定义保存路径
    save_dir = f"./transactions/{address}"
    if os.path.exists(save_dir):
        if is_update == False:
            to_block = -1
    else:
        os.makedirs(save_dir, exist_ok=True)

    # 读取本地已有的区块范围文件
    local_transactions = []
    block_files = sorted([f for f in os.listdir(save_dir) if f.startswith("block_") and f.endswith(".json")])
    if block_files:
        print("本地已有区块范围数据，正在加载...")
        for block_file in block_files:
            with open(os.path.join(save_dir, block_file), "r") as f:
                local_transactions.extend(json.load(f))
        print(f"已加载 {len(local_transactions)} 条本地交易数据。")

        # 检查本地数据是否完整
        last_to_block = max([int(f.replace("block_", "").replace(".json", "").split("_")[1]) for f in block_files])
        if last_to_block < to_block:
            from_block = last_to_block + 1
            print(f"本地数据不完整，从区块 {from_block} 开始补充数据...")
        else:
            print("本地数据已完整，无需补充。")
            return [tx["hash"] for tx in local_transactions]
    else:
        print("本地没有区块范围数据，正在从网络获取...")

    # 如果本地数据不完整，按区块范围获取更多数据
    while from_block <= to_block:
        # 构造 API 请求参数
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": from_block,
            "endblock": to_block,
            "sort": "asc",  # 按区块号升序排序
            "apikey": SCAN_API_INFO[filter_info['network']]['api_key']
        }

        response = requests.get(SCAN_API_INFO[filter_info['network']]['url'], params=params)
        data = response.json()

        if data["status"] == "1" and data["result"]:
            transactions = data["result"]
            local_transactions.extend(transactions)

            # 提取当前区块范围
            block_numbers = [int(tx["blockNumber"]) for tx in transactions]
            min_block = min(block_numbers)
            max_block = max(block_numbers)

            # 保存当前区块范围的数据
            block_file = os.path.join(save_dir, f"block_{min_block}_{max_block}.json")
            with open(block_file, "w") as f:
                json.dump(transactions, f, indent=4)
            print(f"保存区块范围数据到 {block_file}")

            # 更新 from_block 为当前最大区块号 + 1
            from_block = max_block + 1
        else:
            print(f"当前区块范围 {from_block}-{to_block} 没有更多数据。")
            break

    # 提取所有交易哈希
    transaction_hashes = [tx["hash"] for tx in local_transactions]
    return transaction_hashes


def fetch_and_save_logs_by_block(filter_info, is_update=False):
    """
    根据输入的过滤条件获取日志数据，并按区块范围保存到本地文件。
    获取数据时优先检查本地文件，只有在本地文件不完整时才发起网络请求。
    每次循环时输出当前区块范围，并按区块范围命名保存文件。
    
    参数:
        filter_info (dict): 包含过滤条件的字典，格式为:
                            {
                                "address": "0xYourAddressHere",
                                "topic0": "0xYourTopic0Here",
                                "topic1": "0xYourTopic1Here",  # 可选
                                "topic2": "0xYourTopic2Here",  # 可选
                                "from_block": int,              # 可选
                                "to_block": int                # 可选
                            }
    
    返回:
        list: 合并后的日志数据列表。
    """
    # 检查必填项
    if "address" not in filter_info or "topic0" not in filter_info:
        raise ValueError("address 和 topic0 是必填项！")

    # 设置默认区块范围
    from_block = filter_info.get("from_block", 0)
    to_block = filter_info.get("to_block", 9999999999)  # 默认一个很大的值

    # 构造基础查询参数
    base_params = {
        "module": "logs",
        "action": "getLogs",
        # "address": filter_info["address"],
        "topic0": filter_info["topic0"],
        "apikey": SCAN_API_INFO[filter_info['network']]['api_key'],
        "fromBlock": from_block,
        "toBlock": to_block,
    }

    # 添加可选参数
    if "topic1" in filter_info:
        base_params["topic1"] = filter_info["topic1"]
    if "topic2" in filter_info:
        base_params["topic2"] = filter_info["topic2"]
    filter_info['address'] = filter_info["topic2"]

    # 保存路径
    save_dir = f"./logs/{filter_info['address']}_{filter_info['topic0']}"
    if os.path.exists(save_dir):
        if is_update == False:
            to_block = 0
    else:
        os.makedirs(save_dir, exist_ok=True)

    # 读取本地已有的区块范围文件
    local_logs = []
    block_files = sorted([f for f in os.listdir(save_dir) if f.startswith("block_") and f.endswith(".json")])
    if block_files:
        print("本地已有区块范围数据，正在加载...")
        for block_file in block_files:
            with open(os.path.join(save_dir, block_file), "r") as f:
                local_logs.extend(json.load(f))
        print(f"已加载 {len(local_logs)} 条本地日志数据。")

        # 检查本地数据是否完整
        last_to_block = max([int(f.replace("block_", "").replace(".json", "").split("_")[1]) for f in block_files])

        # 如果本地数据不完整，更新 from_block
        if last_to_block < to_block:
            from_block = last_to_block + 1
            print(f"本地数据不完整，从区块 {from_block} 开始补充数据...")
        else:
            print("本地数据已完整，无需补充。")
            return local_logs
    else:
        print("本地没有区块范围数据，正在从网络获取...")

    # 如果本地数据不完整，按区块范围获取更多数据
    while from_block <= to_block:
        base_params["fromBlock"] = from_block
        base_params["toBlock"] = to_block

        response = requests.get(SCAN_API_INFO[filter_info['network']]['url'], params=base_params)
        data = response.json()

        if data["status"] == "1" and data["result"]:
            logs = data["result"]
            local_logs.extend(logs)

            # 提取当前区块范围
            block_numbers = [int(log["blockNumber"], 16) for log in logs]
            min_block = min(block_numbers)
            max_block = max(block_numbers)

            # 保存当前区块范围的数据
            block_file = os.path.join(save_dir, f"block_{min_block}_{max_block}.json")
            with open(block_file, "w") as f:
                json.dump(logs, f, indent=4)
            print(f"保存区块范围数据到 {block_file}")

            # 更新 from_block 为当前最大区块号 + 1
            from_block = max_block + 1
        else:
            print(f"当前区块范围 {from_block}-{to_block} 没有更多数据。")
            break

    return local_logs

def get_contract_bytecode_from_node(info):
    # 检查必填项
    if "address" not in info or "network" not in info:
        raise ValueError("address 和 network 是必填项！")
    contract_address = info.get("address")
    node_url = SCAN_API_INFO[info.get("network")]['node_url']
    # 定义保存路径
    save_dir = f"./bytecode"
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{contract_address}.hex")

    # 检查本地文件是否存在
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            bytecode = file.read()
            return bytecode
    else:
        # 连接到节点
        web3 = Web3(Web3.HTTPProvider(node_url))

        # 获取合约字节码
        bytecode = web3.eth.get_code(Web3.to_checksum_address(contract_address)).hex()

        # 保存数据到本地文件
        with open(file_path, "w") as file:
            file.write(bytecode)
        return bytecode

def get_contract_sourcecode(info):
    # 检查必填项
    if "address" not in info or "network" not in info:
        raise ValueError("address 和 network 是必填项！")
    address = info.get("address")
    # 定义保存路径
    save_dir = f"./sourcecode"
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{address}.json")

    # 检查本地文件是否存在
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            data = json.load(file)
            return data["sourcecode"]
    else:
        # 构造 API 请求参数
        base_url = SCAN_API_INFO[info['network']]['url']
        params = {
            "module": "contract",
            "action": "getsourcecode",
            "address": address,
            "apikey": SCAN_API_INFO[info['network']]['api_key']
        }

        try:
            # 发送 GET 请求
            response = requests.get(base_url, params=params)
            response.raise_for_status()  # 检查请求是否成功
            data = response.json()

            # 检查返回的数据是否有效
            if data["status"] == "1" and data["result"]:
                contract_data = data["result"][0]
                sourcecode = contract_data["SourceCode"]
                
                # 保存数据到本地文件
                with open(file_path, "w") as file:
                    json.dump({"sourcecode": sourcecode}, file, indent=4)
                return sourcecode
            else:
                print(data["status"])
                print(data["result"])
                print(f"Error: {data['message']}")
                return None
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None
        except Exception as e:
            print(f"发生错误: {e}")
            return None

def fetch_and_save_approvals(filter_info, is_update=False):
    """
    根据输入的过滤条件获取日志数据，并按区块范围保存到本地文件。
    获取数据时优先检查本地文件，只有在本地文件不完整时才发起网络请求。
    每次循环时输出当前区块范围，并按区块范围命名保存文件。
    
    参数:
        filter_info (dict): 包含过滤条件的字典，格式为:
                            {
                                "address": "0xYourAddressHere",
                                "topic0": "0xYourTopic0Here",
                                "topic1": "0xYourTopic1Here",  # 可选
                                "topic2": "0xYourTopic2Here",  # 可选
                                "from_block": int,              # 可选
                                "to_block": int                # 可选
                            }
    
    返回:
        list: 合并后的日志数据列表。
    """
    # 检查必填项
    if "topic2" not in filter_info or "topic0" not in filter_info:
        raise ValueError("topic2 和 topic0 是必填项！")

    # 设置默认区块范围
    from_block = filter_info.get("from_block", 0)
    to_block = filter_info.get("to_block", 9999999999)  # 默认一个很大的值

    # 构造基础查询参数
    base_params = {
        "module": "logs",
        "action": "getLogs",
        "topic0": filter_info["topic0"],
        "topic0_2_opr": 'and',
        "topic2": filter_info["topic2"].replace('0x', '0x000000000000000000000000'),
        "apikey": SCAN_API_INFO[filter_info['network']]['api_key'],
        "fromBlock": from_block,
        "toBlock": to_block,
    }

    # 保存路径
    save_dir = f"./approvals/{filter_info['topic2']}_{filter_info['topic0']}"
    if os.path.exists(save_dir):
        if is_update == False:
            to_block = 0
    else:
        os.makedirs(save_dir, exist_ok=True)

    # 读取本地已有的区块范围文件
    local_logs = []
    block_files = sorted([f for f in os.listdir(save_dir) if f.startswith("block_") and f.endswith(".json")])
    if block_files:
        # print("本地已有区块范围数据，正在加载...")
        for block_file in block_files:
            with open(os.path.join(save_dir, block_file), "r") as f:
                local_logs.extend(json.load(f))
        # print(f"已加载 {len(local_logs)} 条本地日志数据。")

        # 检查本地数据是否完整
        last_to_block = max([int(f.replace("block_", "").replace(".json", "").split("_")[1]) for f in block_files])

        # 如果本地数据不完整，更新 from_block
        if last_to_block < to_block:
            from_block = last_to_block + 1
            # print(f"本地数据不完整，从区块 {from_block} 开始补充数据...")
        else:
            # print("本地数据已完整，无需补充。")
            return local_logs
    else:
        pass
        # print("本地没有区块范围数据，正在从网络获取...")

    # 如果本地数据不完整，按区块范围获取更多数据
    while from_block <= to_block:
        base_params["fromBlock"] = from_block
        base_params["toBlock"] = to_block

        response = requests.get(SCAN_API_INFO[filter_info['network']]['url'], params=base_params)
        data = response.json()

        if data["status"] == "1" and data["result"]:
            logs = data["result"]
            local_logs.extend(logs)

            # 提取当前区块范围
            block_numbers = [int(log["blockNumber"], 16) for log in logs]
            min_block = min(block_numbers)
            max_block = max(block_numbers)

            # 保存当前区块范围的数据
            block_file = os.path.join(save_dir, f"block_{min_block}_{max_block}.json")
            with open(block_file, "w") as f:
                json.dump(logs, f, indent=4)
            # print(f"保存区块范围数据到 {block_file}")

            # 更新 from_block 为当前最大区块号 + 1
            from_block = max_block + 1
        else:
            # print(f"当前区块范围 {from_block}-{to_block} 没有更多数据。")
            break

    return local_logs


def get_address_nametag(info):
    """
    根据地址获取以太坊地址的名称标签 (nametag) 信息。

    Args:
        info (dict): 包含地址信息的字典。
                     必需字段：
                     - "address" (str): 要查询的以太坊地址。
                     可选字段：
                     - "network" (str): 网络名称，默认为 "mainnet"。

    Returns:
        str or None: 地址的名称标签，如果获取失败则返回 None。
    Raises:
        ValueError: 如果 "address" 字段缺失。
    """
    # 检查必填项
    if "address" not in info:
        raise ValueError("address 是必填项！")

    address = info.get("address")
    network = info.get("network", "ETH") # 默认为 mainnet

    # 定义保存路径
    save_dir = f"./nametag"
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, f"{address}_nametag.json")

    # 检查本地文件是否存在
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            data = json.load(file)
            return data.get("nametag")
    else:
        # 构造 API 请求参数
        base_url = SCAN_API_INFO.get(network, {}).get('url')
        api_key = SCAN_API_INFO.get(network, {}).get('api_key')

        if not base_url or not api_key:
            print(f"Error: 无法获取 {network} 网络的 API URL 或 API Key。请检查 SCAN_API_INFO 配置。")
            return None

        params = {
            "module": "nametag",
            "action": "getaddresstag",
            "address": address,
            "apikey": api_key
        }
        # 移除 None 值的参数
        params = {k: v for k, v in params.items() if v is not None}

        try:
            # 发送 GET 请求
            response = requests.get(base_url.replace("/api", "/v2/api"), params=params) # 注意 /v2/api
            response.raise_for_status()  # 检查请求是否成功
            data = response.json()

            # 检查返回的数据是否有效
            if data["status"] == "1" and data["result"]:
                nametag = data["result"]
                
                # 保存数据到本地文件
                with open(file_path, "w") as file:
                    json.dump({"nametag": nametag}, file, indent=4)
                return nametag
            else:
                print(f"API 返回错误状态或无结果: status={data.get('status')}, message={data.get('message')}, result={data.get('result')}")
                return None
        except requests.RequestException as e:
            print(f"请求失败: {e}")
            return None
        except Exception as e:
            print(f"发生错误: {e}")
            return None