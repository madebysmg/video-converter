#!/usr/bin/env python3
"""
영상의 짧은 구간(기본 30분~31분)에만 음성 자막 + 화면 텍스트 번역을 적용해 보는 데모 스크립트

사용법:
    python demo_segment.py [입력 파일] [시작 초] [종료 초]

입력 파일을 생략하면 INPUT_VIDEO_PATH 환경변수(기본 ./input_video.mp4)를 사용합니다.
OpenAI API를 호출하므로 사용료가 발생할 수 있습니다.
"""
import sys
import os
from pathlib import Path

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from improved_subtitle_generator import ImprovedSubtitleGenerator
from improved_screen_translator import ImprovedScreenTextTranslator
from file_utils import get_output_path, get_default_input_path, get_segment_suffix

def run_demo_segment(video_path=None, start_time=30 * 60, end_time=31 * 60):
    """개선된 시스템을 지정 구간에만 적용 (기본 30분~31분)"""

    # OpenAI API 키 설정 (환경변수에서 읽기)
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ OPENAI_API_KEY 환경변수를 설정해주세요.")
        print("export OPENAI_API_KEY=your_api_key_here")
        return

    if video_path is None:
        video_path = get_default_input_path()

    if not Path(video_path).exists():
        print(f"❌ 파일을 찾을 수 없습니다: {video_path}")
        return

    final_output_path = str(get_output_path(video_path, f"complete_improved{get_segment_suffix(start_time, end_time)}"))

    print("🚀 개선된 통합 시스템 구간 처리 시작")
    print(f"📹 원본 파일: {video_path}")
    print(f"⏰ 처리 구간: {start_time//60}분{start_time%60:02d}초 ~ {end_time//60}분{end_time%60:02d}초")
    print("="*80)

    # 1단계: 개선된 음성 자막 생성
    print("\n🎤 1단계: 개선된 음성 자막 생성")
    subtitle_generator = ImprovedSubtitleGenerator(api_key)
    subtitle_result = subtitle_generator.process_video_segment(
        video_path,
        start_time=start_time,
        end_time=end_time
    )
    print(f"✅ 음성 자막 완료: {subtitle_result}")

    # 2단계: 개선된 화면 텍스트 번역
    print("\n📺 2단계: 개선된 화면 텍스트 번역")
    # 음성 자막이 적용된 비디오를 입력으로 사용
    if str(subtitle_result).endswith('.mp4'):
        input_for_screen = str(subtitle_result)
    else:
        input_for_screen = video_path

    screen_translator = ImprovedScreenTextTranslator(api_key)
    final_result = screen_translator.process_video_segment_improved(
        input_for_screen,
        final_output_path,
        start_time=start_time,
        end_time=end_time,
        interval_seconds=10
    )
    print(f"✅ 화면 번역 완료: {final_result}")

    print("\n🎉 구간 처리 완료!")
    print(f"📁 최종 결과: {final_result}")
    print("\n적용 내용:")
    print("✅ 음성 자막: 번역문만, 작은 폰트, 긴 자막 분할")
    print("✅ 화면 번역: 향상된 OCR, 더 많은 텍스트 감지, 작은 폰트")

if __name__ == "__main__":
    video_arg = sys.argv[1] if len(sys.argv) > 1 else None
    start_arg = int(sys.argv[2]) if len(sys.argv) > 2 else 30 * 60
    end_arg = int(sys.argv[3]) if len(sys.argv) > 3 else 31 * 60
    run_demo_segment(video_arg, start_arg, end_arg)
