import AdminLayout from "./AdminLayout";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { adminApi } from "../../api/admin";

interface JobPost {
  jobid: number;
  jobtitle: string;
  company?: string;
  jobdescription?: string;
}

export default function AdminJobList() {
  const [jobPosts, setJobPosts] = useState<JobPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const navigate = useNavigate();

  // 페이지네이션 상태 (클라이언트 사이드)
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10; // 페이지당 항목 수

  const loadJobPosts = async () => {
    try {
      setLoading(true);
      const data = await adminApi.getJobPosts();
      setJobPosts(data);
    } catch (error) {
      console.error("Failed to load job posts:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobPosts();
  }, []);

  // 검색어가 변경되면 첫 페이지로 이동
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm]);

  const handleDeleteJobPost = async (jobId: number) => {
    if (!window.confirm("정말 이 공고를 삭제하시겠습니까?")) return;

    try {
      await adminApi.deleteJobPost(jobId);
      setJobPosts(jobPosts.filter((j) => j.jobid !== jobId));
      alert("공고가 삭제되었습니다.");
    } catch (error) {
      console.error("Failed to delete job post:", error);
      alert("공고 삭제에 실패했습니다.");
    }
  };

  const sortedJobPosts = [...jobPosts].sort((a, b) => Number(a.jobid) - Number(b.jobid));

  const filteredJobPosts = sortedJobPosts.filter((job) =>
    job.jobtitle.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (job.company && job.company.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  // 페이지네이션 계산 (클라이언트 사이드)
  const total = filteredJobPosts.length;
  const totalPages = Math.ceil(total / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentJobPosts = filteredJobPosts.slice(startIndex, endIndex);

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
            <h1 className="text-3xl font-bold text-gray-800">채용 공고 관리</h1>
            <p className="text-gray-600 mt-2">전체 공고 조회, 수정, 삭제</p>
          </div>

          <div className="mt-2">
            <input
              type="text"
              placeholder="제목 또는 기업명으로 검색"
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
                    제목
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    기업명
                  </th>
                  <th className="px-6 py-3 text-left text-sm font-semibold text-gray-700">
                    작업
                  </th>
                </tr>
              </thead>

              <tbody>
                {filteredJobPosts.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                      {jobPosts.length === 0 ? "채용 공고가 없습니다." : "검색 결과가 없습니다."}
                    </td>
                  </tr>
                ) : (
                  currentJobPosts.map((job) => (
                    <tr
                      key={job.jobid}
                      className="border-b border-gray-200 hover:bg-gray-50"
                    >
                      <td className="px-6 py-4 text-sm text-gray-900">
                        {job.jobid}
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <Link
                          to={`/jobs/${job.jobid}`}
                          className="text-slate-900 hover:text-primary-600 transition-colors cursor-pointer"
                        >
                          {job.jobtitle}
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">
                        {job.company || "-"}
                      </td>
                      <td className="px-6 py-4 text-sm space-x-2 flex">
                        <button
                          onClick={() => navigate(`/admin/jobposts/${job.jobid}/edit`)}
                          className="px-3 py-1 bg-blue-500 text-white rounded text-xs font-medium hover:bg-blue-600"
                        >
                          수정
                        </button>
                        <button
                          onClick={() => handleDeleteJobPost(job.jobid)}
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
    </AdminLayout>
  );
}
