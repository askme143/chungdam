#!/bin/bash
# EC2 서버에서 파이프라인 결과(문장별 JSON + 페이지 HTML + index.html)를 다운로드한다.
#
# 사용법:
#   ./download_results.sh                     # 전체 결과 다운로드
#   ./download_results.sh 고3_2026_11월_수능   # 특정 시험만 다운로드
#   ./download_results.sh --status            # 진행 상태만 확인

set -euo pipefail

SSH_KEY=~/.ssh/my-ec2-keypair.pem
SSH_USER=ec2-user
REMOTE_DIR=/home/ec2-user/chungdam
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ -z "${SSH_DOMAIN:-}" ]]; then
    echo "❌ SSH_DOMAIN 환경변수가 설정되지 않았습니다."
    echo "   export SSH_DOMAIN=ec2-xx-xx-xx-xx.ap-northeast-2.compute.amazonaws.com"
    exit 1
fi

SSH_CMD="ssh -i $SSH_KEY $SSH_USER@$SSH_DOMAIN"

# --status: 진행 상태만 확인
if [[ "${1:-}" == "--status" ]]; then
    echo "📋 파이프라인 상태:"
    $SSH_CMD "tmux list-sessions 2>/dev/null || echo '(tmux 세션 없음)'; echo '---'; tail -20 ~/pipeline.log 2>/dev/null || echo '(로그 없음)'"
    exit 0
fi

EXAM="${1:-}"

if [[ -n "$EXAM" ]]; then
    # 특정 시험만 다운로드
    echo "📥 $EXAM 결과 다운로드 중..."
    rsync -avz --include='*/' --include='*.json' --include='*.html' --exclude='*' \
        -e "ssh -i $SSH_KEY" \
        "$SSH_USER@$SSH_DOMAIN:$REMOTE_DIR/$EXAM/" \
        "$LOCAL_DIR/$EXAM/"
else
    # 전체 결과 다운로드 (문장별, 페이지 폴더 + index.html)
    echo "📥 전체 결과 다운로드 중..."
    rsync -avz --include='*/' --include='*.json' --include='*.html' --exclude='*' \
        -e "ssh -i $SSH_KEY" \
        "$SSH_USER@$SSH_DOMAIN:$REMOTE_DIR/" \
        "$LOCAL_DIR/" \
        --exclude='.git' --exclude='.venv' --exclude='__pycache__'
fi

echo "✅ 다운로드 완료!"
