import pandas as pd
from config import SCAN_API_INFO
import api_scan
import api_dedaub
import time
from tqdm.contrib.concurrent import process_map

def process_row(row):
    token_address = row['address']
    owner = row['owner']
    spender = row['spender']
    tx_hash = row['transactionHash']
    block_num = int(row['blockNumber'], 16)
    tx_trace = api_dedaub.get_transaction_trace(tx_hash, 'ethereum')
    sender = f"0x{tx_trace['tx_data']['from_a']}"
    token_transfer = tx_trace['token_transfers']
    if sender == owner:
        not_owner_transfer = []
    else:
        not_owner_transfer = [
            i for i in token_transfer 
            if (i['address'].lower() == token_address.lower()) and (i['from_a'].lower() == owner.lower())
        ]
    
    transfer_amt = int(sum([int(i['amount'],16) for i in not_owner_transfer]))
    trace_node = str(tx_trace['trace_node'])
    if "'signature': 'permit" in trace_node:
        is_permit = True
    else:
        is_permit = False
    if 'CREATE2' in trace_node:
        is_create2 = True
    else:
        is_create2 = False
    approval_amt = row['data']
    if approval_amt == 0:
        decimals = 99
        price = 0
    else:
        info = {
            "network": "ETH", 
            "token_address": token_address  # ERC20代币的地址
        }
        decimals = api_scan.get_erc20_decimals(info)

        price = 0
        if token_address in tx_trace['tokens'].keys():
            try:
                price = float(tx_trace['tokens'][token_address]['last_price'])
            except:
                pass
            try:
                decimals = int(tx_trace['tokens'][token_address]['decimals'])
            except:
                pass
    return {
        'tx_hash': tx_hash,
        'block_num': block_num,
        'timestamp': int(row['timeStamp'],16),
        'token_address': token_address,
        'sender': sender,
        'owner': owner,
        'spender': spender,
        'is_permit': is_permit,
        'is_create2': is_create2,
        'not_owner_transfer': not_owner_transfer,
        'approval_amt': approval_amt,
        'transfer_amt': transfer_amt,
        'decimals': decimals,
        'price': price
    }

def main():

    # approval_log = pd.read_csv('approval_log_labeled_filted.csv')
    # # approval_log = approval_log[:100]
    # res = process_map(process_row, [row for _, row in approval_log.iterrows()], max_workers=5, chunksize=50)
    # df = pd.DataFrame(res)
    # df.to_csv('RQ1_result.csv', index=False)

    approval_log = pd.read_csv('TP_wild_txs.csv')
    res = process_map(process_row, [row for _, row in approval_log.iterrows()], max_workers=5, chunksize=50)
    df = pd.DataFrame(res)
    df.to_csv('RQ2_result.csv', index=False)

if __name__ == '__main__':
    while True:
        try:
            main()
            break  # 如果没有异常，正常退出循环
        except Exception as e:
            print(f"出现错误: {e}")
            print("暂停后重试...")
            time.sleep(50) 