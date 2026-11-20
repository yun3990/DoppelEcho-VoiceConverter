# 변환기 배포 관리

## 배포 파일 만들기

이 저장소 루트에서 다음 명령을 실행합니다. 패키징에는 표준 Python만 필요합니다.

```powershell
python ./build_release.py
```

`dist/DoppelEcho-VoiceModelConverter-버전-Windows.zip`과 SHA-256 파일을 만듭니다. 포함 목록을 명시했으므로 테스트 모델, 로그, `.deps`, `.venv`, 캐시, 로컬 개발 경로 및 게임 소스는 배포하지 않습니다. w-okada 소스는 `SOURCE_MANIFEST.json`과 일치하는지 확인한 뒤 포함합니다.

변환기 버전은 `VERSION.txt`에서 관리합니다. 이 ZIP과 SHA-256 파일을 배포 페이지에 올리고, `GUIDE.ko.md` 또는 `GUIDE.en.md`의 내용을 제작 가이드로 제공합니다. 외부 게시와 창작마당 업로드는 이 스크립트가 수행하지 않습니다.

## 검증

깨끗한 위치에 ZIP을 압축 해제하여 `Setup.bat`으로 설치하고, 배포본만으로 변환되는지 확인합니다. 자동 설치 검증에서는 다음과 같이 Python 경로를 지정할 수 있습니다.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Setup-Exporter.ps1 -PythonPath 'C:\Python312\python.exe'
& '.\.venv\Scripts\python.exe' -I '.\check_runtime.py'
& '.\.venv\Scripts\python.exe' -I '.\export_rvc.py' 'D:\Models\voice.pth' 'D:\Models\voice.onnx'
```

원본 도구 폴더에서는 아래 계약 테스트도 실행합니다.

```powershell
& './.venv/Scripts/python.exe' -I './test_exporter.py'
```

실제 모델 변환 결과의 `SUCCESS`와 세 가지 프레임 검사 결과를 확인합니다. 사용자 모델의 실제 음질, CUDA/DirectML, 창작마당 등록과 구독은 별도 검증 범위입니다. 배포용 파일에 테스트 모델을 포함하지 마세요.

## 소스 구성

`export_rvc.py`는 기존 변환 방식과 메타데이터를 유지합니다. 기본 소스 경로를 동봉한 `ThirdParty/wokada`로 바꾸고, 전용 CPU 환경에서 실행합니다. 이전 개발 흐름의 `--voice-root`는 선택 옵션으로 남겨두었습니다.

w-okada 파일 7개와 원본 라이선스 2개만 동봉합니다. 라이선스와 해시는 함께 보존하세요. 소스 파일을 의도적으로 교체했다면 검토와 검증을 마친 뒤 manifest도 갱신해야 합니다.

초기 의존성은 torch 2.6.0+cpu, numpy 1.26.4, onnx 1.17.0, onnxruntime 1.23.0입니다. `weights_only=True`를 유지하고 기존 ONNX export 경로를 명시적으로 사용합니다. 버전 변경 시 `requirements.txt`, `Setup-Exporter.ps1`, `check_runtime.py`를 함께 수정하고 실제 변환을 다시 확인하세요.
