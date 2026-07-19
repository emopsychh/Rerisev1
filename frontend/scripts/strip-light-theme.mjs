import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const stylesDir = path.join(__dirname, "..", "app", "styles");

function readBlock(css, braceIndex) {
  let depth = 0;
  for (let j = braceIndex; j < css.length; j += 1) {
    const ch = css[j];
    if (ch === "{") depth += 1;
    else if (ch === "}") {
      depth -= 1;
      if (depth === 0) return { block: css.slice(braceIndex, j + 1), end: j + 1 };
    }
  }
  return { block: css.slice(braceIndex), end: css.length };
}

function shouldDropSelector(selector) {
  if (selector.includes('[data-theme="light"]')) return true;
  if (
    /\.theme-toggle\b|\.theme-toggle-|\.topbar-theme-toggle\b|\.mobile-theme-toggle\b|\.mobile-theme-footer\b|\.theme-switching\b|\.theme-view-transition\b|theme-view-transition|::view-transition/i.test(
      selector,
    )
  ) {
    return true;
  }
  if (/^@(?:keyframes)\s+theme-fade-/i.test(selector.trim())) return true;
  return false;
}

function stripCss(css) {
  let out = "";
  let i = 0;
  const n = css.length;

  while (i < n) {
    if (css.startsWith("/*", i)) {
      const end = css.indexOf("*/", i + 2);
      const comment = end === -1 ? css.slice(i) : css.slice(i, end + 2);
      if (
        /Compact shared theme switch|theme switch|Light application shell|light theme|view transition|theme-switching|both themes/i.test(
          comment,
        )
      ) {
        i = end === -1 ? n : end + 2;
        continue;
      }
      out += comment;
      i = end === -1 ? n : end + 2;
      continue;
    }

    if (css[i] === "@") {
      const brace = css.indexOf("{", i);
      if (brace === -1) {
        out += css.slice(i);
        break;
      }
      const prelude = css.slice(i, brace).trimEnd();
      const { block, end } = readBlock(css, brace);

      if (/^@keyframes\s+theme-fade-/i.test(prelude.trim())) {
        i = end;
        continue;
      }

      if (/^@(media|supports|layer|container)\b/i.test(prelude.trim())) {
        const inner = stripCss(block.slice(1, -1));
        if (inner.trim()) out += prelude + "{" + inner + "}";
        i = end;
        continue;
      }

      out += prelude + block;
      i = end;
      continue;
    }

    if (/\s/.test(css[i])) {
      out += css[i];
      i += 1;
      continue;
    }

    const brace = css.indexOf("{", i);
    if (brace === -1) {
      out += css.slice(i);
      break;
    }

    const between = css.slice(i, brace);
    const selector = between.trim();
    const { block, end } = readBlock(css, brace);

    if (shouldDropSelector(selector)) {
      i = end;
      continue;
    }

    out += between + block;
    i = end;
  }

  return out;
}

function cleanup(css) {
  return (
    css
      .replace(/:root,\s*:root\[data-theme="dark"\]/g, ":root")
      .replace(/:root\[data-theme="dark"\]/g, ":root")
      .replace(/:root:not\(\[data-theme\]\)/g, ":root")
      .replace(/[ \t]+\n/g, "\n")
      .replace(/\n{3,}/g, "\n\n")
      .trim() + "\n"
  );
}

for (const file of fs.readdirSync(stylesDir).filter((f) => f.endsWith(".css"))) {
  const full = path.join(stylesDir, file);
  const before = fs.readFileSync(full, "utf8");
  const after = cleanup(stripCss(before));
  fs.writeFileSync(full, after);
  const lightLeft = (after.match(/data-theme="light"/g) || []).length;
  console.log(`${file}: ${before.length} -> ${after.length}, light leftovers: ${lightLeft}`);
}
