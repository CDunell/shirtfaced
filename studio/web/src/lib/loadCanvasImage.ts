/** Load a Studio image for canvas use without relying on direct API URL decoding.
 *
 * Some mobile browsers can display a stored WebP in a normal <img> yet fail when
 * Social Studio creates a second HTMLImageElement directly from the API URL for
 * canvas work. Fetching the bytes first and decoding an object URL avoids that path.
 */
export async function loadCanvasImage(url: string): Promise<HTMLImageElement> {
  let response: Response;
  try {
    response = await fetch(url, { credentials: "same-origin", cache: "no-store" });
  } catch (cause) {
    throw new Error("The source image could not be fetched.", { cause });
  }

  if (!response.ok) {
    throw new Error(`The source image could not be fetched (${String(response.status)}).`);
  }

  const blob = await response.blob();
  if (blob.size === 0) throw new Error("The source image is empty.");

  const objectUrl = URL.createObjectURL(blob);
  try {
    const image = new Image();
    const loaded = new Promise<HTMLImageElement>((resolve, reject) => {
      image.onload = () => {
        resolve(image);
      };
      image.onerror = () => {
        reject(new Error("The source image bytes could not be decoded."));
      };
    });
    image.src = objectUrl;
    return await loaded;
  } finally {
    URL.revokeObjectURL(objectUrl);
  }
}
