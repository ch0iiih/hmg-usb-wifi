# HMG USB Wi-Fi

[English](README.md) | **한국어**

HMG-API용 Archer T3U Nano USB Wi-Fi 드라이버와 외부 Wi-Fi 접속 진단 모드입니다.

## 다운로드

[릴리즈 페이지](https://github.com/ch0iiih/hmg-usb-wifi/releases)에서 설치 ZIP을 받을 수 있습니다.

- [USB Wi-Fi Driver 0.1.6](dist/usb-wifi-rtl8822bu-0.1.6.zip)
- [Wi-Fi Client Test 0.1.4](dist/wifi-client-test-0.1.4.zip)

## 주요 기능

- Archer T3U Nano 드라이버 및 순정 Wi-Fi HAL 연동.
- USB·네트워크 연결 이벤트 감지와 제한된 초기화 재시도.
- 어댑터 분리·서비스 종료 시 기존 USB 전원 제어 상태 복원.
- USB로 드라이버·커널·프레임워크 진단 로그 내보내기.
- HMG-API의 원본 드라이버 검사와 백업 파일 복원.
- Client Test에서 Wi-Fi 설정 기능 유지, 실제 인터페이스 준비 확인 및 USB 액세서리 전환 방지.

## 호환성 및 현재 상태

- HMG-API 1.0.2 이상, 한국형(KOR) 시스템을 대상으로 합니다.
- 확인한 어댑터는 TP-Link Archer T3U Nano, USB ID `2357:012e`, RTL8822BU 계열입니다. 같은 제품명이어도 하드웨어 리비전에 따라 USB ID나 칩셋이 다를 수 있습니다.
- 실차 확인 환경은 국내 팰리세이드 LX2 PE, 펌웨어 `260902`입니다. 별도 무선 프로젝션 모드와 함께 무선 CarPlay 연결을 확인했습니다.
- **차종 및 펌웨어 날짜 필터는 없습니다. 다른 차량이나 다른 펌웨어에서의 동작을 보장하지 않습니다.** 지역 필터는 KOR로 유지합니다.
- 드라이버 교체 시 HMG-API가 기존 `/system/wifi/bcmdhd.ko`의 기준 MD5 `ac5bff41f934c996eff5208dbcd9550f`를 검사합니다. 다른 원본 파일이면 교체를 거부합니다. 이 검사는 전체 커널 ABI 검증을 대신하지 않습니다.
- 이 모듈은 캡처한 ARMv7 `3.18.24-tcc` 커널 설정을 기준으로 빌드했습니다. 같은 드라이버 파일을 사용하더라도 커널과 플랫폼이 다른 경우 추가 검증이 필요합니다.
- **외부 Wi-Fi 검색·접속은 아직 실차에서 성공을 확인하지 못했습니다.** Client Test는 진단용입니다. 이 저장소에는 AP/클라이언트 자동 전환이나 무선 프로젝션 기능 자체가 포함되지 않습니다.
- Client Test의 USB 액세서리 방지 훅은 대상 펌웨어에 맞는 HMG-API hook map이 필요합니다. 설치 필터 해제만으로 hook map이 생기지는 않습니다.

## 설치

1. 기존 NEMESIS USB WiFi Hotspot Enabler를 사용 중이면 제거하고 헤드유닛을 재시작합니다.
2. 드라이버 ZIP을 HMG-API에서 설치하고 활성화한 뒤 Apply changes → Restart Unit을 실행합니다.
3. USB ADB를 끄고 T3U Nano를 연결합니다. 무선 CarPlay에는 별도의 호환 프로젝션 모드와 설정이 필요합니다.
4. 외부 Wi-Fi 접속을 시험할 때만 Client Test도 설치합니다. Wireless Phone Projection과 Wireless CarPlay + Android Auto를 비활성화하고 Client Test를 활성화한 뒤 Apply changes → Restart Unit을 실행합니다.
5. 순정 Wi-Fi 설정에서 Wi-Fi를 직접 켜고 검색 결과를 확인합니다. 휴대폰에서 Wi-Fi를 끄는 것만으로 헤드유닛 AP가 종료되지는 않습니다.

Client Test와 무선 프로젝션 모드는 동시에 활성화할 수 없습니다. 무선 CarPlay로 돌아갈 때는 Client Test를 끄고 프로젝션 모드를 켠 뒤 적용·재시작합니다.

## 진단과 복원

USB 저장장치에 `USB-WIFI-LOGS` 폴더를 만들고 헤드유닛에 연결하면 진단을 내보냅니다. 연결 이벤트를 이용하며, 초기화와 제한된 재시도 외에는 주기적으로 USB를 검색하지 않습니다. 어댑터를 빼면 저장한 USB 전원 제어 상태를 복원합니다.

드라이버 모드를 비활성화하고 적용하면 HMG-API가 백업한 원본 드라이버를 복원합니다. 복원 후 재시작합니다.

진단에는 시스템 로그와 분석용 시스템 구성요소가 포함될 수 있습니다. 공개 이슈에 올리기 전에 기기 식별 정보 등 내용을 검토하세요. 개인 차량 로그나 OEM 바이너리는 이 저장소에 포함하지 않았습니다.

## 소스와 빌드

`packages/`에는 패키지 파일, `event-monitor/`에는 이벤트 모니터와 상태 서비스, `client-hooks/`에는 USB 액세서리 방지 훅이 있습니다. `driver-build/`에는 원본 드라이버 소스 아카이브, 수정 패치, 커널 설정과 빌드 절차가 있습니다. [BUILD.md](BUILD.md)를 참고하세요.

`dist/`의 설치 ZIP은 서명된 배포 파일입니다. `packages/`의 파일을 변경한 경우 자신의 HMG-API 작성자 키로 다시 서명해야 합니다. 개인 서명 키는 포함하지 않았습니다.

## 출처와 라이선스

- Realtek 드라이버 및 수정 패치: GPL-2.0. [morrownr/88x2bu-20210702](https://github.com/morrownr/88x2bu-20210702), commit `418d71cc00cd18b4a671f8c49ecce9b19cbfd3c9`.
- 커널 빌드 기반: [C457/android_kernel_telechips_tcc897x](https://github.com/C457/android_kernel_telechips_tcc897x), commit `3402d473aed6a2b82c5d08e0ceafc4a54701a4a0`.
- USB/HAL 통합 참고: dibble9012의 [HMG-API PR #104](https://github.com/Open-HMG/HMG-API/pull/104).
- 이 저장소의 Java 서비스·훅 및 호스트 도구: AGPL-3.0. 드라이버 소스의 기존 라이선스와 저작권 표시는 유지합니다. 라이선스 전문은 `LICENSES/`에 있습니다.

## 변경 내역

- Driver 0.1.6 / Client Test 0.1.4: 펌웨어 날짜 필터 제거. KOR 지역 조건과 기존 드라이버 검사 유지.
- Driver 0.1.5 / Client Test 0.1.3: 차종 필터 제거.
- Driver 0.1.4: 연결된 T3U가 드라이버에 바인딩되지 않은 경우에만 제한적으로 재시도.
- Client Test 0.1.2: T3U에 대한 Android Auto 액세서리 전환 요청 차단 훅 추가. 검색 실패 개선 여부는 추가 실차 검증 필요.
