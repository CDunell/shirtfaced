import Link from "next/link";
import { IconArrowRight, IconCheck } from "@/components/Icons";

export const metadata = { title: "Order placed — Curb Stamps" };

export default async function CheckoutSuccessPage({
  searchParams,
}: {
  searchParams: Promise<{ orderId?: string }>;
}) {
  const { orderId } = await searchParams;

  return (
    <div className="mx-auto max-w-2xl px-4 py-20 text-center sm:px-6">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-grit-green">
        <IconCheck className="h-8 w-8 text-ink" />
      </div>
      <h1 className="display mt-6 text-[13vw] leading-[0.9] sm:text-[48px]">order placed!</h1>
      <p className="mt-3 text-[15px] text-grey-dark">
        Thanks — we&apos;ve got it. A confirmation email is on its way.
      </p>
      {orderId && <p className="mt-2 text-[13px] text-grey">Order reference: {orderId}</p>}
      <Link
        href="/shop"
        className="press mt-8 inline-flex h-14 items-center gap-2 rounded-full bg-ink px-6 text-[16px] font-extrabold text-paper"
      >
        Keep shopping
        <IconArrowRight className="h-5 w-5" />
      </Link>
    </div>
  );
}
