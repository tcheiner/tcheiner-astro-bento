// Import utilities from `astro:content`
import { z, defineCollection } from "astro:content";
// Define a `type` and `schema` for each collection
const projectCollection = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    startDate: z.date(),
    description: z.string(),
    image: z
      .object({
        url: z.string(),
        alt: z.string(),
      })
      .optional(),
    tags: z.array(z.string()).optional(),
  }),
});

const experienceCollection = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    startDate: z.date(),
    endDate: z.date().optional(),
    company: z.string(),
    tags: z.array(z.string()).optional(),
  }),
});

const bookCollection = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    readYear: z.number(),
    author: z.string(),
    tags: z.array(z.string()).optional(),
  }),
});

const postCollection = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    startDate: z.date(),
    description: z.string().optional(),
    image: z
      .object({
        url: z.string(),
        alt: z.string(),
      })
      .optional(),
    tags: z.array(z.string()).optional(),
    canonical: z.string().optional(),
  }),
});

const recipesCollection = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string(),
    postDate: z.date(),
    course: z.array(z.string()),
    cuisine: z.array(z.string()),
    duration: z.number(),
    yields: z.array(z.number()),
    ingredients: z.array(z.string()),
    preparation: z.array(z.string()),
    image: z.object({
      url: z.string(),
      alt: z.string(),
    })
      .optional(),
    tags: z.array(z.string()).optional(),
    sourceUrl: z.string().optional(),
    canonical: z.string().optional(),
  }),
});

// Export a single `collections` object to register your collection(s)
export const collections = {
  projects: projectCollection,
  experiences: experienceCollection,
  books: bookCollection,
  posts: postCollection,
  recipes: recipesCollection,
};
