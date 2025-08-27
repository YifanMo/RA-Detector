def get_var_to_check(tainted_opcode, operands):
    to_check_var = ''
    if tainted_opcode == 'CALL':
        _, _, _, _, in_offset, _, _ = operands
        to_check_var = in_offset
    elif tainted_opcode == 'SSTORE':
        _, mem_value = operands
        if '(' in mem_value:
            mem_value, _ = mem_value.split('(')
        to_check_var = mem_value
    elif tainted_opcode == 'JUMPI':
        _, cond = operands
        to_check_var = cond
    return to_check_var

def get_transfer_to_address(call_tac):
    _, _, _, _, _, out_offset, _ = call_tac
    return out_offset

def find_tainted_opcode_in_block(function, source = ["0xa9059cbb"], tainted_opcode='CALL'):
    tainted_block = []
    tainted_source_pc = []

    # Analyze each block in the function
    for block in function['blocks']:
        tac = block['tac']
        contain_tainted_opcode = tainted_opcode in str(tac)
        # Check if the block contains a tainted_opcode operation influenced by the source
        if contain_tainted_opcode:
            for pc, instr in tac:
                if any([s in instr for s in source]):
                    tainted_pc = pc
                    tainted_block.append({'block_id':block['block_id'], 'pc':tainted_pc})
    return tainted_block, tainted_source_pc

def find_tainted_opcode(function, source = ["0xa9059cbb"], tainted_opcode='CALL'):
    tainted_vars = set()
    tainted_block = []
    tainted_source_pc = []

    # Helper function to propagate taint
    def propagate_taint(tac, tainted_vars):
        tainted_pc = []
        for pc, instr in tac:
            if "=" in instr:
                # SSA form: lhs = opcode rhs
                lhs, rhs = instr.split("=", 1)
                lhs = lhs.strip()
                rhs = rhs.strip()
                opcode, *operands = rhs.split(" ", 1)

                if '(' in lhs:
                    lhs, lhs_val = lhs.split('(')
                    lhs_val = lhs_val.replace(')','')
                    # tainted source in CONST
                    if opcode == "CONST":
                        if lhs_val in source:
                            # If the source is found in the operands, mark lhs as tainted
                            tainted_vars.add(lhs)
                            tainted_source_pc.append(pc)

                # tainted source in CALLER, CALLDATALOAD
                if opcode in source:
                    tainted_vars.add(lhs)
                    tainted_source_pc.append(pc)
                
                if operands == []:
                    continue
                
                operands = [op.strip().split('(0x',1)[0] for op in operands[0].split(", ")]
                if any(op in tainted_vars for op in operands):
                    # If any operand is tainted, mark lhs as tainted
                    tainted_vars.add(lhs)

            else:
                # Non-SSA form: opcode operands
                opcode, *operands = instr.split(" ", 1)
                if operands == []:
                    continue
                operands = [op.strip() for op in operands[0].split(", ")]
                
                if opcode == "MSTORE":
                    if len(operands) == 2:
                        # For MSTORE, the memory location is tainted if the value is tainted
                        mem_location, mem_value = operands
                        if '(' in mem_value:
                            var, value = mem_value.split('(')
                            mem_value = var.replace(')','')
                            if value in source:
                                tainted_vars.add(mem_location)
                                tainted_source_pc.append(pc)
                            elif var in tainted_vars:
                                tainted_vars.add(mem_location)
                        else:
                            if mem_value in tainted_vars:
                                tainted_vars.add(mem_location)
            
            if opcode == tainted_opcode:
                # check if the op is tainted
                to_check_var = get_var_to_check(opcode, operands)
                if to_check_var in tainted_vars:
                    tainted_pc.append(pc)
                    
        return tainted_pc

    # Analyze each block in the function
    for block in function['blocks']:
        tac = block['tac']
        # Check if the block contains a tainted_opcode operation influenced by the source
        tainted_pc = propagate_taint(tac, tainted_vars)
        
        if tainted_pc:
            tainted_block.append({'block_id':block['block_id'], 'pc':tainted_pc})
    
    return tainted_block, tainted_source_pc