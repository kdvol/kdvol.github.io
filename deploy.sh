#!/bin/bash
# deploy.sh — 순살브리핑 letters.soonsal.com 배포 스크립트
# 사용법: ./deploy.sh 0228 2026

DATE=${1:?날짜 입력 필요 (예: 0228)}
YEAR=${2:-2026}

echo "📦 배포 시작: ${YEAR}/${DATE}"

# 디렉토리 생성
mkdir -p newsletters/${YEAR}
mkdir -p cardnews/${YEAR}
mkdir -p english/${YEAR}

# 파일 복사
echo "  📰 뉴스레터..."
cp "순살브리핑_${YEAR}${DATE}.html"           "newsletters/${YEAR}/${DATE}.html"
cp "순살크립토_${YEAR}${DATE}.html"           "newsletters/${YEAR}/${DATE}-crypto.html"

echo "  🎴 카드뉴스..."
cp "순살카드뉴스_${YEAR}${DATE}.html"         "cardnews/${YEAR}/${DATE}.html"
cp "순살크립토카드뉴스_${YEAR}${DATE}.html"    "cardnews/${YEAR}/${DATE}-crypto.html"

echo "  🌏 English..."
cp "SoonsalCrypto_${YEAR}${DATE}_Publish.html" "english/${YEAR}/${DATE}.html"

# _redirects에 새 날짜 추가
cat >> _redirects << EOF

/${YEAR}/${DATE}/              /newsletters/${YEAR}/${DATE}.html      301
/${YEAR}/${DATE}/index.html    /newsletters/${YEAR}/${DATE}.html      301
/${YEAR}/${DATE}/crypto.html   /newsletters/${YEAR}/${DATE}-crypto.html 301
/${YEAR}/${DATE}/publish.html  /english/${YEAR}/${DATE}.html          301
EOF

echo ""
echo "✅ 파일 배치 완료. 남은 작업:"
echo "   1. index.html에 날짜 항목 추가"
echo "   2. newsletters/index.html에 날짜 항목 추가"
echo "   3. cardnews/index.html에 날짜 항목 추가"
echo "   4. english/index.html에 날짜 항목 추가"
echo "   5. git add . && git commit -m 'Add ${YEAR}/${DATE}' && git push"
