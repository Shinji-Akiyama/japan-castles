#!/bin/bash

# デジタル城下町コンポーネント適用スクリプト
# 使用方法: ./apply-digital-jokamachi.sh <城名> <HTMLファイルパス>

if [ "$#" -ne 2 ]; then
    echo "使用方法: $0 <城名> <HTMLファイルパス>"
    echo "例: $0 '松本城' /path/to/matsumoto/index.html"
    exit 1
fi

CASTLE_NAME=$1
HTML_FILE=$2

echo "デジタル城下町コンポーネントを ${CASTLE_NAME} のページに適用します..."

# バックアップを作成
cp "$HTML_FILE" "${HTML_FILE}.backup"
echo "バックアップを作成しました: ${HTML_FILE}.backup"

# 注意: このスクリプトは基本的な例です。
# 実際の適用は、各城のページ構造に応じて手動で調整が必要です。

echo "
=== 手動での適用手順 ===
1. /castles/templates/digital-jokamachi-components.html を開く
2. 必要なコンポーネントをコピー
3. ${HTML_FILE} に貼り付け
4. [城名] を '${CASTLE_NAME}' に置換
5. パスを調整（必要に応じて）
6. フッターの著作権表記を更新

詳細は /castles/templates/castle-page-instructions.md を参照してください。
"

# 簡易的な置換例（実際の適用は手動で行うことを推奨）
# sed -i '' "s/\[城名\]/${CASTLE_NAME}/g" "$HTML_FILE"