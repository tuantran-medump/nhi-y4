import { parseMermaidToExcalidraw } from "@excalidraw/mermaid-to-excalidraw";
import { convertToExcalidrawElements } from "@excalidraw/excalidraw";
window.run = async (def) => {
  try {
    const r = await parseMermaidToExcalidraw(def);
    const elements = convertToExcalidrawElements(r.elements);
    const doc = { type: "excalidraw", version: 2, source: "hoctap", elements, appState: { viewBackgroundColor: "#ffffff" }, files: r.files || {} };
    document.getElementById("out").textContent = JSON.stringify(doc);
  } catch (e) { document.getElementById("out").textContent = "ERR " + String(e).slice(0, 300); }
};
