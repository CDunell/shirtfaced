import { LoginForm } from "./LoginForm";

export default async function LoginPage({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const { next } = await searchParams;
  return (
    <div className="mx-auto flex min-h-[70vh] max-w-sm flex-col justify-center px-4">
      <h1 className="text-[32px] font-extrabold">Curb Stamps Admin</h1>
      <p className="mt-2 text-[14px] text-ink/60">Orders &amp; fulfilment.</p>
      <div className="mt-8">
        <LoginForm next={next ?? "/orders"} />
      </div>
    </div>
  );
}
