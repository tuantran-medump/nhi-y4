import { restore, exportToSvg } from "@excalidraw/excalidraw";
window.render = async (doc) => {
  try {
    const data = restore(doc, null, null);
    const svg = await exportToSvg({ elements: data.elements, appState: { ...data.appState, exportBackground: true, viewBackgroundColor: "#ffffff" }, files: data.files || {} });
    document.getElementById("out").textContent = "OK " + data.elements.length;
    document.getElementById("svg").appendChild(svg);
  } catch (e) { document.getElementById("out").textContent = "ERR " + String(e).slice(0, 300); }
};
