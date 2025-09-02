import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { PROFILE } from "../content/profileData.ts";

/**
 * mergeClassNamesSafely
 * @param inputs
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const shuffleArray = (array: Array<any>) => {
  for (let i = array.length - 1; i >= 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [array[i], array[j]] = [array[j], array[i]];
  }
};

export const getUserTimeZoneInBrowser = (): string => {
  return Intl.DateTimeFormat().resolvedOptions().timeZone;
};

const getLocalLanguage = (): string => {
  return PROFILE.language;
}

export const formateLocalDate = (
  date: Date,
  timeZone: string = PROFILE.timezone,
): string => {
  return new Intl.DateTimeFormat(getLocalLanguage(), {
    year: "numeric",
    month: "short",
    day: "2-digit",
    timeZone: timeZone,
  }).format(date);
};

export const formateLocalMonth = (
  date: Date,
  timeZone: string = PROFILE.timezone,
): string => {
  return new Intl.DateTimeFormat(getLocalLanguage(), {
    year: "numeric",
    month: "short",
    timeZone: timeZone,
  }).format(date);
};
