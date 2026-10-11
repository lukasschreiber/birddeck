export type EntryType = "bird" | "group" | "uncertain";

export interface Entry {
  uuid?: string;
  type: EntryType;
  title?: string;
  icon?: string;
  rotation?: number;
  tag?: string;
  bg?: string;
  favorite?: boolean;
  exotic?: boolean;
  country?: string;
  nabu?: string;
  scientific_name?: string;
  english_name?: string;
  items?: Entry[];
}

export interface Profile {
  uuid?: string;
  title?: never;
  type?: never;
  name: string;
  items: Entry[];
}

export interface Snapshot {
  config: { profile: Profile };
  revision: number;
  file: string;
  selected?: number[];
}

export interface EntryForm {
  type: EntryType;
  title: string;
  icon: string;
  rotation: number;
  tag: string;
  bg: string;
  favorite: boolean;
  exotic: boolean;
  country: string;
  nabu: string;
  scientific_name: string;
  english_name: string;
}

export type IconMap = Record<string, string | number>;

export interface Notice {
  severity: "info" | "error" | "success";
  text: string;
}
