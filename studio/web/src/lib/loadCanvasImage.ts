/** Load a Studio image for canvas use without relying on direct URL decoding.
 *
 * Some mobile browsers can display a WebP in an <img> element but fail when a
 * second HTMLImageElement is created directly from the protected API URL. Fetching
 * the exact bytes first and decoding an object URL makes the canvas path use the
 * same-origin fetch stack and gives us a useful HTTP failure before decode.
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
    image.src = objectUrl;

    if (typeof image.decode === "function") {
      try {
        await image.decode();
        return image;
      } catch {
        // Samsung Internet and older WebViews have had partial decode() support.
        // Fall through to the load/error events before declaring the image bad.
      }
    }

    if (image.complete && image.naturalWidth > 0) return image;

    await new Promise<void>((resolve, reject) => {
      image.onload = () => resolve();
      image.onerror = () => reject(new Error("The source image bytes could not be decoded."));
    });
    return image;
  } finally {
    // The decoded image remains usable after the backing blob URL is released.
    URL.revokeObjectURL(objectUrl);
  }
}
