import React, { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import AdminLayout from "./AdminLayout";
import { bootcampApi, type BootcampItem } from "../../api/bootcamp";
import { adminApi, type AdminBootcampUpdatePayload } from "../../api/admin";

interface FormState {
  Title: string;
  InstituteName: string;
  JobCategoryID: string;
  Location: string;
  OnlineOffline: string;
  CostSupportType: string;
  EducationContent: string;
  Qualification: string;
  Benefits: string;
  StartDate: string;
  RegistrationDate: string;
  CloseDate: string;
  DetailUrl: string;
  ViewCount: string;
}

const formatDateInput = (value: string | null | undefined) => {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toISOString().slice(0, 10);
};

export default function AdminBootcampEdit() {
  const { bootcampId } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const numericBootcampId = bootcampId ? Number(bootcampId) : NaN;

  const [form, setForm] = useState<FormState | null>(null);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const {
    data: bootcamp,
    isLoading,
    isError,
    error,
  } = useQuery<BootcampItem | undefined>({
    queryKey: ["adminBootcampDetail", numericBootcampId],
    queryFn: () => bootcampApi.getBootcampDetail(numericBootcampId),
    enabled: Number.isFinite(numericBootcampId),
  });

  useEffect(() => {
    if (!bootcamp) return;
    setForm({
      Title: bootcamp.Title ?? "",
      InstituteName: bootcamp.InstituteName ?? "",
      JobCategoryID:
        bootcamp.JobCategoryID !== null && bootcamp.JobCategoryID !== undefined
          ? String(bootcamp.JobCategoryID)
          : "",
      Location: bootcamp.Location ?? "",
      OnlineOffline: bootcamp.OnlineOffline ?? "",
      CostSupportType: bootcamp.CostSupportType ?? "",
      EducationContent: bootcamp.EducationContent ?? "",
      Qualification: bootcamp.Qualification ?? "",
      Benefits: bootcamp.Benefits ?? "",
      StartDate: formatDateInput(bootcamp.StartDate),
      RegistrationDate: formatDateInput(bootcamp.RegistrationDate),
      CloseDate: formatDateInput(bootcamp.CloseDate),
      DetailUrl: bootcamp.DetailUrl ?? "",
      ViewCount: bootcamp.ViewCount !== null && bootcamp.ViewCount !== undefined ? String(bootcamp.ViewCount) : "",
    });
  }, [bootcamp]);

  const mutation = useMutation({
    mutationFn: (payload: AdminBootcampUpdatePayload) =>
      adminApi.updateFullBootcamp(numericBootcampId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["adminBootcampDetail", numericBootcampId] });
      queryClient.invalidateQueries({ queryKey: ["bootcampDetail", numericBootcampId] });
      setStatusMessage("부트캠프가 성공적으로 수정되었습니다.");
      setErrorMessage(null);
      setTimeout(() => {
        navigate("/admin/bootcamps");
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!form || !Number.isFinite(numericBootcampId)) return;

    const payload: AdminBootcampUpdatePayload = {
      Title: form.Title || null,
      InstituteName: form.InstituteName || null,
      JobCategoryID: form.JobCategoryID === "" ? null : Number(form.JobCategoryID),
      Location: form.Location || null,
      OnlineOffline: form.OnlineOffline || null,
      CostSupportType: form.CostSupportType || null,
      EducationContent: form.EducationContent || null,
      Qualification: form.Qualification || null,
      Benefits: form.Benefits || null,
      StartDate: form.StartDate ? form.StartDate : null,
      RegistrationDate: form.RegistrationDate ? form.RegistrationDate : null,
      CloseDate: form.CloseDate ? form.CloseDate : null,
      DetailUrl: form.DetailUrl || null,
      ViewCount: form.ViewCount === "" ? null : Number(form.ViewCount),
    };

    mutation.mutate(payload);
  };

  const renderContent = useMemo(() => {
    if (!bootcampId || !Number.isFinite(numericBootcampId)) {
      return <p className="text-red-600">잘못된 부트캠프 ID입니다.</p>;
    }

    if (isLoading || !form) {
      return <p className="text-slate-700">부트캠프 정보를 불러오는 중입니다...</p>;
    }

    if (isError) {
      const message = (error as any)?.message ?? "알 수 없는 에러";
      return <p className="text-red-600">부트캠프 로딩 실패: {message}</p>;
    }

    return (
      <form onSubmit={handleSubmit} className="space-y-8">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <p className="text-sm font-semibold text-primary-700">{form.InstituteName || "기관명 미입력"}</p>
            <h1 className="text-3xl font-bold text-slate-900">{form.Title || "부트캠프 제목"}</h1>
          </div>
          <Link
            to={`/bootcamps/${numericBootcampId}`}
            className="text-sm text-primary-600 hover:text-primary-700 transition"
          >
            사용자 상세 보기
          </Link>
        </div>

        <div className="rounded-2xl border border-slate-100 bg-slate-50/80 p-6 shadow-soft">
          <h2 className="mb-4 text-lg font-bold text-slate-900">기본 정보</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <InputField label="제목" value={form.Title} onChange={handleInputChange("Title")}/>
            <InputField label="기관명" value={form.InstituteName} onChange={handleInputChange("InstituteName")}/>
            <InputField label="카테고리 ID" value={form.JobCategoryID} onChange={handleInputChange("JobCategoryID")} type="number"/>
            <InputField label="위치" value={form.Location} onChange={handleInputChange("Location")}/>
            <InputField label="수강 형태" value={form.OnlineOffline} onChange={handleInputChange("OnlineOffline")}/>
            <InputField label="비용 지원" value={form.CostSupportType} onChange={handleInputChange("CostSupportType")}/>
            <InputField label="시작일" value={form.StartDate} onChange={handleInputChange("StartDate")} type="date"/>
            <InputField label="등록일" value={form.RegistrationDate} onChange={handleInputChange("RegistrationDate")} type="date"/>
            <InputField label="마감일" value={form.CloseDate} onChange={handleInputChange("CloseDate")} type="date"/>
            <InputField label="지원 링크" value={form.DetailUrl} onChange={handleInputChange("DetailUrl")} type="url"/>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-100 bg-white p-6 shadow-soft space-y-6">
          <SectionTextarea
            label="교육 내용"
            value={form.EducationContent}
            onChange={handleTextareaChange("EducationContent")}
          />
          <SectionTextarea
            label="자격 요건"
            value={form.Qualification}
            onChange={handleTextareaChange("Qualification")}
          />
          <SectionTextarea
            label="혜택"
            value={form.Benefits}
            onChange={handleTextareaChange("Benefits")}
          />
        </div>

        <div className="flex items-center justify-between pt-2">
          <Link
            to="/admin/bootcamps"
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
  }, [bootcampId, numericBootcampId, isLoading, isError, error, form, mutation.isPending, statusMessage, errorMessage]);

  return (
    <AdminLayout>
      <div className="mx-auto max-w-5xl px-4 py-10">
        <div className="mb-6">
          <Link
            to="/admin/bootcamps"
            className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 transition"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            부트캠프 관리로 돌아가기
          </Link>
        </div>
        {renderContent}
      </div>
    </AdminLayout>
  );
}

function InputField({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  type?: string;
}) {
  return (
    <div>
      <label className="text-sm font-semibold text-slate-700">{label}</label>
      <input
        type={type}
        value={value}
        onChange={onChange}
        className="mt-2 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm"
      />
    </div>
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
