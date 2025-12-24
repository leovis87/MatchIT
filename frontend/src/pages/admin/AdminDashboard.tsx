import AdminLayout from "./AdminLayout";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { adminApi } from "../../api/admin";

export default function AdminDashboard() {
  const [stats, setStats] = useState({
    totalUsers: 0,
    totalJobPosts: 0,
    totalBootcamps: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        setLoading(true);
        const usersData = await adminApi.getUsers();
        const jobPostsData = await adminApi.getJobPosts();
        const bootcampsData = await adminApi.getBootcamps();

        setStats({
          totalUsers: usersData.length,
          totalJobPosts: jobPostsData.length,
          totalBootcamps: bootcampsData.length,
        });
      } catch (error) {
        console.error("Failed to load dashboard stats:", error);
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, []);

  return (
    <AdminLayout>
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-800">관리자 대시보드</h1>
        <p className="text-gray-600 mt-2">시스템 통계 및 주요 정보</p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-600">✅ 로딩 중...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-6 bg-white shadow rounded-lg border-l-4 border-blue-500">
            <p className="text-gray-600 text-sm font-medium">👤 총 회원 수</p>
            <p className="text-4xl font-bold mt-3 text-blue-600">{stats.totalUsers}</p>
            <p className="text-gray-500 text-xs mt-2">👪 등록된 전체 사용자</p>
          </div>

          <div className="p-6 bg-white shadow rounded-lg border-l-4 border-green-500">
            <p className="text-gray-600 text-sm font-medium">🎯 총 채용 공고</p>
            <p className="text-4xl font-bold mt-3 text-green-600">{stats.totalJobPosts}</p>
            <p className="text-gray-500 text-xs mt-2">💡 등록된 전체 공고</p>
          </div>

          <div className="p-6 bg-white shadow rounded-lg border-l-4 border-purple-500">
            <p className="text-gray-600 text-sm font-medium">⛺ 총 부트캠프</p>
            <p className="text-4xl font-bold mt-3 text-purple-600">{stats.totalBootcamps}</p>
            <p className="text-gray-500 text-xs mt-2">💡 등록된 전체 부트캠프</p>
          </div>
        </div>
      )}

      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="p-6 bg-white shadow rounded-lg">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">빠른 작업</h2>
          <ul className="space-y-2">
            <li>
              <Link to="/admin/users" className="text-blue-600 hover:text-blue-800 font-medium">
                → 회원 관리
              </Link>
            </li>
            <li>
              <Link to="/admin/jobposts" className="text-green-600 hover:text-green-800 font-medium">
                → 채용 공고 관리
              </Link>
            </li>
            <li>
              <Link to="/admin/bootcamps" className="text-purple-600 hover:text-purple-800 font-medium">
                → 부트캠프 관리
              </Link>
            </li>
          </ul>
        </div>

        <div className="p-6 bg-white shadow rounded-lg">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">⚙️ 시스템 정보</h2>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>• 플랫폼: MatchIT</li>
            <li>• 버전: 1.0.0</li>
            <li>• 관리자 권한으로 로그인됨</li>
          </ul>
        </div>
      </div>
    </AdminLayout>
  );
}
