'use client';

import { useState, useEffect } from 'react';
import { Home, FileText, ShoppingCart, Package, Lock, DollarSign } from 'lucide-react';
import HomePage from '@/components/pages/HomePage';
import DetailPage from '@/components/pages/DetailPage';
import ProductSourcingPage from '@/components/pages/ProductSourcingPage';
import UnifiedOrderManagementPage from '@/components/pages/UnifiedOrderManagementPage';
import AdminPage from '@/components/pages/AdminPage';
import AccountingPage from '@/components/pages/AccountingPage';
import { ToastProvider } from '@/app/providers/ToastProvider';
import NotificationCenter from '@/components/ui/NotificationCenter';
import Breadcrumb from '@/components/ui/Breadcrumb';

type Page = 'home' | 'detail' | 'sourcing' | 'orders' | 'accounting' | 'admin';

export default function Main() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState<Page>('home');
  const [rightClickCount, setRightClickCount] = useState(0);
  const [lastRightClickTime, setLastRightClickTime] = useState(0);

  // 인증 체크
  useEffect(() => {
    const auth = localStorage.getItem('mulbada-auth');
    if (auth === 'authenticated') {
      setIsAuthenticated(true);
    }
  }, []);

  // 관리자 페이지 우클릭 감지
  useEffect(() => {
    if (!isAuthenticated) return;

    const handleContextMenu = (e: MouseEvent) => {
      e.preventDefault();

      const now = Date.now();
      const timeDiff = now - lastRightClickTime;

      if (timeDiff < 500) {
        setRightClickCount(prev => prev + 1);

        if (rightClickCount + 1 >= 2) {
          setCurrentPage('admin');
          setRightClickCount(0);
        }
      } else {
        setRightClickCount(1);
      }

      setLastRightClickTime(now);
    };

    document.addEventListener('contextmenu', handleContextMenu);
    return () => document.removeEventListener('contextmenu', handleContextMenu);
  }, [isAuthenticated, rightClickCount, lastRightClickTime]);

  // 로그인 처리
  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (password === '6312') {
      localStorage.setItem('mulbada-auth', 'authenticated');
      setIsAuthenticated(true);
      setError('');
    } else {
      setError('비밀번호가 올바르지 않습니다.');
      setPassword('');
    }
  };

  // 로그아웃 처리
  const handleLogout = () => {
    localStorage.removeItem('mulbada-auth');
    setIsAuthenticated(false);
    setPassword('');
  };

  // 로그인 화면
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 flex items-center justify-center relative overflow-hidden">
        {/* Background Decorations */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-400/20 to-purple-600/20 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-tr from-indigo-400/20 to-pink-600/20 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-cyan-400/10 to-blue-600/10 rounded-full blur-3xl" />
        </div>

        {/* Login Form */}
        <div className="relative z-10 w-full max-w-md px-6">
          <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 border border-white/20 p-8">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl mb-4 shadow-lg">
                <Lock className="w-10 h-10 text-white" />
              </div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2">
                물바다AI
              </h1>
              <p className="text-gray-600">로그인이 필요합니다</p>
            </div>

            <form onSubmit={handleLogin} className="space-y-6">
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                  비밀번호
                </label>
                <input
                  type="password"
                  id="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-white/50 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder="비밀번호를 입력하세요"
                  autoFocus
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
                  {error}
                </div>
              )}

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white py-3 rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02]"
              >
                로그인
              </button>
            </form>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      <ToastProvider />
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100 relative overflow-hidden">
        {/* Background Decorations */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 -right-40 w-80 h-80 bg-gradient-to-br from-blue-400/20 to-purple-600/20 rounded-full blur-3xl" />
          <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-gradient-to-tr from-indigo-400/20 to-pink-600/20 rounded-full blur-3xl" />
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-gradient-to-r from-cyan-400/10 to-blue-600/10 rounded-full blur-3xl" />
        </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 py-12 relative z-10">
        {/* Navigation */}
        <div className="flex justify-between items-center mb-8">
          <div className="bg-white/80 backdrop-blur-xl rounded-2xl p-2 shadow-2xl shadow-black/10 border border-white/20">
            <div className="flex relative">
              <NavButton
                active={currentPage === 'home'}
                onClick={() => setCurrentPage('home')}
                icon={<Home className="w-5 h-5" />}
                label="메인홈"
              />
              <NavButton
                active={currentPage === 'detail'}
                onClick={() => setCurrentPage('detail')}
                icon={<FileText className="w-5 h-5" />}
                label="상세페이지 생성기"
              />
              <NavButton
                active={currentPage === 'sourcing'}
                onClick={() => setCurrentPage('sourcing')}
                icon={<ShoppingCart className="w-5 h-5" />}
                label="상품"
              />
              <NavButton
                active={currentPage === 'orders'}
                onClick={() => setCurrentPage('orders')}
                icon={<Package className="w-5 h-5" />}
                label="주문 관리"
              />
              <NavButton
                active={currentPage === 'accounting'}
                onClick={() => setCurrentPage('accounting')}
                icon={<DollarSign className="w-5 h-5" />}
                label="회계"
              />
            </div>
          </div>
          <div className="flex-1 flex justify-end items-center gap-3">
            <NotificationCenter />
            <button
              onClick={handleLogout}
              className="px-6 py-3 bg-white/80 backdrop-blur-xl rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 border border-white/20 text-gray-700 hover:text-gray-900 font-semibold flex items-center gap-2"
            >
              <Lock className="w-4 h-4" />
              로그아웃
            </button>
          </div>
        </div>

        {/* Breadcrumb */}
        <Breadcrumb
          items={
            currentPage === 'home' ? [{ label: '메인홈' }] :
            currentPage === 'detail' ? [{ label: '상세페이지 생성기' }] :
            currentPage === 'sourcing' ? [{ label: '상품' }] :
            currentPage === 'orders' ? [{ label: '주문 관리' }] :
            currentPage === 'accounting' ? [{ label: '회계' }] :
            currentPage === 'admin' ? [{ label: '관리자' }] :
            [{ label: '메인홈' }]
          }
        />

        {/* Page Content */}
        <div>
          {currentPage === 'home' && <HomePage />}
          {currentPage === 'detail' && <DetailPage />}
          {currentPage === 'sourcing' && <ProductSourcingPage />}
          {currentPage === 'orders' && <UnifiedOrderManagementPage />}
          {currentPage === 'accounting' && <AccountingPage />}
          {currentPage === 'admin' && <AdminPage />}
        </div>
      </div>
      </div>
    </>
  );
}

function NavButton({ active, onClick, icon, label }: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`relative px-8 py-4 rounded-xl font-semibold text-lg transition-all duration-300 ${
        active ? 'text-white shadow-lg' : 'text-gray-600 hover:text-gray-800'
      }`}
    >
      {active && (
        <div className="absolute inset-0 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl shadow-lg" />
      )}
      <span className="relative flex items-center gap-3">
        {icon}
        {label}
      </span>
    </button>
  );
}
