import { lazy } from 'react'
import { Navigate, createBrowserRouter } from 'react-router'
import Loadable from '../layouts/full/shared/loadable/Loadable'

const FullLayout = Loadable(lazy(() => import('../layouts/full/FullLayout')))
const BlankLayout = Loadable(lazy(() => import('../layouts/blank/BlankLayout')))
const Dashboard = Loadable(lazy(() => import('../views/dashboard')))
const Agent = Loadable(lazy(() => import('../views/agent')))
const AiAssistant = Loadable(lazy(() => import('../views/ai-assistant')))
const Tasks = Loadable(lazy(() => import('../views/tasks')))
const Terminal = Loadable(lazy(() => import('../views/terminal')))
const Devices = Loadable(lazy(() => import('../views/devices')))
const DeviceDetail = Loadable(lazy(() => import('../views/devices/detail')))
const Labs = Loadable(lazy(() => import('../views/labs')))
const LabDetail = Loadable(lazy(() => import('../views/labs/detail')))
const Topology = Loadable(lazy(() => import('../views/topology')))
const TopologyBuilder = Loadable(lazy(() => import('../views/topology-builder')))
const Gns3 = Loadable(lazy(() => import('../views/gns3')))
const Containerlab = Loadable(lazy(() => import('../views/containerlab')))
const Environments = Loadable(lazy(() => import('../views/environments')))
const EnvironmentLab = Loadable(lazy(() => import('../views/environments/lab')))
const EnvironmentStaging = Loadable(lazy(() => import('../views/environments/staging')))
const EnvironmentProduction = Loadable(lazy(() => import('../views/environments/production')))
const Configurations = Loadable(lazy(() => import('../views/configurations')))
const Backups = Loadable(lazy(() => import('../views/backups')))
const Alerts = Loadable(lazy(() => import('../views/alerts')))
const Audit = Loadable(lazy(() => import('../views/audit')))
const Discovery = Loadable(lazy(() => import('../views/discovery')))
const Credentials = Loadable(lazy(() => import('../views/settings/credentials')))
const Settings = Loadable(lazy(() => import('../views/settings')))
const Error = Loadable(lazy(() => import('../views/auth/error')))

const router = createBrowserRouter([
  {
    path: '/',
    element: <FullLayout />,
    children: [
      { path: '/', element: <Navigate to="/dashboard" replace /> },
      { path: '/dashboard', element: <Dashboard /> },
      { path: '/agent', element: <Agent /> },
      { path: '/ai-assistant', element: <AiAssistant /> },
      { path: '/tasks', element: <Tasks /> },
      { path: '/terminal', element: <Terminal /> },
      { path: '/devices', element: <Devices /> },
      { path: '/devices/:id', element: <DeviceDetail /> },
      { path: '/topology', element: <Topology /> },
      { path: '/topology-builder', element: <TopologyBuilder /> },
      { path: '/discovery', element: <Discovery /> },
      { path: '/alerts', element: <Alerts /> },
      { path: '/labs', element: <Labs /> },
      { path: '/labs/:id', element: <LabDetail /> },
      { path: '/environments', element: <Environments /> },
      { path: '/environments/lab', element: <EnvironmentLab /> },
      { path: '/environments/staging', element: <EnvironmentStaging /> },
      { path: '/environments/production', element: <EnvironmentProduction /> },
      { path: '/gns3', element: <Gns3 /> },
      { path: '/containerlab', element: <Containerlab /> },
      { path: '/configurations', element: <Configurations /> },
      { path: '/backups', element: <Backups /> },
      { path: '/audit', element: <Audit /> },
      { path: '/settings/credentials', element: <Credentials /> },
      { path: '/settings', element: <Settings /> },
      { path: '*', element: <Navigate to="/auth/404" /> },
    ],
  },
  {
    path: '/',
    element: <BlankLayout />,
    children: [
      { path: '/auth/404', element: <Error /> },
      { path: '*', element: <Navigate to="/auth/404" /> },
    ],
  },
])

export default router
