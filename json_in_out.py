import json
from pydantic import BaseModel
import getpass
import openai
import pandas as pd
import regex as re
import uuid
import os
import parse_code
import extract
OPENAI_API_KEY = getpass.getpass('Enter OPENAI_API_KEY (input hidden): ')

client = openai.OpenAI(api_key=OPENAI_API_KEY)
print('OpenAI client initialized.')


def summarize_code(code):
    prompt = f"""
    Provide a detailed summary of the following Verilog module,
    including its functionality, inputs, outputs, parameters, and 
    key operations.".
    Verilog Code:
    ```verilog
    {code}
    ```
    Summary should be concise (100-200 words) and focus on:
    - Purpose of the module
    - Inputs and outputs (including widths)
    - Parameters (if any)
    - Main operations or logic
    - Any notable features (e.g., sequential, combinational, FSM)
    """
    response = client.chat.completions.create(
            model='gpt-4',
            messages=[{'role': 'user', 'content': prompt}],
            max_tokens=500
        )
    summary = response.choices[0].message.content.strip()
    #print(f'Generated summary: {summary}...')
    return summary

# -----------------------------
# READ
# -----------------------------
with open("data.json", "r") as f:
    rows = json.load(f)

print("=== INPUT ===")
for r in rows:
    print("\nTEXT:", r["text"])
    print("CODE:\n" + r["code"])


# -----------------------------
# PROCESS (example)
# Count lines of code
# -----------------------------
output_rows = []

for idx, row in enumerate(rows):
    code_lines = row["code"].split("\n")
    summary = summarize_code(row["code"])
    print(summary)
    output_rows.append({
        "row_number": idx,
        "text": row["text"],
        "code_line_count": len(code_lines),
        "original_code": row["code"],
        "Summary" : summary
    })
    module_name, input_ports, output_ports, signals, parameters, operations, ast = parse_code.parse_verilog_code(row["code"]) 
           
    print("the module name  is {module_name}")
    print(module_name)
    modules, signals_dict, param_dict, operation_dict, relationships = extract.extract_entities(
                module_name, input_ports, output_ports, signals, parameters, operations, ast
            )
    kg_file = os.path.join('knowledge_graphs', f"kg_{idx}.ttl")
    extract.create_knowledge_graph(modules, signals_dict, param_dict, operation_dict, relationships, kg_file)
        #chunks['knowledge_graph'] = kg_file
#    return chunk


print(f"Updated CSV written to output_file")


# -----------------------------
# WRITE OUTPUT JSON
# -----------------------------
with open("output.json", "w") as f:
    json.dump(output_rows, f, indent=4)

print("\nOutput written to output.json")
