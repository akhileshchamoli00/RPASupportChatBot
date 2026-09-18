import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Bot, UserRound, FileText, Cpu, ExternalLink, X, Copy, Check, Maximize2, Minimize2 } from 'lucide-react';

const MessageBubble = ({ message, onSelectAutomation }) => {
  const isUser = message.role === 'user';
  const isSelectPrompt = message.content && message.content.startsWith('[AUTOMATION_SELECT] ');
  const isSelectedPrompt = message.content && message.content.startsWith('[AUTOMATION_SELECTED] ');
  const sources = message.sources || [];

  const [selectedSource, setSelectedSource] = useState(null);
  const [copiedSnippet, setCopiedSnippet] = useState(false);
  const [isMaximized, setIsMaximized] = useState(false);

  const handleCopySnippet = (text) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedSnippet(true);
    setTimeout(() => setCopiedSnippet(false), 2000);
  };

  const totalTokens = message.total_tokens ?? message.token_usage?.total_tokens ?? 0;
  const promptTokens = message.prompt_tokens ?? message.token_usage?.prompt_tokens ?? 0;
  const completionTokens = message.completion_tokens ?? message.token_usage?.completion_tokens ?? 0;
  const rawModel = message.model_used ?? message.token_usage?.model ?? '';

  const formatModelLabel = (model) => {
    if (!model || model === 'none') return 'AI Model';
    if (model.includes('qwen') || model.includes('compound') || model.includes('groq')) {
      const short = model.replace('qwen/', '').replace('groq/', '');
      return `Groq • ${short}`;
    }
    if (model.includes('llama') || model.includes('ollama')) {
      return `Local AI • ${model}`;
    }
    if (model.includes('gpt')) {
      return `ChatGPT • ${model}`;
    }
    return model;
  };

  // Helper to parse bold (**) and inline code (`)
  const parseInlineStyles = (text) => {
    if (!text) return '';
    
    // Match **bold** and `code`
    const parts = text.split(/(\*\*.*?\*\*|`[^`]+`)/g);
    
    return parts.map((part, index) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return <strong key={index} className="font-bold text-slate-900 dark:text-white">{part.slice(2, -2)}</strong>;
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={index} className="px-1.5 py-0.5 rounded bg-slate-200/80 dark:bg-black/40 border border-slate-300/80 dark:border-white/10 font-mono text-xs text-dayforce-blue dark:text-dayforce-cyan">
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  if (isSelectedPrompt) {
    const selectedText = message.content.replace('[AUTOMATION_SELECTED]', '').trim();
    return (
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="flex gap-4 max-w-3xl w-full py-2 group select-none text-[10px] text-slate-500 dark:text-gray-500 font-semibold uppercase tracking-wider pl-12"
      >
        <span>🎯 Target Workspace: <span className="text-dayforce-blue dark:text-dayforce-cyan font-bold">{selectedText}</span></span>
      </motion.div>
    );
  }

  if (isSelectPrompt) {
    const promptText = message.content.replace('[AUTOMATION_SELECT]', '').trim();
    return (
      <motion.div 
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex gap-4 max-w-3xl w-full py-2 group select-none"
      >
        <div className="w-8 h-8 rounded-full bg-dayforce-blue/15 dark:bg-dayforce-cyan/15 border border-dayforce-blue/30 dark:border-dayforce-cyan/30 flex items-center justify-center flex-shrink-0 mt-1 shadow-sm text-dayforce-blue dark:text-dayforce-cyan animate-pulse">
          <Bot className="w-4 h-4" />
        </div>
        <div className="bg-transparent text-slate-900 dark:text-gray-100 px-1 py-1 flex-1">
          <p className="mb-4 text-slate-800 dark:text-gray-200 leading-relaxed font-sans text-[14px] font-semibold">
            {promptText}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-md">
            {[
              { id: 'ROE', name: 'Record of Employment (ROE)', desc: 'Isolate queries to ROE' },
              { id: 'Overpayment', name: 'Overpayment Support', desc: 'Isolate queries to Overpayment' },
              { id: 'SyncPay', name: 'SyncPay Support', desc: 'Isolate queries to SyncPay' },
              { id: 'Monthly Hourly Update', name: 'Monthly Hourly Update (MHU)', desc: 'Revenue allocation & hourly updates' },
              { id: 'Invoice Supplimental Details', name: 'Invoice Supplemental Details (ISD)', desc: 'Invoicing & billing reports' },
              { id: 'Infrastructure', name: 'Infrastructure Support', desc: 'VMs, bot machines & servers' },
              { id: 'General', name: 'General Support', desc: 'Query all repository documents' }
            ].map((opt) => (
              <button
                key={opt.id}
                onClick={() => onSelectAutomation && onSelectAutomation(opt.id)}
                className="text-left p-3.5 rounded-2xl bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 hover:border-dayforce-blue/50 dark:hover:border-dayforce-cyan/40 hover:bg-blue-50/50 dark:hover:bg-dayforce-blue/5 text-xs text-slate-700 dark:text-gray-300 shadow-sm dark:shadow-none transition-all cursor-pointer hover:-translate-y-0.5 flex flex-col justify-between group/btn"
              >
                <span className="font-semibold text-slate-900 dark:text-white mb-0.5 group-hover/btn:text-dayforce-blue dark:group-hover/btn:text-dayforce-cyan transition-colors">{opt.name}</span>
                <span className="text-[10px] text-slate-500 dark:text-gray-500 mt-0.5">{opt.desc}</span>
              </button>
            ))}
          </div>
        </div>
      </motion.div>
    );
  }

  // Helper to parse line by line (paragraphs, lists, and code blocks)
  const renderMarkdown = (text) => {
    if (!text) return null;

    const lines = text.split('\n');
    const elements = [];
    let inCodeBlock = false;
    let codeBlockContent = [];
    let codeBlockLang = '';

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];

      // Code block toggles
      if (line.trim().startsWith('```')) {
        if (inCodeBlock) {
          // End code block
          elements.push(
            <pre 
              key={`code-${i}`} 
              className="my-3 p-4 rounded-xl bg-slate-900 text-slate-100 dark:bg-black/50 border border-slate-700/50 dark:border-white/10 overflow-x-auto font-mono text-xs leading-normal"
            >
              <code>{codeBlockContent.join('\n')}</code>
            </pre>
          );
          codeBlockContent = [];
          inCodeBlock = false;
        } else {
          // Start code block
          inCodeBlock = true;
          codeBlockLang = line.trim().slice(3);
        }
        continue;
      }

      if (inCodeBlock) {
        codeBlockContent.push(line);
        continue;
      }

      // List items (supports tab and space indentations, bullet markers *, -, +)
      const listMatch = line.match(/^(\s*)([*+-])\s+(.*)/);
      if (listMatch) {
        const indent = listMatch[1];
        const content = listMatch[3];
        const paddingLeft = indent.length * 16 + 12;
        elements.push(
          <div 
            key={i} 
            style={{ paddingLeft: `${paddingLeft}px` }} 
            className="flex items-start gap-2 my-1.5 text-slate-800 dark:text-gray-200"
          >
            <span className="text-dayforce-blue dark:text-dayforce-cyan mt-2 flex-shrink-0 w-1.5 h-1.5 rounded-full bg-dayforce-blue dark:bg-dayforce-cyan/80 shadow-[0_0_5px_rgba(0,98,255,0.4)] dark:shadow-[0_0_5px_rgba(0,210,255,0.4)]" />
            <span className="flex-1 font-sans">{parseInlineStyles(content)}</span>
          </div>
        );
        continue;
      }

      // Normal paragraph line
      if (line.trim() === '') {
        elements.push(<div key={i} className="h-2" />);
        continue;
      }

      elements.push(
        <p key={i} className="mb-2 text-slate-800 dark:text-gray-200 leading-relaxed font-sans last:mb-0">
          {parseInlineStyles(line)}
        </p>
      );
    }

    return elements;
  };

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className={`w-full flex ${isUser ? 'justify-end' : 'justify-start'} py-1`}
      >
        <div className={`flex gap-4 max-w-3xl w-full ${isUser ? 'flex-row-reverse justify-start' : 'flex-row'}`}>
          {/* Avatar */}
          <div 
            className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-1 shadow-sm ${
              isUser 
                ? 'bg-dayforce-blue/15 dark:bg-dayforce-blue/20 border border-dayforce-blue/30 text-dayforce-blue dark:text-white' 
                : 'bg-dayforce-blue/10 dark:bg-dayforce-cyan/20 border border-dayforce-blue/20 dark:border-dayforce-cyan/30 text-dayforce-blue dark:text-dayforce-cyan shadow-[0_0_10px_rgba(0,98,255,0.15)] dark:shadow-[0_0_10px_rgba(0,210,255,0.2)]'
            }`}
          >
            {isUser ? (
              <UserRound className="w-4 h-4 text-dayforce-blue dark:text-white/90" />
            ) : (
              <Bot className="w-4 h-4 text-dayforce-blue dark:text-dayforce-cyan" />
            )}
          </div>

          {/* Text Container */}
          <div 
            className={`leading-relaxed text-[15px] font-sans ${
              isUser 
                ? 'bg-blue-600/10 dark:bg-white/5 border border-blue-200/80 dark:border-white/10 rounded-2xl px-4 py-2.5 text-slate-900 dark:text-gray-100 shadow-xs dark:shadow-[0_2px_8px_rgba(0,0,0,0.15)] max-w-[85%] sm:max-w-[75%]' 
                : 'text-slate-800 dark:text-gray-100 w-full px-1 py-1.5'
            }`}
          >
            <div className="markdown-body">
              {renderMarkdown(message.content)}
            </div>

            {!isUser && sources && sources.length > 0 && (
              <div className="mt-3 pt-2.5 border-t border-slate-200 dark:border-white/10 flex flex-wrap items-center gap-1.5">
                <span className="text-[10px] font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-1 mr-1">
                  <FileText className="w-3 h-3 text-dayforce-blue dark:text-dayforce-cyan" /> Sources:
                </span>
                {sources.map((src, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setSelectedSource(src);
                      setCopiedSnippet(false);
                    }}
                    title="Click to inspect citation snippet & metadata"
                    className="text-[10px] bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 hover:border-dayforce-blue/60 dark:hover:border-dayforce-cyan/50 hover:bg-dayforce-blue/10 dark:hover:bg-dayforce-cyan/10 px-2 py-0.5 rounded-md text-slate-700 dark:text-gray-300 flex items-center gap-1 transition-all cursor-pointer shadow-xs active:scale-95 group/src"
                  >
                    <span className="font-medium text-slate-900 dark:text-white group-hover/src:text-dayforce-blue dark:group-hover/src:text-dayforce-cyan transition-colors">{src.source}</span>
                    {src.page ? <span className="text-dayforce-blue dark:text-dayforce-cyan font-medium">(p. {src.page})</span> : null}
                    {src.sheet ? <span className="text-dayforce-blue dark:text-dayforce-cyan font-medium">({src.sheet})</span> : null}
                    <ExternalLink className="w-2.5 h-2.5 opacity-40 group-hover/src:opacity-100 text-dayforce-blue dark:text-dayforce-cyan ml-0.5 transition-opacity" />
                  </button>
                ))}
              </div>
            )}

            {!isUser && totalTokens > 0 && (
              <div className="mt-2.5 flex items-center gap-2 flex-wrap text-[10px]">
                <div 
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100/90 dark:bg-white/5 border border-slate-200/80 dark:border-white/10 text-slate-600 dark:text-gray-300 shadow-xs cursor-default transition-colors hover:border-dayforce-blue/40 dark:hover:border-dayforce-cyan/40"
                  title={`Input (Prompt): ${promptTokens.toLocaleString()} tokens | Output (Completion): ${completionTokens.toLocaleString()} tokens | Model: ${rawModel}`}
                >
                  <Cpu className="w-3 h-3 text-dayforce-blue dark:text-dayforce-cyan flex-shrink-0" />
                  <span className="font-semibold text-slate-800 dark:text-gray-200">
                    {formatModelLabel(rawModel)}
                  </span>
                  <span className="text-slate-300 dark:text-gray-600">•</span>
                  <span className="font-bold text-slate-900 dark:text-white">
                    {totalTokens.toLocaleString()} <span className="font-normal text-slate-500 dark:text-gray-400">tokens</span>
                  </span>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-200/70 dark:bg-black/40 text-slate-600 dark:text-gray-400 border border-slate-300/60 dark:border-white/5 ml-0.5">
                    ↓ {promptTokens.toLocaleString()} / ↑ {completionTokens.toLocaleString()}
                  </span>
                </div>
              </div>
            )}

            <div className={`text-[9px] mt-2 opacity-60 font-semibold ${isUser ? 'text-right text-slate-400 dark:text-gray-400' : 'text-left text-dayforce-blue dark:text-dayforce-cyan'}`}>
              {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Interactive Citation Inspection Modal */}
      {selectedSource && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 md:p-6 bg-black/70 backdrop-blur-xs animate-in fade-in duration-200"
          onClick={() => {
            setSelectedSource(null);
            setIsMaximized(false);
          }}
        >
          <div 
            className={`bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/15 shadow-2xl overflow-hidden flex flex-col transition-all duration-300 animate-in zoom-in-95 ${
              isMaximized
                ? 'w-full h-full max-w-none max-h-none rounded-none'
                : 'w-[95vw] max-w-4xl lg:max-w-5xl h-[88vh] max-h-[92vh] rounded-2xl'
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-white/10 bg-slate-50/80 dark:bg-white/5 flex-shrink-0">
              <div className="flex items-center gap-3 overflow-hidden">
                <div className="w-9 h-9 rounded-xl bg-dayforce-blue/10 dark:bg-dayforce-cyan/10 border border-dayforce-blue/20 dark:border-dayforce-cyan/20 flex items-center justify-center flex-shrink-0 text-dayforce-blue dark:text-dayforce-cyan shadow-xs">
                  <FileText className="w-4 h-4" />
                </div>
                <div className="min-w-0">
                  <h3 className="text-base font-bold text-slate-900 dark:text-white truncate">
                    {selectedSource.source}
                  </h3>
                  <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-gray-400">
                    <span className="font-semibold text-dayforce-blue dark:text-dayforce-cyan">Source Excerpt Inspector</span>
                    {selectedSource.automation && (
                      <>
                        <span>•</span>
                        <span className="font-medium">
                          {selectedSource.automation} Workspace
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setIsMaximized(!isMaximized)}
                  title={isMaximized ? "Restore window size" : "Maximize window"}
                  className="w-8 h-8 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-white/10 flex items-center justify-center transition-colors cursor-pointer"
                >
                  {isMaximized ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setSelectedSource(null);
                    setIsMaximized(false);
                  }}
                  title="Close inspector"
                  className="w-8 h-8 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-white hover:bg-slate-200/60 dark:hover:bg-white/10 flex items-center justify-center transition-colors cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Metadata Tags Bar */}
            <div className="px-6 py-3 bg-slate-100/70 dark:bg-black/25 border-b border-slate-200 dark:border-white/5 flex flex-wrap items-center gap-2.5 text-xs flex-shrink-0">
              {selectedSource.file_type && (
                <span className="px-2.5 py-1 rounded-md bg-white dark:bg-white/10 border border-slate-200/80 dark:border-white/10 text-slate-700 dark:text-gray-300 font-medium text-xs shadow-xs">
                  Format: <span className="font-bold uppercase text-slate-900 dark:text-white">{selectedSource.file_type}</span>
                </span>
              )}
              {selectedSource.page ? (
                <span className="px-2.5 py-1 rounded-md bg-white dark:bg-white/10 border border-slate-200/80 dark:border-white/10 text-slate-700 dark:text-gray-300 font-medium text-xs shadow-xs">
                  Page: <span className="font-bold text-dayforce-blue dark:text-dayforce-cyan">{selectedSource.page}</span>
                </span>
              ) : null}
              {selectedSource.sheet ? (
                <span className="px-2.5 py-1 rounded-md bg-white dark:bg-white/10 border border-slate-200/80 dark:border-white/10 text-slate-700 dark:text-gray-300 font-medium text-xs shadow-xs">
                  Sheet: <span className="font-bold text-dayforce-blue dark:text-dayforce-cyan">{selectedSource.sheet}</span>
                </span>
              ) : null}
              {selectedSource.row_start ? (
                <span className="px-2.5 py-1 rounded-md bg-white dark:bg-white/10 border border-slate-200/80 dark:border-white/10 text-slate-700 dark:text-gray-300 font-medium text-xs shadow-xs">
                  Rows: <span className="font-bold text-slate-900 dark:text-white">{selectedSource.row_start}-{selectedSource.row_end}</span>
                </span>
              ) : null}
              {selectedSource.section && selectedSource.section !== 'General' && (
                <span className="px-2.5 py-1 rounded-md bg-white dark:bg-white/10 border border-slate-200/80 dark:border-white/10 text-slate-700 dark:text-gray-300 font-medium text-xs truncate max-w-md shadow-xs">
                  Section: <span className="font-bold text-slate-900 dark:text-white">{selectedSource.section}</span>
                </span>
              )}
            </div>

            {/* Chunk Snippet Body */}
            <div className="p-6 overflow-y-auto flex-1 flex flex-col">
              <div className="flex items-center justify-between mb-3 flex-shrink-0">
                <span className="text-xs font-bold text-slate-500 dark:text-gray-400 uppercase tracking-wider flex items-center gap-1.5">
                  <FileText className="w-3.5 h-3.5 text-dayforce-blue dark:text-dayforce-cyan" />
                  Raw Ground Truth Excerpt (Retrieved Document Chunk)
                </span>
                {selectedSource.snippet && (
                  <button
                    type="button"
                    onClick={() => handleCopySnippet(selectedSource.snippet)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-100 dark:bg-white/10 hover:bg-slate-200 dark:hover:bg-white/20 text-slate-800 dark:text-gray-200 transition-colors cursor-pointer border border-slate-200/80 dark:border-white/10 shadow-xs active:scale-95"
                  >
                    {copiedSnippet ? (
                      <>
                        <Check className="w-3.5 h-3.5 text-emerald-500" />
                        <span className="text-emerald-500 font-bold">Copied to Clipboard</span>
                      </>
                    ) : (
                      <>
                        <Copy className="w-3.5 h-3.5 text-slate-500 dark:text-gray-400" />
                        <span>Copy Full Excerpt</span>
                      </>
                    )}
                  </button>
                )}
              </div>
              <div className="p-5 rounded-xl bg-slate-900 text-slate-100 dark:bg-black/60 border border-slate-700/60 dark:border-white/10 font-mono text-xs sm:text-[13px] leading-relaxed whitespace-pre-wrap overflow-x-auto flex-1 selection:bg-dayforce-blue selection:text-white shadow-inner">
                {selectedSource.snippet || 'No raw snippet excerpt is available for this citation.'}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="px-6 py-3.5 border-t border-slate-200 dark:border-white/10 bg-slate-50/70 dark:bg-white/5 flex items-center justify-between text-xs text-slate-500 dark:text-gray-400 flex-shrink-0">
              <span>Selected and verified by FlashRank Neural Re-Ranker.</span>
              <button
                type="button"
                onClick={() => {
                  setSelectedSource(null);
                  setIsMaximized(false);
                }}
                className="px-4 py-2 rounded-xl bg-slate-200 dark:bg-white/10 hover:bg-slate-300 dark:hover:bg-white/20 font-semibold text-slate-800 dark:text-white transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default MessageBubble;
