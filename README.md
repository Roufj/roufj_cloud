# Game Publishing | Business Intelligence — GitHub Pages edition

이 프로젝트는 사용자가 제공한 Streamlit v5 시뮬레이션 포트폴리오를 HTML/CSS/JavaScript 기반 정적 대시보드로 변환한 배포용 버전입니다. 원본의 합성 CSV 7개를 그대로 사용합니다.

## 배포

1. GitHub 저장소에 별도 브랜치(예: `pages-portfolio`)를 생성합니다.
2. **ZIP 안의 파일과 `data` 폴더를 브랜치 루트에** 업로드합니다 (`index.html`이 루트에 있어야 합니다).
3. Repository → Settings → Pages → Build and deployment → Deploy from a branch → `pages-portfolio` / `/(root)` → Save.
4. 몇 분 후 `https://roufj.github.io/roufj_cloud/`와 같은 URL에서 확인합니다. 실제 URL은 Pages 설정 화면을 따릅니다.

## 기술 구성

- GitHub Pages 정적 호스팅. 서버 Python, Streamlit 런타임 없음.
- 원본 CSV 7개를 브라우저에서 읽고 JavaScript로 계산.
- Plotly.js 2.35.2 CDN 의존 (외부 네트워크 필요).
- 합성 데이터만 포함, 실제 게임 API/AI API 연결 없음.

## 검증 및 유의사항

- 정적 웹 버전은 원본 Streamlit의 계산·차트·다운로드 동작을 재구현한 **별도 구현**입니다. 실제 배포 후 원본과 수치를 비교 검증해야 합니다.
- 브라우저의 `file://`로 `index.html`을 열면 CSV fetch 보안 제한으로 동작하지 않을 수 있습니다. GitHub Pages 또는 로컬 HTTP 서버로 테스트하세요.
- 날짜 필터는 CSV 유입일/일자 기준, 월별 정산은 포함 월 전체 기준입니다.
- 전체 기간의 유입일별 리텐션 히트맵은 최신 90일만 보여줍니다.
- Python Streamlit의 외형과 일부 세부 시각 효과는 완전히 동일하지 않습니다.


## v6 테스트 확장 (2026-11-04)
- 기존 7개 메뉴 유지, BM·상품 성과 분석 / 유저 구성·가치 분석 2개 추가 (총 9개).
- 신규 CSV: iap_product_master, iap_product_daily, user_segment_daily, user_cohort_ltv.
- 원본 7개 CSV 변경 없음. 신규 상품 일별 IAP 합계는 원본 daily.csv IAP와 일치.
- 사용자 그룹은 일별 가상 활동 인원으로 월별 고유 유저 집계가 아닙니다.
- 코호트 LTV는 별도 가상 모델로 생성되어 상품 매출과 개인별 거래 단위로 연결되지 않습니다.
- GitHub Pages 배포용: ZIP 내부 파일을 브랜치 루트에 업로드. 공개 브랜치에 덮어쓰기 전 별도 테스트 브랜치 검증 권장.


## v6 검수 개선판
- BM: 상품별 매출 증감액, 프로젝트 전체 대비 상대 성과, 우선 분석 후보, 종합 진단, 운영 이력 전후 7일 비교
- 유저: 유입일별 고정 코호트 D1/D7/D14/D30 리텐션 및 별도 합성 LTV, 유입 채널, 이력 연계, 분석 의견
- 표시: ▲▼ 증감 방향, KPI 비교 기간 표기 및 한국어 단위 유지
- 주의: 유저별 거래 원장이 없어 관측 LTV는 상품별 매출과 직접 연결된 수치가 아니며, 결제 전환율은 산출하지 않습니다.
- 기존 공개 저장소는 수정하지 마세요. 테스트 저장소에 먼저 업로드해 검수하세요.
