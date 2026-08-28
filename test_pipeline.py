import asyncio
import os
from pathlib import Path
from backend.tts_engine import tts_engine
from backend.visual_engine import visual_engine
from backend.audio_engine import audio_engine
from backend.render_engine import render_engine
from backend.config import TEMP_DIR, OUTPUT_DIR, BGM_DIR

async def test_full_pipeline():
    print("=== [1/5] Testing TTS & Subtitle Generation ===")
    test_text = "Đêm khuya thanh vắng, ngọn nến le lói trong căn phòng cổ kính."
    audio_path = str(TEMP_DIR / "test_voice.mp3")
    srt_path = str(TEMP_DIR / "test_sub.srt")
    
    tts_res = await tts_engine.generate_speech(
        text=test_text,
        output_audio_path=audio_path,
        output_srt_path=srt_path,
        voice="vi-VN-HoaiMyNeural"
    )
    print(f"TTS Done! Duration: {tts_res['duration']:.2f}s, Audio: {audio_path}")
    assert os.path.exists(audio_path)
    assert os.path.exists(srt_path)

    print("\n=== [2/5] Testing Image Generation ===")
    img_path = str(TEMP_DIR / "test_img.jpg")
    await visual_engine.generate_image(
        prompt="mysterious dark ancient room, single glowing candle, cinematic lighting",
        output_image_path=img_path,
        style_key="dark_mystery",
        aspect_ratio="16:9"
    )
    print(f"Image Done! Saved to: {img_path}")
    assert os.path.exists(img_path)

    print("\n=== [3/5] Testing Ken Burns Motion Video ===")
    clip_path = str(TEMP_DIR / "test_clip.mp4")
    visual_engine.create_ken_burns_video(
        image_path=img_path,
        output_video_path=clip_path,
        duration=tts_res["duration"],
        aspect_ratio="16:9"
    )
    print(f"Ken Burns Clip Done! Saved to: {clip_path}")
    assert os.path.exists(clip_path)

    print("\n=== [4/5] Testing Audio Mixing (Voice + BGM) ===")
    mixed_audio = str(TEMP_DIR / "test_mixed.mp3")
    bgm_sample = str(BGM_DIR / "ambient_mystery.mp3")
    audio_engine.mix_voice_and_bgm(
        voice_path=audio_path,
        output_path=mixed_audio,
        bgm_path=bgm_sample,
        bgm_volume=0.15
    )
    print(f"Audio Mixed! Saved to: {mixed_audio}")
    assert os.path.exists(mixed_audio)

    print("\n=== [5/5] Testing Final Composite Video Rendering ===")
    final_video = str(OUTPUT_DIR / "test_story_output.mp4")
    render_engine.composite_final_video(
        base_video_path=clip_path,
        audio_path=mixed_audio,
        output_path=final_video,
        srt_subtitles_path=srt_path,
        title_text="TRUYỆN NGẮN ĐÊM KHUYA",
        watermark_text="@TruyenAudioAI",
        enable_waveform=True,
        aspect_ratio="16:9"
    )
    print(f"Final Video Done! Saved to: {final_video}")
    assert os.path.exists(final_video)
    print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
