import { getCollection } from "astro:content";
import { PROFILE } from "../content/profileData.ts";

export const getAndGroupUniqueTags = async (): Promise<Map<string, any[]>> => {
  const allProjects = await getCollection("projects");
  const allExperiences = await getCollection("experiences");
  const books = await getCollection("books");
  const posts = await getCollection("posts");
  const recipes = await getCollection("recipes");

  const allItems = [...allProjects, ...allExperiences, ...books, ...posts];

  // @ts-ignore
  const uniqueTags: string[] = [
    ...new Set(allProjects.map((post: any) => post.data.tags).flat()),
    ...new Set(allExperiences.map((post: any) => post.data.tags).flat()),
    ...new Set(books.map((post: any) => post.data.tags).flat()),
    ...new Set(posts.map((post: any) => post.data.tags).flat()),
    ...new Set(recipes.map((post: any) => post.data.tags).flat()),
  ];
  const tagItemsMap = new Map<string, any[]>();

  uniqueTags.forEach((tag) => {
    const filteredItems = allItems.filter((item) =>
      item?.data?.tags?.includes(tag),
    );

    tagItemsMap.set(tag, filteredItems);
  });
  return tagItemsMap;
};