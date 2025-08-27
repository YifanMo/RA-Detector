import re
from collections import defaultdict

def build_cfg(blocks):
    cfg = defaultdict(list)
    for block in blocks:
        block_id = block['block_id']
        for succ in block['succ']:
            cfg[block_id].append(succ)
    return cfg

def dfs_paths(cfg, start, goal, path=None):
    if path is None:
        path = [start]
    if start == goal:
        yield path
    for next_block in cfg[start]:
        if next_block not in path:
            yield from dfs_paths(cfg, next_block, goal, path + [next_block])

def extract_conditions(blocks, path):
    conditions = []
    for block_id in path:
        for block in blocks:
            if block['block_id'] == block_id:
                for pc, tac in block['tac']:
                    if 'JUMPI' in tac:
                        conditions.append((pc, tac))
                break
    return conditions

def get_control_flow_conditions(blocks, target_pc):
    cfg = build_cfg(blocks)
    start_block = [i['block_id'] for i in blocks][0]
    target_block = None

    for block in blocks:
        for pc, _ in block['tac']:
            if pc == target_pc:
                target_block = block['block_id']
                break
        if target_block:
            break

    if not target_block:
        return "Target PC not found in any block"

    paths = list(dfs_paths(cfg, start_block, target_block))
    if not paths:
        return "No path to target block"

    conditions = []
    for path in paths:
        condition = []
        condition.extend(extract_conditions(blocks, path))
        conditions.append(condition)

    return conditions

def parse_contract(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    functions = []
    current_function = None
    current_block = None
    block_pattern = re.compile(r"Begin block (\w+)")
    prev_succ_pattern = re.compile(r"prev=\[(.*?)\], succ=\[(.*?)\]")
    tac_pattern = re.compile(r"(\w+): (.+)")

    in_function = False
    in_block = False

    for line in lines:
        line = line.strip()

        # Check if we are entering a function
        if line.startswith("function"):
            in_function = True
            current_function = {
                "name": line.split()[1].strip("()"),
                "blocks": [],
                "is_private": 'private' in line
            }
        elif in_function and line == "{":
            continue
        elif in_function and line == "}":
            in_function = False
            # if current_function["name"] != "__function_selector__":
            #     functions.append(current_function)
            functions.append(current_function)
            current_function = None
        elif in_function:
            # if current_function["name"] == "__function_selector__":
            #     continue
            if line.startswith("Begin block"):
                in_block = True
                current_block = {
                    "block_id": block_pattern.match(line).group(1),
                    "prev": [],
                    "succ": [],
                    "tac": []
                }
            elif line == "":
                in_block = False
                current_function["blocks"].append(current_block)
                current_block = None
            elif in_block and "prev=" in line:
                prev_succ_match = prev_succ_pattern.match(line)
                if prev_succ_match:
                    current_block["prev"] = [x.strip() for x in prev_succ_match.group(1).split(',')] if prev_succ_match.group(1) else []
                    current_block["succ"] = [x.strip() for x in prev_succ_match.group(2).split(',')] if prev_succ_match.group(2) else []
            elif in_block:
                tac_match = tac_pattern.match(line)
                if tac_match:
                    current_block["tac"].append((tac_match.group(1), tac_match.group(2)))

    return functions

def format_functions(functions):
    formatted_output = []
    for func in functions:
        formatted_output.append(f"function {func['name']} {{")
        for block in func['blocks']:
            formatted_output.append(f"  Begin block {block['block_id']}")
            formatted_output.append(f"  prev={block['prev']}, succ={block['succ']}")
            formatted_output.append("  ===============================")
            for tac in block['tac']:
                formatted_output.append(f"  {tac[0]}: {tac[1]}")
            # formatted_output.append("\n")
        formatted_output.append("}")
    return "\n".join(formatted_output)

if __name__ == "__main__":
    input_file_path = "bybit_attacker.txt"
    functions = parse_contract(input_file_path)
    formatted_output = format_functions(functions)
    print(functions[1])