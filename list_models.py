#!/usr/bin/env python3

import argparse
import sys
import common_functions as cf

def markdown_models(gpt_models, images_models):
    print("| Mode | Model | Provider | Status | Capability | Notes | About |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    print("| GPT | [`ollama`](https://ollama.com/) | SelfHosted | active | vision`?` | | Self-hosted models using [`ollama`](https://ollama.com/); will search for `OLLAMA_HOST` environment variable |")

    for model in sorted(list(gpt_models.keys())):
        notes = gpt_models[model]['status_details'] if 'status_details' in gpt_models[model] else ''
        meta = gpt_models[model]['meta']
        model_long = f"[`{model}`]({meta['model_url']})" if 'model_url' in meta else f"`{model}`"
        capability = ', '.join(gpt_models[model]['capability'])
        capability = capability.replace('openai_websearch', 'websearch')
        print(f"| GPT | {model_long} | {meta['provider']} | {gpt_models[model]['status']} | {capability} | {notes} | {gpt_models[model]['label']} |")
    for model in sorted(list(images_models.keys())):
        notes = images_models[model]['status_details'] if 'status_details' in images_models[model] else ''
        meta = images_models[model]['meta']
        model_long = f"[`{model}`]({meta['model_url']})" if 'model_url' in meta else f"`{model}`"
        print(f"| Dall-E | {model_long} | {meta['provider']} | {images_models[model]['status']} |  | {notes} | {images_models[model]['label']} |")

if __name__ == "__main__":
    # argparse
    parser = argparse.ArgumentParser(description='List available models, by default in format suitable for use as environment variables')
    parser.add_argument('--markdown', action='store_true', help='Show models in a markdown format and exit')
    args = parser.parse_args()

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