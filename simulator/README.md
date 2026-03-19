# Simulator

Python 기반 가상 차량 TCP 클라이언트다. Gateway의 `newline-delimited JSON` 입력 계약에 맞춰 `HELLO` 메시지를 보내고, 각 전송 뒤에 gateway가 반환하는 `OK`, `ERR`, `IGNORED`를 읽어 출력한다.

다중 차량 모드에서는 차량별로 별도 TCP 연결을 열고 동시에 전송한다.

## Requirements

- `python3`

현재 작업 환경에서는 `Python 3.14.3`가 확인됐다.

## Usage

1회 HELLO 전송:

```bash
python3 simulator/send_hello.py \
  --host 127.0.0.1 \
  --port 9000 \
  --vehicle-id VHC-001 \
  --firmware-version 1.0.0
```

5회 반복 전송:

```bash
python3 simulator/send_hello.py \
  --host 127.0.0.1 \
  --port 9000 \
  --vehicle-id VHC-001 \
  --firmware-version 1.0.0 \
  --count 5 \
  --interval 1
```

차량이 켜져 있는 동안 1초마다 계속 전송:

```bash
/usr/bin/python3 simulator/send_hello.py \
  --host 172.30.1.184 \
  --port 9000 \
  --vehicle-id VHC-001 \
  --firmware-version 1.0.0 \
  --forever \
  --interval 1
```

중지는 `Ctrl+C`로 한다.

15대 차량이 동시에 1초마다 계속 전송:

```bash
/usr/bin/python3 simulator/send_hello.py \
  --host 172.30.1.184 \
  --port 9000 \
  --vehicle-id VHC \
  --vehicle-count 15 \
  --firmware-version 1.0.0 \
  --forever \
  --interval 1
```

이 경우 vehicle ID는 `VHC-001`부터 `VHC-015`까지 자동 생성된다.

접두어를 별도로 주고 싶으면 `--vehicle-id-prefix CAR` 같은 옵션을 추가하면 된다.

고정 timestamp 사용:

```bash
python3 simulator/send_hello.py \
  --vehicle-id VHC-001 \
  --firmware-version 1.0.0 \
  --timestamp 2026-03-19T10:00:00+09:00
```

## Expected Output

성공 예시:

```text
[1/1] SEND vehicle_id=VHC-001 firmware_version=1.0.0 timestamp=2026-03-19T10:00:00+09:00
[1/1] ACK OK
```

실패 예시:

```text
[1/1] SEND vehicle_id=VHC-001 firmware_version=1.0.0 timestamp=2026-03-19T10:00:00+09:00
[1/1] ACK ERR
gateway returned non-success ACK: ERR
```

비정상 ACK, 빈 응답, 타임아웃, 연결 실패는 모두 non-zero 종료 코드로 처리한다.

## Dev Workflow

docker compose dev 환경이 떠 있다면 기본 TCP endpoint는 호스트 기준 `127.0.0.1:9000`이다.

```bash
npm run dc:dev:up:build
python3 simulator/send_hello.py \
  --vehicle-id VHC-001 \
  --firmware-version 1.0.0
```

전송 후에는 backend 또는 DB에서 `hello_messages` insert 여부를 확인하면 된다.

## Remote Windows/WSL Target

Gateway가 외부 Windows 노트북의 Ubuntu/WSL 안 Docker에서 실행 중이어도 같은 Wi-Fi에 있다면 접속할 수 있다.

- Windows Wi-Fi IP를 확인한다. 예: `172.30.1.184`
- WSL 안 Docker gateway가 `0.0.0.0:9000->9000/tcp`로 publish 되어 있어야 한다.
- 필요하면 Windows 방화벽에서 TCP `9000` inbound를 허용한다.
- WSL만 쓰는 구조라면 Windows `portproxy`로 `Wi-Fi IP:9000 -> WSL:9000` 전달이 필요할 수 있다.

원격 타깃 전송 예시:

```bash
/usr/bin/python3 simulator/send_hello.py \
  --host 172.30.1.184 \
  --port 9000 \
  --vehicle-id VHC-001 \
  --firmware-version 1.0.0
```

원격 타깃에 1초 주기 지속 송신:

```bash
/usr/bin/python3 simulator/send_hello.py \
  --host 172.30.1.184 \
  --port 9000 \
  --vehicle-id VHC-001 \
  --firmware-version 1.0.0 \
  --forever \
  --interval 1
```

원격 타깃에 15대 동시 지속 송신:

```bash
/usr/bin/python3 simulator/send_hello.py \
  --host 172.30.1.184 \
  --port 9000 \
  --vehicle-id VHC \
  --vehicle-count 15 \
  --firmware-version 1.0.0 \
  --forever \
  --interval 1
```

접속 확인:

```bash
nc -vz 172.30.1.184 9000
printf '{"type":"HELLO","vehicle_id":"VHC-001","firmware_version":"1.0.0","timestamp":"2026-03-19T12:00:00+09:00"}\n' | nc -w 3 172.30.1.184 9000
```

정상이면 두 번째 명령에서 `OK` 응답이 돌아온다.

## macOS Note

현재 확인된 환경에서는 Homebrew Python (`python3`)이 원격 `172.30.1.184:9000` 접속 시 `No route to host`를 반환했고, 시스템 Python (`/usr/bin/python3`)은 정상 동작했다.

따라서 macOS에서 원격 Windows/WSL gateway로 테스트할 때는 우선 아래 형태를 권장한다.

```bash
/usr/bin/python3 simulator/send_hello.py \
  --host 172.30.1.184 \
  --port 9000 \
  --vehicle-id VHC-001 \
  --firmware-version 1.0.0
```
