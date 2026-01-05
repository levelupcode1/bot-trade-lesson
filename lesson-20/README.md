# Lesson 20: 자동화된 멜론 차트 분석 시스템

매일 아침 8시에 멜론 차트를 자동으로 크롤링하고, 구글 시트에 저장한 후, Gemini AI로 의미있는 분석을 수행하는 완전 자동화 시스템을 구축합니다.

## 📚 목차

### [Part 1: n8n 워크플로우 구축](./PART1_N8N_WORKFLOW.md)
- n8n 설치 및 설정
- 스케줄 트리거 설정 (매일 8시)
- HTTP Request로 멜론 차트 크롤링
- Code 노드로 데이터 파싱
- 구글 시트에 데이터 저장

### [Part 2: 구글 시트 연동](./PART2_GOOGLE_SHEETS.md)
- 구글 클라우드 프로젝트 설정
- 서비스 계정 생성 및 인증
- 구글 시트 API 연동
- 데이터 자동 저장 시스템

### [Part 3: Gemini AI 분석](./PART3_GEMINI_ANALYSIS.md)
- Google Gemini API 설정
- 구글 시트 데이터 읽기
- AI 기반 트렌드 분석
- 인사이트 리포트 생성

## 🎯 학습 목표

이 레슨을 완료하면 다음을 할 수 있습니다:

1. ✅ n8n을 사용한 자동화 워크플로우 구축
2. ✅ 스케줄 기반 자동 크롤링 시스템 구축
3. ✅ 구글 시트 API를 통한 데이터 저장
4. ✅ Gemini AI를 활용한 데이터 분석
5. ✅ 완전 자동화된 데이터 파이프라인 구축

## 🛠️ 필요한 도구

- **n8n**: 워크플로우 자동화 도구
- **Google Cloud Platform**: API 사용을 위한 계정
- **Google Sheets**: 데이터 저장소
- **Google Gemini API**: AI 분석 도구

## 📋 사전 준비사항

1. n8n 설치 (로컬 또는 클라우드)
2. Google Cloud Platform 계정
3. 구글 시트 생성
4. Gemini API 키 발급

## 🚀 빠른 시작

### 방법 1: n8n AI 사용 (가장 빠름) ⚡

1. n8n에서 **AI Assistant** 열기 (`Ctrl+K`)
2. [`AI_PROMPT_COPY_PASTE.txt`](./AI_PROMPT_COPY_PASTE.txt) 파일 내용 복사
3. AI Assistant에 붙여넣기
4. 생성된 워크플로우 검토 및 실행

자세한 내용: [QUICK_START_AI.md](./QUICK_START_AI.md)

### 방법 2: 단계별 학습 (권장) 📚

각 파트를 순서대로 진행하세요:

1. **Part 1** → n8n 워크플로우 구축
2. **Part 2** → 구글 시트 연동
3. **Part 3** → Gemini AI 분석

## 📊 시스템 아키텍처

```
┌─────────────────┐
│  n8n Schedule   │ (매일 8시)
│     Trigger     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  HTTP Request   │ (멜론 차트 크롤링)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Code Node     │ (데이터 파싱)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Google Sheets  │ (데이터 저장)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gemini AI      │ (데이터 분석)
└─────────────────┘
```

## 📁 프로젝트 구조

```
lesson-20/
├── README.md                    # 이 파일
├── PART1_N8N_WORKFLOW.md       # Part 1: n8n 워크플로우
├── PART2_GOOGLE_SHEETS.md      # Part 2: 구글 시트 연동
├── PART3_GEMINI_ANALYSIS.md    # Part 3: Gemini AI 분석
├── N8N_AI_PROMPTS.md           # n8n AI 프롬프트 모음
├── QUICK_START_AI.md           # AI로 빠르게 시작하기
├── AI_PROMPT_COPY_PASTE.txt    # 복사해서 바로 사용할 프롬프트
├── n8n_workflows/              # n8n 워크플로우 JSON
│   └── melon_chart_workflow.json
├── scripts/                     # 유틸리티 스크립트
│   ├── gemini_analyzer.py
│   ├── google_sheets_reader.py
│   └── generate_report.py
└── examples/                    # 예제 코드
    └── complete_pipeline.py
```

## ⏱️ 예상 소요 시간

- **Part 1**: 1-2시간
- **Part 2**: 1시간
- **Part 3**: 1-2시간
- **총 예상 시간**: 3-5시간

## 🎓 난이도

- **초급**: n8n 기본 사용
- **중급**: API 연동 및 데이터 처리
- **고급**: AI 분석 및 인사이트 도출

## 📝 참고사항

- 각 파트는 독립적으로 학습 가능하지만, 순서대로 진행하는 것을 권장합니다
- 실습 중 문제가 발생하면 각 파트의 "문제 해결" 섹션을 참고하세요
- 완성된 시스템은 매일 자동으로 실행되어 데이터를 수집하고 분석합니다

---

**시작하기**: [Part 1: n8n 워크플로우 구축](./PART1_N8N_WORKFLOW.md) →

