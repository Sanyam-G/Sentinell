// Simple Python syntax highlighter
export function highlightPython(code: string): string {
  const keywords = new Set([
    'def', 'class', 'import', 'from', 'return', 'if', 'else', 'elif', 'for', 'while',
    'try', 'except', 'finally', 'with', 'as', 'pass', 'break', 'continue', 'True',
    'False', 'None', 'and', 'or', 'not', 'in', 'is', 'lambda', 'yield', 'raise'
  ]);

  let result = '';
  let i = 0;

  while (i < code.length) {
    // Comments
    if (code[i] === '#') {
      const start = i;
      while (i < code.length && code[i] !== '\n') i++;
      result += `<span class="text-slate-500">${escapeHtml(code.substring(start, i))}</span>`;
      continue;
    }

    // Strings
    if (code[i] === '"' || code[i] === "'") {
      const quote = code[i];
      const start = i;
      i++;
      while (i < code.length && code[i] !== quote) {
        if (code[i] === '\\') i++;
        i++;
      }
      if (i < code.length) i++;
      result += `<span class="text-green-400">${escapeHtml(code.substring(start, i))}</span>`;
      continue;
    }

    // Words (keywords, functions, identifiers)
    if (/[a-zA-Z_]/.test(code[i])) {
      const start = i;
      while (i < code.length && /[a-zA-Z0-9_]/.test(code[i])) i++;
      const word = code.substring(start, i);

      // Check if next non-space char is '(' for function calls
      let j = i;
      while (j < code.length && code[j] === ' ') j++;
      const isFunction = code[j] === '(';

      if (keywords.has(word)) {
        result += `<span class="text-purple-400">${escapeHtml(word)}</span>`;
      } else if (isFunction) {
        result += `<span class="text-blue-400">${escapeHtml(word)}</span>`;
      } else {
        result += escapeHtml(word);
      }
      continue;
    }

    // Default: append character as-is
    result += escapeHtml(code[i]);
    i++;
  }

  return result;
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
