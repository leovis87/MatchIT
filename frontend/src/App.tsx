import { Outlet, Route, Routes } from 'react-router-dom'
import Footer from './components/Footer'
import Header from './components/Header'
import ChatbotModal from './components/ChatbotModal_streaming'
import BootcampsPage from './pages/Bootcamps'
import BootcampDetailPage from './pages/BootcampDetail'
import ComparePage from './pages/Compare'
import HomePage from './pages/Home'
import JobsPage from './pages/Jobs'
import JobDetail from './pages/JobDetail'
import LoginPage from './components/LoginPage'
import ProfilePage from './pages/Profile'
import SearchResultsPage from './pages/SearchResults'
import CallbackPage from './pages/CallbackPage'


const Layout = () => {
  return (
    <div className="flex min-h-screen flex-col bg-white text-slate-950">
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
      <ChatbotModal />
    </div>
  )
}

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/jobs" element={<JobsPage />} />
        <Route path="/jobs/:jobId" element={<JobDetail />} />

        <Route path="/bootcamps" element={<BootcampsPage />} />
        <Route path="/bootcamps/:id" element={<BootcampDetailPage />} />

        <Route path="/search" element={<SearchResultsPage />} />
        <Route path="/compare" element={<ComparePage />} />

        <Route path="/login" element={<LoginPage />} />
        <Route path="/callback" element={<CallbackPage />} />
        <Route path="/profile" element={<ProfilePage />} />

        <Route path="*" element={<HomePage />} />
      </Route>
    </Routes>
  )
}

export default App
