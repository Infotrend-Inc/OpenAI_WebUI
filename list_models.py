#!/usr/bin/env python3

import argparse
import sys
import common_functions as cf

def markdown_models(gpt_models, images_models, mode:str=""):
    print("| Mode | Model | Provider | Status | Capability | Notes | About |")
    print("| --- | --- | --- | --- | --- | --- | --- |")

    if mode == "":
        print("| GPT | [`ollama`](https://ollama.com/) | SelfHosted | active | vision`?` | | Self-hosted models using [`ollama`](https://ollama.com/); will search for `OLLAMA_HOST` environment variable |")
        print("| GPT | [`LiteLLM`](https://github.com/BerriAI/litellm) | SelfHosted | active | vision`?` | | Proxy Server to LLM APIs in OpenAI format. [`LiteLLM Proxy Server`](https://docs.litellm.ai/docs/#litellm-proxy-server-llm-gateway); will search for `LITELLM_URL` and `LITELLM_API_KEY` environment variable |")

    for model in sorted(list(gpt_models.keys())):
        notes = gpt_models[model]['status_details'] if 'status_details' in gpt_models[model] else ''
        meta = gpt_models[model]['meta']
        model_long = f"[`{model}`]({meta['model_url']})" if 'model_url' in meta else f"`{model}`"
        capability = ', '.join(gpt_models[model]['capability'])
        print(f"| GPT | {model_long} | {meta['provider']} | {gpt_models[model]['status']} | {capability} | {notes} | {gpt_models[model]['label']} |")
    for model in sorted(list(images_models.keys())):
        notes = images_models[model]['status_details'] if 'status_details' in images_models[model] else ''
        meta = images_models[model]['meta']
        model_long = f"[`{model}`]({meta['model_url']})" if 'model_url' in meta else f"`{model}`"
        print(f"| Image | {model_long} | {meta['provider']} | {images_models[model]['status']} |  | {notes} | {images_models[model]['label']} |")

if __name__ == "__main__":
    # argparse
    parser = argparse.ArgumentParser(description='List available models, by default in format suitable for use as environment variables')
    parser.add_argument('--markdown', action='store_true', help='Show models in a markdown format and exit')
    parser.add_argument('--ollama', action='store_true', help='Show Ollama models (as found from your .env file) in a markdown format and exit -- might need to be run with: uv run ./list_models.py --ollama > ollama.md')
    parser.add_argument('--litellm', action='store_true', help='Show LiteLLM models (as found from your .env file) in a markdown format and exit -- might need to be run with: uv run ./list_models.py --litellm > litellm.md')
    args = parser.parse_args()

    if args.ollama:
        from dotenv import load_dotenv
        load_dotenv()
        import os
        if 'OLLAMA_HOST' not in os.environ:
            print("OLLAMA_HOST not found in environment variables")
            sys.exit(1)
        from ollama_helper import OllamaHelper

        OLLAMA_HOST = os.environ.get('OLLAMA_HOST')
        oll = OllamaHelper(OLLAMA_HOST)
        err, ollama_models = oll.get_all_ollama_models_and_infos()
        if cf.isNotBlank(err):
            print(f"While testing OLLAMA_HOST {OLLAMA_HOST}: {err}")
            sys.exit(1)

        gpt_models = {}
        for oll_model in ollama_models:
            # We are going to extend the GPT models with the Ollama models
            err, modeljson = oll.ollama_to_modelsjson(oll_model, ollama_models[oll_model])
            if cf.isNotBlank(err):
                print(f"While obtaining OLLAMA model {oll_model} details: {err}")
                sys.exit(1)
            gpt_models[oll_model] = modeljson
        markdown_models(gpt_models, {}, 'Ollama')
        sys.exit(0)

    if args.litellm:
        from dotenv import load_dotenv
        load_dotenv()
        import os
        if 'LITELLM_URL' not in os.environ:
            print("LITELLM_URL not found in environment variables")
            sys.exit(1)
        if 'LITELLM_API_KEY' not in os.environ:
            print("LITELLM_API_KEY not found in environment variables")
            sys.exit(1)
        from litellm_helper import LiteLLMHelper

        LITELLM_URL = os.environ.get('LITELLM_URL')
        LITELLM_API_KEY = os.environ.get('LITELLM_API_KEY')
        lit = LiteLLMHelper(LITELLM_URL, LITELLM_API_KEY)
        err, litellm_models = lit.get_all_litellm_models_and_infos()    
        if cf.isNotBlank(err):
            print(f"While testing LITELLM_URL {LITELLM_URL}: {err}")
            sys.exit(1)

        gpt_models = {}
        for lit_model in litellm_models:
            # We are going to extend the GPT models with the LiteLLM models
            err, modeljson = lit.litellm_to_modelsjson(lit_model, litellm_models[lit_model])
            if cf.isNotBlank(err):
                print(f"While obtaining LiteLLM model {lit_model} details: {err}")
                sys.exit(1)
            gpt_models[lit_model] = modeljson
        markdown_models(gpt_models, {}, 'LiteLLM')
        sys.exit(0)

    err, gpt_models, images_models = cf.load_models()
    if cf.isNotBlank(err):
        print(err)
        sys.exit(1)

    if args.markdown:
        markdown_models(gpt_models, images_models)
        sys.exit(0)


    # remove deprecated models
    gpt_models = {k: v for k, v in gpt_models.items() if v['status'] != 'deprecated'}
    images_models = {k: v for k, v in images_models.items() if v['status'] != 'deprecated'}
    print("OAIWUI_GPT_MODELS=" + " ".join(sorted(list(gpt_models.keys()))))
    print("OAIWUI_IMAGES_MODELS=" + " ".join(sorted(list(images_models.keys()))))

    sys.exit(0)