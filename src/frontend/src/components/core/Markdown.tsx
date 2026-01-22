import type {
  AnchorHTMLAttributes,
  ClassAttributes,
  HTMLAttributes,
  PropsWithChildren,
} from "react";
import type { ExtraProps } from "react-markdown";

import { Text } from "@fluentui/react-components";
import { CopyRegular } from "@fluentui/react-icons";
import copy from "copy-to-clipboard";
import { Fragment, isValidElement, memo, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import SyntaxHighlighter from "react-syntax-highlighter";
import { docco } from "react-syntax-highlighter/dist/esm/styles/hljs";
import RehypeKatex from "rehype-katex";
import RehypeRaw from "rehype-raw";
// TODO: Re-enable when data URI support is fixed
// import rehypeSanitize, { defaultSchema } from "rehype-sanitize";
import RemarkBreaks from "remark-breaks";
import RemarkGfm from "remark-gfm";
import RemarkMath from "remark-math";
import remarkParse from "remark-parse";
import supersub from "remark-supersub";

import { Button } from "@fluentui/react-components";

import { ThinkBlock } from "./ThinkBlock";

import styles from "./Markdown.module.css";

interface ICitation extends React.JSX.Element {
  props: {
    "data-replace"?: string;
    [key: string]: unknown;
  };
}

interface IMarkdownProps {
  citations?: ICitation[] | undefined;
  content: string;
  className?: string;
  customDisallowedElements?: string[];
}

interface IRehypeNode {
  type: string;
  tagName: string;
  properties?: { ref?: unknown; [key: string]: unknown };
  children?: IRehypeNode[];
  value?: string;
}

// Custom Image component to handle base64 data URIs from image generation
function Image({
  node,
  src,
  alt,
}: ClassAttributes<HTMLImageElement> &
  React.ImgHTMLAttributes<HTMLImageElement> &
  ExtraProps) {
  // Props from react-markdown come directly as src/alt, not from node.properties
  // when using the components prop
  const imageSrc = src ?? node?.properties?.src?.toString() ?? "";
  const imageAlt = alt ?? node?.properties?.alt?.toString() ?? "Generated image";
  
  if (!imageSrc) {
    return <span>[Image: {imageAlt}]</span>;
  }
  
  return (
    <img
      src={imageSrc}
      alt={imageAlt}
      className={styles.generatedImage}
      loading="lazy"
    />
  );
}

function Hyperlink({
  node,
  children,
  ...linkProps
}: ClassAttributes<HTMLAnchorElement> &
  AnchorHTMLAttributes<HTMLAnchorElement> &
  ExtraProps) {
  return (
    <a
      href={node?.properties.href?.toString() ?? ""}
      target="_blank"
      rel="noopener noreferrer"
      className={styles.link}
      {...linkProps}
    >
      {children}
    </a>
  );
}

interface ICodeBlockProps
  extends ClassAttributes<HTMLElement>,
    HTMLAttributes<HTMLElement>,
    ExtraProps {
  inline?: boolean;
}

// Preprocesses LaTeX notation to standard math notation for the markdown parser
const preprocessLaTeX = (content: string): string => {
  if (typeof content !== "string") {
    return content;
  }

  // Skip LaTeX preprocessing if content contains base64 data URIs
  // Base64 can contain characters that match LaTeX patterns
  if (content.includes("data:image/")) {
    return content;
  }

  // Convert \[ ... \] to $$ ... $$
  let result = content.replaceAll(
    /\\\[(.*?)\\\]/g,
    (_: string, equation: string) => `$$${equation}$$`
  );

  // Convert \( ... \) to $ ... $
  result = result.replaceAll(
    /\\\((.*?)\\\)/g,
    (_: string, equation: string) => `$${equation}$$`
  );

  // Handle $ notation
  result = result.replaceAll(
    /(^|[^\\])\$(.+?)\$/g,
    (_: string, prefix: string, equation: string) => `${prefix}$${equation}$`
  );

  return result;
};

// Preprocesses <think> tags to convert them to <details> with special attributes
const preprocessThinkTag = (content: string): string => {
  const thinkTagRegex = /<think>\n([\s\S]*?)\n<\/think>/g;

  // Replace <think> tags with <details> only if there's content inside
  return content.replaceAll(
    thinkTagRegex,
    (_match: string, innerContent: string) => {
      // If the inner content is empty or only whitespace, return empty string
      if (!innerContent.trim()) {
        return "";
      }
      // Otherwise, replace with details tag
      return `<details data-think=true>\n${innerContent}\n[ENDTHINKFLAG]</details>`;
    }
  );
};

// Checks if code content looks like code interpreter output
const isCodeInterpreterOutput = (code: string): boolean => {
  const interpreterPatterns = [
    /^import\s+\w+/m,           // import something
    /^from\s+\w+\s+import/m,    // from something import
    /\/mnt\/data\//,            // sandbox file path
    /^plt\./m,                  // matplotlib
    /^img\./m,                  // PIL image operations
    /^df\./m,                   // pandas dataframe
    /^np\./m,                   // numpy
    /Image\.open\(/,            // PIL Image.open
  ];
  return interpreterPatterns.some((pattern) => pattern.test(code));
};

const CodeBlock = memo<ICodeBlockProps>(
  ({ inline, className, children, ...props }) => {
    const match = /language-(\w+)/.exec(className ?? "");

    if (inline || !match) {
      return (
        <code {...props} className={styles.inlineCode}>
          {children}
        </code>
      );
    }

    const language = match[1];
    const content = String(children)
      .replace(/\n$/, "")
      .replaceAll("&nbsp;", "");

    const isInterpreterCode = isCodeInterpreterOutput(content);

    const codeBlockElement = (
      <div className={styles.codeBlock}>
        <div className={styles.codeHeader}>
          <Text weight="semibold">{language}</Text>
          <div className={styles.alignRight}>
            <Button
              appearance="subtle"
              icon={<CopyRegular />}
              onClick={() => {
                copy(content);
              }}
            >
              Copy
            </Button>
          </div>
        </div>
        <SyntaxHighlighter
          PreTag="div"
          customStyle={{
            margin: 0,
            borderBottomLeftRadius: "6px",
            borderBottomRightRadius: "6px",
          }}
          language={language}
          showLineNumbers={true}
          style={docco}
        >
          {content}
        </SyntaxHighlighter>
      </div>
    );

    // Wrap code interpreter output in a collapsible section
    if (isInterpreterCode) {
      return (
        <details className={styles.codeInterpreterDetails}>
          <summary className={styles.codeInterpreterSummary}>
            <span className={styles.codeInterpreterIcon}>🐍</span>
            <span>View code interpreter steps</span>
          </summary>
          {codeBlockElement}
        </details>
      );
    }

    return codeBlockElement;
  }
);

CodeBlock.displayName = "CodeBlock";

function Paragraph({
  children,
  className,
}: PropsWithChildren<{
  className?: string;
}>) {
  return <span className={className}>{children} </span>;
}

// Extract base64 images from content and return segments
// This bypasses react-markdown for images since it strips data URIs
const extractImagesFromContent = (content: string): Array<{
  type: "text" | "image";
  content: string;
  alt?: string;
}> => {
  const segments: Array<{ type: "text" | "image"; content: string; alt?: string }> = [];
  
  // Match both HTML img tags and markdown image syntax with data URIs
  const imgRegex = /<img[^>]*src="(data:image\/[^"]+)"[^>]*alt="([^"]*)"[^>]*\/?>/gi;
  const mdImgRegex = /!\[([^\]]*)\]\((data:image\/[^)]+)\)/gi;
  
  let lastIndex = 0;
  let match;
  
  // Combine all matches and sort by index
  const allMatches: Array<{ index: number; length: number; src: string; alt: string }> = [];
  
  // Find HTML img tags
  const tempContent1 = content;
  while ((match = imgRegex.exec(tempContent1)) !== null) {
    allMatches.push({
      index: match.index,
      length: match[0].length,
      src: match[1],
      alt: match[2] || "Generated Image",
    });
  }
  
  // Find markdown image syntax
  const tempContent2 = content;
  while ((match = mdImgRegex.exec(tempContent2)) !== null) {
    allMatches.push({
      index: match.index,
      length: match[0].length,
      src: match[2],
      alt: match[1] || "Generated Image",
    });
  }
  
  // Sort by index
  allMatches.sort((a, b) => a.index - b.index);
  
  // Build segments
  for (const m of allMatches) {
    if (m.index > lastIndex) {
      segments.push({
        type: "text",
        content: content.slice(lastIndex, m.index),
      });
    }
    segments.push({
      type: "image",
      content: m.src,
      alt: m.alt,
    });
    lastIndex = m.index + m.length;
  }
  
  // Add remaining text
  if (lastIndex < content.length) {
    segments.push({
      type: "text",
      content: content.slice(lastIndex),
    });
  }
  
  // If no images found, return original content as single text segment
  if (segments.length === 0) {
    segments.push({ type: "text", content });
  }
  
  return segments;
};

export function Markdown({
  citations,
  content,
  className,
  customDisallowedElements,
}: IMarkdownProps): React.ReactElement {
  // First, extract any base64 images from the content
  // These need to be rendered directly since react-markdown strips data URIs
  const imageSegments = useMemo(() => extractImagesFromContent(content), [content]);
  
  const segments = useMemo(() => {
    if (!citations || citations.length === 0) {
      return [
        {
          type: "text" as const,
          content: preprocessThinkTag(preprocessLaTeX(content)),
        },
      ];
    }

    const parts: {
      type: "text" | "citation";
      content: string | React.JSX.Element;
    }[] = [];
    let lastIndex = 0;

    for (const citation of citations) {
      const replaceText = String(citation.props["data-replace"] ?? "");
      const index = content.indexOf(replaceText, lastIndex);

      if (index !== -1) {
        if (index > lastIndex) {
          const textContent = content.slice(lastIndex, index);
          parts.push({
            type: "text",
            content: preprocessThinkTag(preprocessLaTeX(textContent)),
          });
        }

        parts.push({
          type: "citation",
          content: citation,
        });

        lastIndex = index + replaceText.length;
      }
    }

    if (lastIndex < content.length) {
      const textContent = content.slice(lastIndex);
      parts.push({
        type: "text",
        content: preprocessThinkTag(preprocessLaTeX(textContent)),
      });
    }

    return parts;
  }, [content, citations]);

  // Check if content contains base64 images - if so, use special rendering
  const hasBase64Images = content.includes("data:image/");

  // If we have base64 images, render using extracted segments
  if (hasBase64Images) {
    return (
      <div className={`${styles.markdown} ${className ?? ""}`}>
        {imageSegments.map((segment, idx) => (
          <Fragment key={idx}>
            {segment.type === "image" ? (
              <img
                src={segment.content}
                alt={segment.alt ?? "Generated Image"}
                className={styles.generatedImage}
                loading="lazy"
              />
            ) : (
              <ReactMarkdown
                components={{
                  code: CodeBlock,
                  a: Hyperlink,
                  details: ThinkBlock,
                  p: Paragraph,
                }}
                disallowedElements={[
                  "iframe",
                  "head",
                  "html",
                  "meta",
                  "link",
                  "style",
                  "body",
                  ...(customDisallowedElements ?? []),
                ]}
                rehypePlugins={[RehypeKatex, RehypeRaw]}
                remarkPlugins={[
                  RemarkGfm,
                  [RemarkMath, { singleDollarTextMath: false }],
                  RemarkBreaks,
                  supersub,
                  remarkParse,
                ]}
              >
                {preprocessThinkTag(preprocessLaTeX(segment.content))}
              </ReactMarkdown>
            )}
          </Fragment>
        ))}
      </div>
    );
  }

  // Normal rendering path (no base64 images)
  return (
    <div className={`${styles.markdown} ${className ?? ""}`}>
      {segments.map((segment, idx) => (
        <Fragment
          key={
            segment.type === "citation" && isValidElement(segment.content)
              ? segment.content.key ?? idx
              : idx
          }
        >
          {segment.type === "text" ? (
            <ReactMarkdown
              components={{
                code: CodeBlock,
                a: Hyperlink,
                details: ThinkBlock,
                p: Paragraph,
                img: Image,
              }}
              disallowedElements={[
                "iframe",
                "head",
                "html",
                "meta",
                "link",
                "style",
                "body",
                ...(customDisallowedElements ?? []),
              ]}
              rehypePlugins={[
                RehypeKatex,
                RehypeRaw,
                // TODO: Re-enable sanitize with proper data URI support
                // rehypeSanitize is currently stripping data: URIs from images
                // [
                //   rehypeSanitize,
                //   {
                //     ...defaultSchema,
                //     tagNames: [...(defaultSchema.tagNames ?? []), "sub", "sup", "img"],
                //     attributes: {
                //       ...defaultSchema.attributes,
                //       code: [["className", /^language-./]],
                //       img: ["src", "alt", "title", "width", "height", "class", "className", "loading"],
                //     },
                //     protocols: {
                //       ...defaultSchema.protocols,
                //       src: ["http", "https", "data"],
                //     },
                //   },
                // ],
                // Remove ref properties and validate tag names
                () => (tree: { children: IRehypeNode[] }) => {
                  const iterate = (node: IRehypeNode) => {
                    if (
                      node.type === "element" &&
                      node.properties !== undefined &&
                      "ref" in node.properties
                    ) {
                      delete node.properties.ref;
                    }

                    if (
                      node.type === "element" &&
                      !/^[a-z][a-z0-9]*$/i.test(node.tagName)
                    ) {
                      node.type = "text";
                      node.value = `<${node.tagName}`;
                    }

                    if (node.children) {
                      for (const child of node.children) {
                        iterate(child);
                      }
                    }
                  };

                  for (const child of tree.children) {
                    iterate(child);
                  }
                },
              ]}
              remarkPlugins={[
                RemarkGfm,
                [RemarkMath, { singleDollarTextMath: false }],
                RemarkBreaks,
                supersub,
                remarkParse,
              ]}
            >
              {segment.content as string}
            </ReactMarkdown>
          ) : (
            segment.content
          )}
        </Fragment>
      ))}
    </div>
  );
}
