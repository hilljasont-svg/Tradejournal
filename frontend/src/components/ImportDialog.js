import React, { useState } from 'react';
import axios from 'axios';
import { Upload, X, CheckCircle, AlertCircle, ArrowRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
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
  const [step, setStep] = useState(1); // 1: upload, 2: mapping, 3: result
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  
  // Preview data
  const [headers, setHeaders] = useState([]);
  const [sampleRows, setSampleRows] = useState([]);
  const [suggestedMapping, setSuggestedMapping] = useState({});
  
  // User mapping
  const [mapping, setMapping] = useState({
    date: '',
    symbol: '',
    action: '',
    price: '',
    quantity: '',
    time: '',
  });
  const [dateTimeCombined, setDateTimeCombined] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.csv')) {
      setFile(selectedFile);
      setError(null);
      setResult(null);
      previewFile(selectedFile);
    } else {
      setError('Please select a valid CSV file');
    }
  };

  const previewFile = async (file) => {
    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API}/preview-csv`, formData);
      
      setHeaders(response.data.headers);
      setSampleRows(response.data.sample_rows);
      setSuggestedMapping(response.data.suggested_mapping);
      
      // Auto-fill mapping with suggestions
      setMapping({
        date: response.data.suggested_mapping.date || '',
        symbol: response.data.suggested_mapping.symbol || '',
        action: response.data.suggested_mapping.action || '',
        price: response.data.suggested_mapping.price || '',
        quantity: response.data.suggested_mapping.quantity || '',
        time: response.data.suggested_mapping.time || '',
      });
      
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to preview file');
    } finally {
      setUploading(false);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file');
      return;
    }

    // Validate required fields
    if (!mapping.date || !mapping.symbol || !mapping.price || !mapping.quantity) {
      setError('Please map all required fields: Date, Symbol, Price, and Quantity');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const mappingData = {
        ...mapping,
        date_time_combined: dateTimeCombined
      };
      formData.append('mapping', JSON.stringify(mappingData));

      const response = await axios.post(`${API}/import-with-mapping`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setResult(response.data);
      setStep(3);
      setTimeout(() => {
        onSuccess();
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to import file');
      setStep(3);
    } finally {
      setUploading(false);
    }
  };

  const handleClose = () => {
    setFile(null);
    setResult(null);
    setError(null);
    setStep(1);
    setMapping({
      date: '',
      symbol: '',
      action: '',
      price: '',
      quantity: '',
      time: '',
    });
    setDateTimeCombined(false);
    onClose();
  };

  const handleBack = () => {
    if (step === 2) {
      setStep(1);
      setFile(null);
    } else if (step === 3) {
      setStep(2);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="bg-[#18181B] border-[#27272A] text-[#FAFAFA] sm:max-w-[700px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-['JetBrains_Mono'] text-xl">
            {step === 1 && 'Import Trade Data'}
            {step === 2 && 'Map Columns'}
            {step === 3 && (result ? 'Import Complete' : 'Import Failed')}
          </DialogTitle>
          <DialogDescription className="text-[#A1A1AA] font-['Inter']">
            {step === 1 && 'Upload your CSV export file to import trades'}
            {step === 2 && 'Match your CSV columns to the required fields'}
            {step === 3 && ''}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* Step 1: File Upload */}
          {step === 1 && (
            <>
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

              {uploading && (
                <p className="text-center text-[#A1A1AA] font-['Inter']">Analyzing file...</p>
              )}
            </>
          )}

          {/* Step 2: Column Mapping */}
          {step === 2 && (
            <div className="space-y-4">
              <div className="bg-[#27272A]/30 p-4 rounded-sm">
                <h3 className="text-sm font-medium text-[#FAFAFA] font-['Inter'] mb-2">Preview</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-[#27272A]">
                        {headers.slice(0, 6).map((h, i) => (
                          <th key={i} className="text-left p-2 text-[#A1A1AA] font-['JetBrains_Mono']">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sampleRows.slice(0, 3).map((row, i) => (
                        <tr key={i} className="border-b border-[#27272A]/50">
                          {row.slice(0, 6).map((cell, j) => (
                            <td key={j} className="p-2 text-[#71717A] font-['Inter'] truncate max-w-[120px]">{cell}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="space-y-3">
                <p className="text-sm text-[#A1A1AA] font-['Inter']">
                  Map your CSV columns to the required fields. <span className="text-[#EF4444]">*</span> = Required
                </p>

                {/* Date */}
                <div>
                  <Label className="text-[#FAFAFA] font-['Inter'] text-sm mb-2 block">
                    Date <span className="text-[#EF4444]">*</span>
                  </Label>
                  <Select value={mapping.date} onValueChange={(val) => setMapping({...mapping, date: val})}>
                    <SelectTrigger className="bg-[#27272A] border-[#3F3F46] text-[#FAFAFA]">
                      <SelectValue placeholder="Select date column" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#27272A] border-[#3F3F46]">
                      {headers.map((h) => (
                        <SelectItem key={h} value={h} className="text-[#FAFAFA] hover:bg-[#3F3F46]">{h}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Symbol */}
                <div>
                  <Label className="text-[#FAFAFA] font-['Inter'] text-sm mb-2 block">
                    Symbol <span className="text-[#EF4444]">*</span>
                  </Label>
                  <Select value={mapping.symbol} onValueChange={(val) => setMapping({...mapping, symbol: val})}>
                    <SelectTrigger className="bg-[#27272A] border-[#3F3F46] text-[#FAFAFA]">
                      <SelectValue placeholder="Select symbol column" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#27272A] border-[#3F3F46]">
                      {headers.map((h) => (
                        <SelectItem key={h} value={h} className="text-[#FAFAFA] hover:bg-[#3F3F46]">{h}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Price */}
                <div>
                  <Label className="text-[#FAFAFA] font-['Inter'] text-sm mb-2 block">
                    Price <span className="text-[#EF4444]">*</span>
                  </Label>
                  <Select value={mapping.price} onValueChange={(val) => setMapping({...mapping, price: val})}>
                    <SelectTrigger className="bg-[#27272A] border-[#3F3F46] text-[#FAFAFA]">
                      <SelectValue placeholder="Select price column" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#27272A] border-[#3F3F46]">
                      {headers.map((h) => (
                        <SelectItem key={h} value={h} className="text-[#FAFAFA] hover:bg-[#3F3F46]">{h}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Quantity */}
                <div>
                  <Label className="text-[#FAFAFA] font-['Inter'] text-sm mb-2 block">
                    Quantity <span className="text-[#EF4444]">*</span>
                  </Label>
                  <Select value={mapping.quantity} onValueChange={(val) => setMapping({...mapping, quantity: val})}>
                    <SelectTrigger className="bg-[#27272A] border-[#3F3F46] text-[#FAFAFA]">
                      <SelectValue placeholder="Select quantity column" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#27272A] border-[#3F3F46]">
                      {headers.map((h) => (
                        <SelectItem key={h} value={h} className="text-[#FAFAFA] hover:bg-[#3F3F46]">{h}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Action (Optional) */}
                <div>
                  <Label className="text-[#FAFAFA] font-['Inter'] text-sm mb-2 block">
                    Action (Optional)
                  </Label>
                  <Select value={mapping.action} onValueChange={(val) => setMapping({...mapping, action: val})}>
                    <SelectTrigger className="bg-[#27272A] border-[#3F3F46] text-[#FAFAFA]">
                      <SelectValue placeholder="Select action column (Buy/Sell)" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#27272A] border-[#3F3F46]">
                      <SelectItem value="" className="text-[#71717A] hover:bg-[#3F3F46]">None</SelectItem>
                      {headers.map((h) => (
                        <SelectItem key={h} value={h} className="text-[#FAFAFA] hover:bg-[#3F3F46]">{h}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Time (Optional) */}
                <div>
                  <Label className="text-[#FAFAFA] font-['Inter'] text-sm mb-2 block">
                    Time (Optional)
                  </Label>
                  <Select value={mapping.time} onValueChange={(val) => setMapping({...mapping, time: val})}>
                    <SelectTrigger className="bg-[#27272A] border-[#3F3F46] text-[#FAFAFA]">
                      <SelectValue placeholder="Select time column" />
                    </SelectTrigger>
                    <SelectContent className="bg-[#27272A] border-[#3F3F46]">
                      <SelectItem value="" className="text-[#71717A] hover:bg-[#3F3F46]">None</SelectItem>
                      {headers.map((h) => (
                        <SelectItem key={h} value={h} className="text-[#FAFAFA] hover:bg-[#3F3F46]">{h}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Date/Time Combined Checkbox */}
                <div className="flex items-center space-x-2 pt-2">
                  <Checkbox
                    id="date-time-combined"
                    checked={dateTimeCombined}
                    onCheckedChange={setDateTimeCombined}
                    className="border-[#3F3F46]"
                  />
                  <Label
                    htmlFor="date-time-combined"
                    className="text-sm text-[#A1A1AA] font-['Inter'] cursor-pointer"
                  >
                    Date and time are in one column (e.g., "3:31:36 PM ET Dec-18-2025")
                  </Label>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Result */}
          {step === 3 && (
            <>
              {error && (
                <div className="flex items-center gap-2 p-4 bg-[#EF4444]/10 border border-[#EF4444]/30 rounded-sm">
                  <AlertCircle className="h-5 w-5 text-[#EF4444] flex-shrink-0" />
                  <p className="text-[#EF4444] text-sm font-['Inter']">{error}</p>
                </div>
              )}

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
            </>
          )}

          {/* Action Buttons */}
          <div className="flex justify-between gap-3 pt-4">
            <div>
              {step > 1 && !result && (
                <Button
                  onClick={handleBack}
                  variant="outline"
                  className="bg-transparent border-[#27272A] hover:bg-[#27272A] text-[#FAFAFA] rounded-sm"
                >
                  Back
                </Button>
              )}
            </div>
            <div className="flex gap-3">
              <Button
                onClick={handleClose}
                variant="outline"
                className="bg-transparent border-[#27272A] hover:bg-[#27272A] text-[#FAFAFA] rounded-sm"
                data-testid="cancel-button"
              >
                {result ? 'Close' : 'Cancel'}
              </Button>
              {step === 2 && (
                <Button
                  onClick={handleUpload}
                  disabled={uploading}
                  className="bg-[#FAFAFA] text-[#18181B] hover:bg-[#E4E4E7] rounded-sm font-['JetBrains_Mono']"
                  data-testid="upload-button"
                >
                  {uploading ? 'Importing...' : (
                    <>
                      Import <ArrowRight className="ml-2 h-4 w-4" />
                    </>
                  )}
                </Button>
              )}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ImportDialog;
