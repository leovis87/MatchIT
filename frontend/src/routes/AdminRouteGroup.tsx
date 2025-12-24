import { Route, Routes } from 'react-router-dom'
import AdminRoute from './AdminRoute'
import AdminDashboard from '../pages/admin/AdminDashboard'
import AdminJobList from '../pages/admin/AdminJobList'
import AdminUserList from '../pages/admin/AdminUserList'
import AdminBootcamps from '../pages/admin/AdminBootcamps'
import AdminBootcampEdit from '../pages/admin/AdminBootcampEdit'
import AdminJobEdit from '../pages/admin/AdminJobEdit'

/**
 * 관리자 전용 라우팅 그룹
 * - AdminRoute 컴포넌트를 통해 관리자만 접근 가능하도록 보호됨
 * - /admin 경로 이하의 하위 페이지들을 관리
 */

export default function AdminRouteGroup() {
  return (
    <Routes>
      {/* AdminRoute: 관리자 로그인 + admin 권한 보유 여부 체크 */}
      <Route element={<AdminRoute />}>

        {/* 기본 관리자 대시보드 (/admin) */}
        <Route index element={<AdminDashboard />} />

        {/* 회원 관리 페이지 (/admin/users) */}
        <Route path="users" element={<AdminUserList />} />

        {/* 채용 공고 관리 페이지 (/admin/jobposts) */}
        <Route path="jobposts" element={<AdminJobList />} />

        {/* 채용 공고 수정 페이지 (/admin/jobposts/:jobId/edit) */}
        <Route path="jobposts/:jobId/edit" element={<AdminJobEdit />} />

        {/* 부트캠프 관리 페이지 (/admin/bootcamps) */}
        <Route path="bootcamps" element={<AdminBootcamps />} />

        {/* 부트캠프 수정 페이지 (/admin/bootcamps/:bootcampId/edit) */}
        <Route path="bootcamps/:bootcampId/edit" element={<AdminBootcampEdit />} />
      </Route>
    </Routes>
  )
}
