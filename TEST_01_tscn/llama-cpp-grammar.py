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

        import hashlib
        filename = hashlib.md5(model_url.encode('utf-8')).hexdigest() + '.gguf'
        model_path = os.path.join(tempfile.gettempdir(), filename)

        if not os.path.exists(model_path):
        if os.path.exists(model_path):
            actual_size = os.path.getsize(model_path)
            if actual_size == total_length:
                print("Model already downloaded.")
                return model_path
            else:
                print(f"Model file seems incomplete. Expected size: {total_length}, actual size: {actual_size}. Redownloading.")
                os.remove(model_path)

        print("Downloading the model...")
        with open(model_path, 'wb') as model_file, tqdm(total=total_length, unit='iB', unit_scale=True, desc=filename) as bar:
            for chunk in response.iter_bytes(1024):
                bar.update(len(chunk))
                model_file.write(chunk)

    return model_path


model_url = "https://huggingface.co/TheBloke/OpenHermes-2.5-Mistral-7B-GGUF/resolve/main/openhermes-2.5-mistral-7b.Q4_K_M.gguf?download=true"
model_path = get_model_file(model_url)

with open("godot_tscn_02.gbnf", 'r') as file:
    grammar_file_contents = file.read()

grammar = LlamaGrammar.from_string(grammar_file_contents)

max_tokens = -1
llm = Llama(model_path=model_path, chat_format="chatml", n_ctx=4096, n_gpu_layers=99)

with open("godot_01_tscn/godot_01_scene_01.tscn", 'r') as file:
    prompt = file.read()

def get_response(prompt):
    response = llm.create_chat_completion(
        grammar=grammar,
        max_tokens=max_tokens,
        messages = [
            {"role": "system", "content": "The task is to echo back the provided Godot Engine 4.2 tscn scene description using the given parsing grammar rules. {}".format(grammar_file_contents)},
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    return response['choices'][0]["message"]["content"]

formatted_json_response = get_response(prompt)

print(prompt)
print(formatted_json_response)