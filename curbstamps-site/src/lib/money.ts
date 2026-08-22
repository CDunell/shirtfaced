export const money = (n: number) =>
  n.toLocaleString("en-AU", { style: "currency", currency: "AUD" });
