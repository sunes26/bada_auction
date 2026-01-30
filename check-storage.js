const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://sfoyspfwjxtcbuykljeu.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmb3lzcGZ3anh0Y2J1eWtsamV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1NTcyOTAsImV4cCI6MjA3MjEzMzI5MH0.qxRVuhcOF-9M7_Yeb9kQfxUiYv0vkdDhLBbc42gXK0c';

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkAllBuckets() {
  console.log('🔍 모든 Supabase Storage 버킷 확인 중...\n');

  try {
    const { data: buckets, error: bucketsError } = await supabase.storage.listBuckets();

    if (bucketsError) {
      console.error('❌ 버킷 목록 조회 실패:', bucketsError.message);
      return;
    }

    console.log('📦 사용 가능한 버킷 목록:');
    buckets.forEach(bucket => {
      const visibility = bucket.public ? '공개' : '비공개';
      console.log(`  - ${bucket.name} (${visibility})`);
    });

    console.log('\n─────────────────────────────────────────\n');

    for (const bucket of buckets) {
      console.log(`📁 "${bucket.name}" 버킷 확인 중...`);

      const { data: files, error: filesError } = await supabase.storage
        .from(bucket.name)
        .list('', {
          limit: 1000,
        });

      if (filesError) {
        console.log(`  ❌ 오류: ${filesError.message}\n`);
        continue;
      }

      if (!files || files.length === 0) {
        console.log(`  📭 비어있음\n`);
        continue;
      }

      console.log(`  ✅ ${files.length}개 항목 발견:`);
      files.slice(0, 10).forEach(file => {
        console.log(`    - ${file.name}`);
      });
      if (files.length > 10) {
        console.log(`    ... 외 ${files.length - 10}개 더`);
      }
      console.log('');
    }

  } catch (error) {
    console.error('❌ 오류 발생:', error.message);
  }
}

checkAllBuckets();
