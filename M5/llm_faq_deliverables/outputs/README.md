# Fine-Tuning a Small LLM for Customer-Support FAQs

## 1. Dataset
* Domain: e-commerce support for a fictional store (ShopEase); 837 synthetic Q&A pairs from 56 policy topics (returns, refunds, shipping, payments, accounts, promotions, warranty, ...).
* Format: JSONL `{"prompt": ..., "response": ...}`; cleaned (Unicode normalisation, whitespace, length filter, de-duplication) -> 837 pairs.
* Split 80/10/10 grouped by question (paraphrases never cross splits): train 671, val 85, test 81.

## 2. Model and training setup
* Base model: `distilgpt2` (82 M parameters) + LoRA (r=32, alpha=64, dropout=0.05); trainable parameters: 2.36 M.
* Prompt format `Customer: <q>\nSupport: <a><eos>`; loss on answer tokens only.
* Hugging Face `Trainer`, 5 epochs max, batch size 8, lr 0.0005 (cosine), fp16, early stopping (patience 2) on validation loss; best validation loss 0.864.
* Quantisation setting: None. Hardware: Tesla T4.

## 3. Results (test set, 81 questions)
| metric           |   base model |   fine-tuned (LoRA) |   change |
|:-----------------|-------------:|--------------------:|---------:|
| BLEU             |        0     |              14.704 |   14.704 |
| ROUGE-1          |        0.007 |               0.323 |    0.316 |
| ROUGE-L          |        0.006 |               0.267 |    0.262 |
| Embedding cosine |        0.067 |               0.517 |    0.45  |
| Test loss        |        3.717 |               0.908 |   -2.808 |
| Perplexity       |       41.135 |               2.48  |  -38.655 |

## 4. Sample outputs (base vs fine-tuned)
| query                                        | base_model   | fine_tuned                                                                                                                                      |
|:---------------------------------------------|:-------------|:------------------------------------------------------------------------------------------------------------------------------------------------|
| Can I return a product after 30 days?        |              | Items must be unused, in their original packaging and with all tags attached to be eligible for a return.                                       |
| How do I track my order?                     |              | We track orders in My Orders until the order ships. Once it has shipped, the tracking details are back in your spam folder.                     |
| My package arrived broken, what should I do? |              | We are sorry about that! Report it within 48 hours of delivery with a photo through My Orders and we will send a free replacement or a refund.  |
| Do you ship to Canada?                       |              | We deliver to over 50 countries. International delivery takes 3-5 business days.                                                                |
| I forgot my password, help!                  |              | Click Forgot Password on the login page and enter your email. We will send a reset link, so please check your spam folder if you do not see it. |

Full 10-query comparison: `manual_evaluation.csv`.

## 5. Challenges & limitations
* The dataset is synthetic and template-based, so test questions are paraphrases of training topics; scores on real customer traffic would be lower.
* A very small model (82 M) can still produce fluent but wrong details; answers should be checked against the policy before use.
* Out-of-domain questions are handled only through the few examples in the dataset.

## 6. Usage
`python inference.py --adapter_dir lora_adapter --query "Can I return a product after 30 days?"` (or `--gradio`).
