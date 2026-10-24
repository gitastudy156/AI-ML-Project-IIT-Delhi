#!/usr/bin/env python
"""Inference for the fine-tuned ShopEase FAQ assistant (LoRA adapter on a small causal LM).

Examples
--------
  python inference.py --adapter_dir lora_adapter --query "Can I return a product after 30 days?"
  python inference.py --adapter_dir lora_adapter              # interactive CLI (type 'quit' to exit)
  python inference.py --adapter_dir lora_adapter --gradio     # web UI (pip install gradio)
"""
import argparse

import torch
from peft import PeftConfig, PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def load_model(adapter_dir, base_model=None, device=None):
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    base_name = base_model or PeftConfig.from_pretrained(adapter_dir).base_model_name_or_path
    try:
        tokenizer = AutoTokenizer.from_pretrained(adapter_dir)
    except Exception:
        tokenizer = AutoTokenizer.from_pretrained(base_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    model = AutoModelForCausalLM.from_pretrained(base_name)
    model = PeftModel.from_pretrained(model, adapter_dir)
    model.to(device).eval()
    return model, tokenizer


def build_prompt(query):
    return f"Customer: {query.strip()}\nSupport:"


@torch.no_grad()
def answer(model, tokenizer, query, max_new_tokens=64):
    enc = tokenizer(build_prompt(query), return_tensors="pt").to(model.device)
    out = model.generate(**enc, max_new_tokens=max_new_tokens, do_sample=False, num_beams=1,
                         no_repeat_ngram_size=4, use_cache=True, pad_token_id=tokenizer.eos_token_id)
    text = tokenizer.decode(out[0, enc["input_ids"].shape[1]:], skip_special_tokens=True)
    return text.split("\n")[0].strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--adapter_dir", default="lora_adapter", help="folder with the saved LoRA adapter")
    ap.add_argument("--base_model", default=None, help="override the base model name stored in the adapter")
    ap.add_argument("--query", default=None, help="single question; prints the answer and exits")
    ap.add_argument("--gradio", action="store_true", help="launch a Gradio web interface")
    ap.add_argument("--max_new_tokens", type=int, default=64)
    args = ap.parse_args()

    model, tokenizer = load_model(args.adapter_dir, args.base_model)

    if args.query:
        print(answer(model, tokenizer, args.query, args.max_new_tokens))
    elif args.gradio:
        import gradio as gr
        demo = gr.Interface(
            fn=lambda q: answer(model, tokenizer, q, args.max_new_tokens),
            inputs=gr.Textbox(label="Customer question", lines=2),
            outputs=gr.Textbox(label="ShopEase assistant"),
            title="ShopEase customer-support assistant (fine-tuned small LLM)",
            examples=["Can I return a product after 30 days?", "How do I track my order?", "Do you ship to Canada?"])
        demo.launch(share=True)
    else:
        print("ShopEase assistant - type a customer question ('quit' to exit)")
        while True:
            q = input("Customer> ").strip()
            if q.lower() in {"quit", "exit", "q"}:
                break
            if q:
                print("Support>", answer(model, tokenizer, q, args.max_new_tokens))


if __name__ == "__main__":
    main()
