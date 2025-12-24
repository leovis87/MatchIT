import AdminLayout from "./AdminLayout";
import { useEffect, useState } from "react";
import { adminApi } from "../../api/admin";

interface AdminUser {
  userid: number;
  email: string;
  name?: string;
  role: number;  // 1 for user, 2 for admin
}

export default function AdminUserList() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [newRole, setNewRole] = useState<number>(1);
  const [searchTerm, setSearchTerm] = useState("");

  // 페이지네이션 상태 (클라이언트 사이드)
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10; // 페이지당 항목 수

  const loadUsers = async () => {
    try {
      setLoading(true);
      const data = await adminApi.getUsers();
      const list = Array.isArray(data) ? data : Array.isArray((data as any)?.users) ? (data as any).users : [];
      const normalized = list.map((u: any) => ({
        userid: u.userid ?? u.user_id ?? u.id,
        email: u.email ?? u.Email ?? "",
        name: u.name ?? u.username ?? u.full_name ?? "",
        role: typeof u.role === "number" ? u.role : 1,
      }));
      setUsers(normalized);
    } catch (error) {
      console.error("Failed to load users:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  // 검색어가 변경되면 첫 페이지로 이동
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm]);

  const handleDeleteUser = async (userId: number) => {
    if (!window.confirm("📢 이 사용자를 삭제하시겠습니까?")) return;

    try {
      await adminApi.deleteUser(userId);
      setUsers(users.filter((u) => u.userid !== userId));
      alert("✅ 사용자가 삭제되었습니다.");
    } catch (error) {
      console.error("Failed to delete user:", error);
      alert("⚠️ 사용자 삭제에 실패했습니다.");
    }
  };

  const handleChangeRole = async () => {
    if (!selectedUser) return;

    try {
      await adminApi.updateUserRole(selectedUser.userid, newRole);
      setUsers(
        users.map((u) =>
          u.userid === selectedUser.userid ? { ...u, role: newRole } : u
        )
      );
      setShowRoleModal(false);
      alert("✅ 권한이 변경되었습니다.");
    } catch (error) {
      console.error("Failed to update user role:", error);
      alert("⚠️ 권한 변경에 실패했습니다.");
    }
  };

  const handleOpenRoleModal = (user: AdminUser) => {
    setSelectedUser(user);
    setNewRole(user.role);
    setShowRoleModal(true);
  };

  const filteredUsers = users.filter(user =>
    user.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // 페이지네이션 계산 (클라이언트 사이드)
  const total = filteredUsers.length;
  const totalPages = Math.ceil(total / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentUsers = filteredUsers.slice(startIndex, endIndex);

  // 페이지 번호 생성 (Bootcamps.tsx와 동일한 로직)
  const getPageNumbers = () => {
    const pages: number[] = [];
    const maxVisible = 5;

    if (totalPages <= maxVisible) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) pages.push(i);
        pages.push(-1);
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1);
        pages.push(-1);
        for (let i = totalPages - 3; i <= totalPages; i++) pages.push(i);
      } else {
        pages.push(1);
        pages.push(-1);
        pages.push(currentPage - 1);
        pages.push(currentPage);
        pages.push(currentPage + 1);
        pages.push(-1);
        pages.push(totalPages);
      }
    }

    return pages;
  };

  return (
    <AdminLayout>
      <div className="mb-6">
        <div className="flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-800">회원 관리</h1>
            <p className="text-gray-600 mt-2">전체 사용자 조회 및 관리</p>
          </div>

          <div className="mt-2">
            <input
              type="text"
              placeholder="이름 또는 이메일로 검색"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-80 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>


      {loading ? (
        <div className="flex items-center justify-center h-64">
          <p className="text-gray-600">로딩 중...</p>
        </div>
      ) : (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    ID
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    이메일
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    이름
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    권한
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    작업
                  </th>
                </tr>
              </thead>

              <tbody>
                {filteredUsers.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                      {searchTerm ? "검색 결과가 없습니다." : "사용자가 없습니다."}
                    </td>
                  </tr>
                ) : (
                  currentUsers.map((user) => (
                    <tr
                      key={user.userid}
                      className="border-b border-gray-200 hover:bg-gray-50"
                    >
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {user.userid}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {user.email}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {user.name || "-"}
                      </td>
                      <td className="px-6 py-4 text-sm">
                        <span
                          className={`px-3 py-1 rounded-full text-xs font-semibold ${
                            user.role === 2
                              ? "bg-red-100 text-red-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {user.role === 2 ? "관리자" : "일반"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm space-x-2 flex">
                        <button
                          onClick={() => handleOpenRoleModal(user)}
                          className="px-3 py-1 bg-blue-500 text-white rounded text-xs font-medium hover:bg-blue-600"
                        >
                          권한 변경
                        </button>
                        <button
                          onClick={() => handleDeleteUser(user.userid)}
                          className="px-3 py-1 bg-red-500 text-white rounded text-xs font-medium hover:bg-red-600"
                        >
                          삭제
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          </div>
      )}

        {/* 페이지네이션 */}
        {!loading && totalPages > 1 && (
          <div className="flex items-center justify-center gap-2 pt-4">
            <button
              onClick={() => setCurrentPage((prev) => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-white"
            >
              이전
            </button>

            {getPageNumbers().map((pageNum, idx) => {
              if (pageNum === -1) {
                return (
                  <span key={`ellipsis-${idx}`} className="px-2 text-slate-400">
                    ...
                  </span>
                );
              }
              return (
                <button
                  key={pageNum}
                  onClick={() => setCurrentPage(pageNum)}
                  className={`min-w-[40px] rounded-lg border px-3 py-2 text-sm font-medium transition ${
                    currentPage === pageNum
                      ? 'border-primary-600 bg-primary-600 text-white'
                      : 'border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}

            <button
              onClick={() => setCurrentPage((prev) => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:bg-white"
            >
              다음
            </button>
          </div>
        )}

      {/* 권한 변경 모달 */}
      {showRoleModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-96 shadow-xl">
            <h2 className="text-xl font-bold mb-4">권한 변경</h2>
            <p className="text-gray-600 mb-4">
              사용자: <span className="font-semibold">{selectedUser.email}</span>
            </p>

            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                새로운 권한
              </label>
              <select
                value={newRole}
                onChange={(e) => setNewRole(Number(e.target.value))}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value={1}>일반 사용자</option>
                <option value={2}>관리자</option>
              </select>
            </div>

            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowRoleModal(false)}
                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 font-medium"
              >
                취소
              </button>
              <button
                onClick={handleChangeRole}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 font-medium"
              >
                변경
              </button>
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
