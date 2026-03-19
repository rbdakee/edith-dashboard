import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div
      className={cn(
        'prose prose-invert prose-sm max-w-none',
        'prose-headings:text-gray-100 prose-p:text-gray-300 prose-strong:text-gray-100',
        'prose-code:text-blue-300 prose-code:bg-gray-800 prose-code:px-1 prose-code:rounded',
        'prose-pre:bg-gray-800 prose-pre:border prose-pre:border-gray-700',
        'prose-blockquote:border-blue-500 prose-blockquote:text-gray-400',
        'prose-a:text-blue-400 prose-li:text-gray-300',
        className
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
}
