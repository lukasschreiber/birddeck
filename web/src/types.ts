export type EntryType = "bird" | "group" | "uncertain";

export interface Entry {
  type: EntryType;
  title?: string;
  icon?: string;
  tag?: string;
  bg?: string;
  favorite?: boolean;
  exotic?: boolean;
  items?: Entry[];
}

export interface Profile {
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
  tag: string;
  bg: string;
  favorite: boolean;
  exotic: boolean;
}

export type IconMap = Record<string, string | number>;

export interface Notice {
  severity: "info" | "error" | "success";
  text: string;
}
