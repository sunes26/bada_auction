/**
 * 통합 설정 페이지
 *
 * 플레이오토 설정, 알림 설정, 소싱처 계정 관리를 통합한 설정 페이지
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { Settings, Bell, Key, Play, Eye, EyeOff, RefreshCw, CheckCircle, Plus, Trash2 } from 'lucide-react';
import { toast } from 'sonner';
import { API_BASE_URL } from '@/lib/api';

type SettingsTab = 'playauto' | 'notifications' | 'accounts';

interface PlayautoSettings {
  api_key: string;
  email: string;
  password: string;
  enabled: boolean;
  auto_sync_enabled: boolean;
  auto_sync_interval: number;
}

interface WebhookSetting {
  id?: number;
  webhook_type: 'slack' | 'discord';
  webhook_url: string;
  enabled: boolean;
  notification_types: string[];
}

interface SourcingAccount {
  id: number;
  source: string;
  account_id: string;
  account_password: string;
  notes: string;
  created_at: string;
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('playauto');
  const [loading, setLoading] = useState(false);

  // 플레이오토 설정 state
  const [playautoSettings, setPlayautoSettings] = useState<PlayautoSettings>({
    api_key: '',
    email: '',
    password: '',
    enabled: false,
    auto_sync_enabled: false,
    auto_sync_interval: 30
  });
  const [showApiSecret, setShowApiSecret] = useState(false);
  const [settingsInfo, setSettingsInfo] = useState<any>(null);

  // 알림 설정 state
  const [slackWebhook, setSlackWebhook] = useState<WebhookSetting>({
    webhook_type: 'slack',
    webhook_url: '',
    enabled: false,
    notification_types: ['all']
  });
  const [discordWebhook, setDiscordWebhook] = useState<WebhookSetting>({
    webhook_type: 'discord',
    webhook_url: '',
    enabled: false,
    notification_types: ['all']
  });

  // 소싱처 계정 state
  const [accounts, setAccounts] = useState<SourcingAccount[]>([]);
  const [accountForm, setAccountForm] = useState({
    source: 'ssg',
    account_id: '',
    account_password: '',
    notes: ''
  });

  // 데이터 로드
  useEffect(() => {
    if (activeTab === 'playauto') {
      loadPlayautoSettings();
    } else if (activeTab === 'notifications') {
      loadNotificationSettings();
    } else if (activeTab === 'accounts') {
      fetchAccounts();
    }
  }, [activeTab]);

  // 플레이오토 설정 로드
  const loadPlayautoSettings = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/playauto/settings`);
      if (!res.ok) throw new Error('설정 조회 실패');
      const data = await res.json();
      setSettingsInfo(data);
      if (data.api_key) {
        setPlayautoSettings({
          api_key: data.api_key,
          email: data.email || '',
          password: data.password || '',
          enabled: data.enabled === 'true',
          auto_sync_enabled: data.auto_sync_enabled === 'true',
          auto_sync_interval: parseInt(data.auto_sync_interval || '30')
        });
      }
    } catch (error) {
      console.error('설정 로드 실패:', error);
    }
  };

  // 플레이오토 설정 저장
  const savePlayautoSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/playauto/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(playautoSettings)
      });
      const data = await res.json();
      if (data.success) {
        toast.success('설정이 저장되었습니다');
        await loadPlayautoSettings();
      }
    } catch (error) {
      console.error('설정 저장 실패:', error);
      toast.error('설정 저장에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 플레이오토 연결 테스트
  const testPlayautoConnection = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/playauto/test-connection`, {
        method: 'POST'
      });
      const data = await res.json();
      if (data.success) {
        toast.success('연결 테스트 성공!');
      } else {
        toast.error(`연결 실패: ${data.message}`);
      }
    } catch (error) {
      console.error('연결 테스트 실패:', error);
      toast.error('연결 테스트에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 알림 설정 로드
  const loadNotificationSettings = async () => {
    try {
      // Slack 웹훅 로드
      const slackRes = await fetch(`${API_BASE_URL}/api/notifications/webhook/slack`);
      const slackData = await slackRes.json();
      if (slackData.success && slackData.webhook) {
        setSlackWebhook(slackData.webhook);
      }

      // Discord 웹훅 로드
      const discordRes = await fetch(`${API_BASE_URL}/api/notifications/webhook/discord`);
      const discordData = await discordRes.json();
      if (discordData.success && discordData.webhook) {
        setDiscordWebhook(discordData.webhook);
      }
    } catch (error) {
      console.error('알림 설정 로드 실패:', error);
    }
  };

  // 웹훅 저장
  const saveWebhook = async (webhook: WebhookSetting) => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/notifications/webhook/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(webhook)
      });
      const data = await res.json();
      if (data.success) {
        toast.success(`${webhook.webhook_type === 'slack' ? 'Slack' : 'Discord'} 웹훅이 저장되었습니다`);
        await loadNotificationSettings();
      }
    } catch (error) {
      console.error('웹훅 저장 실패:', error);
      toast.error('웹훅 저장에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 테스트 알림 발송
  const sendTestNotification = async (type: 'slack' | 'discord') => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/notifications/webhook/test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ webhook_type: type })
      });
      const data = await res.json();
      if (data.success) {
        toast.success('테스트 알림이 발송되었습니다');
      }
    } catch (error) {
      console.error('테스트 알림 발송 실패:', error);
      toast.error('테스트 알림 발송에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 소싱처 계정 로드
  const fetchAccounts = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/sourcing/accounts`);
      const data = await res.json();
      if (data.success) {
        setAccounts(data.accounts || []);
      }
    } catch (error) {
      console.error('계정 로드 실패:', error);
    }
  };

  // 소싱처 계정 추가
  const addAccount = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/sourcing/accounts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(accountForm)
      });
      const data = await res.json();
      if (data.success) {
        toast.success('소싱처 계정이 등록되었습니다');
        setAccountForm({
          source: 'ssg',
          account_id: '',
          account_password: '',
          notes: ''
        });
        fetchAccounts();
      }
    } catch (error) {
      console.error('계정 등록 실패:', error);
      toast.error('계정 등록에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 소싱처 계정 삭제
  const deleteAccount = async (accountId: number) => {
    if (!confirm('정말 이 계정을 삭제하시겠습니까?')) return;

    try {
      const res = await fetch(`${API_BASE_URL}/api/sourcing/accounts/${accountId}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (data.success) {
        toast.success('계정이 삭제되었습니다');
        fetchAccounts();
      }
    } catch (error) {
      console.error('계정 삭제 실패:', error);
      toast.error('계정 삭제에 실패했습니다');
    }
  };

  const notificationTypes = [
    { id: 'new_order', label: '신규 주문 알림', description: '새로운 주문이 들어올 때' },
    { id: 'price_change', label: '가격 변동 알림', description: '소싱가 변동 감지 시' },
    { id: 'inventory_out_of_stock', label: '재고 부족 알림', description: '상품 품절 시' },
    { id: 'margin_alert', label: '역마진 경고', description: '마진이 마이너스일 때' },
    { id: 'order_sync', label: '주문 동기화 결과', description: 'PlayAuto 주문 수집 완료 시' }
  ];

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 p-8 border border-white/20">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">⚙️ 설정</h1>
        <p className="text-gray-600">시스템 설정 및 연동 관리</p>
      </div>

      {/* 서브탭 네비게이션 */}
      <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/10 border border-white/20 overflow-hidden">
        <div className="flex border-b border-gray-200">
          <button
            onClick={() => setActiveTab('playauto')}
            className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors ${
              activeTab === 'playauto'
                ? 'text-purple-600 border-b-2 border-purple-600 bg-purple-50/50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            <Settings className="w-5 h-5" />
            플레이오토 설정
          </button>
          <button
            onClick={() => setActiveTab('notifications')}
            className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors ${
              activeTab === 'notifications'
                ? 'text-purple-600 border-b-2 border-purple-600 bg-purple-50/50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            <Bell className="w-5 h-5" />
            알림 설정
          </button>
          <button
            onClick={() => setActiveTab('accounts')}
            className={`flex items-center gap-2 px-6 py-4 font-medium transition-colors ${
              activeTab === 'accounts'
                ? 'text-purple-600 border-b-2 border-purple-600 bg-purple-50/50'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
            }`}
          >
            <Key className="w-5 h-5" />
            소싱처 계정
          </button>
        </div>

        {/* 컨텐츠 영역 */}
        <div className="p-8">
          {/* 플레이오토 설정 탭 */}
          {activeTab === 'playauto' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">플레이오토 API 설정</h2>
                <p className="text-gray-600">플레이오토 연동을 위한 API 키 및 계정 정보를 설정합니다</p>
              </div>

              {/* 현재 설정 상태 */}
              {settingsInfo && (
                <div className="bg-gradient-to-br from-blue-50 to-purple-50 p-6 rounded-xl border border-blue-200">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`w-3 h-3 rounded-full ${settingsInfo.enabled === 'true' ? 'bg-green-500' : 'bg-gray-400'}`} />
                    <h3 className="text-lg font-semibold text-gray-800">
                      연동 상태: {settingsInfo.enabled === 'true' ? '활성화됨' : '비활성화됨'}
                    </h3>
                  </div>
                  {settingsInfo.sol_no && (
                    <p className="text-sm text-gray-600">솔루션 번호: {settingsInfo.sol_no}</p>
                  )}
                </div>
              )}

              {/* 설정 폼 */}
              <form onSubmit={savePlayautoSettings} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    API Key
                  </label>
                  <div className="relative">
                    <input
                      type={showApiSecret ? 'text' : 'password'}
                      value={playautoSettings.api_key}
                      onChange={(e) => setPlayautoSettings({ ...playautoSettings, api_key: e.target.value })}
                      className="w-full px-4 py-3 pr-12 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="PlayAuto API Key"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowApiSecret(!showApiSecret)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    >
                      {showApiSecret ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      이메일
                    </label>
                    <input
                      type="email"
                      value={playautoSettings.email}
                      onChange={(e) => setPlayautoSettings({ ...playautoSettings, email: e.target.value })}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="your@email.com"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      비밀번호
                    </label>
                    <input
                      type="password"
                      value={playautoSettings.password}
                      onChange={(e) => setPlayautoSettings({ ...playautoSettings, password: e.target.value })}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="••••••••"
                      required
                    />
                  </div>
                </div>

                <div className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg">
                  <input
                    type="checkbox"
                    id="auto_sync"
                    checked={playautoSettings.auto_sync_enabled}
                    onChange={(e) => setPlayautoSettings({ ...playautoSettings, auto_sync_enabled: e.target.checked })}
                    className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                  />
                  <label htmlFor="auto_sync" className="text-sm font-medium text-gray-700">
                    자동 동기화 활성화 ({playautoSettings.auto_sync_interval}분마다)
                  </label>
                </div>

                <div className="flex gap-4">
                  <button
                    type="button"
                    onClick={testPlayautoConnection}
                    disabled={loading || !playautoSettings.api_key || !playautoSettings.email || !playautoSettings.password}
                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <>
                        <RefreshCw className="w-5 h-5 animate-spin" />
                        테스트 중...
                      </>
                    ) : (
                      <>
                        <Play className="w-5 h-5" />
                        연결 테스트
                      </>
                    )}
                  </button>

                  <button
                    type="submit"
                    disabled={loading || !playautoSettings.api_key || !playautoSettings.email || !playautoSettings.password}
                    className="flex-1 flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-600 text-white rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {loading ? (
                      <>
                        <RefreshCw className="w-5 h-5 animate-spin" />
                        저장 중...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-5 h-5" />
                        설정 저장
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* 알림 설정 탭 */}
          {activeTab === 'notifications' && (
            <div className="space-y-8">
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">알림 설정</h2>
                <p className="text-gray-600">Slack 및 Discord 웹훅을 통한 실시간 알림을 설정합니다</p>
              </div>

              {/* Slack 웹훅 */}
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-6 rounded-xl border border-purple-200">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-purple-500 rounded-xl flex items-center justify-center">
                    <Bell className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">Slack 알림</h3>
                    <p className="text-sm text-gray-600">Slack 워크스페이스로 알림 전송</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Webhook URL
                    </label>
                    <input
                      type="url"
                      value={slackWebhook.webhook_url}
                      onChange={(e) => setSlackWebhook({ ...slackWebhook, webhook_url: e.target.value })}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="https://hooks.slack.com/services/..."
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="slack_enabled"
                      checked={slackWebhook.enabled}
                      onChange={(e) => setSlackWebhook({ ...slackWebhook, enabled: e.target.checked })}
                      className="w-5 h-5 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                    />
                    <label htmlFor="slack_enabled" className="text-sm font-medium text-gray-700">
                      Slack 알림 활성화
                    </label>
                  </div>

                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">알림 종류</p>
                    <div className="space-y-2">
                      {notificationTypes.map(type => (
                        <div key={type.id} className="flex items-center gap-3 p-3 bg-white rounded-lg">
                          <input
                            type="checkbox"
                            id={`slack_${type.id}`}
                            checked={slackWebhook.notification_types.includes('all') || slackWebhook.notification_types.includes(type.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                if (!slackWebhook.notification_types.includes(type.id)) {
                                  setSlackWebhook({
                                    ...slackWebhook,
                                    notification_types: [...slackWebhook.notification_types.filter(t => t !== 'all'), type.id]
                                  });
                                }
                              } else {
                                setSlackWebhook({
                                  ...slackWebhook,
                                  notification_types: slackWebhook.notification_types.filter(t => t !== type.id && t !== 'all')
                                });
                              }
                            }}
                            className="w-4 h-4 text-purple-600 rounded focus:ring-2 focus:ring-purple-500"
                          />
                          <div className="flex-1">
                            <label htmlFor={`slack_${type.id}`} className="text-sm font-medium text-gray-700 cursor-pointer">
                              {type.label}
                            </label>
                            <p className="text-xs text-gray-500">{type.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={() => sendTestNotification('slack')}
                      disabled={loading || !slackWebhook.webhook_url}
                      className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      테스트 발송
                    </button>
                    <button
                      onClick={() => saveWebhook(slackWebhook)}
                      disabled={loading || !slackWebhook.webhook_url}
                      className="flex-1 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      저장
                    </button>
                  </div>
                </div>
              </div>

              {/* Discord 웹훅 */}
              <div className="bg-gradient-to-br from-indigo-50 to-blue-50 p-6 rounded-xl border border-indigo-200">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-indigo-500 rounded-xl flex items-center justify-center">
                    <Bell className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-800">Discord 알림</h3>
                    <p className="text-sm text-gray-600">Discord 채널로 알림 전송</p>
                  </div>
                </div>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Webhook URL
                    </label>
                    <input
                      type="url"
                      value={discordWebhook.webhook_url}
                      onChange={(e) => setDiscordWebhook({ ...discordWebhook, webhook_url: e.target.value })}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      placeholder="https://discord.com/api/webhooks/..."
                    />
                  </div>

                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      id="discord_enabled"
                      checked={discordWebhook.enabled}
                      onChange={(e) => setDiscordWebhook({ ...discordWebhook, enabled: e.target.checked })}
                      className="w-5 h-5 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500"
                    />
                    <label htmlFor="discord_enabled" className="text-sm font-medium text-gray-700">
                      Discord 알림 활성화
                    </label>
                  </div>

                  <div>
                    <p className="text-sm font-medium text-gray-700 mb-2">알림 종류</p>
                    <div className="space-y-2">
                      {notificationTypes.map(type => (
                        <div key={type.id} className="flex items-center gap-3 p-3 bg-white rounded-lg">
                          <input
                            type="checkbox"
                            id={`discord_${type.id}`}
                            checked={discordWebhook.notification_types.includes('all') || discordWebhook.notification_types.includes(type.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                if (!discordWebhook.notification_types.includes(type.id)) {
                                  setDiscordWebhook({
                                    ...discordWebhook,
                                    notification_types: [...discordWebhook.notification_types.filter(t => t !== 'all'), type.id]
                                  });
                                }
                              } else {
                                setDiscordWebhook({
                                  ...discordWebhook,
                                  notification_types: discordWebhook.notification_types.filter(t => t !== type.id && t !== 'all')
                                });
                              }
                            }}
                            className="w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500"
                          />
                          <div className="flex-1">
                            <label htmlFor={`discord_${type.id}`} className="text-sm font-medium text-gray-700 cursor-pointer">
                              {type.label}
                            </label>
                            <p className="text-xs text-gray-500">{type.description}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <button
                      onClick={() => sendTestNotification('discord')}
                      disabled={loading || !discordWebhook.webhook_url}
                      className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      테스트 발송
                    </button>
                    <button
                      onClick={() => saveWebhook(discordWebhook)}
                      disabled={loading || !discordWebhook.webhook_url}
                      className="flex-1 px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      저장
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 소싱처 계정 탭 */}
          {activeTab === 'accounts' && (
            <div className="space-y-6">
              <div>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">소싱처 계정 관리</h2>
                <p className="text-gray-600">SSG, 트레이더스, 오뚜기몰 등 소싱처 계정을 관리합니다</p>
              </div>

              {/* 계정 추가 폼 */}
              <form onSubmit={addAccount} className="space-y-6 p-6 bg-gray-50 rounded-xl">
                <h4 className="text-lg font-semibold text-gray-800">새 계정 등록</h4>
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">소싱처</label>
                    <select
                      value={accountForm.source}
                      onChange={(e) => setAccountForm({ ...accountForm, source: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    >
                      <option value="ssg">SSG.COM</option>
                      <option value="traders">홈플러스/Traders</option>
                      <option value="11st">11번가</option>
                      <option value="gmarket">G마켓</option>
                      <option value="smartstore">스마트스토어</option>
                      <option value="otokimall">오뚜기몰</option>
                      <option value="dongwonmall">동원몰</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">로그인 ID</label>
                    <input
                      type="text"
                      value={accountForm.account_id}
                      onChange={(e) => setAccountForm({ ...accountForm, account_id: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="아이디"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">비밀번호</label>
                    <input
                      type="password"
                      value={accountForm.account_password}
                      onChange={(e) => setAccountForm({ ...accountForm, account_password: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="••••••••"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">메모 (선택)</label>
                    <input
                      type="text"
                      value={accountForm.notes}
                      onChange={(e) => setAccountForm({ ...accountForm, notes: e.target.value })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="메모"
                    />
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-purple-500 to-pink-600 text-white px-6 py-3 rounded-xl font-semibold hover:shadow-lg transition-all disabled:opacity-50"
                >
                  <Plus className="w-5 h-5 inline mr-2" />
                  계정 추가
                </button>
              </form>

              {/* 계정 목록 */}
              <div className="space-y-3">
                {accounts.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    등록된 계정이 없습니다
                  </div>
                ) : (
                  accounts.map(account => (
                    <div key={account.id} className="bg-white p-6 rounded-xl border border-gray-200 flex items-center justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-semibold">
                            {account.source.toUpperCase()}
                          </span>
                          <span className="text-lg font-semibold text-gray-800">{account.account_id}</span>
                        </div>
                        {account.notes && (
                          <p className="text-sm text-gray-600">{account.notes}</p>
                        )}
                        <p className="text-xs text-gray-400 mt-1">
                          등록일: {new Date(account.created_at).toLocaleDateString('ko-KR')}
                        </p>
                      </div>
                      <button
                        onClick={() => deleteAccount(account.id)}
                        className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
