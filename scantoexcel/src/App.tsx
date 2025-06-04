import React, { useState, useRef, type DragEvent, type ChangeEvent } from 'react';
import { Upload, FileImage, X, Check, Copy, Download } from 'lucide-react';

const DataXtract: React.FC = () => {
  const [isDragOver, setIsDragOver] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [ocrResult, setOcrResult] = useState<string | null>(null);
  const [copySuccess, setCopySuccess] = useState<boolean>(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>): void => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        setSelectedFile(file);
      }
    }
  };

  const handleFileSelect = (e: ChangeEvent<HTMLInputElement>): void => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleBrowseClick = (): void => {
    fileInputRef.current?.click();
  };

  const handleRemoveFile = (): void => {
    setSelectedFile(null);
    setOcrResult(null);
    setCopySuccess(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleExtractData = async (): Promise<void> => {
    if (!selectedFile) return;
    
    setIsUploading(true);
    
    try {
      const formData = new FormData();
      formData.append("image", selectedFile);
      
      const response = await fetch(`https://obscure-space-doodle-5p6q7x5xgw9cpxqr-5000.app.github.dev/ocr?cb=${Date.now()}`, {
        method: "POST",
        body: formData,
      });
      
      const data = await response.json();
      console.log("OCR result:", data);
      
      // Assuming the API returns text in data.text or data.result
      const extractedText = data.text || data.result || data.extracted_text || JSON.stringify(data, null, 2);
      setOcrResult(extractedText);
      
    } catch (error) {
      console.error("Error extracting data:", error);
      setOcrResult("Error occurred while extracting data. Please try again.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleCopyText = async (): Promise<void> => {
    if (!ocrResult) return;
    
    try {
      await navigator.clipboard.writeText(ocrResult);
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (error) {
      console.error("Failed to copy text:", error);
    }
  };

  const handleDownloadText = (): void => {
    if (!ocrResult) return;
    
    const blob = new Blob([ocrResult], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `extracted-text-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const formatFileSize = (bytes: number): string => {
    return (bytes / 1024 / 1024).toFixed(2);
  };

  const getDragOverClasses = (): string => {
    if (isDragOver) {
      return 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/20';
    }
    if (selectedFile) {
      return 'border-green-500 bg-green-50/50 dark:bg-green-900/20';
    }
    return 'border-slate-300 dark:border-slate-600 bg-white/50 dark:bg-slate-800/50 hover:border-slate-400 dark:hover:border-slate-500';
  };

  const getUploadIconClasses = (): string => {
    return `w-16 h-16 mx-auto transition-colors ${
      isDragOver ? 'text-blue-500' : 'text-slate-400 dark:text-slate-500'
    }`;
  };

  interface FeatureCardProps {
    icon: React.ReactNode;
    title: string;
    description: string;
    bgColor: string;
  }

  const FeatureCard: React.FC<FeatureCardProps> = ({ icon, title, description, bgColor }) => (
    <div className="text-center p-6 rounded-xl bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border border-slate-200 dark:border-slate-700">
      <div className={`w-12 h-12 ${bgColor} rounded-lg flex items-center justify-center mx-auto mb-4`}>
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200 mb-2">
        {title}
      </h3>
      <p className="text-slate-600 dark:text-slate-400 text-sm">
        {description}
      </p>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <div className="w-full border-b bg-white/50 dark:bg-slate-900/50 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-blue-600 rotate-45"></div>
            <h1 className="text-xl font-bold text-slate-800 dark:text-slate-200">
              DataXtract
            </h1>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 sm:py-12 lg:py-16">
        <div className="max-w-4xl mx-auto">
          {/* Title Section */}
          <div className="text-center mb-8 sm:mb-12">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-slate-800 dark:text-slate-200 mb-4">
              Extract data from images
            </h2>
            <p className="text-lg sm:text-xl text-slate-600 dark:text-slate-400">
              Upload an image to extract data
            </p>
          </div>

          {/* Upload Area */}
          <div className="w-full max-w-2xl mx-auto">
            <div
              className={`relative border-2 border-dashed rounded-2xl p-8 sm:p-12 lg:p-16 transition-all duration-300 ${getDragOverClasses()} backdrop-blur-sm`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
              />

              {!selectedFile ? (
                <div className="text-center">
                  <div className="mb-6">
                    <Upload className={getUploadIconClasses()} />
                  </div>
                  
                  <h3 className="text-xl sm:text-2xl font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    Drag and drop an image here, or
                  </h3>
                  
                  <p className="text-slate-500 dark:text-slate-400 mb-6">
                    Browse files
                  </p>
                  
                  <button
                    onClick={handleBrowseClick}
                    type="button"
                    className="inline-flex items-center px-6 py-3 bg-slate-800 dark:bg-slate-700 text-white rounded-lg hover:bg-slate-700 dark:hover:bg-slate-600 transition-colors font-medium"
                  >
                    Select file
                  </button>
                </div>
              ) : (
                <div className="text-center">
                  <div className="mb-6">
                    <div className="relative inline-block">
                      <FileImage className="w-16 h-16 mx-auto text-green-500" />
                      <div className="absolute -top-2 -right-2 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                        <Check className="w-4 h-4 text-white" />
                      </div>
                    </div>
                  </div>
                  
                  <h3 className="text-xl sm:text-2xl font-semibold text-slate-700 dark:text-slate-300 mb-2">
                    File selected
                  </h3>
                  
                  <p className="text-slate-600 dark:text-slate-400 mb-4 break-all">
                    {selectedFile.name}
                  </p>
                  
                  <p className="text-sm text-slate-500 dark:text-slate-400 mb-6">
                    {formatFileSize(selectedFile.size)} MB
                  </p>
                  
                  <div className="flex flex-col sm:flex-row gap-3 justify-center items-center">
                    <button
                      onClick={handleExtractData}
                      disabled={isUploading}
                      type="button"
                      className="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white rounded-lg transition-colors font-medium min-w-[140px]"
                    >
                      {isUploading ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2"></div>
                          Processing...
                        </>
                      ) : (
                        'Extract Data'
                      )}
                    </button>
                    
                    <button
                      onClick={handleRemoveFile}
                      type="button"
                      className="inline-flex items-center px-4 py-3 text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
                    >
                      <X className="w-4 h-4 mr-1" />
                      Remove
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Supported Formats */}
            <div className="mt-6 text-center">
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Supports: JPG, PNG, GIF, WEBP, and other image formats
              </p>
            </div>
          </div>

          {/* OCR Results Section */}
          {ocrResult && (
            <div className="mt-12 max-w-4xl mx-auto">
              <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur-sm rounded-2xl border border-slate-200 dark:border-slate-700 overflow-hidden">
                {/* Results Header */}
                <div className="px-6 py-4 border-b border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center">
                        <Check className="w-4 h-4 text-green-600 dark:text-green-400" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-200">
                          Extracted Text
                        </h3>
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                          Text extracted from your image
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={handleCopyText}
                        className="inline-flex items-center px-3 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
                      >
                        <Copy className="w-4 h-4 mr-1" />
                        {copySuccess ? 'Copied!' : 'Copy'}
                      </button>
                      <button
                        onClick={handleDownloadText}
                        className="inline-flex items-center px-3 py-2 text-sm bg-slate-600 hover:bg-slate-700 text-white rounded-lg transition-colors font-medium"
                      >
                        <Download className="w-4 h-4 mr-1" />
                        Download
                      </button>
                    </div>
                  </div>
                </div>
                
                {/* Results Content */}
                <div className="p-6">
                  <div className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-4 border border-slate-200 dark:border-slate-600">
                    <pre className="whitespace-pre-wrap text-sm text-slate-700 dark:text-slate-300 font-mono leading-relaxed max-h-96 overflow-y-auto">
                      {ocrResult}
                    </pre>
                  </div>
                  
                  {/* Text Statistics */}
                  <div className="mt-4 flex flex-wrap gap-4 text-sm text-slate-600 dark:text-slate-400">
                    <span>Characters: {ocrResult.length}</span>
                    <span>Words: {ocrResult.trim().split(/\s+/).length}</span>
                    <span>Lines: {ocrResult.split('\n').length}</span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Features Section */}
          {!ocrResult && (
            <div className="mt-16 sm:mt-20">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8">
                <FeatureCard
                  icon={<FileImage className="w-6 h-6 text-blue-600 dark:text-blue-400" />}
                  title="Smart Recognition"
                  description="Advanced AI algorithms to accurately extract text and data from images"
                  bgColor="bg-blue-100 dark:bg-blue-900/30"
                />

                <FeatureCard
                  icon={<Upload className="w-6 h-6 text-green-600 dark:text-green-400" />}
                  title="Easy Upload"
                  description="Drag and drop or browse to upload your images quickly and securely"
                  bgColor="bg-green-100 dark:bg-green-900/30"
                />

                <FeatureCard
                  icon={<Check className="w-6 h-6 text-purple-600 dark:text-purple-400" />}
                  title="Instant Results"
                  description="Get extracted data in seconds with high accuracy and formatting"
                  bgColor="bg-purple-100 dark:bg-purple-900/30"
                />
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DataXtract;