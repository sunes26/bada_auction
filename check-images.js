const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://sfoyspfwjxtcbuykljeu.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmb3lzcGZ3anh0Y2J1eWtsamV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1NTcyOTAsImV4cCI6MjA3MjEzMzI5MH0.qxRVuhcOF-9M7_Yeb9kQfxUiYv0vkdDhLBbc42gXK0c';

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkImages() {
  console.log('🔍 Supabase 이미지 저장소 확인 중...\n');

  try {
    // List all folders in the images bucket
    const { data: folders, error: foldersError } = await supabase.storage
      .from('images')
      .list('', {
        limit: 1000,
        sortBy: { column: 'name', order: 'asc' }
      });

    if (foldersError) {
      console.error('❌ 폴더 목록 조회 실패:', foldersError.message);
      return;
    }

    if (!folders || folders.length === 0) {
      console.log('📁 저장소가 비어있습니다.');
      return;
    }

    let totalImages = 0;
    const folderDetails = [];

    // Check each folder
    for (const folder of folders) {
      if (folder.id) {
        const { data: files, error: filesError } = await supabase.storage
          .from('images')
          .list(folder.name, {
            limit: 1000,
            sortBy: { column: 'name', order: 'asc' }
          });

        if (!filesError && files) {
          const imageFiles = files.filter(file => {
            const ext = file.name.toLowerCase().split('.').pop();
            return ['jpg', 'jpeg', 'png', 'webp', 'gif'].includes(ext || '');
          });

          if (imageFiles.length > 0) {
            totalImages += imageFiles.length;
            folderDetails.push({
              name: folder.name,
              count: imageFiles.length
            });
          }
        }
      }
    }

    // Print results
    console.log('📊 카테고리별 이미지 현황:\n');
    console.log('┌─────────────────────────────────────────┬─────────┐');
    console.log('│ 폴더명                                   │ 이미지 수 │');
    console.log('├─────────────────────────────────────────┼─────────┤');

    folderDetails
      .sort((a, b) => b.count - a.count)
      .forEach(folder => {
        const nameDisplay = folder.name.padEnd(38, ' ');
        const countDisplay = folder.count.toString().padStart(5, ' ');
        console.log(`│ ${nameDisplay} │ ${countDisplay}   │`);
      });

    console.log('└─────────────────────────────────────────┴─────────┘');
    console.log(`\n✅ 총 ${folderDetails.length}개 카테고리에 ${totalImages}개의 이미지가 저장되어 있습니다.\n`);

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
  }
}

checkImages();
