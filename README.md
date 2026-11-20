# Doppel Echo Voice Model Converter

RVC 추론용 `.pth`를 도플 에코의 w-okada 호환 ONNX 규격으로 변환하는 Windows용 도구입니다. 별도의 음성 서버 프로젝트나 GPU 없이 사용할 수 있습니다. Python 3.10–3.12 64비트 설치가 필요하며, 최초 설정은 인터넷을 사용합니다.

**시작:** ZIP 전체 압축 해제 → `ONNX Export.bat` → 처음 실행 시 설정 동의 → `.pth`와 `.onnx` 저장 위치 선택.

**도플 에코에서는 RVC v1 모델을 권장합니다.** v2도 변환할 수 있지만, 게임에서 속삭임이나 특정 음역대에 가벼운 음성 왜곡이 생길 수 있습니다. 업로드 전 해당 발성까지 직접 들어보고 확인하세요. 변환 검증 성공은 게임 내 음질 보장을 의미하지 않습니다.

**RVC v1 is recommended for Doppel Echo.** v2 can also be exported, but slight audio distortion may occur with whispering or certain vocal pitch ranges in the game. Test these conditions before uploading. Passing export validation does not guarantee in-game audio quality.

- [한국어 사용 가이드](GUIDE.ko.md)
- [English guide](GUIDE.en.md)
- [Third party notices](THIRD_PARTY_NOTICES.md)

이 도구는 모델 변환만 수행하며 Steam 로그인이나 창작마당 업로드 기능은 포함하지 않습니다. 원본 모델은 수정하지 않고, 검증 성공 후에만 출력을 저장합니다.

## 변환 가능한 모델과 게임 권장 버전

일반 RVC v1/v2, f0 포함, 32/40/48kHz의 추론용 `.pth`입니다. 학습 체크포인트, non-f0, 다른 `params` 형식, 기존 ONNX는 지원하지 않습니다. `.index`는 변환에 사용하지 않습니다.

CPU FP32, opset 17로 내보내며 입력 규격과 32/64/97 프레임 추론을 검증합니다. 게임에서의 실제 음질과 GPU 실행은 별도로 확인해야 합니다.
