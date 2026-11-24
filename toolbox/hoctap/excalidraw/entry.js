import { parseMermaidToExcalidraw } from "@excalidraw/mermaid-to-excalidraw";
window.run = async (def) => {
  try {
    const r = await parseMermaidToExcalidraw(def);
    const el = r.elements;
    document.getElementById("out").textContent = JSON.stringify({ok:true, n: el.length, types: [...new Set(el.map(e=>e.type))], labeled: el.filter(e=>e.label && e.label.text).length, sample: el.filter(e=>e.label && e.label.text).slice(0,3).map(e=>e.label.text)});
    window.__result = r;
  } catch (e) { document.getElementById("out").textContent = JSON.stringify({ok:false, err: String(e).slice(0,300)}); }
};
