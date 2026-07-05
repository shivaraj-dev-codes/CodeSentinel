import Editor from "@monaco-editor/react";

interface Props {
  code: string;
  language?: string;
  highlightLines?: [number, number];
  /** If true, shows a green background (fix suggestion) instead of red */
  isFix?: boolean;
}

export function CodeViewer({ code, language = "python", highlightLines, isFix = false }: Props) {
  function handleEditorMount(editor: import("monaco-editor").editor.IStandaloneCodeEditor, monaco: typeof import("monaco-editor")) {
    if (!highlightLines) return;

    const [start, end] = highlightLines;
    editor.deltaDecorations(
      [],
      [
        {
          range: new monaco.Range(start, 1, end, 1),
          options: {
            isWholeLine: true,
            className: isFix ? "highlighted-fix-line" : "highlighted-vuln-line",
            glyphMarginClassName: isFix ? "glyph-fix" : "glyph-vuln",
          },
        },
      ]
    );
  }

  return (
    <div className="rounded-md overflow-hidden border border-border-default">
      <Editor
        height="280px"
        language={language}
        value={code}
        theme="vs-dark"
        options={{
          readOnly: true,
          minimap: { enabled: false },
          lineNumbers: "on",
          scrollBeyondLastLine: false,
          fontSize: 13,
          fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
          padding: { top: 8, bottom: 8 },
          renderLineHighlight: "none",
          overviewRulerLanes: 0,
          folding: false,
          lineDecorationsWidth: 6,
          automaticLayout: true,
        }}
        onMount={handleEditorMount}
        beforeMount={(monaco) => {
          monaco.editor.defineTheme("codesentinel-dark", {
            base: "vs-dark",
            inherit: true,
            rules: [],
            colors: {
              "editor.background": "#161b22",
              "editor.lineHighlightBackground": "#21262d",
              "editor.selectionBackground": "#264f78",
              "editorLineNumber.foreground": "#484f58",
              "editorLineNumber.activeForeground": "#8b949e",
              "editor.foreground": "#e6edf3",
            },
          });
          // Inject decoration styles
          const style = document.createElement("style");
          style.textContent = `
            .highlighted-vuln-line { background: rgba(255,110,110,0.12) !important; border-left: 3px solid #ff6e6e; }
            .highlighted-fix-line  { background: rgba(63,185,80,0.12)  !important; border-left: 3px solid #3fb950; }
          `;
          document.head.appendChild(style);
        }}
      />
    </div>
  );
}
