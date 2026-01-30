const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://sfoyspfwjxtcbuykljeu.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmb3lzcGZ3anh0Y2J1eWtsamV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1NTcyOTAsImV4cCI6MjA3MjEzMzI5MH0.qxRVuhcOF-9M7_Yeb9kQfxUiYv0vkdDhLBbc42gXK0c';

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkSpecificFolders() {
  console.log('🔍 특정 카테고리 폴더 확인...\n');

  const testFolders = [
    { name: '김치만두', id: '50' },
    { name: '고기만두', id: '49' },
    { name: '미역국', id: '29' },
    { name: '흰밥', id: '1' },
  ];

  for (const folder of testFolders) {
    console.log(`📁 "${folder.name}" (폴더 ${folder.id}):`);

    const { data: files, error } = await supabase.storage
      .from('images')
      .list(folder.id, { limit: 100 });

    if (error) {
      console.log(`   ❌ 오류: ${error.message}\n`);
      continue;
    }

    if (!files || files.length === 0) {
      console.log(`   📭 이미지 없음\n`);
      continue;
    }

    const imageFiles = files.filter(f => {
      const ext = f.name.toLowerCase().split('.').pop();
      return ['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext || '');
    });

    console.log(`   ✅ ${imageFiles.length}개 이미지 발견!`);

    // Show first 3 images with their full URLs
    imageFiles.slice(0, 3).forEach((img, i) => {
      const { data: urlData } = supabase.storage
        .from('images')
        .getPublicUrl(`${folder.id}/${img.name}`);

      console.log(`   ${i + 1}. ${img.name}`);
      console.log(`      ${urlData.publicUrl}`);
    });

    if (imageFiles.length > 3) {
      console.log(`   ... 외 ${imageFiles.length - 3}개 더`);
    }

    console.log('');
  }

  // Count total images across all folders
  console.log('\n📊 전체 통계 계산 중...\n');

  let totalImages = 0;
  let foldersWithImages = 0;

  for (let i = 1; i <= 191; i++) {
    const { data: files } = await supabase.storage
      .from('images')
      .list(i.toString(), { limit: 1000 });

    if (files && files.length > 0) {
      const images = files.filter(f => {
        const ext = f.name.toLowerCase().split('.').pop();
        return ['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext || '');
      });

      if (images.length > 0) {
        totalImages += images.length;
        foldersWithImages++;
      }
    }
  }

  console.log(`✅ 총 ${foldersWithImages}개 카테고리에 ${totalImages}개 이미지 저장되어 있습니다!`);
}

checkSpecificFolders().catch(console.error);
