import api_scan 
import pandas as pd
import json
import multiprocessing

def fetch_contract_data(contract_address):
    info = {
        'address': contract_address,
        'network': 'ETH'
    }
    sourcecode = api_scan.get_contract_sourcecode(info)
    bytecode = api_scan.get_contract_bytecode_from_node(info)

if __name__ == '__main__':
    df = phishing_contracts = pd.read_csv('phishing_contracts.csv')
    contract_list = df['address'].tolist()
    cpu_count = 4#multiprocessing.cpu_count()-2
    # print(cpu_count)
    # exit()
    with multiprocessing.Pool(processes=cpu_count) as pool:
        pool.map(fetch_contract_data, contract_list)