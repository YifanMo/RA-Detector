from api_scan import fetch_and_save_approvals
from tqdm.contrib.concurrent import process_map
from config import SCAN_API_INFO
import pandas as pd
import time

# 定义处理单个地址的函数
def process_address(address):
    filter_info = {
        "topic0": "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925", # Approval
        'network': 'ETH', 
        "topic2": address, # attacker
    }
    # filter_info['from_block'] = 16286696#SCAN_API_INFO[filter_info['network']]['from_block']
    # filter_info['to_block'] = 21525890#SCAN_API_INFO[filter_info['network']]['to_block']
    logs = fetch_and_save_approvals(filter_info, is_update=False)
    print(f"获取到的日志总数: {len(logs)}")
    return logs

def main(phishing_contract_list, num_processes=4):
    logs = process_map(process_address, phishing_contract_list, max_workers=num_processes,chunksize=10)
    res = []
    for log in logs:
        res.extend(log)
    return res

# 示例调用
if __name__ == "__main__":
    while True:
        try:
            phishing_contract_list = pd.read_csv('phishing_contracts.csv')['address'].tolist()  # 替换为你的地址列表
            logs = main(phishing_contract_list, num_processes=12)
            df = pd.DataFrame(logs)
            print(df)
            df.to_csv('approval_log_labeled.csv',index=False)
            break  # 如果没有异常，正常退出循环
        except Exception as e:
            print(f"出现错误: {e}")
            print("暂停后重试...")
            time.sleep(5) 
