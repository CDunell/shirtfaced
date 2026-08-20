import { asc, eq } from "drizzle-orm";
import { db } from "./client";
import {
  aboutContent,
  shippingContent,
  returnsContent,
  contactContent,
  sizeGuideContent,
  homeContent,
  moreContent,
  productPageContent,
  accountContent,
  garmentCareContent,
  faqContent,
  faqItems,
} from "./schema";

export const getAboutContent = () =>
  db.query.aboutContent.findFirst({ where: eq(aboutContent.id, 1) });
export const getShippingContent = () =>
  db.query.shippingContent.findFirst({ where: eq(shippingContent.id, 1) });
export const getReturnsContent = () =>
  db.query.returnsContent.findFirst({ where: eq(returnsContent.id, 1) });
export const getContactContent = () =>
  db.query.contactContent.findFirst({ where: eq(contactContent.id, 1) });
export const getSizeGuideContent = () =>
  db.query.sizeGuideContent.findFirst({ where: eq(sizeGuideContent.id, 1) });
export const getHomeContent = () =>
  db.query.homeContent.findFirst({ where: eq(homeContent.id, 1) });
export const getMoreContent = () =>
  db.query.moreContent.findFirst({ where: eq(moreContent.id, 1) });
export const getProductPageContent = () =>
  db.query.productPageContent.findFirst({ where: eq(productPageContent.id, 1) });
export const getAccountContent = () =>
  db.query.accountContent.findFirst({ where: eq(accountContent.id, 1) });
export const getGarmentCareContent = () =>
  db.query.garmentCareContent.findFirst({
    where: eq(garmentCareContent.id, 1),
  });
export const getFaqContent = () =>
  db.query.faqContent.findFirst({ where: eq(faqContent.id, 1) });
export const listFaqItems = () =>
  db.query.faqItems.findMany({ orderBy: asc(faqItems.sortOrder) });

type WithoutId<T> = Omit<T, "id" | "updatedAt">;

export async function updateAboutContent(
  data: WithoutId<typeof aboutContent.$inferInsert>,
) {
  await db
    .update(aboutContent)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(aboutContent.id, 1));
}

export async function updateShippingContent(
  data: WithoutId<typeof shippingContent.$inferInsert>,
) {
  await db
    .update(shippingContent)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(shippingContent.id, 1));
}

export async function updateReturnsContent(
  data: WithoutId<typeof returnsContent.$inferInsert>,
) {
  await db
    .update(returnsContent)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(returnsContent.id, 1));
}

export async function updateContactContent(
  data: WithoutId<typeof contactContent.$inferInsert>,
) {
  await db
    .update(contactContent)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(contactContent.id, 1));
}

export async function updateSizeGuideContent(
  data: WithoutId<typeof sizeGuideContent.$inferInsert>,
) {
  await db
    .update(sizeGuideContent)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(sizeGuideContent.id, 1));
}

export async function updateHomeContent(
  data: WithoutId<typeof homeContent.$inferInsert>,
) {
  await db
    .update(homeContent)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(homeContent.id, 1));
}

export async function updateMoreContent(
  data: WithoutId<typeof moreContent.$inferInsert>,
) {
  await db
    .update(moreContent)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(moreContent.id, 1));
}

export async function updateProductPageContent(
  data: WithoutId<typeof productPageContent.$inferInsert>,
) {
  await db
    .update(productPageContent)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(productPageContent.id, 1));
}

export async function updateAccountContent(
  data: WithoutId<typeof accountContent.$inferInsert>,
) {
  await db
    .update(accountContent)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(accountContent.id, 1));
}

export async function updateGarmentCareContent(
  data: WithoutId<typeof garmentCareContent.$inferInsert>,
) {
  await db
    .update(garmentCareContent)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(garmentCareContent.id, 1));
}

export async function updateFaqContent(
  data: WithoutId<typeof faqContent.$inferInsert>,
) {
  await db
    .update(faqContent)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(faqContent.id, 1));
}

type FaqItemInput = {
  question: string;
  answer: string;
  linkHref: string | null;
  linkLabel: string | null;
  sortOrder: number;
};

export async function addFaqItem(data: FaqItemInput) {
  await db.insert(faqItems).values(data);
}

export async function updateFaqItem(id: string, data: FaqItemInput) {
  await db
    .update(faqItems)
    .set({ ...data, updatedAt: new Date() })
    .where(eq(faqItems.id, id));
}

export async function deleteFaqItem(id: string) {
  await db.delete(faqItems).where(eq(faqItems.id, id));
}
