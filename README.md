# 6장 — Text-to-SQL 미세 조정 (sLLM 강의)

자연어 질문을 SQL로 변환하는 한국어 sLLM(`beomi/Yi-Ko-6B`)을 LoRA로 미세 조정하는 실습 자료입니다. 데이터셋은 [`shangrilar/ko_text2sql`](https://huggingface.co/datasets/shangrilar/ko_text2sql)을 사용합니다.

## 빠른 시작 (Google Colab)

1. **Colab에서 노트북 열기** — 아래 배지를 클릭하거나 직접 열기:
   - [`chapter_6.ipynb`를 Colab에서 열기](https://colab.research.google.com/github/taejungpark/ch6-sLLM/blob/main/chapter_6.ipynb)

2. **런타임 설정** — `런타임 → 런타임 유형 변경 → T4 GPU` 선택

3. **API 키 등록** (좌측 🔑 Secrets 탭, "Notebook access" ON):
   - `GEMINI_API_KEY` — [Google AI Studio](https://aistudio.google.com/apikey)에서 무료 발급
   - `HF_TOKEN` *(선택)* — 학습한 모델을 허깅페이스 허브에 업로드하려는 경우만

4. **셀 순서대로 실행** — 첫 셀이 이 저장소를 자동으로 클론합니다.

## 파이프라인 개요

| 단계 | 셀 | 내용 |
|---|---|---|
| 1 | 6.7 | `Yi-Ko-6B` 4-bit 양자화 로드 |
| 2 | 6.8 | 기초 모델로 테스트셋 SQL 생성 → Gemini judge로 정답률 측정 |
| 3 | 6.9 | 학습 데이터(`ko_text2sql/train`) 전처리 |
| 4 | 6.10 | LoRA 미세 조정 (`trl.SFTTrainer`) |
| 5 | 6.11 | LoRA 어댑터 결합 → (선택) HF Hub 업로드 |
| 6 | 6.12-6.13 | 미세 조정 모델 재평가 → 기초 모델과 정답률 비교 |

## 파일 구성

- `chapter_6.ipynb` — 메인 노트북
- `utils.py` — 프롬프트 포맷팅 / 평가 요청 JSONL 작성 / 결과 CSV 변환
- `api_request_parallel_processor.py` — OpenAI 호환 엔드포인트(Gemini/OpenAI/Ollama/Groq) 비동기 배치 클라이언트
- `requirements.txt` — Colab에서 핀할 패키지 버전

## 평가 백엔드 변경

기본 judge는 **Gemini 2.0 Flash**(무료, 15 RPM)이지만, `--request_url`만 바꾸면 다른 백엔드로 전환됩니다:

| 백엔드 | URL | 환경변수 |
|---|---|---|
| Gemini (기본) | `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions` | `GEMINI_API_KEY` |
| OpenAI | `https://api.openai.com/v1/chat/completions` | `OPENAI_API_KEY` |
| Groq | `https://api.groq.com/openai/v1/chat/completions` | `GROQ_API_KEY` |
| Ollama (로컬) | `http://localhost:11434/v1/chat/completions` | `OPENAI_API_KEY=ollama` |

## 라이선스

[CC BY 4.0](LICENSE) — 자유 사용/수정/재배포 가능, 출처 표시 필요.
