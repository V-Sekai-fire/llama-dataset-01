# Copyright (c) 2023-present. This file is part of V-Sekai https://v-sekai.org/.
# K. S. Ernest (Fire) Lee & Contributors (see .all-contributorsrc).
# llama-cpp-grammar.py
# SPDX-License-Identifier: MIT

from llama_cpp import Llama, LlamaGrammar
import httpx
import os
import tempfile
from functools import lru_cache
from tqdm import tqdm
import json

@lru_cache(maxsize=1)
def get_model_file(model_url):
    with httpx.stream('GET', model_url, follow_redirects=True) as response:
        response.raise_for_status()

        total_length = int(response.headers.get('content-length'))
        download_so_far = 0

        import hashlib
        filename = hashlib.md5(model_url.encode('utf-8')).hexdigest() + '.gguf'
        model_path = os.path.join(tempfile.gettempdir(), filename)

        if not os.path.exists(model_path):
            print("Downloading the model...")

            with open(model_path, 'wb') as model_file, tqdm(total=total_length, unit='iB', unit_scale=True, desc=filename) as bar:
                for chunk in response.iter_bytes(1024):
                    download_so_far += len(chunk)
                    bar.update(len(chunk))
                    model_file.write(chunk)

    return model_path

model_url = "https://huggingface.co/TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/resolve/main/openhermes-2.5-mistral-7b.Q4_K_M.gguf?download=true"
model_path = get_model_file(model_url)

with open("json_arr.gbnf", 'r') as file:
    grammar_file_contents = file.read()

grammar = LlamaGrammar.from_string(grammar_file_contents)

max_tokens = -1
llm = Llama(model_path=model_path, chat_format="chatml", n_ctx=4096, n_gpu_layers=99)

def get_response(prompt, output):
    response = llm.create_chat_completion(
        grammar=grammar,
        max_tokens=max_tokens,
        messages = [
            {"role": "system", "content": "Your replies are json lists."},
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    output.append(response['choices'][0]["message"]["content"])

import time
import threading

def threaded_get_response(user_input, output):
    response_thread = threading.Thread(target=get_response, args=(user_input, output))
    response_thread.start()
    
    response_thread.join(timeout=5)
    
    if response_thread.is_alive():
        print("The operation exceeded 5 seconds.")
        response_thread.join()

while True:
    user_input = input("Enter your prompt like 'List some cat names.' (or type 'exit' to quit): ")
    if user_input.lower() == 'exit':
        print("Exiting...")
        break
    
    formatted_json_response = []
    
    start_time = time.time()
    
    threaded_get_response(user_input, formatted_json_response)
    
    end_time = time.time()
    elapsed_time = end_time - start_time
    
    if elapsed_time <= 5 and formatted_json_response:
        print(formatted_json_response[0]) 