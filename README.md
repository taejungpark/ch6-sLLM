# LLM 강의 실습 노트북

대규모 언어 모델(LLM) 강의에서 사용하는 챕터별 실습 노트북 모음. 모든 노트북은 **Google Colab (T4 GPU)** 환경을 기준으로 동작합니다.

## 챕터 목록

| 챕터 | 주제 | 노트북 | 핵심 사용 도구 |
|---|---|---|---|
| 6장 | Text-to-SQL 미세 조정 | [`chapter_6.ipynb`](https://colab.research.google.com/github/taejungpark/LLM-class/blob/main/chapter_6.ipynb) · [`chapter_6_Groq.ipynb`](https://colab.research.google.com/github/taejungpark/LLM-class/blob/main/chapter_6_Groq.ipynb) | `Yi-Ko-6B` + LoRA(`trl.SFTTrainer`) + LLM judge |
| 9장 | RAG · 캐시 · 가드레일 · 로깅 | [`chapter_9.ipynb`](https://colab.research.google.com/github/taejungpark/LLM-class/blob/main/chapter_9.ipynb) | LlamaIndex · ChromaDB · NeMo-Guardrails · W&B |

---

## 공통 준비

1. **런타임 설정** — `런타임 → 런타임 유형 변경 → T4 GPU` 선택
2. **API 키 등록** — 좌측 🔑 **Secrets** 탭에서 사용할 키 등록 (Notebook access **ON**)
   - `GROQ_API_KEY` — Groq 노트북용 ([Groq Console](https://console.groq.com/keys))
   - `GEMINI_API_KEY` — Gemini judge 노트북용 ([Google AI Studio](https://aistudio.google.com/apikey))
   - `HF_TOKEN` *(선택)* — 학습한 모델을 허깅페이스 허브에 업로드할 때만 필요
3. **셀 순서대로 실행** — 노트북 첫 셀이 이 저장소를 자동 클론하거나 의존성을 설치합니다.

---

## 6장 — Text-to-SQL 미세 조정

자연어 질문을 SQL로 변환하는 한국어 sLLM(`beomi/Yi-Ko-6B`)을 LoRA로 미세 조정합니다. 데이터셋은 [`shangrilar/ko_text2sql`](https://huggingface.co/datasets/shangrilar/ko_text2sql)입니다.

### 노트북 두 가지 (Judge 백엔드만 다름)

| 노트북 | Judge 백엔드 | 발급 | 무료 tier 특성 |
|---|---|---|---|
| `chapter_6.ipynb` | Gemini 2.5 Flash | [Google AI Studio](https://aistudio.google.com/apikey) | 5 RPM (느림), 100건 평가에 ~20분 |
| `chapter_6_Groq.ipynb` | Groq (Llama 3.3 70B) | [Groq Console](https://console.groq.com/keys) | 30 RPM, 100건에 ~3-4분 |

> 계정에 따라 Gemini free tier가 `limit: 0`으로 막혀있는 경우(billing 활성화된 GCP 프로젝트 등)가 있어, 강의용으로는 **Groq 버전을 권장**합니다.

### 파이프라인 개요

| 단계 | 셀 | 내용 |
|---|---|---|
| 1 | 6.7 | `Yi-Ko-6B` 4-bit 양자화 로드 |
| 2 | 6.8 | 기초 모델로 테스트셋 SQL 생성 → judge로 정답률 측정 |
| 3 | 6.9 | 학습 데이터(`ko_text2sql/train`) 전처리 |
| 4 | 6.10 | LoRA 미세 조정 (`trl.SFTTrainer`) |
| 5 | 6.11 | LoRA 어댑터 결합 → (선택) HF Hub 업로드 |
| 6 | 6.12-6.13 | 미세 조정 모델 재평가 → 기초 모델과 정답률 비교 |

### Judge 백엔드 변경

`--request_url`만 바꾸면 다른 OpenAI 호환 백엔드로 전환됩니다:

| 백엔드 | URL | 환경변수 |
|---|---|---|
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions` | `GEMINI_API_KEY` |
| Groq | `https://api.groq.com/openai/v1/chat/completions` | `GROQ_API_KEY` |
| OpenAI | `https://api.openai.com/v1/chat/completions` | `OPENAI_API_KEY` |
| Ollama (로컬) | `http://localhost:11434/v1/chat/completions` | `OPENAI_API_KEY=ollama` |

---

## 9장 — RAG · LLM 캐시 · 데이터 검증 · 로깅

LLM을 실제 서비스에 붙일 때 필요한 주변 기술 네 가지를 실습합니다. LLM 백엔드는 **Groq (`llama-3.3-70b-versatile`)** 를 OpenAI 호환 엔드포인트로 사용하고, Groq에는 임베딩 API가 없으므로 모든 임베딩은 **로컬 HuggingFace 모델**(`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`)을 사용합니다.

| 절 | 셀 | 내용 |
|---|---|---|
| 9.1 RAG | 9.1-9.5 | KLUE-MRC 기사 100건을 LlamaIndex `VectorStoreIndex`로 색인하고 질문에 답변 |
| 9.2 LLM 캐시 | 9.6-9.10 | 딕셔너리 기반 정확 일치 캐시 → ChromaDB 기반 유사 검색(semantic) 캐시 |
| 9.3 데이터 검증 | 9.11-9.14 | NeMo-Guardrails로 의도 기반 흐름 / 주제 차단 / 프롬프트 인젝션 방어 |
| 9.4 로깅 | 9.15-9.17 | Weights & Biases로 OpenAI 호출과 LlamaIndex 쿼리 trace 기록 |

> 추가 Secret이 필요한 절: 9.4는 W&B 로그인 시 토큰 입력 프롬프트가 뜹니다 ([W&B Authorize](https://wandb.ai/authorize)).

---

## 파일 구성

| 파일 | 챕터 | 설명 |
|---|---|---|
| `chapter_6.ipynb` / `chapter_6_Groq.ipynb` | 6장 | Text-to-SQL 미세 조정 (judge 백엔드 두 종) |
| `chapter_9.ipynb` | 9장 | RAG / 캐시 / 가드레일 / 로깅 |
| `utils.py` | 6장 | 프롬프트 포맷팅 / 평가 요청 JSONL 작성 / 결과 CSV 변환 |
| `api_request_parallel_processor.py` | 6장 | OpenAI 호환 엔드포인트 비동기 배치 클라이언트 |
| `requirements.txt` | 6장 | Colab 핀 버전 (9장은 노트북 첫 셀에서 직접 설치) |

## 라이선스

[CC BY 4.0](LICENSE) — 자유 사용/수정/재배포 가능, 출처 표시 필요.
