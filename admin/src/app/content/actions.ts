"use server";

import { revalidatePath } from "next/cache";
import { z } from "zod";
import * as queries from "@/db/content-queries";

export type FormState = { error: string | null; saved?: boolean };

const nonEmpty = z.string().trim().min(1, "This field can't be empty.");

function parse<T extends z.ZodRawShape>(schema: z.ZodObject<T>, formData: FormData) {
  const raw = Object.fromEntries(formData.entries());
  return schema.safeParse(raw);
}

const aboutSchema = z.object({
  intro: nonEmpty,
  ideaP1: nonEmpty,
  ideaP2: nonEmpty,
  howMadeP1: nonEmpty,
  howMadeP2: nonEmpty,
  wontDoP1: nonEmpty,
  whoP1: nonEmpty,
});

export async function updateAboutAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = parse(aboutSchema, formData);
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };
  await queries.updateAboutContent(result.data);
  revalidatePath("/content/about");
  return { error: null, saved: true };
}

const shippingSchema = z.object({
  intro: nonEmpty,
  standardName: nonEmpty,
  standardTime: nonEmpty,
  standardPrice: nonEmpty,
  expressName: nonEmpty,
  expressTime: nonEmpty,
  expressPrice: nonEmpty,
  whereP1: nonEmpty,
  whereP2: nonEmpty,
  trackingP1: nonEmpty,
  packagingP1: nonEmpty,
});

export async function updateShippingAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = parse(shippingSchema, formData);
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };
  await queries.updateShippingContent(result.data);
  revalidatePath("/content/shipping");
  return { error: null, saved: true };
}

const returnsSchema = z.object({
  intro: nonEmpty,
  step1Title: nonEmpty,
  step1Body: nonEmpty,
  step2Title: nonEmpty,
  step2Body: nonEmpty,
  step3Title: nonEmpty,
  step3Body: nonEmpty,
  step4Title: nonEmpty,
  step4Body: nonEmpty,
  exchangesP1: nonEmpty,
  exchangesP2: nonEmpty,
  wrongP1: nonEmpty,
  wrongP2: nonEmpty,
  cantTakeP1: nonEmpty,
});

export async function updateReturnsAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = parse(returnsSchema, formData);
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };
  await queries.updateReturnsContent(result.data);
  revalidatePath("/content/returns");
  return { error: null, saved: true };
}

const contactSchema = z.object({
  intro: nonEmpty,
  email: z.string().trim().email("Must be a valid email address."),
  wholesaleP1: nonEmpty,
  pressP1: nonEmpty,
  bottomBlurb: nonEmpty,
});

export async function updateContactAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = parse(contactSchema, formData);
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };
  await queries.updateContactContent(result.data);
  revalidatePath("/content/contact");
  return { error: null, saved: true };
}

const sizeGuideSchema = z.object({
  intro: nonEmpty,
  measureChest: nonEmpty,
  measureLength: nonEmpty,
  betweenSizesP1: nonEmpty,
  betweenSizesP2: nonEmpty,
  careP1: nonEmpty,
  sChest: nonEmpty,
  sLength: nonEmpty,
  mChest: nonEmpty,
  mLength: nonEmpty,
  lChest: nonEmpty,
  lLength: nonEmpty,
  xlChest: nonEmpty,
  xlLength: nonEmpty,
  xxlChest: nonEmpty,
  xxlLength: nonEmpty,
});

export async function updateSizeGuideAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = parse(sizeGuideSchema, formData);
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };
  await queries.updateSizeGuideContent(result.data);
  revalidatePath("/content/size-guide");
  return { error: null, saved: true };
}

const homeSchema = z.object({
  trust1: nonEmpty,
  trust2: nonEmpty,
  trust3: nonEmpty,
  promoHeading: nonEmpty,
  promoAlt: nonEmpty,
  newsletterHeading: nonEmpty,
});

export async function updateHomeAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = parse(homeSchema, formData);
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };
  await queries.updateHomeContent(result.data);
  revalidatePath("/content/home");
  return { error: null, saved: true };
}

const moreSchema = z.object({
  blurbHeading: nonEmpty,
  blurbSubline: nonEmpty,
});

export async function updateMoreAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = parse(moreSchema, formData);
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };
  await queries.updateMoreContent(result.data);
  revalidatePath("/content/more");
  return { error: null, saved: true };
}

const productPageSchema = z.object({
  feature1A: nonEmpty,
  feature1B: nonEmpty,
  feature2A: nonEmpty,
  feature2B: nonEmpty,
  feature3A: nonEmpty,
  feature3B: nonEmpty,
  feature4A: nonEmpty,
  feature4B: nonEmpty,
});

export async function updateProductPageAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = parse(productPageSchema, formData);
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };
  await queries.updateProductPageContent(result.data);
  revalidatePath("/content/product");
  return { error: null, saved: true };
}

const accountSchema = z.object({
  intro: nonEmpty,
  benefit1A: nonEmpty,
  benefit1B: nonEmpty,
  benefit2A: nonEmpty,
  benefit2B: nonEmpty,
  benefit3A: nonEmpty,
  benefit3B: nonEmpty,
});

export async function updateAccountAction(
  _prevState: FormState,
  formData: FormData,
): Promise<FormState> {
  const result = parse(accountSchema, formData);
  if (!result.success) return { error: result.error.issues[0]?.message ?? "Invalid input." };
  await queries.updateAccountContent(result.data);
  revalidatePath("/content/account");
  return { error: null, saved: true };
}
