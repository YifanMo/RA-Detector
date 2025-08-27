import api_dedaub
from tqdm.contrib.concurrent import process_map
import pandas as pd
from config import SCAN_API_INFO
from api_scan import fetch_and_save_approvals
import time

def get_all_approvals():
    phishing_contracts = pd.read_csv('phishing_contracts.csv')['address'].tolist()
    approval_log = []
    for address in phishing_contracts:
        filter_info = {
            "topic0": "0x8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925", # Approval
            'network': 'ETH', 
            "topic2": address, # attacker
        }
        filter_info['from_block'] = SCAN_API_INFO[filter_info['network']]['from_block']
        filter_info['to_block'] = SCAN_API_INFO[filter_info['network']]['to_block']
        log = fetch_and_save_approvals(filter_info, is_update=False)
        if log != []:
            log = pd.DataFrame(log)
            approval_log.append(log)
    approval_log = pd.concat(approval_log)
    approval_amt = approval_log['data'].apply(lambda x: int(x.replace('0x','0x0'), 16))
    approval_log = approval_log[approval_amt!=0]
    phishing_tx_list = approval_log['transactionHash'].tolist()
    return phishing_tx_list

def main(phishing_tx):
    network = 'ethereum'
    api_dedaub.get_transaction_trace(phishing_tx, network)

if __name__ == '__main__':
    while True:
        try:
            # phishing_tx_list = get_all_approvals()
            df = pd.read_csv('approval_log_labeled_filted.csv')
            phishing_tx_list = df['transactionHash'].value_counts().index.tolist()
            process_map(main, phishing_tx_list, max_workers=5,chunksize=1)
            break  # 如果没有异常，正常退出循环
        except Exception as e:
            print(f"出现错误: {e}")
            print("暂停后重试...")
            time.sleep(5) 