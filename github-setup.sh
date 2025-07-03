#!/bin/bash

# GitHubリポジトリのURLを設定
echo "GitHubのユーザー名を入力してください："
read GITHUB_USERNAME

GITHUB_URL="https://github.com/$GITHUB_USERNAME/japan-castles.git"

echo "GitHubリポジトリをリモートに追加します..."
echo "URL: $GITHUB_URL"
git remote add origin $GITHUB_URL

echo "現在のブランチ名を確認..."
git branch

echo "mainブランチにプッシュします..."
git push -u origin main

echo "完了！GitHubでリポジトリを確認してください。"
echo "URL: https://github.com/$GITHUB_USERNAME/japan-castles"