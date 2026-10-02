import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Sparkles, HelpCircle, FileCheck, Layers } from 'lucide-react';
import { toast } from 'sonner';

import BatchDropzone, { autoTagDocument, validateUploadFile } from '../components/upload/BatchDropzone';
import DocumentCard from '../components/upload/DocumentCard';
import ReadinessCheck, { EXTRACTION_STAGES } from '../components/upload/ReadinessCheck';
import { uploadDocument, triggerAnalysis } from '../services/api';

const DOCUMENT_KEYS = ['HOSPITAL_BILL', 'INSURANCE_POLICY', 'REJECTION_LETTER'];

export default function Upload() {
  const navigate = useNavigate();
  const [claimId, setClaimId] = useState(null);
  const [mode, setMode] = useState('batch'); // 'batch' | 'guided'
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [extractionStage, setExtractionStage] = useState(0);
  const [extractionProgress, setExtractionProgress] = useState(0);

  const [documents, setDocuments] = useState({
    HOSPITAL_BILL: null,
    INSURANCE_POLICY: null,
    REJECTION_LETTER: null,
  });

  const animationIntervalRef = useRef(null);

  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (animationIntervalRef.current) {
        clearInterval(animationIntervalRef.current);
      }
    };
  }, []);

  /**
   * Uploads a single file to a document slot and associates it with the session claim ID.
   */
  const uploadSingleFile = async (file, docType, activeClaimId = claimId) => {
    const validation = validateUploadFile(file);
    if (!validation.valid) {
      toast.error('Invalid Document', {
        description: validation.error,
      });
      return activeClaimId;
    }

    // Set optimistic uploading state for this slot
    const optimisticRecord = {
      file,
      name: file.name,
      size: file.size,
      type: file.type || 'application/pdf',
      uploadStatus: 'uploading'
    };

    setDocuments(prev => ({ ...prev, [docType]: optimisticRecord }));

    try {
      const response = await uploadDocument(file, docType, activeClaimId);
      const assignedClaimId = activeClaimId || response.claim_id;

      if (!activeClaimId && assignedClaimId) {
        setClaimId(assignedClaimId);
      }

      setDocuments(prev => ({
        ...prev,
        [docType]: {
          file,
          name: file.name,
          size: file.size,
          type: file.type || 'application/pdf',
          uploadStatus: 'ready',
          serverDocId: response.document_id,
          status: 'VERIFIED'
        }
      }));

      const friendlyTitle = docType.replace(/_/g, ' ').toLowerCase();
      toast.success('Document Attached', {
        description: `${file.name} attached as ${friendlyTitle}.`,
      });
      return assignedClaimId;
    } catch (error) {
      console.error(`Failed to upload ${docType}:`, error);
      setDocuments(prev => ({
        ...prev,
        [docType]: {
          file,
          name: file.name,
          size: file.size,
          type: file.type,
          uploadStatus: 'error'
        }
      }));
      toast.error('Upload Failed', {
        description: `Unable to upload ${file.name}. Check network connection and retry.`,
      });
      return activeClaimId;
    }
  };

  /**
   * Mode A: Batch Multi-Drop handler with auto-tagging heuristics and fallback filling.
   */
  const handleBatchFiles = async (files) => {
    if (!files || files.length === 0) return;
    setIsUploading(true);

    let currentClaimId = claimId;
    const assignedSlots = {};
    const unassignedFiles = [];

    // Step 1: Run regex auto-tagging
    files.forEach((file) => {
      const detected = autoTagDocument(file.name);
      if (detected && !assignedSlots[detected] && !documents[detected]) {
        assignedSlots[detected] = file;
      } else {
        unassignedFiles.push(file);
      }
    });

    // Step 2: Fill remaining unfilled slots with unassigned files
    for (const key of DOCUMENT_KEYS) {
      if (!assignedSlots[key] && !documents[key] && unassignedFiles.length > 0) {
        assignedSlots[key] = unassignedFiles.shift();
      }
    }

    // Step 3: If still unassigned files exist (all 3 slots had something or duplicate tags),
    // replace any remaining slots that matched
    for (const file of unassignedFiles) {
      const detected = autoTagDocument(file.name) || DOCUMENT_KEYS.find(k => !assignedSlots[k]);
      if (detected) {
        assignedSlots[detected] = file;
      }
    }

    // Step 4: Execute uploads sequentially so claimId propagates cleanly
    for (const [docType, file] of Object.entries(assignedSlots)) {
      currentClaimId = await uploadSingleFile(file, docType, currentClaimId);
    }

    setIsUploading(false);
  };

  /**
   * Mode B: Slotted target file drop / browse.
   */
  const handleSlotFile = async (file, docType) => {
    setIsUploading(true);
    await uploadSingleFile(file, docType, claimId);
    setIsUploading(false);
  };

  /**
   * Replace file in specific slot.
   */
  const handleReplace = async (file, docType) => {
    setIsUploading(true);
    await uploadSingleFile(file, docType, claimId);
    setIsUploading(false);
  };

  /**
   * Remove file from specific slot.
   */
  const handleRemove = (docType) => {
    setDocuments(prev => ({ ...prev, [docType]: null }));
    const friendlyTitle = docType.replace(/_/g, ' ').toLowerCase();
    toast.success('Document Removed', {
      description: `Detached file from ${friendlyTitle} slot.`,
    });
  };

  /**
   * Retag / swap document category slots.
   */
  const handleRetag = (sourceType, targetType) => {
    if (sourceType === targetType) return;
    setDocuments(prev => {
      const sourceDoc = prev[sourceType];
      const targetDoc = prev[targetType];
      return {
        ...prev,
        [sourceType]: targetDoc,
        [targetType]: sourceDoc
      };
    });
    const friendlyTarget = targetType.replace(/_/g, ' ').toLowerCase();
    toast.success('Document Reclassified', {
      description: `Slot reassigned to ${friendlyTarget}.`,
    });
  };

  /**
   * Clear all documents and reset session.
   */
  const handleClearAll = () => {
    setDocuments({
      HOSPITAL_BILL: null,
      INSURANCE_POLICY: null,
      REJECTION_LETTER: null,
    });
    setClaimId(null);
    setExtractionStage(0);
    setExtractionProgress(0);
    setIsAnalyzing(false);
    toast.success('Session Reset', {
      description: 'All attached documents cleared from intake session.',
    });
  };

  /**
   * Run Claim Forensics & Audit with 4-Stage Extraction Progress Animation.
   */
  const handleRunAudit = async () => {
    const activeId = claimId;
    if (!activeId) {
      toast.error('No Active Session', {
        description: 'Please attach documents before initiating audit.',
      });
      return;
    }

    setIsAnalyzing(true);
    setExtractionProgress(5);
    setExtractionStage(0);

    toast.loading('Starting claim analysis…', { id: 'analysis-start' });

    try {
      await triggerAnalysis(activeId);
      toast.success('Analysis started', { id: 'analysis-start' });
      navigate(`/analysis/${activeId}`);
    } catch (error) {
      console.error('Trigger analysis error:', error);
      if (animationIntervalRef.current) clearInterval(animationIntervalRef.current);
      setIsAnalyzing(false);
      toast.dismiss('analysis-start');
      toast.error('Pipeline Execution Failed', {
        description: error?.response?.status === 503
          ? (error?.response?.data?.detail || 'Analysis capacity is full. Please retry shortly.')
          : (error?.response?.data?.detail || error?.message || 'Failed to initiate analysis pipeline.'),
      });
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">
              Claim Intake & Upload Studio
            </h1>
            <span className="bg-sky-100 text-sky-800 text-[10px] font-bold px-2.5 py-0.5 rounded-full border border-sky-200 uppercase tracking-wider">
              VLM OCR v2.4
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Intake itemized hospital bills, insurance policy schedules, and TPA rejection letters for statutory IRDAI audits.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <div className="text-[10px] uppercase font-bold text-slate-400">
              Statutory Compliance
            </div>
            <div className="text-xs font-bold text-slate-700">
              IRDAI Master Circular 2024
            </div>
          </div>
          <div className="w-10 h-10 rounded-xl bg-teal-50 border border-teal-200 text-teal-600 flex items-center justify-center shadow-xs">
            <Shield className="w-5 h-5" />
          </div>
        </div>
      </div>

      {/* Main Studio Grid: Left (7 Cols) + Right (5 Cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Dropzone & Attached Document Cards */}
        <div className="lg:col-span-7 space-y-5">
          {/* Dual-Mode Dropzone */}
          <div className="card-enterprise p-5 bg-white border-slate-200/90 shadow-card">
            <BatchDropzone
              mode={mode}
              onModeChange={setMode}
              onBatchFiles={handleBatchFiles}
              onSlotFile={handleSlotFile}
              documents={documents}
              isUploading={isUploading || isAnalyzing}
            />
          </div>

          {/* Attached Document Records Stack */}
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1">
              <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 flex items-center gap-2">
                <FileCheck className="w-3.5 h-3.5 text-slate-400" />
                Attached Document Records
              </h2>
              <span className="text-[11px] text-slate-400">
                Audit slots can be reclassified or replaced
              </span>
            </div>

            {DOCUMENT_KEYS.map((key) => (
              <DocumentCard
                key={key}
                documentType={key}
                docRecord={documents[key]}
                onReplace={(file) => handleReplace(file, key)}
                onRemove={() => handleRemove(key)}
                onRetag={(newType) => handleRetag(key, newType)}
                disabled={isUploading || isAnalyzing}
              />
            ))}
          </div>
        </div>

        {/* Right Column: Pre-Analysis Health Check & Forensics Trigger */}
        <div className="lg:col-span-5 lg:sticky lg:top-6">
          <ReadinessCheck
            documents={documents}
            claimId={claimId}
            isAnalyzing={isAnalyzing}
            extractionStage={extractionStage}
            extractionProgress={extractionProgress}
            onRunAudit={handleRunAudit}
            onClearAll={handleClearAll}
          />
        </div>
      </div>
    </div>
  );
}
