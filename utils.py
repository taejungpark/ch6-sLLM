import json
from pathlib import Path

import pandas as pd


def make_prompt(ddl, question, query=""):
    prompt = f"""당신은 SQL을 생성하는 SQL 봇입니다. DDL의 테이블을 활용한 Question을 해결할 수 있는 SQL 쿼리를 생성하세요.

### DDL:
{ddl}

### Question:
{question}

### SQL:
{query}"""
    return prompt


def make_requests_for_gpt_evaluation(df, filename, dir="requests", model="gemini-2.5-flash"):
    """Build a JSONL of OpenAI-compatible chat-completion requests for an LLM judge.

    Default judge is Gemini 2.5 Flash via the OpenAI-compatible endpoint, but the
    request body works unchanged against any OpenAI-compatible backend (OpenAI,
    Ollama, Groq, etc.) — switch by changing `--request_url` on the parallel
    processor.
    """
    Path(dir).mkdir(parents=True, exist_ok=True)
    prompts = []
    for _, row in df.iterrows():
        prompts.append(
            'Based on below DDL and Question, evaluate gen_sql can resolve Question. '
            'If gen_sql and gt_sql do equal job, return "yes" else return "no". '
            'Output JSON Format: {"resolve_yn": ""}'
            f"\n\nDDL: {row['context']}\nQuestion: {row['question']}\n"
            f"gt_sql: {row['answer']}\ngen_sql: {row['gen_sql']}"
        )

    jobs = [
        {
            "model": model,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        }
        for prompt in prompts
    ]
    out_path = Path(dir) / filename
    with open(out_path, "w") as f:
        for job in jobs:
            f.write(json.dumps(job) + "\n")
    return out_path


def change_jsonl_to_csv(input_file, output_file, prompt_column="prompt", response_column="response"):
    """Parse parallel-processor output JSONL into a (prompt, response) DataFrame.

    Each line is `[request_json, response_or_errors, ...]`. On success,
    `response_or_errors` is the API response dict; on failure (after all
    retries exhausted) it's a list of error strings, which we skip with a
    summary log so the caller can investigate.
    """
    prompts, responses = [], []
    failures = []
    with open(input_file, "r") as json_file:
        for line in json_file:
            data = json.loads(line)
            request, payload = data[0], data[1]
            if isinstance(payload, list):
                failures.append(payload)
                continue
            prompts.append(request["messages"][0]["content"])
            responses.append(payload["choices"][0]["message"]["content"])

    if failures:
        print(f"⚠️  {len(failures)} request(s) failed after all retries (skipped).")
        print(f"   First failure errors: {failures[0]}")

    df = pd.DataFrame({prompt_column: prompts, response_column: responses})
    df.to_csv(output_file, index=False)
    return df
