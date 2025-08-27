# example https://app.dedaub.com/api/transaction/arbitrum/0x05ff1daf578fe5f5c239c8709aca781c56c0c9fad111691175e77bb23a02bf1e/debug
# 95d43674655911a7b8a0851a1dfb21afaf72c92f3bc5d572a60a9bc0282ef660d816b34bdc2771b85788a3a3d70a342cfb1bd8475e6bf9b1d88111297a125157

import requests
import json
import os

def get_transaction_trace(tx_hash,network):
    # 创建保存目录
    os.makedirs('./tx_trace', exist_ok=True)

    # 构造文件路径
    file_path = f'./tx_trace/{tx_hash}.json'

    # 检查本地文件是否存在
    if os.path.exists(file_path):
        try:
            # 读取本地文件内容
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
        except Exception as e:
            print(f"Failed to read local file for address {tx_hash}. Error: {e}")
    else:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': f'https://app.dedaub.com/app/tx/{network}/{tx_hash}',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }
        url = f'https://app.dedaub.com/api/transaction/{network}/{tx_hash}/debug'

        try:
            # 发送GET请求
            response = requests.get(url, headers=headers)

            # 检查请求是否成功
            if response.status_code == 200:
                # 获取返回的JSON数据
                data = response.json()

                # 保存数据为JSON文件
                with open(file_path, 'w') as json_file:
                    json.dump(data, json_file, indent=4)
            else:
                print(f"Failed to fetch data for {tx_hash}. Status code: {response.status_code}")
        except Exception as e:
            print(f"An error occurred while fetching data: {e}")
    return data