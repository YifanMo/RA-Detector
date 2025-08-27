from cfg_builder import parse_contract, get_control_flow_conditions
from taint_analysis import find_tainted_opcode, find_tainted_opcode_in_block

def extract_transfer_in_call(function):
    source = ['0x23b872dd'] # transferFrom
    tainted_opcode='CALL'
    tainted_call, _ = find_tainted_opcode_in_block(function, source, tainted_opcode) # transfer erc20 token
    tainted_call_pc = [i['pc'] for i in tainted_call]
    return tainted_call

def extract_arbitrary_call(function):
    source = ['CALLDATALOAD','CALLDATASIZE'] # transferFrom
    tainted_opcode='CALL'
    tainted_call, _ = find_tainted_opcode(function, source, tainted_opcode) # transfer erc20 token
    tainted_call_pc = [i['pc'] for i in tainted_call]
    return tainted_call

def detect_one_way_trip(function):
    SLOAD_position = [] # SLOAD CALLER constraint
    transfer_to_address = [] # transfer to constraint
    NONZERO_CALL_pc = [] # transfer eth
    tac_list = [instr for block in function['blocks'] for instr in block['tac']]


    for pc, instr in tac_list:
        if "=" in instr:
            # SSA form: lhs = opcode rhs
            lhs, rhs = instr.split("=", 1)
            lhs = lhs.strip()
            rhs = rhs.strip()
            opcode, *operands = rhs.split(" ", 1)
            if operands == []:
                continue
            operands = [op.strip() for op in operands[0].split(", ")]
            if opcode=='SLOAD':
                if '(' in rhs:
                    rhs, rhs_val = rhs.split('(')
                    rhs_val = rhs_val.replace(')','')
                    SLOAD_position.append({'pc': pc, 'pos': rhs_val})
            
            if opcode=='CALL':
                transfer_to = operands[1].split('(')[-1].replace(')','')
                transfer_amt = operands[2].split('(')[-1].replace(')','')
                if transfer_amt[:2]=='0x' and int(transfer_amt,16) > 0: # transfer eth
                    NONZERO_CALL_pc.append(pc)
                    transfer_to_address.append(transfer_to)

    # transfer call 
    source = ["0xa9059cbb","0xba087652"] # transfer redeem
    tainted_opcode='CALL'
    tainted_call, _ = find_tainted_opcode_in_block(function, source, tainted_opcode) # transfer erc20 token
    tainted_call_pc = [i['pc'] for i in tainted_call] + NONZERO_CALL_pc
    if len(tainted_call_pc) == 0: # This function do not have call to transfer asset
        return True

    # conditional JUMP
    source = ["CALLER"]
    tainted_opcode='JUMPI'
    tainted_CALLER_JUMPI, _ = find_tainted_opcode(function, source, tainted_opcode)
    if len(tainted_CALLER_JUMPI) == 0: # Any Caller can call this funciton
        if len(NONZERO_CALL_pc) != 0:
            return {'transfer_to check': set(transfer_to_address)} # check transfer to address
        elif len(tainted_call) != 0:
            return False
    
    source = ["SLOAD"]
    tainted_opcode='JUMPI'
    tainted_SLOAD_JUMPI, tainted_SLOAD_source  = find_tainted_opcode(function, source, tainted_opcode)
    tainted_JUMPI_pc = list(set([j for i in tainted_SLOAD_JUMPI for j in i['pc']]) & set([j for i in tainted_CALLER_JUMPI for j in i['pc']]))

    # accessibe check
    target_pc_accessibe = []
    for target_pc in tainted_call_pc:
        conditions = get_control_flow_conditions(function['blocks'], target_pc)
        path_len = len(conditions)
        unaccessibe_path_count = []
        for path in conditions:
            for condition in path:
                pc = condition[0]
                # tac = condition[1]
                if pc in tainted_JUMPI_pc:
                    unaccessibe_path_count.append(1)
                    break
        if sum(unaccessibe_path_count)==path_len:
            target_pc_accessibe.append(False)
        else:
            target_pc_accessibe.append(True)

    if all(target_pc_accessibe)==False: # all transfer may be unaccessiable for CALLER, need to check storage
        if SLOAD_position == []:
            return True
        else: # check SLOAD
            return {'SLOAD check': set([i['pos'] for i in SLOAD_position if i['pc'] in tainted_SLOAD_source])}
    else:
        # return False
        return {'transfer_to check': set(transfer_to_address)} # check transfer to address
    # return target_pc_accessibe



if __name__ == "__main__":
    input_file_path = "./tac/0x58ef7653b93aca0449dc77619a9efb3472d39158.tac"
    functions = parse_contract(input_file_path)
    # print([fun['name'] for fun in functions])
    i = 1
    print(functions[i]['name'])
    print(detect_one_way_trip(functions[i]))