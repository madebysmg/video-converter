#!/usr/bin/env python3
import ffmpeg
import os
import sys
from pathlib import Path
from file_utils import get_output_path, get_default_input_path

def convert_mov_to_mp4(input_path, output_path=None, target_size_mb=200):
    """
    MOV 파일을 MP4로 변환합니다.
    목표 파일 크기에 맞춰 최적화된 설정을 적용합니다.
    """
    
    input_file = Path(input_path)
    
    if not input_file.exists():
        print(f"오류: 입력 파일이 존재하지 않습니다: {input_path}")
        return False
    
    if output_path is None:
        output_path = input_file.with_suffix('.mp4')
    
    output_file = Path(output_path)
    
    # 비디오 길이 확인
    probe = ffmpeg.probe(str(input_file))
    duration = float(probe['format']['duration'])
    
    # 목표 비트레이트 계산 (여유분 10% 제외)
    target_total_bitrate = (target_size_mb * 8 * 1024 * 1024 * 0.9) / duration
    audio_bitrate = 128 * 1024  # 128k 오디오
    video_bitrate = target_total_bitrate - audio_bitrate
    
    print(f"비디오 길이: {duration:.1f}초")
    print(f"목표 비디오 비트레이트: {video_bitrate/1024:.0f}k")
    
    try:
        print(f"변환 시작: {input_file.name} -> {output_file.name}")
        
        # 최적화된 설정
        # - 2-pass 인코딩으로 품질 최적화
        # - 계산된 비트레이트로 용량 제어
        # - 슬라이드 영상에 최적화된 튜닝
        
        # 1st pass
        (
            ffmpeg
            .input(str(input_file))
            .output(
                '/dev/null' if os.name != 'nt' else 'NUL',
                vcodec='libx264',
                acodec='aac',
                video_bitrate=f"{int(video_bitrate)}",
                audio_bitrate='128k',
                preset='veryslow',  # 최고 압축 효율
                tune='stillimage',  # 슬라이드/정적 이미지 최적화
                **{'pass': 1, 'f': 'null'}
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        # 2nd pass
        (
            ffmpeg
            .input(str(input_file))
            .output(
                str(output_file),
                vcodec='libx264',
                acodec='aac',
                video_bitrate=f"{int(video_bitrate)}",
                audio_bitrate='128k',
                preset='veryslow',
                tune='stillimage',
                **{'pass': 2}
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        
        if output_file.exists():
            input_size = input_file.stat().st_size
            output_size = output_file.stat().st_size
            
            print(f"변환 완료!")
            print(f"입력 파일 크기: {input_size / (1024*1024):.2f} MB")
            print(f"출력 파일 크기: {output_size / (1024*1024):.2f} MB")
            print(f"출력 파일: {output_file}")
            
            return True
        else:
            print("오류: 출력 파일이 생성되지 않았습니다.")
            return False
            
    except ffmpeg.Error as e:
        print(f"FFmpeg 오류 발생:")
        if e.stderr:
            print(e.stderr.decode('utf-8'))
        return False
    except Exception as e:
        print(f"예상치 못한 오류 발생: {e}")
        return False

def main():
    # 사용법: python convert_video.py [입력 파일] [목표 크기(MB)]
    # 입력 파일을 생략하면 INPUT_VIDEO_PATH 환경변수(기본 ./input_video.mp4)를 사용
    input_path = sys.argv[1] if len(sys.argv) > 1 else get_default_input_path()
    output_path = get_output_path(input_path, "compressed")
    target_size = int(sys.argv[2]) if len(sys.argv) > 2 else 190  # 기본 190MB 목표 (여유분 확보)

    print("=== MOV to MP4 압축 변환기 ===")
    print(f"입력 파일: {input_path}")
    print(f"출력 파일: {output_path}")
    print(f"목표 크기: {target_size}MB")
    print()
    
    success = convert_mov_to_mp4(input_path, output_path, target_size)
    
    if success:
        print("\n✅ 변환이 성공적으로 완료되었습니다!")
    else:
        print("\n❌ 변환 중 오류가 발생했습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main()