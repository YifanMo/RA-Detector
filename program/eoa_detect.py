from detect_contract import detect_one_way_trip
from cfg_builder import parse_contract
from tqdm.contrib.concurrent import process_map
import os
import pandas as pd
from tqdm import tqdm
import time
import json
import multiprocessing



# nohup python eoa_detect.py > eoa_detect.py.log 2>&1 &
# lsof -p 1588790
# tail -f eoa_detect.py.log

def get_tac_files(file_folder):
    # 确保文件夹路径存在
    if not os.path.exists(file_folder):
        print(f"文件夹 {file_folder} 不存在")
        return []

    # 获取文件夹下所有文件和文件夹
    all_files = os.listdir(file_folder)
    # 筛选出扩展名为.tac的文件
    tac_files = [os.path.join(file_folder, file) for file in all_files if file.endswith('.tac')]
    return tac_files

def process_file(file_path):
    contract_address = file_path.replace('./tac/', '').replace('.tac', '')
    results = []
    try:
        local_res_path = f"./contract_res/{contract_address}_SUCCESS.json"
        if os.path.exists(local_res_path):
            with open(local_res_path, "r") as f:
                _res = json.load(f)
            results.append(_res)
        else:
            functions = parse_contract(file_path)
            for fun in functions:
                local_res_path = f"./contract_res/{contract_address}_{fun['name']}.json"
                if os.path.exists(local_res_path):
                    with open(local_res_path, "r") as f:
                        _res = json.load(f)

                start_time = time.perf_counter()
                _res = {
                    'contract': contract_address,
                    'function': fun['name'],
                    'is_one_way_trip': detect_one_way_trip(fun)
                }
                end_time = time.perf_counter()

                elapsed_time = end_time - start_time
                _res['time'] = elapsed_time
                results.append(_res)

    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        local_res_path = f"./contract_res/{contract_address}_ERROR.json"
        results.append({
                'contract': contract_address,
                'function': '',
                'is_one_way_trip': '',
                'time': 'Error or Timeout'
        })

    finally:
        # print(_res)
        # with open(local_res_path, "w") as f:
        #     json.dump(_res, f, indent=4)
        
        return results

def process_with_timeout(pool, func, arg, timeout):
    """
    使用 Pool 并发执行一个任务，带 timeout。
    """
    async_result = pool.apply_async(func, args=(arg,))
    try:
        result = async_result.get(timeout=timeout)
        return result
    except multiprocessing.TimeoutError:
        print(f"Task with input {arg} timed out.")
        return []

def main():
    # file_paths = [f'./tac/0x6c92ceeb09c83f1018d5bca81d933df3eeaed0a1.tac']
    file_paths = []
    for contract in pd.read_csv('phishing_contracts.csv')['address'].value_counts().index.tolist():
        file_paths.append(f'./tac/{contract}.tac')
    # file_paths = get_tac_files('./tac')
    # file_paths = file_paths[:1000]
    # 使用 process_map 并行处理文件
    # all_results = process_map(process_file, file_paths, max_workers=15, chunksize=1)
    # for file_path in tqdm(file_paths):
        # all_results.append(process_file(file_path))
    with multiprocessing.Pool(processes=5) as pool:
        all_results = []
        for file_path in tqdm(file_paths):
            result = process_with_timeout(pool, process_file, file_path, timeout=5)
            all_results.append(result)

    # 将所有结果展平成一个列表
    # print(all_results)
    res = [item for sublist in all_results for item in sublist]

    df = pd.DataFrame(res)
    df = df[df['function']!='']
    df.to_csv('eoa_res.csv', index=False)
    # df['SLOAD check'] = df['is_one_way_trip'].apply(lambda x: x['SLOAD check'] if (x != True) and (x != False) and ('SLOAD check' in x.keys()) else False)
    # df['transfer_to check'] = df['is_one_way_trip'].apply(lambda x: x['transfer_to check'] if (x != True) and (x != False) and ('transfer_to check' in x.keys()) else False)

    # print(df[(df['is_one_way_trip']!=True)&(df['transfer_to check']!=set())])

    # print(df['is_one_way_trip'].value_counts())

    # df.to_csv('`eoa_res`.csv', index=False)

if __name__ == "__main__":
    main()