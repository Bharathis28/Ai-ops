"use client"

import type React from "react"

import { useEffect, useState, useRef } from "react"
import {
  Activity,
  AlertTriangle,
  Bell,
  CheckCircle2,
  ChevronDown,
  Clock,
  Cpu,
  Eye,
  Filter,
  Hexagon,
  LayoutDashboard,
  Play,
  RefreshCw,
  RotateCcw,
  Scale,
  Search,
  Server,
  Settings,
  Shield,
  X,
  Zap,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

// Types
type Page = "overview" | "anomalies" | "services" | "actions" | "settings"
type Severity = "critical" | "high" | "medium" | "low"
type Environment = "prod" | "staging" | "dev"

interface Anomaly {
  id: string
  service: string
  detectedAt: string
  severity: Severity
  summary: string
  status: "open" | "resolved"
  rootCause?: string
}

interface Service {
  name: string
  latencyP95: number
  errorRate: number
  anomalyScore: number
  status: "healthy" | "degraded" | "critical"
}

interface Action {
  id: string
  time: string
  service: string
  type: "restart" | "scale" | "rollout"
  result: "success" | "failed" | "pending"
  triggeredBy: "auto" | "manual"
}

// Sample data
const anomalies: Anomaly[] = [
  {
    id: "ANM-001",
    service: "payment-api",
    detectedAt: "2025-11-27 14:23:00",
    severity: "critical",
    summary: "Sudden latency spike detected - response times increased 400%",
    status: "open",
    rootCause:
      "Database connection pool exhaustion detected. The payment-api service is experiencing connection timeouts due to max_connections limit being reached. Recommended action: Increase pool size or implement connection recycling.",
  },
  {
    id: "ANM-002",
    service: "user-auth",
    detectedAt: "2025-11-27 13:45:00",
    severity: "high",
    summary: "Elevated error rate on authentication endpoints",
    status: "open",
    rootCause:
      "Redis cache miss rate increased significantly. Token validation is falling back to database queries, causing increased latency and occasional timeouts.",
  },
  {
    id: "ANM-003",
    service: "inventory-svc",
    detectedAt: "2025-11-27 12:30:00",
    severity: "medium",
    summary: "Memory usage trending above threshold",
    status: "resolved",
    rootCause: "Memory leak in inventory sync job. Fixed by restarting the service and deploying patch v2.3.1.",
  },
  {
    id: "ANM-004",
    service: "notification-svc",
    detectedAt: "2025-11-27 11:15:00",
    severity: "low",
    summary: "Minor increase in queue processing time",
    status: "resolved",
  },
  {
    id: "ANM-005",
    service: "order-processor",
    detectedAt: "2025-11-27 10:00:00",
    severity: "high",
    summary: "CPU utilization exceeded 90% for 15 minutes",
    status: "open",
    rootCause: "Sudden traffic spike from flash sale event. Auto-scaling triggered but HPA max replicas reached.",
  },
  {
    id: "ANM-006",
    service: "search-api",
    detectedAt: "2025-11-27 09:30:00",
    severity: "medium",
    summary: "Elasticsearch cluster showing yellow status",
    status: "open",
  },
]

const services: Service[] = [
  { name: "payment-api", latencyP95: 1250, errorRate: 4.2, anomalyScore: 92, status: "critical" },
  { name: "user-auth", latencyP95: 340, errorRate: 2.1, anomalyScore: 78, status: "degraded" },
  { name: "order-processor", latencyP95: 890, errorRate: 1.8, anomalyScore: 71, status: "degraded" },
  { name: "inventory-svc", latencyP95: 120, errorRate: 0.3, anomalyScore: 15, status: "healthy" },
  { name: "notification-svc", latencyP95: 85, errorRate: 0.1, anomalyScore: 8, status: "healthy" },
  { name: "search-api", latencyP95: 210, errorRate: 0.8, anomalyScore: 45, status: "degraded" },
  { name: "analytics-svc", latencyP95: 150, errorRate: 0.2, anomalyScore: 12, status: "healthy" },
  { name: "cdn-proxy", latencyP95: 45, errorRate: 0.05, anomalyScore: 5, status: "healthy" },
]

const actions: Action[] = [
  {
    id: "ACT-001",
    time: "2025-11-27 14:25:00",
    service: "payment-api",
    type: "restart",
    result: "success",
    triggeredBy: "auto",
  },
  {
    id: "ACT-002",
    time: "2025-11-27 13:50:00",
    service: "user-auth",
    type: "scale",
    result: "success",
    triggeredBy: "auto",
  },
  {
    id: "ACT-003",
    time: "2025-11-27 12:35:00",
    service: "inventory-svc",
    type: "restart",
    result: "success",
    triggeredBy: "manual",
  },
  {
    id: "ACT-004",
    time: "2025-11-27 10:05:00",
    service: "order-processor",
    type: "scale",
    result: "success",
    triggeredBy: "auto",
  },
  {
    id: "ACT-005",
    time: "2025-11-27 09:45:00",
    service: "search-api",
    type: "rollout",
    result: "pending",
    triggeredBy: "manual",
  },
  {
    id: "ACT-006",
    time: "2025-11-26 22:30:00",
    service: "analytics-svc",
    type: "restart",
    result: "success",
    triggeredBy: "auto",
  },
  {
    id: "ACT-007",
    time: "2025-11-26 18:15:00",
    service: "notification-svc",
    type: "scale",
    result: "failed",
    triggeredBy: "auto",
  },
]

export default function Dashboard() {
  const [currentPage, setCurrentPage] = useState<Page>("overview")
  const [environment, setEnvironment] = useState<Environment>("prod")
  const [selectedAnomaly, setSelectedAnomaly] = useState<Anomaly | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // Simulate loading
  useEffect(() => {
    const timer = setTimeout(() => setIsLoading(false), 1500)
    return () => clearTimeout(timer)
  }, [])

  // Particle effect
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    canvas.width = canvas.offsetWidth
    canvas.height = canvas.offsetHeight

    const particles: { x: number; y: number; size: number; speedX: number; speedY: number; color: string }[] = []
    const particleCount = 80

    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 2 + 1,
        speedX: (Math.random() - 0.5) * 0.3,
        speedY: (Math.random() - 0.5) * 0.3,
        color: `rgba(${Math.floor(Math.random() * 50) + 50}, ${Math.floor(Math.random() * 100) + 150}, ${Math.floor(Math.random() * 55) + 200}, ${Math.random() * 0.4 + 0.1})`,
      })
    }

    let animationId: number

    function animate() {
      if (!ctx || !canvas) return
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      for (const p of particles) {
        p.x += p.speedX
        p.y += p.speedY
        if (p.x > canvas.width) p.x = 0
        if (p.x < 0) p.x = canvas.width
        if (p.y > canvas.height) p.y = 0
        if (p.y < 0) p.y = canvas.height

        ctx.fillStyle = p.color
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fill()
      }

      animationId = requestAnimationFrame(animate)
    }

    animate()

    const handleResize = () => {
      canvas.width = canvas.offsetWidth
      canvas.height = canvas.offsetHeight
    }
    window.addEventListener("resize", handleResize)

    return () => {
      window.removeEventListener("resize", handleResize)
      cancelAnimationFrame(animationId)
    }
  }, [])

  const navItems = [
    { id: "overview" as Page, label: "Overview", icon: LayoutDashboard },
    { id: "anomalies" as Page, label: "Anomalies", icon: AlertTriangle },
    { id: "services" as Page, label: "Services", icon: Server },
    { id: "actions" as Page, label: "Actions", icon: Zap },
    { id: "settings" as Page, label: "Settings", icon: Settings },
  ]

  const criticalCount = anomalies.filter((a) => a.severity === "critical" && a.status === "open").length
  const totalAnomalies24h = anomalies.length
  const servicesMonitored = services.length
  const autoRemediations = actions.filter((a) => a.triggeredBy === "auto").length

  return (
    <div className="dark min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950 text-slate-100 relative overflow-hidden">
      {/* Background particle effect */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full opacity-30" />

      {/* Loading overlay */}
      {isLoading && (
        <div className="absolute inset-0 bg-black/80 flex items-center justify-center z-50">
          <div className="flex flex-col items-center">
            <div className="relative w-20 h-20">
              <div className="absolute inset-0 border-4 border-cyan-500/30 rounded-full animate-ping" />
              <div className="absolute inset-2 border-4 border-t-cyan-500 border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin" />
              <div
                className="absolute inset-4 border-4 border-r-emerald-500 border-t-transparent border-b-transparent border-l-transparent rounded-full animate-spin"
                style={{ animationDirection: "reverse", animationDuration: "1.5s" }}
              />
            </div>
            <div className="mt-4 text-cyan-400 font-mono text-sm tracking-wider">INITIALIZING SENTRY</div>
          </div>
        </div>
      )}

      <div className="relative z-10 flex flex-col h-screen">
        {/* Top Navbar */}
        <header className="flex items-center justify-between px-6 py-3 border-b border-slate-700/50 bg-slate-900/60 backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <Hexagon className="h-7 w-7 text-cyan-400" />
              <span className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-emerald-400 bg-clip-text text-transparent">
                AI Ops Sentry
              </span>
            </div>

            {/* Environment Selector */}
            <div className="ml-6">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    className="bg-slate-800/50 border-slate-700 text-slate-300 hover:bg-slate-700/50 hover:text-slate-100"
                  >
                    <div
                      className={`h-2 w-2 rounded-full mr-2 ${environment === "prod" ? "bg-emerald-500" : environment === "staging" ? "bg-amber-500" : "bg-blue-500"}`}
                    />
                    {environment.toUpperCase()}
                    <ChevronDown className="ml-2 h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="bg-slate-800 border-slate-700">
                  <DropdownMenuItem
                    onClick={() => setEnvironment("prod")}
                    className="text-slate-300 focus:bg-slate-700 focus:text-slate-100"
                  >
                    <div className="h-2 w-2 rounded-full bg-emerald-500 mr-2" /> Production
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setEnvironment("staging")}
                    className="text-slate-300 focus:bg-slate-700 focus:text-slate-100"
                  >
                    <div className="h-2 w-2 rounded-full bg-amber-500 mr-2" /> Staging
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    onClick={() => setEnvironment("dev")}
                    className="text-slate-300 focus:bg-slate-700 focus:text-slate-100"
                  >
                    <div className="h-2 w-2 rounded-full bg-blue-500 mr-2" /> Development
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 bg-slate-800/50 rounded-lg px-3 py-1.5 border border-slate-700/50">
              <Search className="h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search..."
                className="bg-transparent border-none focus:outline-none text-sm w-40 placeholder:text-slate-500"
              />
            </div>
            <Button variant="ghost" size="icon" className="relative text-slate-400 hover:text-slate-100">
              <Bell className="h-5 w-5" />
              {criticalCount > 0 && (
                <span className="absolute -top-1 -right-1 h-4 w-4 bg-red-500 rounded-full text-xs flex items-center justify-center">
                  {criticalCount}
                </span>
              )}
            </Button>
          </div>
        </header>

        <div className="flex flex-1 overflow-hidden">
          {/* Left Sidebar */}
          <aside className="w-56 border-r border-slate-700/50 bg-slate-900/40 backdrop-blur-sm p-4">
            <nav className="space-y-1">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = currentPage === item.id
                return (
                  <button
                    key={item.id}
                    onClick={() => setCurrentPage(item.id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    {item.label}
                    {item.id === "anomalies" && criticalCount > 0 && (
                      <Badge className="ml-auto bg-red-500/20 text-red-400 border-red-500/30 text-xs px-1.5">
                        {criticalCount}
                      </Badge>
                    )}
                  </button>
                )
              })}
            </nav>
          </aside>

          {/* Main Content */}
          <main className="flex-1 overflow-auto p-6">
            {currentPage === "overview" && (
              <OverviewPage
                totalAnomalies={totalAnomalies24h}
                criticalCount={criticalCount}
                servicesMonitored={servicesMonitored}
                autoRemediations={autoRemediations}
                anomalies={anomalies}
                services={services}
              />
            )}
            {currentPage === "anomalies" && (
              <AnomaliesPage
                anomalies={anomalies}
                selectedAnomaly={selectedAnomaly}
                setSelectedAnomaly={setSelectedAnomaly}
              />
            )}
            {currentPage === "services" && <ServicesPage services={services} />}
            {currentPage === "actions" && <ActionsPage actions={actions} />}
            {currentPage === "settings" && <SettingsPage />}
          </main>
        </div>
      </div>
    </div>
  )
}

// Overview Page Component
function OverviewPage({
  totalAnomalies,
  criticalCount,
  servicesMonitored,
  autoRemediations,
  anomalies,
  services,
}: {
  totalAnomalies: number
  criticalCount: number
  servicesMonitored: number
  autoRemediations: number
  anomalies: Anomaly[]
  services: Service[]
}) {
  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          title="Total Anomalies (24h)"
          value={totalAnomalies}
          icon={AlertTriangle}
          trend="+12%"
          trendUp={false}
          color="amber"
        />
        <KPICard
          title="Critical Anomalies"
          value={criticalCount}
          icon={Shield}
          trend={criticalCount > 0 ? "Needs attention" : "All clear"}
          trendUp={criticalCount === 0}
          color="red"
        />
        <KPICard
          title="Services Monitored"
          value={servicesMonitored}
          icon={Server}
          trend="All connected"
          trendUp={true}
          color="cyan"
        />
        <KPICard
          title="Auto-Remediations"
          value={autoRemediations}
          icon={Zap}
          trend="Last 24h"
          trendUp={true}
          color="emerald"
        />
      </div>

      {/* Middle Section: Chart + Incidents */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Time Series Chart */}
        <Card className="lg:col-span-2 bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-slate-100 flex items-center text-base">
                <Activity className="mr-2 h-5 w-5 text-cyan-400" />
                Anomaly Trend (24h)
              </CardTitle>
              <Badge variant="outline" className="bg-slate-800/50 text-cyan-400 border-cyan-500/50 text-xs">
                <div className="h-1.5 w-1.5 rounded-full bg-cyan-500 mr-1 animate-pulse" />
                LIVE
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <AnomalyChart />
            </div>
          </CardContent>
        </Card>

        {/* Latest Incidents Panel */}
        <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
          <CardHeader className="pb-2">
            <CardTitle className="text-slate-100 flex items-center text-base">
              <Clock className="mr-2 h-5 w-5 text-amber-400" />
              Latest Incidents
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {anomalies
              .filter((a) => a.status === "open")
              .slice(0, 5)
              .map((anomaly) => (
                <div
                  key={anomaly.id}
                  className="flex items-start gap-3 p-2 rounded-lg bg-slate-800/30 border border-slate-700/30"
                >
                  <SeverityBadge severity={anomaly.severity} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-200 truncate">{anomaly.service}</p>
                    <p className="text-xs text-slate-400 truncate">{anomaly.summary}</p>
                  </div>
                </div>
              ))}
          </CardContent>
        </Card>
      </div>

      {/* Services Table */}
      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader className="pb-2">
          <CardTitle className="text-slate-100 flex items-center text-base">
            <Server className="mr-2 h-5 w-5 text-cyan-400" />
            Service Health
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-xs text-slate-400 border-b border-slate-700/50">
                  <th className="text-left py-3 px-4 font-medium">Service</th>
                  <th className="text-right py-3 px-4 font-medium">Latency P95</th>
                  <th className="text-right py-3 px-4 font-medium">Error Rate</th>
                  <th className="text-right py-3 px-4 font-medium">Anomaly Score</th>
                  <th className="text-center py-3 px-4 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/30">
                {services.map((service) => (
                  <tr key={service.name} className="text-sm hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4">
                      <span className="font-medium text-slate-200">{service.name}</span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className={service.latencyP95 > 500 ? "text-amber-400" : "text-slate-300"}>
                        {service.latencyP95}ms
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span className={service.errorRate > 2 ? "text-red-400" : "text-slate-300"}>
                        {service.errorRate}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <div className="w-16 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              service.anomalyScore > 70
                                ? "bg-red-500"
                                : service.anomalyScore > 40
                                  ? "bg-amber-500"
                                  : "bg-emerald-500"
                            }`}
                            style={{ width: `${service.anomalyScore}%` }}
                          />
                        </div>
                        <span className="text-slate-400 w-8">{service.anomalyScore}</span>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <StatusBadge status={service.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Anomalies Page Component
function AnomaliesPage({
  anomalies,
  selectedAnomaly,
  setSelectedAnomaly,
}: {
  anomalies: Anomaly[]
  selectedAnomaly: Anomaly | null
  setSelectedAnomaly: (anomaly: Anomaly | null) => void
}) {
  const [severityFilter, setSeverityFilter] = useState<string>("all")
  const [serviceFilter, setServiceFilter] = useState<string>("all")

  const uniqueServices = [...new Set(anomalies.map((a) => a.service))]

  const filteredAnomalies = anomalies.filter((a) => {
    if (severityFilter !== "all" && a.severity !== severityFilter) return false
    if (serviceFilter !== "all" && a.service !== serviceFilter) return false
    return true
  })

  return (
    <div className="flex gap-6 h-full">
      {/* Main Content */}
      <div className={`flex-1 space-y-4 ${selectedAnomaly ? "lg:w-2/3" : "w-full"}`}>
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 p-4 bg-slate-900/50 border border-slate-700/50 rounded-lg backdrop-blur-sm">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-slate-400" />
            <span className="text-sm text-slate-400">Filters:</span>
          </div>

          <Select value={severityFilter} onValueChange={setSeverityFilter}>
            <SelectTrigger className="w-36 bg-slate-800/50 border-slate-700 text-slate-300">
              <SelectValue placeholder="Severity" />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="all">All Severities</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
              <SelectItem value="high">High</SelectItem>
              <SelectItem value="medium">Medium</SelectItem>
              <SelectItem value="low">Low</SelectItem>
            </SelectContent>
          </Select>

          <Select value={serviceFilter} onValueChange={setServiceFilter}>
            <SelectTrigger className="w-44 bg-slate-800/50 border-slate-700 text-slate-300">
              <SelectValue placeholder="Service" />
            </SelectTrigger>
            <SelectContent className="bg-slate-800 border-slate-700">
              <SelectItem value="all">All Services</SelectItem>
              {uniqueServices.map((service) => (
                <SelectItem key={service} value={service}>
                  {service}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Anomalies Table */}
        <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-xs text-slate-400 border-b border-slate-700/50 bg-slate-800/30">
                    <th className="text-left py-3 px-4 font-medium">ID</th>
                    <th className="text-left py-3 px-4 font-medium">Service</th>
                    <th className="text-left py-3 px-4 font-medium">Detected</th>
                    <th className="text-center py-3 px-4 font-medium">Severity</th>
                    <th className="text-left py-3 px-4 font-medium">Summary</th>
                    <th className="text-center py-3 px-4 font-medium">Status</th>
                    <th className="text-center py-3 px-4 font-medium">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/30">
                  {filteredAnomalies.map((anomaly) => (
                    <tr
                      key={anomaly.id}
                      className={`text-sm hover:bg-slate-800/30 transition-colors cursor-pointer ${
                        selectedAnomaly?.id === anomaly.id ? "bg-slate-800/50" : ""
                      }`}
                      onClick={() => setSelectedAnomaly(anomaly)}
                    >
                      <td className="py-3 px-4 font-mono text-slate-400">{anomaly.id}</td>
                      <td className="py-3 px-4 font-medium text-slate-200">{anomaly.service}</td>
                      <td className="py-3 px-4 text-slate-400 text-xs">{anomaly.detectedAt}</td>
                      <td className="py-3 px-4 text-center">
                        <SeverityBadge severity={anomaly.severity} />
                      </td>
                      <td className="py-3 px-4 text-slate-300 max-w-xs truncate">{anomaly.summary}</td>
                      <td className="py-3 px-4 text-center">
                        <Badge
                          className={
                            anomaly.status === "open"
                              ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                              : "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                          }
                        >
                          {anomaly.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-7 w-7 text-slate-400 hover:text-cyan-400"
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedAnomaly(anomaly)
                          }}
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detail Drawer */}
      {selectedAnomaly && (
        <div className="hidden lg:block w-96 bg-slate-900/70 border border-slate-700/50 rounded-lg backdrop-blur-sm p-5 space-y-4 h-fit sticky top-0">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-slate-100">Incident Details</h3>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 text-slate-400 hover:text-slate-100"
              onClick={() => setSelectedAnomaly(null)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          <div className="space-y-3">
            <div>
              <span className="text-xs text-slate-400">Incident ID</span>
              <p className="font-mono text-cyan-400">{selectedAnomaly.id}</p>
            </div>
            <div>
              <span className="text-xs text-slate-400">Service</span>
              <p className="text-slate-200">{selectedAnomaly.service}</p>
            </div>
            <div>
              <span className="text-xs text-slate-400">Detected At</span>
              <p className="text-slate-200">{selectedAnomaly.detectedAt}</p>
            </div>
            <div>
              <span className="text-xs text-slate-400">Severity</span>
              <div className="mt-1">
                <SeverityBadge severity={selectedAnomaly.severity} />
              </div>
            </div>
            <div>
              <span className="text-xs text-slate-400">Summary</span>
              <p className="text-slate-300 text-sm">{selectedAnomaly.summary}</p>
            </div>

            {selectedAnomaly.rootCause && (
              <div className="pt-3 border-t border-slate-700/50">
                <div className="flex items-center gap-2 mb-2">
                  <Cpu className="h-4 w-4 text-cyan-400" />
                  <span className="text-xs font-medium text-cyan-400">AI Root Cause Analysis</span>
                </div>
                <p className="text-slate-300 text-sm leading-relaxed bg-slate-800/50 p-3 rounded-lg border border-slate-700/30">
                  {selectedAnomaly.rootCause}
                </p>
              </div>
            )}

            <div className="pt-3 flex gap-2">
              <Button className="flex-1 bg-cyan-600 hover:bg-cyan-500 text-white">
                <Play className="h-4 w-4 mr-2" />
                Run Remediation
              </Button>
              <Button variant="outline" className="border-slate-600 text-slate-300 hover:bg-slate-700 bg-transparent">
                <CheckCircle2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

// Services Page Component
function ServicesPage({ services }: { services: Service[] }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-100">Services</h2>
        <Button variant="outline" className="border-slate-700 text-slate-300 hover:bg-slate-800 bg-transparent">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {services.map((service) => (
          <Card
            key={service.name}
            className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm hover:border-slate-600/50 transition-colors"
          >
            <CardContent className="p-5">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div
                    className={`p-2 rounded-lg ${
                      service.status === "healthy"
                        ? "bg-emerald-500/10"
                        : service.status === "degraded"
                          ? "bg-amber-500/10"
                          : "bg-red-500/10"
                    }`}
                  >
                    <Server
                      className={`h-5 w-5 ${
                        service.status === "healthy"
                          ? "text-emerald-400"
                          : service.status === "degraded"
                            ? "text-amber-400"
                            : "text-red-400"
                      }`}
                    />
                  </div>
                  <div>
                    <h3 className="font-medium text-slate-200">{service.name}</h3>
                    <StatusBadge status={service.status} />
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Latency P95</span>
                  <span className={service.latencyP95 > 500 ? "text-amber-400" : "text-slate-200"}>
                    {service.latencyP95}ms
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Error Rate</span>
                  <span className={service.errorRate > 2 ? "text-red-400" : "text-slate-200"}>
                    {service.errorRate}%
                  </span>
                </div>
                <div className="flex justify-between text-sm items-center">
                  <span className="text-slate-400">Anomaly Score</span>
                  <div className="flex items-center gap-2">
                    <div className="w-20 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          service.anomalyScore > 70
                            ? "bg-red-500"
                            : service.anomalyScore > 40
                              ? "bg-amber-500"
                              : "bg-emerald-500"
                        }`}
                        style={{ width: `${service.anomalyScore}%` }}
                      />
                    </div>
                    <span className="text-slate-300 text-xs w-6">{service.anomalyScore}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

// Actions Page Component
function ActionsPage({ actions }: { actions: Action[] }) {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-slate-100">Auto-Remediation Actions</h2>
        <Badge variant="outline" className="bg-slate-800/50 text-cyan-400 border-cyan-500/50">
          <Zap className="h-3 w-3 mr-1" />
          Auto-remediation enabled
        </Badge>
      </div>

      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-xs text-slate-400 border-b border-slate-700/50 bg-slate-800/30">
                  <th className="text-left py-3 px-4 font-medium">Time</th>
                  <th className="text-left py-3 px-4 font-medium">Service</th>
                  <th className="text-center py-3 px-4 font-medium">Action Type</th>
                  <th className="text-center py-3 px-4 font-medium">Result</th>
                  <th className="text-center py-3 px-4 font-medium">Triggered By</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/30">
                {actions.map((action) => (
                  <tr key={action.id} className="text-sm hover:bg-slate-800/30 transition-colors">
                    <td className="py-3 px-4 text-slate-400 text-xs font-mono">{action.time}</td>
                    <td className="py-3 px-4 font-medium text-slate-200">{action.service}</td>
                    <td className="py-3 px-4 text-center">
                      <ActionTypeBadge type={action.type} />
                    </td>
                    <td className="py-3 px-4 text-center">
                      <ResultBadge result={action.result} />
                    </td>
                    <td className="py-3 px-4 text-center">
                      <Badge
                        variant="outline"
                        className={
                          action.triggeredBy === "auto"
                            ? "bg-cyan-500/10 text-cyan-400 border-cyan-500/30"
                            : "bg-slate-500/10 text-slate-400 border-slate-500/30"
                        }
                      >
                        {action.triggeredBy}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Settings Page Component
function SettingsPage() {
  return (
    <div className="space-y-6 max-w-2xl">
      <h2 className="text-xl font-semibold text-slate-100">Settings</h2>

      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-base text-slate-200">Auto-Remediation</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-200">Enable auto-remediation</p>
              <p className="text-xs text-slate-400">Automatically execute remediation actions</p>
            </div>
            <div className="h-6 w-11 bg-cyan-600 rounded-full relative cursor-pointer">
              <div className="h-5 w-5 bg-white rounded-full absolute right-0.5 top-0.5" />
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-200">Require approval for critical</p>
              <p className="text-xs text-slate-400">Manual approval needed for critical severity</p>
            </div>
            <div className="h-6 w-11 bg-cyan-600 rounded-full relative cursor-pointer">
              <div className="h-5 w-5 bg-white rounded-full absolute right-0.5 top-0.5" />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
        <CardHeader>
          <CardTitle className="text-base text-slate-200">Notifications</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-200">Email alerts</p>
              <p className="text-xs text-slate-400">Receive email for critical anomalies</p>
            </div>
            <div className="h-6 w-11 bg-cyan-600 rounded-full relative cursor-pointer">
              <div className="h-5 w-5 bg-white rounded-full absolute right-0.5 top-0.5" />
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-200">Slack integration</p>
              <p className="text-xs text-slate-400">Post alerts to Slack channel</p>
            </div>
            <div className="h-6 w-11 bg-slate-600 rounded-full relative cursor-pointer">
              <div className="h-5 w-5 bg-white rounded-full absolute left-0.5 top-0.5" />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

// Helper Components
function KPICard({
  title,
  value,
  icon: Icon,
  trend,
  trendUp,
  color,
}: {
  title: string
  value: number
  icon: React.ElementType
  trend: string
  trendUp: boolean
  color: "cyan" | "emerald" | "amber" | "red"
}) {
  const colorClasses = {
    cyan: "text-cyan-400 bg-cyan-500/10",
    emerald: "text-emerald-400 bg-emerald-500/10",
    amber: "text-amber-400 bg-amber-500/10",
    red: "text-red-400 bg-red-500/10",
  }

  return (
    <Card className="bg-slate-900/50 border-slate-700/50 backdrop-blur-sm">
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <div className={`p-2 rounded-lg ${colorClasses[color]}`}>
            <Icon className={`h-5 w-5 ${colorClasses[color].split(" ")[0]}`} />
          </div>
          <span className={`text-xs ${trendUp ? "text-emerald-400" : "text-amber-400"}`}>{trend}</span>
        </div>
        <div className="mt-3">
          <p className="text-2xl font-bold text-slate-100">{value}</p>
          <p className="text-sm text-slate-400">{title}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function SeverityBadge({ severity }: { severity: Severity }) {
  const classes = {
    critical: "bg-red-500/20 text-red-400 border-red-500/30",
    high: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    medium: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    low: "bg-slate-500/20 text-slate-400 border-slate-500/30",
  }

  return <Badge className={classes[severity]}>{severity}</Badge>
}

function StatusBadge({ status }: { status: "healthy" | "degraded" | "critical" }) {
  const classes = {
    healthy: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    degraded: "bg-amber-500/20 text-amber-400 border-amber-500/30",
    critical: "bg-red-500/20 text-red-400 border-red-500/30",
  }

  return <Badge className={classes[status]}>{status}</Badge>
}

function ActionTypeBadge({ type }: { type: "restart" | "scale" | "rollout" }) {
  const icons = {
    restart: RotateCcw,
    scale: Scale,
    rollout: RefreshCw,
  }
  const Icon = icons[type]

  return (
    <Badge variant="outline" className="bg-slate-800/50 text-slate-300 border-slate-600">
      <Icon className="h-3 w-3 mr-1" />
      {type}
    </Badge>
  )
}

function ResultBadge({ result }: { result: "success" | "failed" | "pending" }) {
  const classes = {
    success: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
    failed: "bg-red-500/20 text-red-400 border-red-500/30",
    pending: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  }

  return <Badge className={classes[result]}>{result}</Badge>
}

function AnomalyChart() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext("2d")
    if (!ctx) return

    canvas.width = canvas.offsetWidth * 2
    canvas.height = canvas.offsetHeight * 2
    ctx.scale(2, 2)

    const width = canvas.offsetWidth
    const height = canvas.offsetHeight
    const padding = 40

    // Generate sample data points
    const dataPoints = Array.from({ length: 24 }, (_, i) => ({
      hour: i,
      value: Math.floor(Math.random() * 8) + (i > 10 && i < 16 ? 5 : 0),
    }))

    // Draw grid lines
    ctx.strokeStyle = "rgba(100, 116, 139, 0.2)"
    ctx.lineWidth = 1
    for (let i = 0; i <= 4; i++) {
      const y = padding + ((height - padding * 2) / 4) * i
      ctx.beginPath()
      ctx.moveTo(padding, y)
      ctx.lineTo(width - padding, y)
      ctx.stroke()
    }

    // Draw axes labels
    ctx.fillStyle = "rgba(148, 163, 184, 0.8)"
    ctx.font = "10px monospace"
    ctx.textAlign = "center"
    for (let i = 0; i < 24; i += 4) {
      const x = padding + ((width - padding * 2) / 23) * i
      ctx.fillText(`${i}:00`, x, height - 10)
    }

    // Draw line chart
    ctx.beginPath()
    ctx.strokeStyle = "rgba(34, 211, 238, 0.8)"
    ctx.lineWidth = 2

    dataPoints.forEach((point, i) => {
      const x = padding + ((width - padding * 2) / 23) * point.hour
      const y = height - padding - (point.value / 15) * (height - padding * 2)

      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })
    ctx.stroke()

    // Draw gradient fill
    const gradient = ctx.createLinearGradient(0, padding, 0, height - padding)
    gradient.addColorStop(0, "rgba(34, 211, 238, 0.3)")
    gradient.addColorStop(1, "rgba(34, 211, 238, 0)")

    ctx.beginPath()
    dataPoints.forEach((point, i) => {
      const x = padding + ((width - padding * 2) / 23) * point.hour
      const y = height - padding - (point.value / 15) * (height - padding * 2)

      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })
    ctx.lineTo(width - padding, height - padding)
    ctx.lineTo(padding, height - padding)
    ctx.closePath()
    ctx.fillStyle = gradient
    ctx.fill()

    // Draw data points
    dataPoints.forEach((point) => {
      const x = padding + ((width - padding * 2) / 23) * point.hour
      const y = height - padding - (point.value / 15) * (height - padding * 2)

      ctx.beginPath()
      ctx.arc(x, y, 3, 0, Math.PI * 2)
      ctx.fillStyle = "rgba(34, 211, 238, 1)"
      ctx.fill()
    })
  }, [])

  return <canvas ref={canvasRef} className="w-full h-full" />
}
