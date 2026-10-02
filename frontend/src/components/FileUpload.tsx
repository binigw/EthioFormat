"use client";

import React, { useRef, useState } from "react";
import { formatFileSize } from "@/lib/utils";
import { FileUp, FileText, CheckCircle2, AlertCircle, X } from "lucide-react";

interface FileUploadProps {
  file: File | null;
  onFileSelect: (file: File | null) => void;
  disabled?: boolean;
}

export function FileUpload({ file, onFileSelect, disabled = false }: FileUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (selectedFile: File) => {
    setErrorMessage(null);
    if (!selectedFile.name.toLowerCase().endsWith(".docx")) {
      setErrorMessage("Only Microsoft Word (.docx) files are supported for thesis formatting.");
      return;
    }
    if (selectedFile.size > 50 * 1024 * 1024) {
      setErrorMessage("File exceeds 50 MB limit. Please select a smaller .docx file.");
      return;
    }
    onFileSelect(selectedFile);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
          <FileUp className="h-4 w-4 text-emerald-600" />
          <span>Upload Academic Thesis (.docx)</span>
          <span className="text-rose-500">*</span>
        </label>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        className="hidden"
        disabled={disabled}
        onChange={(e) => {
          if (e.target.files && e.target.files[0]) {
            validateAndSetFile(e.target.files[0]);
          }
        }}
      />

      {!file ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !disabled && inputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-6 sm:p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? "border-emerald-500 bg-emerald-50/50 scale-[1.01]"
              : "border-slate-300 hover:border-emerald-500/80 hover:bg-slate-50/50 bg-white"
          } ${disabled ? "opacity-60 cursor-not-allowed" : ""}`}
        >
          <div className="mx-auto w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600 mb-3 shadow-sm">
            <FileUp className="h-6 w-6" />
          </div>
          <div className="text-sm font-semibold text-slate-800">
            Click to upload or drag & drop your thesis (.docx)
          </div>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Standard Ethiopian thesis formatting (.docx format, up to 50 MB).
          </p>
        </div>
      ) : (
        <div className="flex items-center justify-between p-4 bg-emerald-50/70 border border-emerald-200 rounded-xl">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-10 h-10 rounded-lg bg-emerald-600 text-white flex items-center justify-center flex-shrink-0 shadow-sm">
              <FileText className="h-5 w-5" />
            </div>
            <div className="truncate">
              <div className="font-semibold text-sm text-slate-900 truncate">
                {file.name}
              </div>
              <div className="text-xs text-emerald-800 flex items-center gap-2">
                <span>{formatFileSize(file.size)}</span>
                <span>•</span>
                <span className="flex items-center gap-1 text-emerald-700 font-medium">
                  <CheckCircle2 className="h-3 w-3" /> Ready for formatting
                </span>
              </div>
            </div>
          </div>

          <button
            type="button"
            disabled={disabled}
            onClick={(e) => {
              e.stopPropagation();
              onFileSelect(null);
            }}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-white transition-colors"
            title="Remove file"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="flex items-center gap-2 p-3 text-xs text-rose-700 bg-rose-50 rounded-lg border border-rose-200">
          <AlertCircle className="h-4 w-4 flex-shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}
    </div>
  );
}
