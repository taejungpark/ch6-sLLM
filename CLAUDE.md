# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Chapter 6 of an LLM course — a **Text-to-SQL** pipeline that fine-tunes a Korean LLM (`beomi/Yi-Ko-6B`) to generate SQL from natural language questions using the `shangrilar/ko_text2sql` dataset.

Target environment: **Google Colab (T4 GPU)**. Local macOS execution is not supported because `bitsandbytes` 4-bit quantization is CUDA-only.


## Running the Project

The primary workflow lives in `chapter_6.ipynb`; run cells in order on Colab. Pinned dependencies are in `requirements.txt` and the install cell at the top of the notebook:

- `transformers==4.46.3`, `accelerate==1.1.1`, `bitsandbytes==0.44.1` — model loading with 4-bit quantization
- `trl==0.12.2`, `peft==0.13.2` — LoRA fine-tuning via `SFTTrainer`
- `datasets==3.1.0` — HuggingFace dataset loading
- `tiktoken==0.8.0` — token counting for rate-limit budgeting

**Required Colab Secrets** (left-side 🔑 panel, Notebook access ON):
- `GEMINI_API_KEY` — get from https://aistudio.google.com/apikey (free)
- `HF_TOKEN` — optional, only for pushing the merged model to the Hub

**LLM-judge evaluation** (default backend = Gemini 2.0 Flash):
```bash
python api_request_parallel_processor.py \
  --requests_filepath <input.jsonl> \
  --save_filepath <output.jsonl> \
  --request_url https://generativelanguage.googleapis.com/v1beta/openai/chat/completions \
  --max_requests_per_minute 15 \
  --max_tokens_per_minute 1000000
```
The script auto-reads `OPENAI_API_KEY` / `GEMINI_API_KEY` / `GROQ_API_KEY` env vars. To switch backends, change `--request_url` only:
- OpenAI: `https://api.openai.com/v1/chat/completions`
- Ollama (local): `http://localhost:11434/v1/chat/completions` (set `OPENAI_API_KEY=ollama`)
- Groq: `https://api.groq.com/openai/v1/chat/completions`

**Fine-tuning** is now done in-notebook via `trl.SFTTrainer` (no longer `autotrain` CLI). See cell "예제 6.10".

## Architecture

### Pipeline Stages (notebook order)

1. **Data prep** — Load `ko_text2sql`, format prompts as `DDL + question → SQL`, save to CSV
2. **Base model inference** — Load `Yi-Ko-6B` with 4-bit quant, generate SQL predictions on test set
3. **LLM-judge evaluation** — Use `api_request_parallel_processor.py` (Gemini by default) to score predictions asynchronously
4. **Fine-tuning** — LoRA via `trl.SFTTrainer`
5. **Merge & push** — Merge LoRA adapter into base weights, upload to HuggingFace Hub (optional)
6. **Comparison** — Re-evaluate fine-tuned model and compare against base model results

### Key Files

**`api_request_parallel_processor.py`** — Async batch client for any OpenAI-compatible chat-completions endpoint:
- `StatusTracker`: tracks success/failure/rate-limit counts
- `APIRequest`: per-request retry logic with exponential backoff
- `process_api_requests_from_file()`: async loop that respects RPM/TPM caps via token-counting
- `api_endpoint_from_url()`: parses OpenAI / Gemini (`v1beta`) / Ollama (`http://`) / Groq / Azure URLs

**`utils.py`** — Three helpers:
- `make_prompt(ddl, question, query="")` — formats the DDL+question prompt
- `make_requests_for_gpt_evaluation(df, filename, dir="requests", model="gemini-2.0-flash")` — converts a DataFrame of predictions to a JSONL request file
- `change_jsonl_to_csv(input, output, ...)` — converts judge response JSONL to CSV for analysis

**`requirements.txt`** — pinned versions for reproducibility on Colab.


## Change History

### 2026-05-05 — Modernization (resolved original "Problems to solve")

The codebase was originally written in 2023 and had two blocking problems:
1. **Dependency rot** — `autotrain-advanced==0.7.77` pinned `transformers 4.40.x`, which conflicted with the rest of the modern PyTorch/HF ecosystem and frequently broke on fresh Colab runtimes.
2. **OpenAI cost/deprecation** — the GPT-4 judge models (`gpt-4-turbo-preview`, `gpt-4-1106-preview`) were deprecated, and OpenAI no longer offers a meaningful free tier for educational use.

**Resolution decisions** (in conversation):
- Replaced `autotrain` CLI with **`trl.SFTTrainer`** — same LoRA result, far cleaner deps, and the training loop is now visible/debuggable for students.
- Replaced GPT-4 judge with **Gemini 2.0 Flash** via its OpenAI-compatible endpoint (free tier: 15 RPM, 1500 RPD). `api_request_parallel_processor.py` was generalized so the same code works against OpenAI / Gemini / Ollama / Groq by changing only `--request_url`.
- API keys load from **Colab Secrets** (`userdata.get('GEMINI_API_KEY')`) instead of being typed inline.
- Considered but rejected: running Ollama on Colab (model re-download per session, VRAM contention with `Yi-Ko-6B` training). Ollama is documented as a local-only alternative in a markdown cell.
