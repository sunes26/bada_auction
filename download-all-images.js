const { createClient } = require('@supabase/supabase-js');
const fs = require('fs');
const path = require('path');
const https = require('https');

const supabaseUrl = 'https://sfoyspfwjxtcbuykljeu.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmb3lzcGZ3anh0Y2J1eWtsamV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1NTcyOTAsImV4cCI6MjA3MjEzMzI5MH0.qxRVuhcOF-9M7_Yeb9kQfxUiYv0vkdDhLBbc42gXK0c';

const supabase = createClient(supabaseUrl, supabaseKey);

// 카테고리 매핑
const categoryIdMapping = {
  흰밥: "1", 흑미: "2", 잡곡: "3", 현미: "4", 렌틸콩현미: "5",
  채소영양: "6", 버섯영양: "7", 스팸김치: "8", 참치마요: "9", 치킨마요: "10",
  팥죽: "11", 야채죽: "12", 소고기죽: "13", 전복죽: "14", 햄: "15",
  닭: "16", 일반참치: "17", 고추참치: "18", 꽁치: "19", 고등어: "20",
  파인애플: "21", 황도: "22", 후르츠칵테일: "23", 스위트콘: "24", 카레: "25",
  짜장: "26", 마파두부: "27", 곰탕류: "28", 미역국: "29", 육개장: "30",
  청국장: "31", 추어탕: "32", 삼계탕: "33", 무국: "34", 황태국: "35",
  갈비탕: "36", 순두부찌개: "37", 부대찌개: "38", 버섯류: "39", 옥수수류: "40",
  라면: "41", 짜파게티: "42", 비빔면: "43", 칼국수: "44", 물냉면: "45",
  비빔냉면: "46", 소바: "47", 우동: "48", 고기만두: "49", 김치만두: "50",
  새우만두: "51", 빨간떡볶이: "52", 크림떡볶이: "53", 짜장떡볶이: "54", 허니치킨: "55",
  양념치킨: "56", 핫도그: "57", 피자: "58", 감자튀김: "59", 돈까스: "60",
  치즈볼: "61", 치즈스틱: "62", 동그랑땡: "63", 떡갈비: "64", 치킨너겟: "65",
  김치주먹밥: "66", 참치주먹밥: "67", 간장주먹밥: "68", 통합: "69", 콜라색: "70",
  사이다색: "71", 오렌지색: "72", 라임색: "73", 파인색: "74", 포도색: "75",
  밀키스색: "76", 블루색: "77", 레몬색: "84", 토마토색: "86", 망고색: "88",
  살구색: "90", 무색: "92", 라떼: "93", 아메리카노: "94", 블랙: "95",
  보리: "96", 녹차: "97", 유자: "98", 생수: "99", 식혜: "100",
  수정과: "101", 올리브: "102", "참기름/들기름": "103", 기타: "104", 초코: "105",
  딸기: "106", 커피: "107", 바나나: "108", 미숫가루: "109", 일반두유: "110",
  검은콩: "111", 아몬드: "112", 샴푸: "113", "린스/트리트먼트": "114", 헤어케어: "115",
  "바디워시/바디로션": "116", "핸드워시/핸드크림": "117", 풋케어: "118", 롤화장지: "119", 키친타월: "120",
  티슈: "121", 물티슈: "122", 생리대: "123", 남성: "124", 여성: "125",
  치약: "126", 칫솔: "127", 가글: "128", 면도: "129", 세탁세제: "130",
  섬유유연제: "131", 욕실세제: "132", 주방세제: "133", 탈취제: "134", 제습제: "135",
  장향제: "136", 살충제: "137", 기저귀: "138", 분유: "139", 유산균: "140",
  비타민: "141", "홍삼/인상": "142", "어린이/청소년": "143", 스킨케어: "144", 썬케어: "145",
  클렌징: "146", 팩: "147", 향수: "148", 남성화장품: "149"
};

// ID to name mapping (역매핑)
const idToName = {};
Object.entries(categoryIdMapping).forEach(([name, id]) => {
  idToName[id] = name;
});

// 다운로드 함수
function downloadImage(url, filepath) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(filepath);
    https.get(url, (response) => {
      response.pipe(file);
      file.on('finish', () => {
        file.close();
        resolve();
      });
    }).on('error', (err) => {
      fs.unlink(filepath, () => {}); // 실패시 파일 삭제
      reject(err);
    });
  });
}

async function downloadAllImages() {
  const baseDir = path.join(__dirname, 'supabase-images');

  // 기본 디렉토리 생성
  if (!fs.existsSync(baseDir)) {
    fs.mkdirSync(baseDir, { recursive: true });
  }

  console.log('📦 Supabase 이미지 다운로드 시작...');
  console.log(`📁 저장 경로: ${baseDir}\n`);

  let totalDownloaded = 0;
  let totalFolders = 0;
  let totalImages = 0;

  // 모든 카테고리 폴더 확인
  for (let folderId = 1; folderId <= 191; folderId++) {
    const folderIdStr = folderId.toString();
    const categoryName = idToName[folderIdStr] || `카테고리_${folderIdStr}`;

    const { data: files, error } = await supabase.storage
      .from('images')
      .list(folderIdStr, { limit: 1000 });

    if (error || !files || files.length === 0) {
      continue;
    }

    // 이미지 파일만 필터링
    const imageFiles = files.filter(f => {
      const ext = f.name.toLowerCase().split('.').pop();
      return ['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext || '');
    });

    if (imageFiles.length === 0) {
      continue;
    }

    totalFolders++;
    totalImages += imageFiles.length;

    // 폴더 생성 (ID_이름 형식)
    const folderName = `${folderIdStr}_${categoryName}`;
    const folderPath = path.join(baseDir, folderName);

    if (!fs.existsSync(folderPath)) {
      fs.mkdirSync(folderPath, { recursive: true });
    }

    console.log(`📁 ${folderName} (${imageFiles.length}개 이미지)`);

    // 각 이미지 다운로드
    for (const imageFile of imageFiles) {
      const { data: urlData } = supabase.storage
        .from('images')
        .getPublicUrl(`${folderIdStr}/${imageFile.name}`);

      const imagePath = path.join(folderPath, imageFile.name);

      try {
        await downloadImage(urlData.publicUrl, imagePath);
        totalDownloaded++;
        process.stdout.write(`\r   진행: ${totalDownloaded}/${totalImages} (${Math.round(totalDownloaded/totalImages*100)}%)`);
      } catch (err) {
        console.error(`\n   ❌ 실패: ${imageFile.name} - ${err.message}`);
      }
    }

    console.log('\n');
  }

  console.log('\n✅ 다운로드 완료!');
  console.log(`📊 결과:`);
  console.log(`   - 총 폴더: ${totalFolders}개`);
  console.log(`   - 총 이미지: ${totalDownloaded}/${totalImages}개`);
  console.log(`   - 저장 위치: ${baseDir}`);
}

downloadAllImages().catch(console.error);
