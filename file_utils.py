#!/usr/bin/env python3
"""
파일 경로 및 이름 처리 유틸리티 함수들
동적 파일 경로 생성과 환경변수 기반 설정 관리
"""

import os
from pathlib import Path
import datetime

def get_file_config():
    """환경변수에서 파일 관련 설정들을 읽어옴"""
    return {
        'input_video_path': os.getenv('INPUT_VIDEO_PATH', './input_video.mp4'),
        'output_dir': os.getenv('OUTPUT_DIR', './output'),
        'temp_dir': os.getenv('TEMP_DIR', './temp'),
        'default_output_format': os.getenv('DEFAULT_OUTPUT_FORMAT', 'mp4'),
        'supported_input_formats': os.getenv('SUPPORTED_INPUT_FORMATS', 'mp4,mov,avi,mkv,wmv,flv,webm,m4v').split(','),
        'output_filename_pattern': os.getenv('OUTPUT_FILENAME_PATTERN', '{stem}_{task}.{ext}')
    }

def ensure_directory_exists(dir_path):
    """디렉토리가 없으면 생성"""
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def generate_output_filename(input_path, task, output_format=None, timestamp=None):
    """
    출력 파일명을 패턴에 따라 생성
    
    Args:
        input_path: 입력 파일 경로
        task: 작업명 (subtitles, translated, screen_translation 등)
        output_format: 출력 확장자 (None이면 기본값 사용)
        timestamp: 타임스탬프 (None이면 현재 시간 사용)
    
    Returns:
        생성된 파일명
    """
    config = get_file_config()
    input_file = Path(input_path)
    
    # 기본값 설정
    if output_format is None:
        output_format = config['default_output_format']
    
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 패턴 변수 치환
    filename = config['output_filename_pattern'].format(
        stem=input_file.stem,
        task=task,
        ext=output_format,
        timestamp=timestamp
    )
    
    return filename

def get_output_path(input_path, task, output_format=None, output_dir=None):
    """
    완전한 출력 파일 경로 생성
    
    Args:
        input_path: 입력 파일 경로
        task: 작업명
        output_format: 출력 확장자
        output_dir: 출력 디렉토리 (None이면 환경변수 사용)
    
    Returns:
        Path: 생성된 출력 파일 경로
    """
    config = get_file_config()
    
    if output_dir is None:
        output_dir = config['output_dir']
    
    # 출력 디렉토리 생성
    output_directory = ensure_directory_exists(output_dir)
    
    # 파일명 생성
    filename = generate_output_filename(input_path, task, output_format)
    
    return output_directory / filename

def get_temp_file_path(prefix="temp", suffix=".wav"):
    """
    임시 파일 경로 생성
    
    Args:
        prefix: 파일명 접두사
        suffix: 파일 확장자
    
    Returns:
        Path: 임시 파일 경로
    """
    config = get_file_config()
    temp_dir = ensure_directory_exists(config['temp_dir'])
    
    # 임시 파일명 생성
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 밀리초까지
    temp_filename = f"{prefix}_{timestamp}{suffix}"
    
    return temp_dir / temp_filename

def validate_input_format(input_path):
    """
    입력 파일 확장자가 지원되는지 확인
    
    Args:
        input_path: 입력 파일 경로
    
    Returns:
        bool: 지원되는 형식이면 True
    """
    config = get_file_config()
    input_file = Path(input_path)
    file_extension = input_file.suffix.lower().lstrip('.')
    
    return file_extension in [fmt.strip().lower() for fmt in config['supported_input_formats']]

def get_default_input_path():
    """환경변수에서 기본 입력 비디오 경로 가져오기"""
    config = get_file_config()
    return config['input_video_path']

def resolve_path(path_str):
    """
    경로 문자열을 절대경로로 변환
    상대경로는 현재 작업 디렉토리 기준으로 해석
    
    Args:
        path_str: 경로 문자열
    
    Returns:
        Path: 해석된 절대경로
    """
    path = Path(path_str)
    if path.is_absolute():
        return path
    else:
        return Path.cwd() / path

def get_segment_suffix(start_time=None, end_time=None):
    """
    비디오 구간 정보를 파일명 suffix로 변환
    
    Args:
        start_time: 시작 시간 (초)
        end_time: 종료 시간 (초)
    
    Returns:
        str: 구간 정보 suffix (예: "_1800s-1860s")
    """
    if start_time is not None and end_time is not None:
        return f"_{start_time}s-{end_time}s"
    return ""

def clean_temp_files(keep_recent=5):
    """
    임시 파일 정리 (최근 N개 제외하고 삭제)
    
    Args:
        keep_recent: 보관할 최근 파일 개수
    """
    config = get_file_config()
    temp_dir = Path(config['temp_dir'])
    
    if not temp_dir.exists():
        return
    
    # 임시 파일들을 수정시간 순으로 정렬
    temp_files = sorted(
        [f for f in temp_dir.glob("temp_*") if f.is_file()],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    # 최근 파일들 제외하고 삭제
    files_to_delete = temp_files[keep_recent:]
    for file_path in files_to_delete:
        try:
            file_path.unlink()
            print(f"🗑️  임시 파일 삭제: {file_path.name}")
        except Exception as e:
            print(f"⚠️  임시 파일 삭제 실패: {file_path.name} - {e}")

# 사용 예시
if __name__ == "__main__":
    # 설정 출력
    config = get_file_config()
    print("📁 파일 설정:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # 경로 생성 테스트
    input_path = "./test_video.mp4"
    output_path = get_output_path(input_path, "subtitles")
    temp_path = get_temp_file_path("audio_segment")
    
    print(f"\n🧪 테스트 결과:")
    print(f"  입력: {input_path}")
    print(f"  출력: {output_path}")
    print(f"  임시: {temp_path}")
    print(f"  확장자 검증: {validate_input_format(input_path)}")