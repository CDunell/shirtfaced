import { SearchClient } from "./SearchClient";

export const metadata = {
  title: "Search — Shirtfaced",
  description: "Find the tee you're after.",
};

export default function SearchPage() {
  return (
    <>
      <div className="mx-auto max-w-5xl px-4 pt-8 sm:px-6">
        <h1 className="display text-[16vw] leading-[0.84] sm:text-[76px]">
          search
        </h1>
      </div>
      <SearchClient />
    </>
  );
}
