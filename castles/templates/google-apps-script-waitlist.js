/**
 * デジタル城下町ウェイトリスト管理
 * Google Apps Script + Google Sheets
 */

// スプレッドシートID（作成後に変更してください）
const SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID';

// メール設定
const EMAIL_CONFIG = {
  fromName: 'デジタル城下町プロジェクト',
  fromEmail: 'noreply@jkrs.jp', // 実際のメールアドレスに変更
  subject: '【${castle}】デジタル城下町民ウェイトリスト登録完了'
};

/**
 * POSTリクエストを処理（ウェイトリスト登録）
 */
function doPost(e) {
  try {
    // CORSヘッダーを設定
    const output = ContentService.createTextOutput();
    output.setMimeType(ContentService.MimeType.JSON);
    
    // データを解析
    const data = JSON.parse(e.postData.contents);
    
    // バリデーション
    if (!data.email || !data.castle) {
      return output.setContent(JSON.stringify({
        success: false,
        error: 'メールアドレスとお城名は必須です'
      }));
    }
    
    // 重複チェック
    const isDuplicate = checkDuplicate(data.email, data.castle_id);
    if (isDuplicate) {
      return output.setContent(JSON.stringify({
        success: false,
        error: 'このお城のウェイトリストに既に登録済みです'
      }));
    }
    
    // スプレッドシートに保存
    const success = saveToSheet(data);
    if (!success) {
      throw new Error('データの保存に失敗しました');
    }
    
    // 確認メールを送信
    sendConfirmationEmail(data);
    
    // 管理者に通知（オプション）
    notifyAdmin(data);
    
    return output.setContent(JSON.stringify({
      success: true,
      message: '登録が完了しました'
    }));
    
  } catch (error) {
    console.error('Error:', error);
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        error: error.toString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * スプレッドシートにデータを保存
 */
function saveToSheet(data) {
  try {
    const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getActiveSheet();
    
    // ヘッダーが存在しない場合は作成
    if (sheet.getLastRow() === 0) {
      sheet.appendRow([
        '登録日時',
        'メールアドレス',
        '名前',
        'お城名',
        'お城ID',
        '都道府県',
        'お城種別',
        'お城分類',
        'ニュースレター',
        'ソース',
        'ページURL',
        'ユーザーエージェント',
        'ステータス'
      ]);
    }
    
    // データを追加
    sheet.appendRow([
      new Date(data.timestamp),
      data.email,
      data.name || '',
      data.castle,
      data.castle_id,
      data.prefecture,
      data.castle_type,
      data.castle_category,
      data.newsletter ? 'はい' : 'いいえ',
      data.source,
      data.page_url,
      data.user_agent,
      'アクティブ'
    ]);
    
    return true;
  } catch (error) {
    console.error('Sheet save error:', error);
    return false;
  }
}

/**
 * 重複チェック
 */
function checkDuplicate(email, castleId) {
  try {
    const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getActiveSheet();
    const data = sheet.getDataRange().getValues();
    
    // ヘッダー行をスキップして検索
    for (let i = 1; i < data.length; i++) {
      const rowEmail = data[i][1]; // B列（メールアドレス）
      const rowCastleId = data[i][4]; // E列（お城ID）
      
      if (rowEmail === email && rowCastleId === castleId) {
        return true;
      }
    }
    
    return false;
  } catch (error) {
    console.error('Duplicate check error:', error);
    return false;
  }
}

/**
 * 確認メールを送信
 */
function sendConfirmationEmail(data) {
  try {
    const subject = EMAIL_CONFIG.subject.replace('${castle}', data.castle);
    
    const htmlBody = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Hiragino Sans', 'Hiragino Kaku Gothic ProN', Meiryo, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #3498db 0%, #2ecc71 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .castle-info { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #666; }
        .button { display: inline-block; background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏯 ウェイトリスト登録完了</h1>
            <p>ありがとうございます！</p>
        </div>
        <div class="content">
            <p>こんにちは${data.name ? '、' + data.name + 'さん' : ''}！</p>
            
            <p><strong>${data.castle}</strong>のデジタル城下町民ウェイトリストにご登録いただき、ありがとうございます。</p>
            
            <div class="castle-info">
                <h3>📍 登録内容</h3>
                <ul>
                    <li><strong>お城：</strong>${data.castle}（${data.prefecture}）</li>
                    <li><strong>種別：</strong>${data.castle_type}</li>
                    <li><strong>分類：</strong>${data.castle_category}</li>
                    <li><strong>ニュースレター：</strong>${data.newsletter ? '配信希望' : '配信希望なし'}</li>
                </ul>
            </div>
            
            <h3>🎁 ウェイトリスト登録特典</h3>
            <ul>
                <li>${data.castle}デジタル城下町民の優先取得権</li>
                <li>限定コンテンツへのアクセス</li>
                <li>お城ファンコミュニティでの交流</li>
                <li>自動登城記録機能</li>
            </ul>
            
            <p style="text-align: center;">
                <a href="https://note.com/digitaljokers/n/n2a93cd7365e1" class="button">
                    📖 デジタル城下町について詳しく見る
                </a>
            </p>
            
            <h3>📱 公式SNSもフォローしてください</h3>
            <p>
                <a href="https://line.me/R/ti/p/@172rjlow">LINE公式アカウント</a> | 
                <a href="https://x.com/digitaljokers">X (Twitter)</a> | 
                <a href="https://note.com/digitaljokers">note</a>
            </p>
        </div>
        <div class="footer">
            <p>このメールは自動送信です。</p>
            <p>デジタル城下町プロジェクト | <a href="https://jkrs.jp">https://jkrs.jp</a></p>
        </div>
    </div>
</body>
</html>
    `;
    
    GmailApp.sendEmail(
      data.email,
      subject,
      '', // プレーンテキスト版（空でも可）
      {
        htmlBody: htmlBody,
        name: EMAIL_CONFIG.fromName
      }
    );
    
    console.log(`確認メール送信完了: ${data.email}`);
    
  } catch (error) {
    console.error('Email sending error:', error);
  }
}

/**
 * 管理者に通知
 */
function notifyAdmin(data) {
  try {
    const adminEmail = 'admin@jkrs.jp'; // 管理者メールアドレス
    const subject = `【新規登録】${data.castle} - ${data.email}`;
    
    const body = `
新しいウェイトリスト登録がありました。

お城: ${data.castle}
メール: ${data.email}
名前: ${data.name || '未入力'}
都道府県: ${data.prefecture}
登録日時: ${new Date(data.timestamp).toLocaleString('ja-JP')}
ニュースレター: ${data.newsletter ? 'はい' : 'いいえ'}

管理画面: https://docs.google.com/spreadsheets/d/${SPREADSHEET_ID}
    `;
    
    GmailApp.sendEmail(adminEmail, subject, body);
    
  } catch (error) {
    console.error('Admin notification error:', error);
  }
}

/**
 * 統計情報を取得（管理用）
 */
function getWaitlistStats() {
  try {
    const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getActiveSheet();
    const data = sheet.getDataRange().getValues();
    
    if (data.length <= 1) {
      return { total: 0, byCastle: {}, byPrefecture: {} };
    }
    
    const stats = {
      total: data.length - 1, // ヘッダーを除く
      byCastle: {},
      byPrefecture: {},
      byDate: {}
    };
    
    // ヘッダー行をスキップして集計
    for (let i = 1; i < data.length; i++) {
      const castle = data[i][3]; // お城名
      const prefecture = data[i][5]; // 都道府県
      const date = new Date(data[i][0]).toDateString(); // 登録日
      
      // お城別
      stats.byCastle[castle] = (stats.byCastle[castle] || 0) + 1;
      
      // 都道府県別
      stats.byPrefecture[prefecture] = (stats.byPrefecture[prefecture] || 0) + 1;
      
      // 日別
      stats.byDate[date] = (stats.byDate[date] || 0) + 1;
    }
    
    return stats;
    
  } catch (error) {
    console.error('Stats error:', error);
    return null;
  }
}

/**
 * スプレッドシートを初期化（初回実行用）
 */
function initializeSpreadsheet() {
  try {
    // 新しいスプレッドシートを作成
    const spreadsheet = SpreadsheetApp.create('デジタル城下町ウェイトリスト');
    
    console.log(`スプレッドシートが作成されました: ${spreadsheet.getId()}`);
    console.log(`URL: ${spreadsheet.getUrl()}`);
    
    // ヘッダーを設定
    const sheet = spreadsheet.getActiveSheet();
    sheet.setName('ウェイトリスト');
    
    // このスクリプトファイルの SPREADSHEET_ID を更新してください
    console.log(`SPREADSHEET_ID = '${spreadsheet.getId()}';`);
    
    return spreadsheet.getId();
    
  } catch (error) {
    console.error('Initialization error:', error);
    return null;
  }
}