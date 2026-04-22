import React from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";

function Message({ role, content }) {
  return (
    <div className={`msg ${role}`}>
      <ReactMarkdown
        children={content}
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          p: ({ children }) => (
            <span style={{ margin: 0 }}>{children}</span> // 🔥 FIX
          )
        }}
      />
    </div>
  );
}

export default React.memo(Message);