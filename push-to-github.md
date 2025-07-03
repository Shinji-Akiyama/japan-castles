# GitHubへのプッシュ手順

## 1. リモートリポジトリを追加

```bash
# YOUR_USERNAME を自分のGitHubユーザー名に置き換えてください
git remote add origin https://github.com/YOUR_USERNAME/japan-castles.git
```

## 2. プッシュ

```bash
git push -u origin main
```

## 3. GitHub Pagesの設定（オプション）

GitHubにプッシュ後、以下の手順でWebサイトとして公開できます：

1. GitHubの`japan-castles`リポジトリページを開く
2. 「Settings」タブをクリック
3. 左メニューの「Pages」をクリック
4. 「Source」セクションで：
   - 「Deploy from a branch」を選択
   - Branch: `main`
   - Folder: `/ (root)`
   - 「Save」をクリック

数分後、以下のURLでサイトが公開されます：
`https://YOUR_USERNAME.github.io/japan-castles/`

## トラブルシューティング

### もしエラーが出た場合

1. すでにoriginが設定されている場合：
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/japan-castles.git
```

2. 認証エラーの場合：
- GitHubで Personal Access Token を作成
- Settings > Developer settings > Personal access tokens > Tokens (classic)
- 「Generate new token」でトークンを作成（repo権限を付与）
- プッシュ時にパスワードの代わりにこのトークンを使用

3. ブランチ名の問題：
```bash
# 現在のブランチ名を確認
git branch
# もしmasterブランチの場合、mainに変更
git branch -m master main
```