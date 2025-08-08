# 1. 필수 패키지 설치
!pip install buildozer cython==0.29.19

# 2. 리눅스 의존성 설치 (Colab은 리눅스 기반)
!apt-get update
!apt-get install -y \
    python3-pip \
    build-essential \
    git \
    unzip \
    openjdk-11-jdk \
    zlib1g-dev \
    libncurses5-dev \
    libgdbm-dev \
    libnss3-dev \
    libssl-dev \
    libreadline-dev \
    libffi-dev \
    libsqlite3-dev \
    wget \
    libltdl-dev \
    libwxgtk3.0-gtk3-dev

# 3. Android SDK 설치
!mkdir -p /content/android
!wget -q https://dl.google.com/android/repository/commandlinetools-linux-8512546_latest.zip -O /content/android/cmdline-tools.zip
!unzip -q /content/android/cmdline-tools.zip -d /content/android/cmdline-tools
!mv /content/android/cmdline-tools/cmdline-tools /content/android/cmdline-tools/latest

# 4. 환경 변수 설정
import os
os.environ['PATH'] += os.pathsep + '/content/android/cmdline-tools/latest/bin'
os.environ['ANDROID_HOME'] = '/content/android'
os.environ['ANDROID_SDK_ROOT'] = '/content/android'

# 5. Android SDK 구성
!yes | /content/android/cmdline-tools/latest/bin/sdkmanager --licenses
!sdkmanager "platform-tools" "platforms;android-29" "build-tools;30.0.3" "ndk;21.4.7075529"

# 6. 프로젝트 설정
%cd /content
!git clone https://github.com/your-repo/your-kivy-app.git
%cd /content/your-kivy-app

# 7. buildozer.spec 파일 생성 (기존 파일이 없다면)
!buildozer init

# 8. buildozer.spec 수정 (필요시)
print("""
[app]
title = MyKivyApp
package.name = mykivyapp
package.domain = org.test
source.dir = .
version = 0.1
requirements = python3,kivy==2.1.0
orientation = portrait
osx.python_version = 3
osx.kivy_version = 2.1.0
android.api = 29
android.minapi = 21
android.sdk = 29
android.ndk = 21.4.7075529
""", file=open("buildozer.spec", "w"))

# 9. APK 빌드 실행
!buildozer -v android debug

# 10. 빌드 완료 후 APK 다운로드
from google.colab import files
files.download('/content/your-kivy-app/bin/*.apk')
