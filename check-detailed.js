const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://sfoyspfwjxtcbuykljeu.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmb3lzcGZ3anh0Y2J1eWtsamV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1NTcyOTAsImV4cCI6MjA3MjEzMzI5MH0.qxRVuhcOF-9M7_Yeb9kQfxUiYv0vkdDhLBbc42gXK0c';

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkDetailedStorage() {
  console.log('🔍 Supabase 상세 확인 중...\n');

  // Check buckets
  console.log('1️⃣ 버킷 목록 확인:');
  const { data: buckets, error: bucketsError } = await supabase.storage.listBuckets();

  if (bucketsError) {
    console.error('❌ 버킷 조회 실패:', bucketsError);
  } else if (!buckets || buckets.length === 0) {
    console.log('📭 버킷이 없습니다');
  } else {
    console.log(`✅ ${buckets.length}개 버킷 발견:`);
    buckets.forEach(b => console.log(`   - ${b.name}`));
  }

  console.log('\n2️⃣ images 버킷 내용 확인:');

  // Try to list root of images bucket
  const { data: rootFiles, error: rootError } = await supabase.storage
    .from('images')
    .list('', { limit: 1000 });

  if (rootError) {
    console.error('❌ images 버킷 접근 실패:', rootError.message);
  } else if (!rootFiles || rootFiles.length === 0) {
    console.log('📭 images 버킷이 비어있습니다');
  } else {
    console.log(`✅ images 버킷에 ${rootFiles.length}개 항목:`);

    let totalImages = 0;
    for (const item of rootFiles) {
      if (item.id) {
        // It's a folder
        console.log(`\n   📁 폴더: ${item.name}`);

        const { data: folderFiles, error: folderError } = await supabase.storage
          .from('images')
          .list(item.name, { limit: 1000 });

        if (!folderError && folderFiles) {
          const images = folderFiles.filter(f => {
            const ext = f.name.toLowerCase().split('.').pop();
            return ['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext || '');
          });

          console.log(`      이미지 ${images.length}개`);
          totalImages += images.length;

          // Show first 3 images as examples
          images.slice(0, 3).forEach(img => {
            const { data: urlData } = supabase.storage
              .from('images')
              .getPublicUrl(`${item.name}/${img.name}`);
            console.log(`      - ${img.name}`);
            console.log(`        ${urlData.publicUrl.substring(0, 80)}...`);
          });
          if (images.length > 3) {
            console.log(`      ... 외 ${images.length - 3}개 더`);
          }
        }
      }
    }
    console.log(`\n📊 총 이미지 개수: ${totalImages}개`);
  }

  console.log('\n3️⃣ 특정 카테고리 테스트 (만두):');
  // Test specific categories that user mentioned
  const testFolders = ['만두', 'mandu', '즉석밥', 'instant_rice', 'rice'];

  for (const folder of testFolders) {
    const { data: testFiles, error: testError } = await supabase.storage
      .from('images')
      .list(folder, { limit: 5 });

    if (!testError && testFiles && testFiles.length > 0) {
      console.log(`✅ "${folder}" 폴더 발견! (${testFiles.length}개 파일)`);
      testFiles.forEach(f => console.log(`   - ${f.name}`));
    }
  }
}

checkDetailedStorage().catch(console.error);
