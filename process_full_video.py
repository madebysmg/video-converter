#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from improved_subtitle_generator import ImprovedSubtitleGenerator
from improved_screen_translator import ImprovedScreenTextTranslator
from file_utils import get_output_path, get_default_input_path

def process_full_video(video_path=None):
    """전체 영상에 개선된 시스템(음성 자막 + 화면 텍스트 번역) 적용"""

    # OpenAI API 키 설정 (환경변수에서 읽기)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ OPENAI_API_KEY 환경변수를 설정해주세요.")
        print("export OPENAI_API_KEY=your_api_key_here")
        return None

    # 입력 비디오 (명령행 인자 또는 INPUT_VIDEO_PATH 환경변수)
    if video_path is None:
        video_path = sys.argv[1] if len(sys.argv) > 1 else get_default_input_path()

    if not Path(video_path).exists():
        print(f"❌ 파일을 찾을 수 없습니다: {video_path}")
        return None

    final_output_path = str(get_output_path(video_path, "complete"))

    print("🚀 전체 영상 개선된 시스템 처리 시작")
    print(f"📹 원본 파일: {video_path}")
    print("⏰ 전체 영상 처리")
    print("="*80)

    # 1단계: 전체 영상 개선된 음성 자막 생성
    print("\n🎤 1단계: 전체 영상 개선된 음성 자막 생성")
    print("⚠️  영상 길이에 따라 오래 걸릴 수 있습니다 (Whisper 처리 + GPT-4o 번역)")

    subtitle_generator = ImprovedSubtitleGenerator(api_key)
    subtitle_result = subtitle_generator.process_video_segment(
        video_path,
        start_time=None,
        end_time=None  # 전체 영상 처리
    )
    print(f"✅ 전체 음성 자막 완료: {subtitle_result}")

    # 2단계: 전체 영상 개선된 화면 텍스트 번역
    print("\n📺 2단계: 전체 영상 개선된 화면 텍스트 번역")
    print("⚠️  영상 길이에 따라 오래 걸릴 수 있습니다 (OCR 처리 + GPT-4o 번역)")

    # 음성 자막이 적용된 비디오를 입력으로 사용
    if str(subtitle_result).endswith('.mp4'):
        input_for_screen = str(subtitle_result)
    else:
        input_for_screen = video_path

    screen_translator = ImprovedScreenTextTranslator(api_key)
    final_result = screen_translator.process_video_segment_improved(
        input_for_screen,
        final_output_path,
        start_time=None,
        end_time=None,  # 전체 영상 처리
        interval_seconds=15  # 15초마다 화면 텍스트 확인
    )
    print(f"✅ 전체 화면 번역 완료: {final_result}")

    print("\n🎉 전체 영상 처리 완료!")
    print(f"📁 최종 결과: {final_result}")
    print("\n적용 내용:")
    print("✅ 음성 자막: 번역문만, 작은 폰트, 긴 자막 분할")
    print("✅ 화면 번역: 향상된 OCR, 더 많은 텍스트 감지, 작은 폰트")

    # 파일 크기 확인
    if os.path.exists(final_result):
        file_size = os.path.getsize(final_result) / (1024*1024*1024)  # GB
        print(f"📊 최종 파일 크기: {file_size:.2f} GB")

    return final_result

if __name__ == "__main__":
    process_full_video()
