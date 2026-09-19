# Video Converter

외국어 발표 영상에 번역 자막과 화면 텍스트 번역을 입혀 주는 Python 스크립트 모음입니다. OpenAI Whisper로 음성을 인식하고, GPT-4o로 번역한 뒤 FFmpeg로 자막을 영상에 합성합니다. 슬라이드나 UI처럼 화면에 보이는 글자는 EasyOCR로 찾아 번역문을 영상 위에 덧씌웁니다.

일본어 기술 발표 영상을 한국어로 보기 위해 만든 개인 프로젝트입니다. 기본값은 일본어 → 한국어이고, `improved_*` 스크립트는 환경변수로 언어와 입출력 경로를 바꿀 수 있습니다.

## 주요 기능

- **음성 자막 생성**: Whisper(`large` 모델)로 음성을 인식해 타임스탬프가 있는 세그먼트를 만듭니다.
- **자막 번역**: 세그먼트를 한 번의 GPT-4o 요청으로 묶어 번역하고, 결과 개수가 맞지 않으면 문장마다 다시 요청합니다.
- **자막 합성**: SRT 파일을 만들고 FFmpeg `subtitles` 필터로 영상에 입힙니다. 개선 버전은 번역문만 넣고, 40자가 넘는 자막은 공백 기준으로 최대 3조각으로 나눠 세그먼트 시간을 나눠 차례로 보여 줍니다.
- **화면 텍스트 번역**: 일정 간격으로 프레임을 뽑아 EasyOCR로 글자를 찾고, 번역문을 원문 바로 아래에 그립니다. 개선 버전은 OCR 전에 흑백 변환, 2배 업스케일, 노이즈 제거, 대비 보정을 합니다.
- **구간 처리**: 개선 버전은 시작/종료 시각(초)을 지정해 일부 구간만 처리할 수 있습니다. 자막 생성기는 음성 인식과 번역만 그 구간으로 제한하고, 자막을 합성한 영상은 원본 전체 길이로 다시 인코딩합니다(자막은 해당 구간에만 들어감). 화면 번역기는 지정 구간의 프레임만 새 영상으로 씁니다.
- **MOV → MP4 압축**: 목표 용량에 맞춰 비트레이트를 계산하고 2-pass H.264로 인코딩합니다.

## 설치

```bash
git clone https://github.com/madebysmg/video-converter.git
cd video-converter

python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

FFmpeg가 시스템에 설치되어 있어야 합니다.

- **Mac**: `brew install ffmpeg`
- **Ubuntu**: `sudo apt install ffmpeg`
- **Windows**: [FFmpeg 공식 사이트](https://ffmpeg.org/download.html)에서 다운로드

Whisper `large` 모델과 EasyOCR 모델은 첫 실행 때 내려받습니다.

## 환경 변수 설정

스크립트는 설정을 환경변수에서 읽습니다. `.env` 파일을 직접 읽지는 않으므로, 복사해서 수정한 뒤 실행 전에 셸로 불러옵니다.

```bash
cp .env.example .env
# .env 파일을 열어 OPENAI_API_KEY 등을 수정

set -a; source .env; set +a
```

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `OPENAI_API_KEY` | (없음) | OpenAI API 키. [OpenAI 플랫폼](https://platform.openai.com/api-keys)에서 발급 |
| `SOURCE_LANGUAGE` | `ja` | 영상 원본 언어 (Whisper 언어 코드) |
| `TARGET_LANGUAGE` | `Korean` | 번역할 언어 (GPT 프롬프트에 들어가는 언어 이름) |
| `OCR_LANGUAGES` | `ja,en` | 화면 텍스트 인식 언어 (EasyOCR 언어 코드, 쉼표로 구분) |
| `INPUT_VIDEO_PATH` | `./input_video.mp4` | 명령행 인자가 없을 때 쓰는 입력 영상 |
| `OUTPUT_DIR` | `./output` | 결과 파일 저장 위치 |
| `TEMP_DIR` | `./temp` | 구간 처리 시 임시 오디오 저장 위치 |
| `DEFAULT_OUTPUT_FORMAT` | `mp4` | 출력 확장자 기본값 |
| `SUPPORTED_INPUT_FORMATS` | `mp4,mov,avi,mkv,wmv,flv,webm,m4v` | 개선 버전이 받는 입력 확장자 |
| `OUTPUT_FILENAME_PATTERN` | `{stem}_{task}.{ext}` | 출력 파일명 패턴 |

### 언어 코드

- **SOURCE_LANGUAGE** (Whisper): `ja` 일본어, `en` 영어, `ko` 한국어, `zh` 중국어, `fr` 프랑스어, `de` 독일어, `es` 스페인어, `ru` 러시아어, `pt` 포르투갈어, `it` 이탈리아어 등
- **TARGET_LANGUAGE** (GPT): `Korean`, `English`, `Japanese`, `Chinese`, `French`, `German`, `Spanish` 등 언어 이름
- **OCR_LANGUAGES** (EasyOCR): `en`, `ja`, `ko`, `ch_sim`(중국어 간체), `ch_tra`(중국어 번체), `fr`, `de`, `es`, `ru`, `pt`, `it` 등. EasyOCR은 일본어·한국어·중국어를 영어와만 함께 쓸 수 있습니다.

```bash
# 일본어 영상 → 한국어
SOURCE_LANGUAGE=ja
TARGET_LANGUAGE=Korean
OCR_LANGUAGES=ja,en

# 영어 영상 → 일본어
SOURCE_LANGUAGE=en
TARGET_LANGUAGE=Japanese
OCR_LANGUAGES=en

# 중국어 영상 → 영어
SOURCE_LANGUAGE=zh
TARGET_LANGUAGE=English
OCR_LANGUAGES=ch_sim,en
```

### 출력 파일명 패턴

`OUTPUT_FILENAME_PATTERN`에서 쓸 수 있는 변수입니다.

- `{stem}`: 입력 파일명 (확장자 제외)
- `{task}`: 작업 이름 (`improved_subtitles`, `improved_screen_translation`, `compressed`, `complete` 등)
- `{ext}`: 출력 확장자
- `{timestamp}`: 실행 시각 (YYYYMMDD_HHMMSS)

```bash
OUTPUT_FILENAME_PATTERN={stem}_{task}.{ext}
# 결과: lecture_improved_subtitles.mp4

OUTPUT_FILENAME_PATTERN={stem}_{task}_{timestamp}.{ext}
# 결과: lecture_improved_subtitles_20250821_143022.mp4
```

## 사용법

모든 스크립트는 첫 번째 인자로 입력 영상을 받습니다. 인자를 생략하면 `INPUT_VIDEO_PATH`를 씁니다.

```bash
# 음성 자막 생성 + 번역 + 합성 (개선 버전, 번역문만)
python improved_subtitle_generator.py /path/to/video.mp4

# 화면 텍스트 번역 오버레이 (개선 버전, 10초 간격)
python improved_screen_translator.py /path/to/video.mp4

# 전체 처리: 음성 자막을 입힌 뒤 그 결과에 화면 텍스트 번역(15초 간격)
python process_full_video.py /path/to/video.mp4

# 짧은 구간만 시험 처리 (기본 1800초~1860초, 1단계 자막 합성은 원본 전체 길이로 인코딩)
python demo_segment.py /path/to/video.mp4 1800 1860

# MOV → MP4 압축 (목표 용량 MB, 기본 190)
python convert_video.py /path/to/video.mov 190
```

기본 버전도 같은 방식으로 실행할 수 있습니다. 기본 버전은 일본어 → 한국어로 고정되어 있습니다(아래 "제한 사항" 참고).

```bash
python subtitle_generator.py /path/to/video.mp4       # 원문 + 번역 이중 자막
python screen_text_translator.py /path/to/video.mp4   # 화면 텍스트 번역 (10초 간격)
```

### 결과 파일

기본 파일명 패턴(`{stem}_{task}.{ext}`) 기준입니다.

| 스크립트 | 결과 |
| --- | --- |
| `improved_subtitle_generator.py` | `OUTPUT_DIR/{stem}_improved_subtitles.srt`, `.mp4` (구간 처리 시 `_{시작}s-{끝}s`가 붙음) |
| `improved_screen_translator.py` | `OUTPUT_DIR/{stem}_improved_screen_translation.mp4` |
| `process_full_video.py` | 위 자막 결과 + `OUTPUT_DIR/{stem}_complete.mp4` |
| `demo_segment.py` | 위 자막 결과(원본 전체 길이) + `OUTPUT_DIR/{stem}_complete_improved_{시작}s-{끝}s.mp4`(지정 구간만) |
| `convert_video.py` | `OUTPUT_DIR/{stem}_compressed.mp4` |
| `subtitle_generator.py` | 입력 영상과 같은 폴더의 `{stem}_subtitles.srt`, `{stem}_with_subtitles.mp4` |
| `screen_text_translator.py` | `OUTPUT_DIR/{stem}_screen_translation.mp4` |

## 파이썬에서 사용하기

생성자의 API 키 인자 이름은 `openai_api_key`입니다. 언어 인자를 생략하면 환경변수 값을 씁니다.

```python
import os
from improved_subtitle_generator import ImprovedSubtitleGenerator
from improved_screen_translator import ImprovedScreenTextTranslator

api_key = os.environ["OPENAI_API_KEY"]

# 음성 자막: 0~60초 구간만 처리
generator = ImprovedSubtitleGenerator(
    openai_api_key=api_key,
    source_language="en",      # 영어 음성
    target_language="Korean",  # 한국어로 번역
)
result = generator.process_video_segment("video.mp4", start_time=0, end_time=60)

# 화면 텍스트 번역
translator = ImprovedScreenTextTranslator(
    openai_api_key=api_key,
    source_language="zh",      # 중국어 텍스트만 번역 대상으로 거름
    target_language="English",
    ocr_languages="ch_sim,en",
)
translator.process_video_segment_improved("input.mp4", "output.mp4", interval_seconds=10)
```

기본 버전은 다음과 같이 씁니다.

```python
import os
from subtitle_generator import SubtitleGenerator
from screen_text_translator import ScreenTextTranslator

api_key = os.environ["OPENAI_API_KEY"]

SubtitleGenerator(openai_api_key=api_key).process_video("video.mp4")
ScreenTextTranslator(openai_api_key=api_key).process_video_with_translation("input.mp4", "output.mp4")
```

## 처리 과정

1. **음성 자막**
   - (구간 지정 시) FFmpeg로 해당 구간 오디오를 임시 WAV로 추출
   - Whisper로 음성 인식, 구간 시작 시각만큼 타임스탬프 보정
   - GPT-4o로 번역 → SRT 생성 → FFmpeg로 영상에 합성 (구간을 지정해도 합성은 원본 전체 길이로 다시 인코딩)
2. **화면 텍스트 번역**
   - 지정한 간격으로 프레임 추출 (구간 지정 시 그 구간 안에서만)
   - EasyOCR로 글자 인식 후 신뢰도와 원본 언어 문자 포함 여부로 걸러냄
   - GPT-4o로 번역, PIL로 번역문을 프레임에 그림
   - OpenCV로 영상을 다시 씀 (구간 지정 시 그 구간만)

## 제한 사항

개인용으로 만든 프로토타입이며, 자동화된 테스트는 없습니다.

- **기본 버전은 일본어 → 한국어 고정**: `subtitle_generator.py`는 Whisper 언어를 `ja`로, 번역 프롬프트를 일본어→한국어로 고정해 두었습니다(시작할 때 출력하는 언어 설정 값은 실제로 쓰이지 않음). `screen_text_translator.py`는 OCR 언어만 `OCR_LANGUAGES`를 따르고, 일본어 문자가 있는 텍스트만 골라 한국어로 번역합니다. 원본·번역 언어 설정이 실제로 반영되는 것은 `improved_*` 스크립트와 이를 쓰는 `process_full_video.py`, `demo_segment.py`입니다.
- **화면 번역 결과에는 오디오가 없음**: 화면 번역 단계는 OpenCV `VideoWriter`(mp4v)로 영상을 다시 쓰기 때문에 오디오 트랙이 빠집니다. `process_full_video.py`, `demo_segment.py`의 최종 결과도 같습니다.
- **슬라이드형 영상 기준**: 번역할 글자가 있는 샘플 프레임은 다음 샘플 시점까지 그 프레임(오버레이 적용본)이 그대로 반복됩니다. 화면 변화가 적은 발표 슬라이드 영상에 맞춘 방식입니다.
- **원본 언어 문자 필터**: 개선 버전의 화면 텍스트 필터는 `ja`, `ko`, `zh`, `en` 문자 범위만 정의되어 있고, 다른 언어는 일본어 범위로 판단합니다.
- **오버레이 번역문 길이**: 개선 버전은 20자가 넘는 번역문을 18자 + `...`로 자릅니다. 자막 분할은 최대 3조각까지만 남기므로 그보다 긴 자막은 뒷부분이 빠집니다.
- **폰트**: 오버레이 폰트는 macOS 시스템 폰트 경로(`AppleSDGothicNeo` 등)를 찾고, 없으면 PIL 기본 폰트를 씁니다. 다른 OS에서는 한글 등이 제대로 표시되지 않을 수 있습니다.
- **비용과 시간**: OpenAI API 사용료가 발생하고, 긴 영상은 처리에 오래 걸립니다. 개선 버전 OCR은 CPU(`gpu=False`)로 동작합니다.

## 문제 해결

- **FFmpeg 오류**: FFmpeg가 설치되어 있는지 확인하세요. 자막 합성에 쓰는 `subtitles` 필터는 libass가 포함된 FFmpeg 빌드가 필요합니다.
- **OpenAI API 오류**: `OPENAI_API_KEY`가 현재 셸 환경변수로 설정되어 있는지, 계정에 크레딧이 있는지 확인하세요. 번역 요청이 실패하면 해당 문장에 `[번역 실패]` 표시가 들어갑니다.
- **메모리 부족**: 개선 버전의 구간 처리로 나눠 실행하면 Whisper가 한 번에 인식하는 오디오 길이를 줄일 수 있습니다.

  ```python
  generator.process_video_segment("video.mp4", start_time=0, end_time=1800)
  generator.process_video_segment("video.mp4", start_time=1800, end_time=3600)
  ```

  구간마다 SRT와 영상이 따로 만들어지고, 영상은 각각 원본 전체 길이에 해당 구간 자막만 들어갑니다. 결과를 하나로 합치는 기능은 없고, 자막 합성이 구간 수만큼 반복되므로 전체 처리 시간은 줄지 않습니다.

## 파일 구조

```
video-converter/
├── README.md
├── requirements.txt                 # Python 의존성
├── .env.example                     # 환경변수 예시
├── file_utils.py                    # 환경변수 기반 경로·파일명 유틸리티
├── subtitle_generator.py            # 기본 자막 생성기 (일본어 → 한국어, 이중 자막)
├── improved_subtitle_generator.py   # 개선된 자막 생성기 (언어 설정, 구간 처리, 긴 자막 분할)
├── screen_text_translator.py        # 기본 화면 텍스트 번역기 (일본어 → 한국어)
├── improved_screen_translator.py    # 개선된 화면 텍스트 번역기 (OCR 전처리, 언어 설정, 구간 처리)
├── process_full_video.py            # 음성 자막 + 화면 번역 전체 처리
├── demo_segment.py                  # 짧은 구간 시험 처리
└── convert_video.py                 # MOV → MP4 압축 변환
```

## 라이선스

MIT License
