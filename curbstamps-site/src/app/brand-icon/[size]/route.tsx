import { ImageResponse } from "next/og";
import { CurbStampsLogo } from "@/components/CurbStampsLogo";

const ALLOWED_SIZES = new Set([16, 32, 48, 180, 192, 512]);

export const runtime = "edge";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ size: string }> },
) {
  const { size: rawSize } = await params;
  const size = Number(rawSize);

  if (!ALLOWED_SIZES.has(size)) {
    return new Response("Unsupported icon size", { status: 404 });
  }

  const scale = (size * 0.92) / 300;

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
          background: "#000000",
        }}
      >
        <div
          style={{
            width: 300,
            height: 200,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            transform: `scale(${scale})`,
          }}
        >
          <CurbStampsLogo />
        </div>
      </div>
    ),
    {
      width: size,
      height: size,
    },
  );
}
