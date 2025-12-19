import React, { useState } from 'react';
import axios from 'axios';
import { Upload, X, CheckCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const ImportDialog = ({ open, onClose, onSuccess }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
      setError(null);
      setResult(null);
    } else {
      setError('Please select a valid CSV file');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/import`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);
      setTimeout(() => {
        onSuccess();
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to import file');
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setResult(null);
    setError(null);
    onClose();
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="bg-[#18181B] border-[#27272A] text-[#FAFAFA] sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="font-['JetBrains_Mono'] text-xl">Import Trade Data</DialogTitle>
          <DialogDescription className="text-[#A1A1AA] font-['Inter']">
            Upload your Fidelity CSV export file to import trades
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* File Upload Area */}
          <div
            className="border-2 border-dashed border-[#27272A] rounded-sm p-8 text-center hover:border-[#3F3F46] transition-colors cursor-pointer"
            onClick={() => document.getElementById('file-input').click()}
          >
            <input
              id="file-input"
              type="file"
              accept=".csv"
              onChange={handleFileChange}
              className="hidden"
              data-testid="file-input"
            />
            <Upload className="mx-auto h-12 w-12 text-[#A1A1AA] mb-4" />
            {file ? (
              <div>
                <p className="text-[#FAFAFA] font-['JetBrains_Mono'] font-medium">{file.name}</p>
                <p className="text-[#71717A] text-sm mt-1 font-['Inter']">
                  {(file.size / 1024).toFixed(2)} KB
                </p>
              </div>
            ) : (
              <div>
                <p className="text-[#FAFAFA] font-['Inter'] mb-2">Click to select a CSV file</p>
                <p className="text-[#71717A] text-sm font-['Inter']">or drag and drop here</p>
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 p-4 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-sm">
              <AlertCircle className="h-5 w-5 text-[#EF4444] flex-shrink-0" />
              <p className="text-[#EF4444] text-sm font-['Inter']">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {result && (
            <div className="space-y-3 p-4 bg-[#10B981]/10 border border-[#10B981]/30 rounded-sm">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-[#10B981] flex-shrink-0" />
                <p className="text-[#10B981] font-['Inter'] font-medium">Import Successful!</p>
              </div>
              <div className="text-[#FAFAFA] text-sm font-['JetBrains_Mono'] space-y-1 pl-7">
                <p>• Imported: {result.imported_count} new trades</p>
                <p>• Duplicates skipped: {result.duplicate_count}</p>
                <p>• Matched trades: {result.matched_trades_count}</p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-3 pt-4">
            <Button
              onClick={handleClose}
              variant="outline"
              className="bg-transparent border-[#27272A] hover:bg-[#27272A] text-[#FAFAFA] rounded-sm"
              data-testid="cancel-button"
            >
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!file || uploading || result}
              className="bg-[#FAFAFA] text-[#18181B] hover:bg-[#E4E4E7] rounded-sm font-['JetBrains_Mono']"
              data-testid="upload-button"
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ImportDialog;
