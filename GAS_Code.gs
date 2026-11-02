// ================================================================
//  MuBig_UI 인증 서버 — Google Apps Script
//
//  스프레드시트 구조 (시트명: config)
//  ┌─────────────────┬──────────────────────────────────────┐
//  │ A열 (키)        │ B열 (값)                             │
//  ├─────────────────┼──────────────────────────────────────┤
//  │ password        │ mb26310                              │
//  │ retail          │ https://drive.google.com/...         │
//  │ classic         │ https://drive.google.com/...         │
//  │ anniversary     │ https://drive.google.com/...         │
//  │ classic_era     │ https://drive.google.com/...         │
//  └─────────────────┴──────────────────────────────────────┘
//
//  관리 방법:
//    암호 변경 → B2 셀 값만 수정 → 즉시 반영
//    링크 변경 → 해당 행 B열 값 수정 → 즉시 반영
// ================================================================

const SHEET_NAME = 'config';

function doPost(e) {
  try {
    const data   = JSON.parse(e.postData.contents);
    const action = (data.action || 'verify').trim();

    if (action === 'verify') {
      return handleVerify(data.code || '');
    }
    if (action === 'downloads') {
      return handleDownloads();
    }
    return respond({ valid: false, message: '알 수 없는 요청' });

  } catch (err) {
    return respond({ valid: false, message: '서버 오류: ' + err.message });
  }
}

function doGet(e) {
  return respond({ valid: true, message: 'MuBig_UI Auth Server OK' });
}

// ── 암호 검증 ────────────────────────────────────────────────────
function handleVerify(code) {
  code = String(code).trim();
  if (!code) {
    return respond({ valid: false, message: '코드를 입력해주세요.' });
  }

  const config = getConfig();
  const stored = String(config['password'] || '').trim();

  if (!stored) {
    return respond({ valid: false, message: '서버 설정 오류 (암호 미설정)' });
  }

  if (code === stored) {
    return respond({ valid: true, message: '인증 성공' });
  }
  return respond({ valid: false, message: '암호가 올바르지 않습니다.' });
}

// ── 다운로드 링크 반환 ────────────────────────────────────────────
function handleDownloads() {
  const config = getConfig();
  return respond({
    valid: true,
    downloads: {
      retail:      config['retail']      || '',
      classic:     config['classic']     || '',
      anniversary: config['anniversary'] || '',
      classic_era: config['classic_era'] || '',
    }
  });
}

// ── 스프레드시트에서 config 읽기 ─────────────────────────────────
function getConfig() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet()
                              .getSheetByName(SHEET_NAME);
  if (!sheet) return {};

  const rows   = sheet.getDataRange().getValues();
  const config = {};
  for (const row of rows) {
    const key = String(row[0]).trim();
    const val = String(row[1]).trim();
    if (key) config[key] = val;
  }
  return config;
}

// ── 응답 헬퍼 ────────────────────────────────────────────────────
function respond(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
