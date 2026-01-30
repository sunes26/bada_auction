const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = 'https://sfoyspfwjxtcbuykljeu.supabase.co';
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNmb3lzcGZ3anh0Y2J1eWtsamV1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTY1NTcyOTAsImV4cCI6MjA3MjEzMzI5MH0.qxRVuhcOF-9M7_Yeb9kQfxUiYv0vkdDhLBbc42gXK0c';

const supabase = createClient(supabaseUrl, supabaseKey);

async function checkAssignments() {
  console.log('📋 weeks 테이블의 assignment_content 확인 중...\n');

  const { data, error } = await supabase
    .from('weeks')
    .select('*')
    .order('week_number', { ascending: true });

  if (error) {
    console.error('❌ 오류:', error);
    return;
  }

  if (!data || data.length === 0) {
    console.log('⚠️  weeks 테이블에 데이터가 없습니다.');
    return;
  }

  console.log(`✅ 총 ${data.length}개의 주차 데이터 발견\n`);
  console.log('='.repeat(80));

  data.forEach((week, index) => {
    console.log(`\n${index + 1}. 주차 ${week.week_number}`);
    console.log('-'.repeat(80));
    console.log(`과제 내용:\n${week.assignment_content || '(내용 없음)'}`);
    console.log('='.repeat(80));
  });

  console.log(`\n📊 총 ${data.length}개의 주차 발견`);
}

checkAssignments().catch(console.error);
