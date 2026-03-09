dev 계열

dc:dev:up
docker-compose.dev.yml로 컨테이너를 실행합니다. 기존 이미지 기준으로 올립니다.

dc:dev:up:build
개발 중 코드 변경이 있을 때 이미지를 다시 빌드하고 실행합니다. 가장 자주 쓰게 될 명령입니다.

dc:dev:down
dev 환경 컨테이너와 네트워크를 내립니다.

dc:dev:down:volumes
dev 환경을 내리면서 volume까지 삭제합니다.
Postgres 데이터도 지워지므로 초기화가 필요할 때만 써야 합니다.

dc:dev:restart
dev 환경을 내렸다가 다시 빌드해서 올립니다.

dc:dev:logs
dev 전체 로그를 실시간으로 봅니다.

dc:dev:ps
dev 환경 컨테이너 상태를 확인합니다.

dc:dev:backend:logs
backend 로그만 봅니다.

dc:dev:gateway:logs
gateway 로그만 봅니다.

dc:dev:db:logs
postgres 로그만 봅니다.

prod 계열

dc:prod:pull
운영용 이미지들을 registry에서 pull 합니다.

dc:prod:up
.env를 읽어 운영용 compose를 백그라운드로 실행합니다.

dc:prod:up:build
prod 파일 기준으로 빌드 후 실행하는 명령인데, 운영에서는 보통 잘 안 씁니다.
prod는 원칙적으로 image pull 방식이므로 참고용/임시용입니다.

dc:prod:down
운영용 컨테이너를 내립니다.

dc:prod:restart
운영 환경을 재시작합니다.

dc:prod:up:pull
최신 이미지 pull 후 바로 운영 환경을 다시 올립니다.
나중에 서버에서 가장 자주 쓰게 될 배포 명령 후보입니다.

dc:prod:logs
운영 전체 로그를 실시간으로 봅니다.

dc:prod:ps
운영 컨테이너 상태를 확인합니다.

dc:prod:backend:logs
운영 backend 로그만 봅니다.

dc:prod:gateway:logs
운영 gateway 로그만 봅니다.

dc:prod:db:logs
운영 postgres 로그만 봅니다.