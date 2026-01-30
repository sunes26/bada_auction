const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://sfoyspfwjxtcbuykljeu.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmb3lzcGZ3anh0Y2J1eWtsamV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1NTcyOTAsImV4cCI6MjA3MjEzMzI5MH0.qxRVuhcOF-9M7_Yeb9kQfxUiYv0vkdDhLBbc42gXK0c';

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkItems() {
  console.log('🔍 images 버킷의 150개 항목 확인 중...\n');

  const { data: items, error } = await supabase.storage
    .from('images')
    .list('', { limit: 1000 });

  if (error) {
    console.error('❌ 오류:', error.message);
    return;
  }

  console.log(`총 ${items.length}개 항목:\n`);

  // Show first 20 items
  console.log('처음 20개 항목:');
  items.slice(0, 20).forEach((item, i) => {
    console.log(`${i + 1}. ${item.name}`);
    console.log(`   - id: ${item.id ? '있음(폴더)' : '없음(파일)'}`);
    console.log(`   - metadata: ${JSON.stringify(item.metadata || {})}`);
  });

  if (items.length > 20) {
    console.log(`\n... 외 ${items.length - 20}개 항목 더\n`);
  }

  // Count folders vs files
  const folders = items.filter(i => i.id);
  const files = items.filter(i => !i.id && i.name);

  console.log(`\n📊 요약:`);
  console.log(`   폴더: ${folders.length}개`);
  console.log(`   파일: ${files.length}개`);

  // If there are folders, check the first few
  if (folders.length > 0) {
    console.log(`\n🔍 첫 3개 폴더의 내용 확인:\n`);

    for (const folder of folders.slice(0, 3)) {
      console.log(`📁 "${folder.name}" 폴더:`);

      const { data: folderContents, error: folderError } = await supabase.storage
        .from('images')
        .list(folder.name, { limit: 100 });

      if (folderError) {
        console.log(`   ❌ 오류: ${folderError.message}`);
      } else if (!folderContents || folderContents.length === 0) {
        console.log(`   📭 비어있음`);
      } else {
        console.log(`   ✅ ${folderContents.length}개 파일:`);

        const imageFiles = folderContents.filter(f => {
          const ext = f.name.toLowerCase().split('.').pop();
          return ['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext || '');
        });

        console.log(`   🖼️ 이미지: ${imageFiles.length}개`);

        imageFiles.slice(0, 3).forEach(img => {
          const { data: urlData } = supabase.storage
            .from('images')
            .getPublicUrl(`${folder.name}/${img.name}`);
          console.log(`      - ${img.name}`);
          console.log(`        URL: ${urlData.publicUrl}`);
        });
      }
      console.log('');
    }
  }
}

checkItems().catch(console.error);
