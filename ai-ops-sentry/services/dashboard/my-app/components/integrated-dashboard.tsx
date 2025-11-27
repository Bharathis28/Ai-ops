"use client"

import { useEffect, useState } from 'react'
import { apiClient, type ServiceHealth, type AnomalyResult, type ActionResponse } from '@/lib/api-client'
import { POLLING_INTERVALS } from '@/lib/config'
import Dashboard from '../dashboard'

// Transform backend data to dashboard format
function transformAnomalies(backendAnomalies: AnomalyResult[]) {
  return backendAnomalies.map(anomaly => ({
    id: `ANM-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
    service: anomaly.service_name,
    detectedAt: new Date(anomaly.timestamp).toLocaleString(),
    severity: anomaly.severity || 'medium',
    summary: `Anomaly detected - Score: ${anomaly.anomaly_score.toFixed(2)}`,
    status: 'open' as const,
    rootCause: `Metrics: CPU ${anomaly.metric_values.cpu_usage?.toFixed(1) || 'N/A'}%, Memory ${anomaly.metric_values.memory_usage?.toFixed(1) || 'N/A'}%, Latency ${anomaly.metric_values.latency_p95?.toFixed(0) || 'N/A'}ms, Error Rate ${anomaly.metric_values.error_rate?.toFixed(2) || 'N/A'}%`,
  }))
}

function transformServices(backendServices: ServiceHealth[]) {
  return backendServices.map(svc => ({
    name: svc.name,
    latencyP95: svc.latency_p95,
    errorRate: svc.error_rate,
    anomalyScore: svc.anomaly_score,
    status: svc.status,
  }))
}

export default function IntegratedDashboard() {
  const [services, setServices] = useState<any[]>([])
  const [anomalies, setAnomalies] = useState<any[]>([])
  const [actions, setActions] = useState<any[]>([])
  const [backendHealth, setBackendHealth] = useState({
    ingestionAPI: false,
    actionEngine: false,
  })
  const [isLoading, setIsLoading] = useState(true)

  // Check backend health
  useEffect(() => {
    const checkHealth = async () => {
      const [ingestion, actions] = await Promise.all([
        apiClient.checkIngestionAPIHealth(),
        apiClient.checkActionEngineHealth(),
      ])
      
      setBackendHealth({
        ingestionAPI: ingestion,
        actionEngine: actions,
      })
    }

    checkHealth()
    const interval = setInterval(checkHealth, 30000) // Check every 30s
    return () => clearInterval(interval)
  }, [])

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [servicesData, anomaliesData] = await Promise.all([
          apiClient.getServices(),
          apiClient.getAnomalies(20),
        ])

        setServices(transformServices(servicesData))
        setAnomalies(transformAnomalies(anomaliesData))
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [])

  // Poll for updates
  useEffect(() => {
    const pollServices = setInterval(async () => {
      try {
        const servicesData = await apiClient.getServices()
        setServices(transformServices(servicesData))
      } catch (error) {
        console.error('Failed to poll services:', error)
      }
    }, POLLING_INTERVALS.SERVICES)

    const pollAnomalies = setInterval(async () => {
      try {
        const anomaliesData = await apiClient.getAnomalies(20)
        setAnomalies(transformAnomalies(anomaliesData))
      } catch (error) {
        console.error('Failed to poll anomalies:', error)
      }
    }, POLLING_INTERVALS.ANOMALIES)

    return () => {
      clearInterval(pollServices)
      clearInterval(pollAnomalies)
    }
  }, [])

  // Action handlers
  const handleRestartService = async (serviceName: string, targetType: 'gke' | 'cloud_run') => {
    try {
      const response = await apiClient.restartDeployment({
        service_name: serviceName,
        target_type: targetType,
        cluster_name: targetType === 'gke' ? 'prod-cluster' : undefined,
        region: targetType === 'cloud_run' ? 'us-central1' : undefined,
        namespace: 'default',
        reason: `Manual restart triggered from dashboard for ${serviceName}`,
      })

      // Add to actions list
      setActions(prev => [{
        id: response.action_id,
        time: new Date(response.timestamp).toLocaleString(),
        service: response.service_name,
        type: response.action_type as any,
        result: response.status,
        triggeredBy: 'manual' as const,
      }, ...prev])

      return response
    } catch (error) {
      console.error('Failed to restart service:', error)
      throw error
    }
  }

  const handleScaleService = async (
    serviceName: string,
    targetType: 'gke' | 'cloud_run',
    replicas?: number,
    minReplicas?: number,
    maxReplicas?: number
  ) => {
    try {
      const response = await apiClient.scaleDeployment({
        service_name: serviceName,
        target_type: targetType,
        cluster_name: targetType === 'gke' ? 'prod-cluster' : undefined,
        region: targetType === 'cloud_run' ? 'us-central1' : undefined,
        namespace: 'default',
        replicas,
        min_replicas: minReplicas,
        max_replicas: maxReplicas,
        reason: `Manual scale triggered from dashboard for ${serviceName}`,
      })

      // Add to actions list
      setActions(prev => [{
        id: response.action_id,
        time: new Date(response.timestamp).toLocaleString(),
        service: response.service_name,
        type: 'scale' as const,
        result: response.status,
        triggeredBy: 'manual' as const,
      }, ...prev])

      return response
    } catch (error) {
      console.error('Failed to scale service:', error)
      throw error
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
        <div className="text-center">
          <div className="mb-4 inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent"></div>
          <p className="text-slate-400">Loading AI Ops Sentry...</p>
        </div>
      </div>
    )
  }

  return (
    <>
      {/* Backend Health Status Banner */}
      {(!backendHealth.ingestionAPI || !backendHealth.actionEngine) && (
        <div className="bg-yellow-900/50 border-b border-yellow-800 px-4 py-2 text-sm text-yellow-200">
          <strong>⚠️ Backend Connection Issues:</strong>
          {!backendHealth.ingestionAPI && ' Ingestion API offline.'}
          {!backendHealth.actionEngine && ' Action Engine offline.'}
          {' Using mock data.'}
        </div>
      )}
      
      {/* Pass data and handlers to original Dashboard */}
      <Dashboard 
        services={services}
        anomalies={anomalies}
        actions={actions}
        onRestartService={handleRestartService}
        onScaleService={handleScaleService}
      />
    </>
  )
}
