import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import AdminLayout from "./AdminLayout";
import { fetchJobDetail, type JobPost } from "../../api/jobposts";
import { adminApi, type AdminJobUpdatePayload } from "../../api/admin";

interface FormState {
  Title: string;
  CompanyName: string;
  Location: string;
  EmploymentType: string;
  ExperienceRequirement: string;
  MinExperienceYears: string;
  EducationRequirement: string;
  MainTasks: string;
  Qualifications: string;
  Preferences: string;
  Benefits: string;
  Process: string;
  Salary: string;
  CloseDate: string;
  Url: string;
  IsActive: boolean;
}

const formatDateInput = (value: string | null | undefined) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toISOString().slice(0, 10);
};

export default function AdminJobEdit() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const numericJobId = jobId ? Number(jobId) : NaN;

  const [form, setForm] = useState<FormState | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    data: job,
    isLoading,
    isError,
    error,
  } = useQuery<JobPost | undefined>({
    queryKey: ["adminJobDetail", numericJobId],
    queryFn: () => fetchJobDetail(numericJobId),
    enabled: Number.isFinite(numericJobId),
  });

  useEffect(() => {
    if (!job) return;
    setForm({
      Title: job.Title ?? "",
      CompanyName: job.CompanyName ?? "",
      Location: job.Location ?? "",
      EmploymentType: job.EmploymentType ?? "",
      ExperienceRequirement: job.ExperienceRequirement ?? "",
      MinExperienceYears:
        job.MinExperienceYears !== null && job.MinExperienceYears !== undefined
          ? String(job.MinExperienceYears)
          : "",
      EducationRequirement: job.EducationRequirement ?? "",
      MainTasks: job.MainTasks ?? "",
      Qualifications: job.Qualifications ?? "",
      Preferences: job.Preferences ?? "",
      Benefits: job.Benefits ?? "",
      Process: job.Process ?? "",
      Salary: job.Salary ?? "",
      CloseDate: formatDateInput(job.CloseDate),
      Url: job.Url ?? "",
      IsActive: job.IsActive,
    });
  }, [job]);

  const mutation = useMutation({
    mutationFn: (payload: AdminJobUpdatePayload) =>
      adminApi.updateFullJobPost(numericJobId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminJobDetail", numericJobId] });
      queryClient.invalidateQueries({ queryKey: ["jobDetail", numericJobId] });
      setStatusMessage("공고가 성공적으로 수정되었습니다.");
      setErrorMessage(null);
      setTimeout(() => {
        navigate("/admin/jobposts");
      }, 800);
    },
    onError: (err: unknown) => {
      const message = err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.";
      setErrorMessage(message);
      setStatusMessage(null);
    },
  });

  const handleInputChange = (key: keyof FormState) => (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    setForm((prev) => (prev ? { ...prev, [key]: e.target.value } : prev));
  };

  const handleTextareaChange = (key: keyof FormState) => (
    e: React.ChangeEvent<HTMLTextAreaElement>
  ) => {
    setForm((prev) => (prev ? { ...prev, [key]: e.target.value } : prev));
  };

  const handleToggleActive = () => {
    setForm((prev) => (prev ? { ...prev, IsActive: !prev.IsActive } : prev));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form || !Number.isFinite(numericJobId)) return;

    const payload: AdminJobUpdatePayload = {
      Title: form.Title || null,
      CompanyName: form.CompanyName || null,
      EmploymentType: form.EmploymentType || null,
      ExperienceRequirement: form.ExperienceRequirement || null,
      MinExperienceYears: form.MinExperienceYears === "" ? null : Number(form.MinExperienceYears),
      EducationRequirement: form.EducationRequirement || null,
      Location: form.Location || null,
      MainTasks: form.MainTasks || null,
      Qualifications: form.Qualifications || null,
      Preferences: form.Preferences || null,
      Benefits: form.Benefits || null,
      Process: form.Process || null,
      Salary: form.Salary || null,
      CloseDate: form.CloseDate ? form.CloseDate : null,
      Url: form.Url || null,
      IsActive: form.IsActive,
    };

    mutation.mutate(payload);
  };

  const renderContent = useMemo(() => {
    if (!jobId || !Number.isFinite(numericJobId)) {
      return <p className="text-red-600">잘못된 공고 ID입니다.</p>;
    }

    if (isLoading || !form) {
      return <p className="text-slate-700">공고 정보를 불러오는 중입니다...</p>;
    }

    if (isError) {
      const message = (error as any)?.message ?? "알 수 없는 에러";
      return <p className="text-red-600">공고 로딩 실패: {message}</p>;
    }

    return (
      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <p className="text-sm font-semibold text-primary-700">{form.CompanyName || "회사명 미입력"}</p>
            <h1 className="text-3xl font-bold text-slate-900">{form.Title || "공고 제목"}</h1>
          </div>
          <div className="flex items-center gap-3">
            <span className={`text-sm font-medium ${form.IsActive ? "text-green-600" : "text-red-500"}`}>
              {form.IsActive ? "게시 중" : "비활성"}
            </span>
            <button
              type="button"
              onClick={handleToggleActive}
              className="rounded-lg border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
            >
              {form.IsActive ? "비활성으로 전환" : "게시로 전환"}
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-100 bg-slate-50/80 p-6 shadow-soft">
          <h2 className="mb-4 text-lg font-bold text-slate-900">기본 정보</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="text-sm font-semibold text-slate-700">제목</label>
              <input
                type="text"
                value={form.Title}
                onChange={handleInputChange("Title")}
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                required
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-slate-700">기업명</label>
              <input
                type="text"
                value={form.CompanyName}
                onChange={handleInputChange("CompanyName")}
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                required
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-slate-700">근무지역</label>
              <input
                type="text"
                value={form.Location}
                onChange={handleInputChange("Location")}
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-slate-700">고용 형태</label>
              <input
                type="text"
                value={form.EmploymentType}
                onChange={handleInputChange("EmploymentType")}
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-slate-700">경력 조건</label>
              <input
                type="text"
                value={form.ExperienceRequirement}
                onChange={handleInputChange("ExperienceRequirement")}
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                placeholder="신입 / 경력 / 무관"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-slate-700">최소 경력(년)</label>
              <input
                type="number"
                min={0}
                value={form.MinExperienceYears}
                onChange={handleInputChange("MinExperienceYears")}
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-slate-700">마감일</label>
              <input
                type="date"
                value={form.CloseDate}
                onChange={handleInputChange("CloseDate")}
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="text-sm font-semibold text-slate-700">지원 링크</label>
              <input
                type="url"
                value={form.Url}
                onChange={handleInputChange("Url")}
                className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
                placeholder="https://..."
              />
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-soft space-y-6">
          <SectionTextarea
            label="주요 업무"
            value={form.MainTasks}
            onChange={handleTextareaChange("MainTasks")}
          />
          <SectionTextarea
            label="자격 요건"
            value={form.Qualifications}
            onChange={handleTextareaChange("Qualifications")}
          />
          <SectionTextarea
            label="우대 사항"
            value={form.Preferences}
            onChange={handleTextareaChange("Preferences")}
          />
          <SectionTextarea
            label="복지 / 혜택"
            value={form.Benefits}
            onChange={handleTextareaChange("Benefits")}
          />
          <SectionTextarea
            label="전형 절차"
            value={form.Process}
            onChange={handleTextareaChange("Process")}
          />
          <div>
            <label className="block text-sm font-semibold text-slate-700 mb-2">연봉 / 보상</label>
            <input
              type="text"
              value={form.Salary}
              onChange={handleInputChange("Salary")}
              className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
              placeholder="예: 면접 후 협의"
            />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-2">기술 스택 (읽기 전용)</h3>
            <p className="text-sm text-slate-500">기술 스택 수정은 현재 API에서 지원되지 않아 표시만 제공합니다.</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {job?.Skills?.length ? (
                job.Skills.map((skill) => (
                  <span
                    key={skill}
                    className="rounded-full bg-primary-50 px-3 py-1 text-sm font-semibold text-primary-700"
                  >
                    {skill}
                  </span>
                ))
              ) : (
                <span className="text-sm text-slate-500">기술 스택 정보가 없습니다.</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between pt-2">
          <Link
            to="/admin/jobposts"
            className="text-sm text-slate-600 hover:text-slate-900 transition"
          >
            목록으로 돌아가기
          </Link>
          <div className="flex items-center gap-3">
            {errorMessage && <span className="text-sm text-red-600">{errorMessage}</span>}
            {statusMessage && <span className="text-sm text-green-600">{statusMessage}</span>}
            <button
              type="submit"
              disabled={mutation.isPending}
              className="rounded-lg bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary-700 disabled:opacity-60"
            >
              {mutation.isPending ? "저장 중..." : "변경사항 저장"}
            </button>
          </div>
        </div>
      </form>
    );
  }, [jobId, numericJobId, isLoading, isError, error, form, mutation.isPending, statusMessage, errorMessage, job]);

  return (
    <AdminLayout>
      <div className="mx-auto max-w-5xl px-4 py-10">
        <div className="mb-6">
          <Link
            to="/admin/jobposts"
            className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            채용공고 관리로 돌아가기
          </Link>
        </div>
        {renderContent}
      </div>
    </AdminLayout>
  );
}

function SectionTextarea({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLTextAreaElement>) => void;
}) {
  return (
    <div>
      <label className="block text-sm font-semibold text-slate-700 mb-2">{label}</label>
      <textarea
        value={value}
        onChange={onChange}
        rows={4}
        className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
      />
    </div>
  );
}
