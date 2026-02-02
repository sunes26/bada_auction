'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  Lock,
  Activity,
  Database,
  Image as ImageIcon,
  Settings,
  FileText,
  Trash2,
  TrendingUp,
  Zap,
  RefreshCw,
  Download,
  Upload,
  AlertCircle,
  CheckCircle,
  Server,
  Cpu,
  HardDrive,
  Wifi,
  Clock,
  FolderOpen,
  Eye,
  Code,
  Users,
  Plus
} from 'lucide-react';

import { API_BASE_URL } from '@/lib/api';
import { adminGet, adminPost, adminDelete, adminFetch, adminUpload } from '@/lib/adminApi';
type TabType = 'dashboard' | 'images' | 'database' | 'logs' | 'settings' | 'cleanup' | 'performance' | 'devtools' | 'activity' | 'mappings';

interface SystemStatus {
  database: {
    status: string;
    size_mb: number;
  };
  server: {
    status: string;
    response_time_ms: number;
    uptime_seconds: number;
  };
  system: {
    cpu_percent: number;
    memory_used_mb: number;
    memory_total_mb: number;
    memory_percent: number;
    disk_used_gb: number;
    disk_total_gb: number;
    disk_percent: number;
  };
}

interface ImageStats {
  total_folders: number;
  total_images: number;
  total_size_mb: number;
  folders: Array<{
    name: string;
    display_name?: string;
    image_count: number;
    size_mb: number;
  }>;
}

interface DatabaseStats {
  database_size_mb: number;
  tables: Array<{
    table: string;
    count: number;
  }>;
  total_records: number;
}

export default function AdminPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [loading, setLoading] = useState(false);

  // 상태 데이터
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [imageStats, setImageStats] = useState<ImageStats | null>(null);
  const [databaseStats, setDatabaseStats] = useState<DatabaseStats | null>(null);

  const handleLogin = () => {
    const adminPassword = process.env.NEXT_PUBLIC_ADMIN_PASSWORD || '8888';
    if (password === adminPassword) {
      setIsAuthenticated(true);
      setPassword('');
      loadDashboardData();
    } else {
      alert('비밀번호가 올바르지 않습니다.');
    }
  };

  const loadDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      const [statusData, imageData, dbData] = await Promise.all([
        adminGet('/api/admin/system/status'),
        adminGet('/api/admin/images/stats'),
        adminGet('/api/admin/database/stats')
      ]);

      if (statusData.success) setSystemStatus(statusData);
      if (imageData.success) setImageStats(imageData);
      if (dbData.success) setDatabaseStats(dbData);
    } catch (error) {
      console.error('대시보드 데이터 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      loadDashboardData();
    }
  }, [isAuthenticated, loadDashboardData]);

  if (!isAuthenticated) {
    return (
      <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
        <div className="max-w-md mx-auto">
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-gradient-to-br from-red-500 to-pink-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Shield className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-4xl font-bold text-gray-800 mb-4">관리자 모드</h2>
            <p className="text-gray-600">비밀번호를 입력하세요</p>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                비밀번호
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                  placeholder="비밀번호 입력"
                  className="w-full pl-12 pr-4 py-3 rounded-xl border-2 border-gray-200 focus:border-red-500 focus:outline-none transition-colors"
                />
              </div>
            </div>

            <button
              onClick={handleLogin}
              className="w-full px-6 py-3 bg-gradient-to-r from-red-500 to-pink-600 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all"
            >
              로그인
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-gradient-to-br from-red-500 to-pink-600 rounded-2xl flex items-center justify-center">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <div>
            <h2 className="text-4xl font-bold text-gray-800">관리자 모드</h2>
            <p className="text-gray-600">시스템 관리 및 모니터링</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={loadDashboardData}
            disabled={loading}
            className="p-2 bg-white rounded-xl hover:shadow-lg transition-all border border-gray-200"
            title="새로고침"
          >
            <RefreshCw className={`w-5 h-5 text-blue-600 ${loading ? 'animate-spin' : ''}`} />
          </button>
          <button
            onClick={() => setIsAuthenticated(false)}
            className="px-6 py-2 bg-red-100 text-red-700 font-semibold rounded-xl hover:bg-red-200 transition-colors"
          >
            로그아웃
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        <TabButton
          active={activeTab === 'dashboard'}
          onClick={() => setActiveTab('dashboard')}
          icon={<Activity className="w-4 h-4" />}
          label="대시보드"
        />
        <TabButton
          active={activeTab === 'images'}
          onClick={() => setActiveTab('images')}
          icon={<ImageIcon className="w-4 h-4" />}
          label="이미지"
        />
        <TabButton
          active={activeTab === 'database'}
          onClick={() => setActiveTab('database')}
          icon={<Database className="w-4 h-4" />}
          label="DB"
        />
        <TabButton
          active={activeTab === 'logs'}
          onClick={() => setActiveTab('logs')}
          icon={<FileText className="w-4 h-4" />}
          label="로그"
        />
        <TabButton
          active={activeTab === 'settings'}
          onClick={() => setActiveTab('settings')}
          icon={<Settings className="w-4 h-4" />}
          label="설정"
        />
        <TabButton
          active={activeTab === 'cleanup'}
          onClick={() => setActiveTab('cleanup')}
          icon={<Trash2 className="w-4 h-4" />}
          label="정리"
        />
        <TabButton
          active={activeTab === 'performance'}
          onClick={() => setActiveTab('performance')}
          icon={<TrendingUp className="w-4 h-4" />}
          label="성능"
        />
        <TabButton
          active={activeTab === 'devtools'}
          onClick={() => setActiveTab('devtools')}
          icon={<Code className="w-4 h-4" />}
          label="개발"
        />
        <TabButton
          active={activeTab === 'activity'}
          onClick={() => setActiveTab('activity')}
          icon={<Users className="w-4 h-4" />}
          label="활동"
        />
        <TabButton
          active={activeTab === 'mappings'}
          onClick={() => setActiveTab('mappings')}
          icon={<FolderOpen className="w-4 h-4" />}
          label="카테고리 매핑"
        />
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'dashboard' && (
          <DashboardTab
            systemStatus={systemStatus}
            imageStats={imageStats}
            databaseStats={databaseStats}
            onRefresh={loadDashboardData}
          />
        )}
        {activeTab === 'images' && <ImagesTab />}
        {activeTab === 'database' && <DatabaseTab stats={databaseStats} />}
        {activeTab === 'logs' && <LogsTab />}
        {activeTab === 'settings' && <SettingsTab />}
        {activeTab === 'cleanup' && <CleanupTab />}
        {activeTab === 'performance' && <PerformanceTab />}
        {activeTab === 'devtools' && <DevToolsTab />}
        {activeTab === 'activity' && <ActivityTab />}
        {activeTab === 'mappings' && <CategoryMappingTab />}
      </div>
    </div>
  );
}

function TabButton({ active, onClick, icon, label }: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-xl font-semibold text-sm transition-all whitespace-nowrap ${
        active
          ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-lg'
          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

// ========== 대시보드 탭 ==========
function DashboardTab({ systemStatus, imageStats, databaseStats, onRefresh }: {
  systemStatus: SystemStatus | null;
  imageStats: ImageStats | null;
  databaseStats: DatabaseStats | null;
  onRefresh: () => void;
}) {
  // 빠른 액션 핸들러들
  const handleBackupDB = async () => {
    try {
      const data = await adminPost('/api/admin/database/backup');
      if (data.success) {
        alert('✓ 데이터베이스 백업 완료!');
        onRefresh();
      }
    } catch (error) {
      alert('백업 실패: ' + error);
    }
  };

  const handleOptimizeDB = async () => {
    if (!confirm('데이터베이스를 최적화하시겠습니까?')) return;
    try {
      const data = await adminPost('/api/admin/database/optimize');
      if (data.success) {
        alert('✓ 데이터베이스 최적화 완료!');
        onRefresh();
      }
    } catch (error) {
      alert('최적화 실패: ' + error);
    }
  };

  const handleClearCache = () => {
    localStorage.clear();
    sessionStorage.clear();
    alert('✓ 브라우저 캐시가 삭제되었습니다!');
  };

  return (
    <div className="space-y-6">
      {/* 시스템 상태 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatusCard
          title="데이터베이스"
          value={systemStatus?.database.status || '확인 중'}
          subtitle={`${systemStatus?.database.size_mb.toFixed(2) || 0} MB`}
          icon={<Database className="w-6 h-6" />}
          color="blue"
          status={systemStatus?.database.status === '연결됨' ? 'success' : 'error'}
        />
        <StatusCard
          title="API 서버"
          value={systemStatus?.server.status || '확인 중'}
          subtitle={`${systemStatus?.server.response_time_ms?.toFixed(2) ?? 0} ms`}
          icon={<Server className="w-6 h-6" />}
          color="green"
          status={systemStatus?.server.status === '정상' ? 'success' : 'error'}
        />
        <StatusCard
          title="메모리 사용량"
          value={`${systemStatus?.system.memory_percent?.toFixed(1) ?? 0}%`}
          subtitle={`${((systemStatus?.system.memory_used_mb ?? 0) / 1024).toFixed(1)} GB / ${((systemStatus?.system.memory_total_mb ?? 0) / 1024).toFixed(1)} GB`}
          icon={<Cpu className="w-6 h-6" />}
          color="purple"
          status={systemStatus ? (systemStatus.system.memory_percent > 80 ? 'warning' : 'success') : 'info'}
        />
        <StatusCard
          title="디스크 사용량"
          value={`${systemStatus?.system.disk_percent?.toFixed(1) ?? 0}%`}
          subtitle={`${systemStatus?.system.disk_used_gb?.toFixed(1) ?? 0} GB / ${systemStatus?.system.disk_total_gb?.toFixed(1) ?? 0} GB`}
          icon={<HardDrive className="w-6 h-6" />}
          color="orange"
          status={systemStatus ? (systemStatus.system.disk_percent > 80 ? 'warning' : 'success') : 'info'}
        />
      </div>

      {/* 이미지 & DB 통계 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 이미지 통계 */}
        <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl p-6 border border-blue-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <ImageIcon className="w-6 h-6 text-blue-600" />
              이미지 통계
            </h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">총 폴더</span>
              <span className="text-2xl font-bold text-blue-600">{imageStats?.total_folders || 0}개</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">총 이미지</span>
              <span className="text-2xl font-bold text-purple-600">{imageStats?.total_images.toLocaleString() || 0}개</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">총 용량</span>
              <span className="text-2xl font-bold text-pink-600">{imageStats?.total_size_mb.toFixed(2) || 0} MB</span>
            </div>
          </div>
        </div>

        {/* DB 통계 */}
        <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border border-green-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-800 flex items-center gap-2">
              <Database className="w-6 h-6 text-green-600" />
              데이터베이스 통계
            </h3>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">DB 크기</span>
              <span className="text-2xl font-bold text-green-600">{databaseStats?.database_size_mb.toFixed(2) || 0} MB</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">총 테이블</span>
              <span className="text-2xl font-bold text-emerald-600">{databaseStats?.tables.length || 0}개</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">총 레코드</span>
              <span className="text-2xl font-bold text-teal-600">{databaseStats?.total_records.toLocaleString() || 0}개</span>
            </div>
          </div>
        </div>
      </div>

      {/* 빠른 작업 */}
      <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-2xl p-6 border border-orange-200">
        <h3 className="text-xl font-bold text-gray-800 mb-4 flex items-center gap-2">
          <Zap className="w-6 h-6 text-orange-600" />
          빠른 작업
        </h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <QuickActionButton
            label="DB 백업"
            icon={<Download className="w-5 h-5" />}
            onClick={handleBackupDB}
          />
          <QuickActionButton
            label="캐시 삭제"
            icon={<Trash2 className="w-5 h-5" />}
            onClick={handleClearCache}
          />
          <QuickActionButton
            label="DB 최적화"
            icon={<Database className="w-5 h-5" />}
            onClick={handleOptimizeDB}
          />
          <QuickActionButton
            label="새로고침"
            icon={<RefreshCw className="w-5 h-5" />}
            onClick={onRefresh}
          />
        </div>
      </div>
    </div>
  );
}

function StatusCard({ title, value, subtitle, icon, color, status }: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  color: 'blue' | 'green' | 'purple' | 'orange';
  status: 'success' | 'warning' | 'error' | 'info';
}) {
  const colors = {
    blue: 'from-blue-500 to-blue-600',
    green: 'from-green-500 to-green-600',
    purple: 'from-purple-500 to-purple-600',
    orange: 'from-orange-500 to-orange-600'
  };

  const statusColors = {
    success: 'bg-green-100 text-green-700',
    warning: 'bg-yellow-100 text-yellow-700',
    error: 'bg-red-100 text-red-700',
    info: 'bg-blue-100 text-blue-700'
  };

  return (
    <div className="bg-white rounded-xl p-5 shadow-lg border border-gray-200">
      <div className="flex items-center justify-between mb-3">
        <div className={`w-12 h-12 bg-gradient-to-br ${colors[color]} rounded-xl flex items-center justify-center text-white`}>
          {icon}
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${statusColors[status]}`}>
          {status === 'success' ? '정상' : status === 'warning' ? '주의' : status === 'error' ? '오류' : '확인'}
        </span>
      </div>
      <div className="text-sm text-gray-600 mb-1">{title}</div>
      <div className="text-2xl font-bold text-gray-900 mb-1">{value}</div>
      <div className="text-xs text-gray-500">{subtitle}</div>
    </div>
  );
}

function QuickActionButton({ label, icon, onClick }: {
  label: string;
  icon: React.ReactNode;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className="flex flex-col items-center justify-center gap-2 p-4 bg-white rounded-xl hover:shadow-lg transition-all border border-gray-200 hover:border-blue-300"
    >
      <div className="text-blue-600">{icon}</div>
      <span className="text-sm font-semibold text-gray-700">{label}</span>
    </button>
  );
}

// ========== 이미지 탭 ==========
function ImagesTab() {
  const [imageStats, setImageStats] = useState<ImageStats | null>(null);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [folderImages, setFolderImages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [nextFolderNumber, setNextFolderNumber] = useState<number | null>(null);
  const [newFolderName, setNewFolderName] = useState('');
  const [newLevel1, setNewLevel1] = useState('');
  const [newLevel2, setNewLevel2] = useState('');
  const [newLevel3, setNewLevel3] = useState('');
  const [newLevel4, setNewLevel4] = useState('');

  interface CategoryOptions {
    level1: string[];
    level2: string[];
    level3: string[];
    level4: string[];
  }

  const [categoryOptions, setCategoryOptions] = useState<CategoryOptions>({ level1: [], level2: [], level3: [], level4: [] });

  useEffect(() => {
    loadImageStats();
  }, []);

  // 폴더 추가 모달이 열릴 때 데이터 로드
  useEffect(() => {
    if (showCreateFolder) {
      loadNextFolderNumber();
      loadCategoryOptions();
      // 카테고리 초기화
      setNewLevel1('');
      setNewLevel2('');
      setNewLevel3('');
      setNewLevel4('');
    }
  }, [showCreateFolder]);

  // 대분류 변경 시 중분류 로드
  useEffect(() => {
    const loadLevel2 = async () => {
      if (!newLevel1) {
        setCategoryOptions(prev => ({ ...prev, level2: [], level3: [], level4: [] }));
        return;
      }
      try {
        const res = await fetch(`${API_BASE_URL}/api/categories/levels?level1=${encodeURIComponent(newLevel1)}`);
        const data = await res.json();
        if (data.success) {
          setCategoryOptions(prev => ({ ...prev, level2: data.options, level3: [], level4: [] }));
        }
      } catch (error) {
        console.error('중분류 로드 실패:', error);
      }
    };
    loadLevel2();
    // 하위 카테고리 초기화
    setNewLevel2('');
    setNewLevel3('');
    setNewLevel4('');
  }, [newLevel1]);

  // 중분류 변경 시 소분류 로드
  useEffect(() => {
    const loadLevel3 = async () => {
      if (!newLevel1 || !newLevel2) {
        setCategoryOptions(prev => ({ ...prev, level3: [], level4: [] }));
        return;
      }
      try {
        const res = await fetch(`${API_BASE_URL}/api/categories/levels?level1=${encodeURIComponent(newLevel1)}&level2=${encodeURIComponent(newLevel2)}`);
        const data = await res.json();
        if (data.success) {
          setCategoryOptions(prev => ({ ...prev, level3: data.options, level4: [] }));
        }
      } catch (error) {
        console.error('소분류 로드 실패:', error);
      }
    };
    loadLevel3();
    // 하위 카테고리 초기화
    setNewLevel3('');
    setNewLevel4('');
  }, [newLevel1, newLevel2]);

  // 소분류 변경 시 제품종류 로드
  useEffect(() => {
    const loadLevel4 = async () => {
      if (!newLevel1 || !newLevel2 || !newLevel3) {
        setCategoryOptions(prev => ({ ...prev, level4: [] }));
        return;
      }
      try {
        const res = await fetch(`${API_BASE_URL}/api/categories/levels?level1=${encodeURIComponent(newLevel1)}&level2=${encodeURIComponent(newLevel2)}&level3=${encodeURIComponent(newLevel3)}`);
        const data = await res.json();
        if (data.success) {
          setCategoryOptions(prev => ({ ...prev, level4: data.options }));
        }
      } catch (error) {
        console.error('제품종류 로드 실패:', error);
      }
    };
    loadLevel4();
    // 제품종류 초기화
    setNewLevel4('');
  }, [newLevel1, newLevel2, newLevel3]);

  const loadNextFolderNumber = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/categories/next-number`);
      const data = await res.json();
      if (data.success) {
        setNextFolderNumber(data.next_number);
      }
    } catch (error) {
      console.error('다음 폴더 번호 로드 실패:', error);
    }
  };

  const loadCategoryOptions = async () => {
    try {
      // 대분류만 로드 (level1)
      const res = await fetch(`${API_BASE_URL}/api/categories/levels`);
      const data = await res.json();
      if (data.success) {
        setCategoryOptions({ level1: data.options, level2: [], level3: [], level4: [] });
      }
    } catch (error) {
      console.error('카테고리 옵션 로드 실패:', error);
    }
  };

  const loadImageStats = async () => {
    try {
      const data = await adminGet('/api/admin/images/stats');
      if (data.success) {
        setImageStats(data);
      }
    } catch (error) {
      console.error('이미지 통계 로드 실패:', error);
    }
  };

  const loadFolderImages = async (folderName: string) => {
    setLoading(true);
    try {
      const data = await adminGet(`/api/admin/images/gallery/${folderName}`);
      if (data.success) {
        setFolderImages(data.images);
        setSelectedFolder(folderName);
      }
    } catch (error) {
      console.error('폴더 이미지 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteImage = async (folderName: string, filename: string) => {
    if (!confirm(`"${filename}"을(를) 삭제하시겠습니까?`)) return;
    try {
      const data = await adminDelete(`/api/admin/images/delete?folder_name=${folderName}&filename=${filename}`);
      if (data.success) {
        alert('이미지가 삭제되었습니다.');
        loadFolderImages(folderName);
        loadImageStats();
      }
    } catch (error) {
      alert('삭제 실패: ' + error);
    }
  };

  const handleCreateFolder = async () => {
    // 입력값 검증
    if (!newFolderName.trim()) {
      alert('제품명을 입력해주세요.');
      return;
    }
    if (!newLevel1.trim() || !newLevel2.trim() || !newLevel3.trim() || !newLevel4.trim()) {
      alert('모든 카테고리를 입력해주세요.');
      return;
    }

    try {
      const params = new URLSearchParams({
        folder_name: newFolderName.trim(),
        level1: newLevel1.trim(),
        level2: newLevel2.trim(),
        level3: newLevel3.trim(),
        level4: newLevel4.trim()
      });

      const data = await adminPost('/api/admin/images/create-folder?${params}');
      if (data.success) {
        alert(data.message);
        // 입력 필드 초기화
        setNewFolderName('');
        setNewLevel1('');
        setNewLevel2('');
        setNewLevel3('');
        setNewLevel4('');
        setShowCreateFolder(false);
        loadImageStats();
      } else {
        alert(data.detail);
      }
    } catch (error) {
      alert('폴더 생성 실패: ' + error);
    }
  };

  const handleUploadImages = async (folderName: string, files: FileList) => {
    if (files.length === 0) return;

    const formData = new FormData();
    Array.from(files).forEach(file => {
      formData.append('files', file);
    });

    try {
      const data = await adminUpload(`/api/admin/images/upload?folder_name=${encodeURIComponent(folderName)}`, formData);
      if (data.success) {
        alert(data.message);
        loadFolderImages(folderName);
        loadImageStats();
      } else {
        alert(data.detail);
      }
    } catch (error) {
      alert('업로드 실패: ' + error);
    }
  };

  return (
    <div className="space-y-6">
      {/* 전체 통계 */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-200">
        <h3 className="text-xl font-bold text-gray-800 mb-4">전체 이미지 통계</h3>
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">{imageStats?.total_folders || 0}</div>
            <div className="text-sm text-gray-600">폴더</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600">{imageStats?.total_images.toLocaleString() || 0}</div>
            <div className="text-sm text-gray-600">이미지</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-pink-600">{imageStats?.total_size_mb.toFixed(2) || 0} MB</div>
            <div className="text-sm text-gray-600">용량</div>
          </div>
        </div>
      </div>

      {/* 폴더 목록 */}
      {!selectedFolder ? (
        <div className="bg-white rounded-xl p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-800">폴더 목록</h3>
            <button
              onClick={() => setShowCreateFolder(!showCreateFolder)}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              폴더 추가
            </button>
          </div>

          {/* 폴더 생성 UI */}
          {showCreateFolder && (
            <div className="mb-4 p-6 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="text-lg font-bold text-gray-800 mb-4">새 폴더 및 카테고리 추가</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                {/* 폴더 정보 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    폴더 번호 (자동생성)
                  </label>
                  <div className="w-full px-3 py-2 border border-gray-200 rounded-lg bg-gray-50 text-gray-700 font-semibold">
                    {nextFolderNumber || '로딩 중...'}
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    제품명 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={newFolderName}
                    onChange={(e) => setNewFolderName(e.target.value)}
                    placeholder="예: 유기농우유"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                {/* 카테고리 계층 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    대분류 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    list="level1-options"
                    value={newLevel1}
                    onChange={(e) => setNewLevel1(e.target.value)}
                    placeholder="예: 우유/두유 (기존 카테고리 선택 또는 직접 입력)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <datalist id="level1-options">
                    {categoryOptions.level1.map((option: string) => (
                      <option key={option} value={option} />
                    ))}
                  </datalist>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    중분류 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    list="level2-options"
                    value={newLevel2}
                    onChange={(e) => setNewLevel2(e.target.value)}
                    placeholder="예: 우유 (기존 카테고리 선택 또는 직접 입력)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <datalist id="level2-options">
                    {categoryOptions.level2.map((option: string) => (
                      <option key={option} value={option} />
                    ))}
                  </datalist>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    소분류 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    list="level3-options"
                    value={newLevel3}
                    onChange={(e) => setNewLevel3(e.target.value)}
                    placeholder="예: 유기농우유 (기존 카테고리 선택 또는 직접 입력)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <datalist id="level3-options">
                    {categoryOptions.level3.map((option: string) => (
                      <option key={option} value={option} />
                    ))}
                  </datalist>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    제품종류 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    list="level4-options"
                    value={newLevel4}
                    onChange={(e) => setNewLevel4(e.target.value)}
                    placeholder="예: 유기농우유 (기존 카테고리 선택 또는 직접 입력)"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <datalist id="level4-options">
                    {categoryOptions.level4.map((option: string) => (
                      <option key={option} value={option} />
                    ))}
                  </datalist>
                </div>
              </div>

              {/* 미리보기 */}
              {nextFolderNumber && newFolderName && (
                <div className="mb-4 p-3 bg-white rounded-lg border border-gray-300">
                  <div className="text-sm text-gray-600 mb-1">생성될 폴더:</div>
                  <div className="font-bold text-gray-800">{nextFolderNumber}_{newFolderName}</div>
                  {newLevel1 && newLevel2 && newLevel3 && newLevel4 && (
                    <>
                      <div className="text-sm text-gray-600 mt-2 mb-1">카테고리 경로:</div>
                      <div className="text-sm text-gray-700">{newLevel1} &gt; {newLevel2} &gt; {newLevel3} &gt; {newLevel4}</div>
                    </>
                  )}
                </div>
              )}

              {/* 버튼 */}
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => {
                    setShowCreateFolder(false);
                    setNextFolderNumber(null);
                    setNewFolderName('');
                    setNewLevel1('');
                    setNewLevel2('');
                    setNewLevel3('');
                    setNewLevel4('');
                  }}
                  className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                >
                  취소
                </button>
                <button
                  onClick={handleCreateFolder}
                  className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                >
                  생성
                </button>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[600px] overflow-y-auto">
            {imageStats?.folders.map((folder) => (
              <button
                key={folder.name}
                onClick={() => loadFolderImages(folder.display_name || folder.name)}
                className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-blue-50 transition-colors border border-gray-200 hover:border-blue-300 text-left"
              >
                <div className="flex items-center gap-3">
                  <FolderOpen className="w-8 h-8 text-blue-600" />
                  <div>
                    <div className="font-semibold text-gray-800">{folder.display_name || folder.name}</div>
                    <div className="text-xs text-gray-500">
                      {folder.image_count}개 · {folder.size_mb.toFixed(2)} MB
                    </div>
                  </div>
                </div>
                <Eye className="w-5 h-5 text-gray-400" />
              </button>
            ))}
          </div>
        </div>
      ) : (
        /* 이미지 갤러리 */
        <div className="bg-white rounded-xl p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold text-gray-800">{selectedFolder}</h3>
            <div className="flex gap-2">
              <label className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors cursor-pointer flex items-center gap-2">
                <Upload className="w-4 h-4" />
                이미지 업로드
                <input
                  type="file"
                  multiple
                  accept="image/*"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && selectedFolder) {
                      handleUploadImages(selectedFolder, e.target.files);
                      e.target.value = ''; // 초기화
                    }
                  }}
                />
              </label>
              <button
                onClick={() => setSelectedFolder(null)}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                ← 돌아가기
              </button>
            </div>
          </div>

          {loading ? (
            <div className="flex justify-center items-center py-20">
              <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 max-h-[600px] overflow-y-auto">
              {folderImages.map((img, index) => (
                <div key={`${selectedFolder}-${img.filename}-${index}`} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                  <img
                    src={img.path}
                    alt={img.filename}
                    loading="lazy"
                    className="w-full h-40 object-cover rounded-lg mb-2"
                  />
                  <div className="text-xs text-gray-600 mb-2 truncate" title={img.filename}>
                    {img.filename}
                  </div>
                  <div className="text-xs text-gray-500 mb-2">
                    {img.width} × {img.height} · {img.size_kb} KB
                  </div>
                  <button
                    onClick={() => handleDeleteImage(selectedFolder!, img.filename)}
                    className="w-full px-3 py-1 bg-red-500 text-white rounded text-xs hover:bg-red-600 transition-colors"
                  >
                    삭제
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ========== 데이터베이스 탭 ==========
function DatabaseTab({ stats }: { stats: DatabaseStats | null }) {
  const [backups, setBackups] = useState<any[]>([]);

  useEffect(() => {
    loadBackups();
  }, []);

  const loadBackups = async () => {
    try {
      const data = await adminGet('/api/admin/database/backups');
      if (data.success) {
        setBackups(data.backups);
      }
    } catch (error) {
      console.error('백업 목록 로드 실패:', error);
    }
  };

  const handleBackup = async () => {
    try {
      const data = await adminPost('/api/admin/database/backup');
      if (data.success) {
        alert('✓ 백업 완료!');
        loadBackups();
      }
    } catch (error) {
      alert('백업 실패: ' + error);
    }
  };

  const handleRestore = async (filename: string) => {
    if (!confirm(`"${filename}"으로 복원하시겠습니까?\n\n⚠️ 현재 데이터는 백업 후 덮어쓰기됩니다.`)) return;
    try {
      const data = await adminPost('/api/admin/database/restore?backup_filename=${filename}');
      if (data.success) {
        alert('✓ 복원 완료!');
        loadBackups();
      }
    } catch (error) {
      alert('복원 실패: ' + error);
    }
  };

  const handleOptimize = async () => {
    if (!confirm('데이터베이스를 최적화하시겠습니까?')) return;
    try {
      const data = await adminPost('/api/admin/database/optimize');
      if (data.success) {
        alert('✓ 최적화 완료!');
      }
    } catch (error) {
      alert('최적화 실패: ' + error);
    }
  };

  return (
    <div className="space-y-6">
      {/* DB 통계 */}
      <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl p-6 border border-green-200">
        <h3 className="text-xl font-bold text-gray-800 mb-4">데이터베이스 통계</h3>
        <div className="grid grid-cols-3 gap-4 mb-4">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{stats?.database_size_mb.toFixed(2) || 0} MB</div>
            <div className="text-sm text-gray-600">DB 크기</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-emerald-600">{stats?.tables.length || 0}</div>
            <div className="text-sm text-gray-600">테이블 수</div>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-teal-600">{stats?.total_records.toLocaleString() || 0}</div>
            <div className="text-sm text-gray-600">총 레코드</div>
          </div>
        </div>

        {/* 테이블별 레코드 */}
        <div className="bg-white rounded-lg p-4">
          <h4 className="font-semibold text-gray-700 mb-3">테이블별 레코드 수</h4>
          <div className="space-y-2">
            {stats?.tables.map((table) => (
              <div key={table.table} className="flex justify-between items-center text-sm">
                <span className="text-gray-600">{table.table}</span>
                <span className="font-bold text-gray-800">{table.count.toLocaleString()}개</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 백업 관리 */}
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-gray-800">백업 관리</h3>
          <div className="flex gap-2">
            <button
              onClick={handleBackup}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              새 백업
            </button>
            <button
              onClick={handleOptimize}
              className="px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
            >
              최적화
            </button>
          </div>
        </div>

        <div className="space-y-2 max-h-[400px] overflow-y-auto">
          {backups.length === 0 ? (
            <div className="text-center py-8 text-gray-500">백업 파일이 없습니다</div>
          ) : (
            backups.map((backup) => (
              <div key={backup.filename} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <div className="font-semibold text-gray-800">{backup.filename}</div>
                  <div className="text-xs text-gray-500">
                    {backup.size_mb.toFixed(2)} MB · {new Date(backup.created).toLocaleString()}
                  </div>
                </div>
                <button
                  onClick={() => handleRestore(backup.filename)}
                  className="px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center gap-2"
                >
                  <Upload className="w-4 h-4" />
                  복원
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// ========== 로그 탭 ==========
function LogsTab() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await adminGet('/api/admin/logs/recent?limit=100');
      if (data.success) {
        setLogs(data.logs);
      }
    } catch (error) {
      console.error('로그 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-800">시스템 로그</h3>
        <button
          onClick={loadLogs}
          disabled={loading}
          className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
        >
          {loading ? '로딩 중...' : '새로고침'}
        </button>
      </div>

      <div className="bg-gray-900 rounded-lg p-4 h-[600px] overflow-y-auto font-mono text-sm text-green-400">
        {logs.length === 0 ? (
          <div className="text-center text-gray-500 py-8">로그가 없습니다</div>
        ) : (
          logs.map((log, index) => (
            <div key={index} className="mb-1">
              <span className="text-gray-500">[{log.timestamp}]</span>{' '}
              <span className={`font-semibold ${
                log.level === 'ERROR' ? 'text-red-400' :
                log.level === 'WARN' ? 'text-yellow-400' :
                'text-green-400'
              }`}>{log.level}</span>{' '}
              <span className="text-gray-300">{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// ========== 설정 탭 ==========
function SettingsTab() {
  const [envVars, setEnvVars] = useState<Record<string, string>>({});
  const [templates, setTemplates] = useState<any[]>([]);
  const [defaultTemplates, setDefaultTemplates] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [playautoCredentials, setPlayautoCredentials] = useState({
    api_key: '',
    email: '',
    password: '',
    api_base_url: 'https://openapi.playauto.io/api',
    enabled: true,
    auto_sync_enabled: false,
    auto_sync_interval: 300,
    encrypt_credentials: false
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadEnvVars();
    loadTemplates();
    loadDefaultTemplates();
  }, []);

  const loadEnvVars = async () => {
    try {
      const data = await adminGet('/api/admin/settings/env');
      if (data.success) {
        setEnvVars(data.environment_variables);
      }
    } catch (error) {
      console.error('환경 변수 로드 실패:', error);
    }
  };

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/playauto/templates`);
      const data = await res.json();
      if (data.success) {
        setTemplates(data.data.template_info || []);
      }
    } catch (error) {
      console.error('템플릿 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadDefaultTemplates = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/playauto/templates/default`);
      const data = await res.json();
      if (data.success && data.templates) {
        setDefaultTemplates(data.templates);
      }
    } catch (error) {
      console.error('기본 템플릿 로드 실패:', error);
    }
  };

  const handleToggleTemplate = (template: any) => {
    const isSelected = defaultTemplates.some(t => t.template_no === template.template_no);

    if (isSelected) {
      setDefaultTemplates(defaultTemplates.filter(t => t.template_no !== template.template_no));
    } else {
      setDefaultTemplates([...defaultTemplates, {
        shop_cd: template.shop_cd,
        shop_id: template.shop_id,
        shop_name: template.shop_name,
        template_no: template.template_no,
        template_name: template.name
      }]);
    }
  };

  const handleSavePlayautoCredentials = async () => {
    if (!playautoCredentials.api_key || !playautoCredentials.email || !playautoCredentials.password) {
      alert('API 키, 이메일, 비밀번호를 모두 입력해주세요.');
      return;
    }

    setSaving(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/playauto/settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(playautoCredentials)
      });

      const data = await res.json();

      if (data.success) {
        alert('플레이오토 API 설정이 저장되었습니다.\n\n이제 템플릿 목록을 불러올 수 있습니다.');
        // 템플릿 다시 로드
        loadTemplates();
      } else {
        alert('저장 실패: ' + (data.detail || data.error || '알 수 없는 오류'));
      }
    } catch (error) {
      console.error('API 설정 저장 실패:', error);
      alert('API 설정 저장 중 오류가 발생했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveTemplates = async () => {
    if (defaultTemplates.length === 0) {
      alert('최소 1개 이상의 템플릿을 선택해주세요.');
      return;
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/playauto/templates/save-default`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          templates: defaultTemplates
        })
      });

      const data = await res.json();

      if (data.success) {
        alert('기본 템플릿이 저장되었습니다.\n\n이제 상품 등록 시 자동으로 이 템플릿이 사용됩니다.');
      } else {
        alert('저장 실패: ' + (data.error || '알 수 없는 오류'));
      }
    } catch (error) {
      console.error('템플릿 저장 실패:', error);
      alert('템플릿 저장 중 오류가 발생했습니다.');
    }
  };

  return (
    <div className="space-y-6">
      {/* 플레이오토 API 자격 증명 */}
      <div className="bg-white rounded-xl p-6 border-2 border-blue-200">
        <div className="flex items-center gap-2 mb-4">
          <Settings className="w-6 h-6 text-blue-600" />
          <h3 className="text-xl font-bold text-gray-800">플레이오토 API 자격 증명</h3>
        </div>
        <p className="text-sm text-gray-600 mb-6">
          플레이오토 API를 사용하려면 먼저 자격 증명을 입력해주세요.
        </p>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              API 키 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={playautoCredentials.api_key}
              onChange={(e) => setPlayautoCredentials({ ...playautoCredentials, api_key: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="플레이오토 API 키를 입력하세요"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              이메일 <span className="text-red-500">*</span>
            </label>
            <input
              type="email"
              value={playautoCredentials.email}
              onChange={(e) => setPlayautoCredentials({ ...playautoCredentials, email: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="example@email.com"
            />
          </div>

          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">
              비밀번호 <span className="text-red-500">*</span>
            </label>
            <input
              type="password"
              value={playautoCredentials.password}
              onChange={(e) => setPlayautoCredentials({ ...playautoCredentials, password: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="비밀번호를 입력하세요"
            />
          </div>

          <button
            onClick={handleSavePlayautoCredentials}
            disabled={saving || !playautoCredentials.api_key || !playautoCredentials.email || !playautoCredentials.password}
            className="w-full px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold flex items-center justify-center gap-2"
          >
            {saving ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                저장 중...
              </>
            ) : (
              '자격 증명 저장'
            )}
          </button>
        </div>

        <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
            <div className="text-sm text-yellow-800">
              <p className="font-semibold mb-1">참고사항:</p>
              <ul className="list-disc list-inside space-y-1">
                <li>자격 증명을 저장하면 DB에 안전하게 저장됩니다</li>
                <li>저장 후 아래에서 템플릿 목록을 확인할 수 있습니다</li>
                <li>템플릿이 보이지 않으면 페이지를 새로고침해주세요</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* 플레이오토 템플릿 설정 */}
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <h3 className="text-xl font-bold text-gray-800 mb-4">플레이오토 기본 템플릿 설정</h3>
        <p className="text-sm text-gray-600 mb-4">
          상품 등록 시 자동으로 사용할 템플릿을 선택하세요. 여러 개를 선택하면 모든 쇼핑몰에 등록됩니다.
        </p>

        {loading ? (
          <div className="flex justify-center items-center py-20">
            <RefreshCw className="w-8 h-8 text-blue-500 animate-spin" />
          </div>
        ) : templates.length === 0 ? (
          <div className="text-center py-10 text-gray-500">
            <AlertCircle className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p className="font-semibold text-gray-700 mb-2">등록된 템플릿이 없습니다</p>
            <div className="text-sm space-y-1">
              <p>다음 사항을 확인해주세요:</p>
              <ul className="list-disc list-inside text-left max-w-md mx-auto mt-2 space-y-1">
                <li>위에서 플레이오토 API 자격 증명을 올바르게 입력했는지 확인</li>
                <li>플레이오토 웹사이트에서 템플릿을 먼저 등록했는지 확인</li>
                <li>자격 증명 저장 후 페이지 새로고침 시도</li>
              </ul>
            </div>
            <button
              onClick={loadTemplates}
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors inline-flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              템플릿 다시 불러오기
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-2 mb-4 max-h-[400px] overflow-y-auto">
              {templates.map((template) => {
                const isSelected = defaultTemplates.some(t => t.template_no === template.template_no);
                return (
                  <button
                    key={template.template_no}
                    onClick={() => handleToggleTemplate(template)}
                    className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
                      isSelected
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 bg-white hover:border-blue-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-semibold text-gray-800">{template.name}</span>
                          <span className="px-2 py-0.5 bg-gray-200 rounded text-xs text-gray-600">
                            {template.shop_name}
                          </span>
                        </div>
                        <div className="text-sm text-gray-600">
                          템플릿 번호: {template.template_no} | 적용 상품: {template.apply_prod_cnt}개
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          쇼핑몰: {template.shop_id}
                        </div>
                      </div>
                      <div className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                        isSelected ? 'border-blue-500 bg-blue-500' : 'border-gray-300'
                      }`}>
                        {isSelected && <CheckCircle className="w-5 h-5 text-white" />}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>

            {defaultTemplates.length > 0 && (
              <div className="bg-blue-50 rounded-lg p-4 mb-4">
                <div className="text-sm font-semibold text-gray-700 mb-2">
                  선택된 템플릿 ({defaultTemplates.length}개):
                </div>
                <div className="space-y-1">
                  {defaultTemplates.map((template) => (
                    <div key={template.template_no} className="text-sm text-gray-600">
                      • {template.template_name} ({template.shop_name})
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              onClick={handleSaveTemplates}
              disabled={defaultTemplates.length === 0}
              className="w-full px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold"
            >
              기본 템플릿 저장
            </button>
          </>
        )}
      </div>

      {/* 환경 변수 */}
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <h3 className="text-xl font-bold text-gray-800 mb-4">환경 변수</h3>
        <div className="bg-gray-50 rounded-lg p-4 space-y-2 max-h-[400px] overflow-y-auto">
          {Object.entries(envVars).map(([key, value]) => (
            <div key={key} className="flex items-center justify-between p-3 bg-white rounded border border-gray-200">
              <span className="font-semibold text-gray-700">{key}</span>
              <span className="text-gray-600 font-mono text-sm">{value}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ========== 정리 탭 ==========
function CleanupTab() {
  const handleCleanupOrders = async () => {
    const days = prompt('몇 일 이전의 주문을 삭제하시겠습니까? (기본: 90일)', '90');
    if (!days) return;

    if (!confirm(`${days}일 이전의 주문을 삭제하시겠습니까?`)) return;

    try {
      const data = await adminPost('/api/admin/cleanup/old-orders?days=${days}');
      if (data.success) {
        alert(`✓ ${data.deleted_count}개의 주문이 삭제되었습니다.`);
      }
    } catch (error) {
      alert('삭제 실패: ' + error);
    }
  };

  const handleCleanupTemp = async () => {
    if (!confirm('임시 파일을 정리하시겠습니까?')) return;

    try {
      const data = await adminPost('/api/admin/cleanup/temp-files');
      if (data.success) {
        alert(`✓ ${data.deleted_files}개 파일 삭제 (${data.freed_mb} MB 확보)`);
      }
    } catch (error) {
      alert('정리 실패: ' + error);
    }
  };

  const handleClearCache = () => {
    localStorage.clear();
    sessionStorage.clear();
    alert('✓ 브라우저 캐시가 삭제되었습니다!');
  };

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <h3 className="text-xl font-bold text-gray-800 mb-4">데이터 정리</h3>
        <div className="space-y-3">
          <CleanupButton
            title="오래된 주문 삭제"
            description="지정된 기간 이전의 주문 데이터를 삭제합니다"
            onClick={handleCleanupOrders}
            color="red"
          />
          <CleanupButton
            title="임시 파일 정리"
            description="시스템의 임시 파일을 삭제합니다"
            onClick={handleCleanupTemp}
            color="orange"
          />
          <CleanupButton
            title="캐시 삭제"
            description="브라우저 캐시를 삭제합니다"
            onClick={handleClearCache}
            color="blue"
          />
        </div>
      </div>
    </div>
  );
}

function CleanupButton({ title, description, onClick, color }: {
  title: string;
  description: string;
  onClick: () => void;
  color: 'red' | 'orange' | 'blue';
}) {
  const colors = {
    red: 'bg-red-50 border-red-200 hover:bg-red-100',
    orange: 'bg-orange-50 border-orange-200 hover:bg-orange-100',
    blue: 'bg-blue-50 border-blue-200 hover:bg-blue-100'
  };

  return (
    <button
      onClick={onClick}
      className={`w-full p-4 rounded-lg border-2 transition-colors text-left ${colors[color]}`}
    >
      <div className="font-semibold text-gray-800 mb-1">{title}</div>
      <div className="text-sm text-gray-600">{description}</div>
    </button>
  );
}

// ========== 성능 탭 ==========
function PerformanceTab() {
  const [metrics, setMetrics] = useState<any>(null);

  useEffect(() => {
    loadMetrics();
  }, []);

  const loadMetrics = async () => {
    try {
      const data = await adminGet('/api/admin/performance/metrics');
      if (data.success) {
        setMetrics(data);
      }
    } catch (error) {
      console.error('성능 메트릭 로드 실패:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 border border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-4">CPU</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">평균 사용률</span>
              <span className="font-bold">{metrics?.cpu.average_percent.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">코어 수</span>
              <span className="font-bold">{metrics?.cpu.core_count}개</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-4">메모리</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">사용 중</span>
              <span className="font-bold">{(metrics?.memory.used_mb / 1024).toFixed(1)} GB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">사용률</span>
              <span className="font-bold">{metrics?.memory.percent.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-4">디스크 I/O</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">읽기</span>
              <span className="font-bold">{metrics?.disk.read_mb.toFixed(1)} MB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">쓰기</span>
              <span className="font-bold">{metrics?.disk.write_mb.toFixed(1)} MB</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 border border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-4">네트워크</h3>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-600">송신</span>
              <span className="font-bold">{metrics?.network.sent_mb.toFixed(1)} MB</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">수신</span>
              <span className="font-bold">{metrics?.network.recv_mb.toFixed(1)} MB</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ========== 개발자 도구 탭 ==========
function DevToolsTab() {
  const [testResults, setTestResults] = useState<any>(null);

  const handleTestAPI = async () => {
    try {
      const data = await adminGet('/api/admin/api/test');
      if (data.success) {
        setTestResults(data.tests);
      }
    } catch (error) {
      alert('API 테스트 실패: ' + error);
    }
  };

  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200">
      <h3 className="text-xl font-bold text-gray-800 mb-4">API 테스트</h3>
      <button
        onClick={handleTestAPI}
        className="px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors mb-4"
      >
        API 엔드포인트 테스트
      </button>

      {testResults && (
        <div className="space-y-2">
          {testResults.map((test: any, index: number) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="font-mono text-sm text-gray-700">{test.endpoint}</span>
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-600">{test.response_time_ms.toFixed(2)} ms</span>
                <span className={`px-2 py-1 rounded text-xs font-semibold ${
                  test.status === 'OK' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}>
                  {test.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ========== 활동 로그 탭 ==========
function ActivityTab() {
  return (
    <div className="bg-white rounded-xl p-6 border border-gray-200">
      <h3 className="text-xl font-bold text-gray-800 mb-4">사용자 활동</h3>
      <div className="text-center py-20 text-gray-500">
        <Users className="w-16 h-16 mx-auto mb-4 text-gray-300" />
        <p>활동 로그 기능은 추후 구현 예정입니다</p>
      </div>
    </div>
  );
}

// ========== 카테고리 매핑 탭 ==========
function CategoryMappingTab() {
  const [mappings, setMappings] = useState<any[]>([]);
  const [availableInfoCodes, setAvailableInfoCodes] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editMode, setEditMode] = useState<'none' | 'add' | 'edit'>('none');
  const [editingId, setEditingId] = useState<number | null>(null);
  const [formData, setFormData] = useState({
    level1: '',
    info_code: '',
    info_code_name: '',
    notes: ''
  });

  useEffect(() => {
    loadMappings();
    loadAvailableInfoCodes();
  }, []);

  const loadMappings = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/category-infocode-mappings`);
      if (!response.ok) throw new Error('매핑 조회 실패');
      const data = await response.json();
      setMappings(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableInfoCodes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/available-infocodes`);
      if (!response.ok) throw new Error('infoCode 목록 조회 실패');
      const data = await response.json();
      setAvailableInfoCodes(data);
    } catch (err: any) {
      console.error('infoCode 목록 조회 실패:', err);
    }
  };

  const handleAdd = () => {
    setEditMode('add');
    setFormData({ level1: '', info_code: '', info_code_name: '', notes: '' });
  };

  const handleEdit = (mapping: any) => {
    setEditMode('edit');
    setEditingId(mapping.id);
    setFormData({
      level1: mapping.level1,
      info_code: mapping.info_code,
      info_code_name: mapping.info_code_name,
      notes: mapping.notes || ''
    });
  };

  const handleCancel = () => {
    setEditMode('none');
    setEditingId(null);
    setFormData({ level1: '', info_code: '', info_code_name: '', notes: '' });
  };

  const handleSave = async () => {
    try {
      setLoading(true);

      if (editMode === 'add') {
        const response = await fetch(`${API_BASE_URL}/api/category-infocode-mappings`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || '추가 실패');
        }
      } else if (editMode === 'edit' && editingId) {
        const response = await fetch(`${API_BASE_URL}/api/category-infocode-mappings/${editingId}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            info_code: formData.info_code,
            info_code_name: formData.info_code_name,
            notes: formData.notes
          })
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.detail || '수정 실패');
        }
      }

      await loadMappings();
      handleCancel();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number, level1: string) => {
    if (!confirm(`'${level1}' 매핑을 삭제하시겠습니까?`)) return;

    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/category-infocode-mappings/${id}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '삭제 실패');
      }

      await loadMappings();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInfoCodeChange = (code: string) => {
    const selected = availableInfoCodes.find((ic: any) => ic.code === code);
    setFormData({
      ...formData,
      info_code: code,
      info_code_name: selected?.name || ''
    });
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold text-gray-800">카테고리 - infoCode 매핑 관리</h3>
          {editMode === 'none' && (
            <button
              onClick={handleAdd}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              새 매핑 추가
            </button>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {editMode !== 'none' && (
          <div className="bg-gray-50 p-4 rounded-lg mb-6 space-y-4">
            <h4 className="text-lg font-semibold">
              {editMode === 'add' ? '새 매핑 추가' : '매핑 수정'}
            </h4>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">카테고리 (level1)</label>
                <input
                  type="text"
                  value={formData.level1}
                  onChange={(e) => setFormData({ ...formData, level1: e.target.value })}
                  disabled={editMode === 'edit'}
                  placeholder="예: 간편식"
                  className="w-full border rounded px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">infoCode</label>
                <select
                  value={formData.info_code}
                  onChange={(e) => handleInfoCodeChange(e.target.value)}
                  className="w-full border rounded px-3 py-2"
                >
                  <option value="">선택하세요</option>
                  {availableInfoCodes.map((ic: any) => (
                    <option key={ic.code} value={ic.code}>
                      {ic.code} - {ic.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">infoCode 이름</label>
                <input
                  type="text"
                  value={formData.info_code_name}
                  onChange={(e) => setFormData({ ...formData, info_code_name: e.target.value })}
                  placeholder="예: 가공식품"
                  className="w-full border rounded px-3 py-2"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">메모</label>
                <input
                  type="text"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  placeholder="예: 즉석밥, 죽, 국/탕/찌개 등"
                  className="w-full border rounded px-3 py-2"
                />
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={loading}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
              >
                {loading ? '저장 중...' : '저장'}
              </button>
              <button
                onClick={handleCancel}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                취소
              </button>
            </div>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100">
                <th className="border px-4 py-2 text-left">카테고리 (level1)</th>
                <th className="border px-4 py-2 text-left">infoCode</th>
                <th className="border px-4 py-2 text-left">infoCode 이름</th>
                <th className="border px-4 py-2 text-left">메모</th>
                <th className="border px-4 py-2 text-center">작업</th>
              </tr>
            </thead>
            <tbody>
              {loading && mappings.length === 0 ? (
                <tr>
                  <td colSpan={5} className="border px-4 py-8 text-center text-gray-500">
                    로딩 중...
                  </td>
                </tr>
              ) : mappings.length === 0 ? (
                <tr>
                  <td colSpan={5} className="border px-4 py-8 text-center text-gray-500">
                    등록된 매핑이 없습니다
                  </td>
                </tr>
              ) : (
                mappings.map((mapping: any) => (
                  <tr key={mapping.id} className="hover:bg-gray-50">
                    <td className="border px-4 py-2 font-medium">{mapping.level1}</td>
                    <td className="border px-4 py-2 text-sm font-mono">{mapping.info_code}</td>
                    <td className="border px-4 py-2">{mapping.info_code_name}</td>
                    <td className="border px-4 py-2 text-sm text-gray-600">{mapping.notes || '-'}</td>
                    <td className="border px-4 py-2 text-center">
                      <div className="flex gap-2 justify-center">
                        <button
                          onClick={() => handleEdit(mapping)}
                          disabled={editMode !== 'none'}
                          className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 disabled:opacity-50"
                        >
                          수정
                        </button>
                        <button
                          onClick={() => handleDelete(mapping.id, mapping.level1)}
                          disabled={editMode !== 'none'}
                          className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 disabled:opacity-50"
                        >
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        <div className="mt-4 text-sm text-gray-600">
          총 {mappings.length}개 매핑
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <h3 className="text-xl font-bold text-gray-800 mb-4">사용 가능한 infoCode 목록</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {availableInfoCodes.map((ic: any) => (
            <div key={ic.code} className="border rounded p-3 bg-gray-50">
              <div className="font-mono text-sm text-blue-600">{ic.code}</div>
              <div className="font-semibold mt-1">{ic.name}</div>
              <div className="text-xs text-gray-600 mt-1">{ic.description}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
