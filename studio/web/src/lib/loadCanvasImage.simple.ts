export async function loadCanvasImageSimple(url: string): Promise<HTMLImageElement> {
  const response = await fetch(url, { credentials: "same-origin", cache: "no-store" });
  if (!response.ok) throw new Error(`The source image could not be fetched (${String(response.status)}).`);
  const blob = await response.blob();
  if (blob.size === 0) throw new Error("The source image is empty.");
  const objectUrl = URL.createObjectURL(blob);
  try {
    const image = new Image();
    const loaded = new Promise<HTMLImageElement>((resolve, reject) => {
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error("The source image bytes could not be decoded."));
    });
    image.src = objectUrl;
    return await loaded;
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}
