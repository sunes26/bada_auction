'use client'

import React, { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Badge } from '@/components/ui/badge'
import { toast } from 'sonner'
import {
  Clock,
  PlayCircle,
  Save,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Package,
  TrendingUp
} from 'lucide-react'
import { format } from 'date-fns'
import { ko } from 'date-fns/locale'
import { API_BASE_URL } from '@/lib/api';

interface SchedulerConfig {
  enabled: boolean
  schedule_time: string
  retry_count: number
  notify_discord: boolean
  notify_slack: boolean
  discord_webhook: string | null
  slack_webhook: string | null
  last_run_at: string | null
  next_run_at: string | null
}

interface Job {
  id: number
  job_type: string
  status: string
  total_count: number
  success_count: number
  failed_count: number
  progress_percent: number
  started_at: string
  completed_at: string | null
}

export default function TrackingSchedulerPage() {
  const [config, setConfig] = useState<SchedulerConfig>({
    enabled: false,
    schedule_time: '17:00',
    retry_count: 3,
    notify_discord: false,
    notify_slack: false,
    discord_webhook: null,
    slack_webhook: null,
    last_run_at: null,
    next_run_at: null
  })
  const [jobs, setJobs] = useState<Job[]>([])
  const [pendingCount, setPendingCount] = useState(0)
  const [loading, setLoading] = useState(false)
  const [executing, setExecuting] = useState(false)

  // 설정 및 작업 목록 로드
  useEffect(() => {
    loadConfig()
    loadJobs()
    loadPendingCount()

    // 30초마다 갱신
    const interval = setInterval(() => {
      loadJobs()
      loadPendingCount()
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const loadConfig = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tracking-scheduler/config`)
      if (response.ok) {
        const data = await response.json()
        setConfig(data)
      }
    } catch (error) {
      console.error('설정 로드 실패:', error)
    }
  }

  const loadJobs = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tracking-scheduler/jobs/recent?limit=10`)
      if (response.ok) {
        const data = await response.json()
        setJobs(data.jobs || [])
      }
    } catch (error) {
      console.error('작업 목록 로드 실패:', error)
    }
  }

  const loadPendingCount = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tracking-scheduler/pending-count`)
      if (response.ok) {
        const data = await response.json()
        setPendingCount(data.pending_count || 0)
      }
    } catch (error) {
      console.error('대기 주문 수 로드 실패:', error)
    }
  }

  const handleSaveConfig = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/tracking-scheduler/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      })

      if (response.ok) {
        toast.success('스케줄러 설정이 저장되었습니다')
        loadConfig()
      } else {
        throw new Error('설정 저장 실패')
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '설정 저장 실패')
    } finally {
      setLoading(false)
    }
  }

  const handleManualExecute = async () => {
    setExecuting(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/tracking-scheduler/execute`, {
        method: 'POST'
      })

      if (response.ok) {
        const result = await response.json()
        toast.success(`송장 업로드 완료 - 성공: ${result.success_count}건, 실패: ${result.failed_count}건`)
        loadJobs()
        loadPendingCount()
      } else {
        throw new Error('송장 업로드 실패')
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : '송장 업로드 실패')
    } finally {
      setExecuting(false)
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-500"><CheckCircle2 className="w-3 h-3 mr-1" />완료</Badge>
      case 'running':
        return <Badge className="bg-blue-500"><RefreshCw className="w-3 h-3 mr-1 animate-spin" />실행 중</Badge>
      case 'failed':
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />실패</Badge>
      case 'pending':
        return <Badge variant="secondary"><AlertCircle className="w-3 h-3 mr-1" />대기</Badge>
      default:
        return <Badge variant="outline">{status}</Badge>
    }
  }

  const formatDateTime = (dateStr: string | null) => {
    if (!dateStr) return '-'
    try {
      return format(new Date(dateStr), 'yyyy-MM-dd HH:mm:ss', { locale: ko })
    } catch {
      return dateStr
    }
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">송장 자동 업로드 스케줄러</h1>
          <p className="text-muted-foreground mt-1">
            플레이오토로 송장 정보를 자동으로 업로드합니다
          </p>
        </div>
        <Button
          onClick={handleManualExecute}
          disabled={executing || pendingCount === 0}
          className="bg-gradient-to-r from-blue-500 to-purple-500"
        >
          {executing ? (
            <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />업로드 중...</>
          ) : (
            <><PlayCircle className="w-4 h-4 mr-2" />수동 실행</>
          )}
        </Button>
      </div>

      {/* 현황 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              업로드 대기 중
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-3xl font-bold">{pendingCount}</div>
              <Package className="w-8 h-8 text-blue-500" />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              송장번호가 입력된 주문
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              마지막 실행
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">
              {formatDateTime(config.last_run_at)}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {config.last_run_at ? '완료' : '실행 기록 없음'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              다음 실행 예정
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-medium">
              {config.enabled ? formatDateTime(config.next_run_at) : '비활성화'}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              {config.enabled ? `매일 ${config.schedule_time}` : '스케줄러가 꺼져 있습니다'}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 스케줄러 설정 */}
      <Card>
        <CardHeader>
          <CardTitle>스케줄러 설정</CardTitle>
          <CardDescription>
            자동 업로드 일정과 알림을 설정합니다
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* 활성화/비활성화 */}
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label>자동 업로드 활성화</Label>
              <div className="text-sm text-muted-foreground">
                매일 지정한 시간에 자동으로 송장을 업로드합니다
              </div>
            </div>
            <Switch
              checked={config.enabled}
              onCheckedChange={(checked) => setConfig({ ...config, enabled: checked })}
            />
          </div>

          {/* 실행 시간 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="schedule_time">실행 시간</Label>
              <div className="flex items-center">
                <Clock className="w-4 h-4 mr-2 text-muted-foreground" />
                <Input
                  id="schedule_time"
                  type="time"
                  value={config.schedule_time}
                  onChange={(e) => setConfig({ ...config, schedule_time: e.target.value })}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="retry_count">재시도 횟수</Label>
              <Input
                id="retry_count"
                type="number"
                min="0"
                max="10"
                value={config.retry_count}
                onChange={(e) => setConfig({ ...config, retry_count: parseInt(e.target.value) })}
              />
            </div>
          </div>

          {/* 알림 설정 */}
          <div className="space-y-4 pt-4 border-t">
            <h3 className="font-semibold">알림 설정</h3>

            {/* Discord */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Discord 알림</Label>
                <Switch
                  checked={config.notify_discord}
                  onCheckedChange={(checked) => setConfig({ ...config, notify_discord: checked })}
                />
              </div>
              {config.notify_discord && (
                <Input
                  placeholder="Discord Webhook URL"
                  value={config.discord_webhook || ''}
                  onChange={(e) => setConfig({ ...config, discord_webhook: e.target.value })}
                />
              )}
            </div>

            {/* Slack */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <Label>Slack 알림</Label>
                <Switch
                  checked={config.notify_slack}
                  onCheckedChange={(checked) => setConfig({ ...config, notify_slack: checked })}
                />
              </div>
              {config.notify_slack && (
                <Input
                  placeholder="Slack Webhook URL"
                  value={config.slack_webhook || ''}
                  onChange={(e) => setConfig({ ...config, slack_webhook: e.target.value })}
                />
              )}
            </div>
          </div>

          {/* 저장 버튼 */}
          <div className="flex justify-end pt-4">
            <Button onClick={handleSaveConfig} disabled={loading}>
              {loading ? (
                <><RefreshCw className="w-4 h-4 mr-2 animate-spin" />저장 중...</>
              ) : (
                <><Save className="w-4 h-4 mr-2" />설정 저장</>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* 실행 기록 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>실행 기록</CardTitle>
              <CardDescription>최근 10개의 작업 내역</CardDescription>
            </div>
            <Button variant="outline" size="sm" onClick={loadJobs}>
              <RefreshCw className="w-4 h-4 mr-2" />새로고침
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {jobs.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                실행 기록이 없습니다
              </div>
            ) : (
              jobs.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors"
                >
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      {getStatusBadge(job.status)}
                      <Badge variant="outline">
                        {job.job_type === 'scheduled' ? '자동 실행' : '수동 실행'}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      시작: {formatDateTime(job.started_at)}
                      {job.completed_at && ` • 완료: ${formatDateTime(job.completed_at)}`}
                    </div>
                  </div>
                  <div className="flex items-center gap-4 text-sm">
                    <div className="text-center">
                      <div className="font-semibold">{job.total_count}</div>
                      <div className="text-xs text-muted-foreground">전체</div>
                    </div>
                    <div className="text-center">
                      <div className="font-semibold text-green-600">{job.success_count}</div>
                      <div className="text-xs text-muted-foreground">성공</div>
                    </div>
                    <div className="text-center">
                      <div className="font-semibold text-red-600">{job.failed_count}</div>
                      <div className="text-xs text-muted-foreground">실패</div>
                    </div>
                    {job.status === 'running' && (
                      <div className="text-center">
                        <div className="font-semibold text-blue-600">{job.progress_percent.toFixed(0)}%</div>
                        <div className="text-xs text-muted-foreground">진행률</div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
