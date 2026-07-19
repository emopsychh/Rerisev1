import { redirect } from "next/navigation";

/** Биржа труда снята с релиза — старые ссылки ведём на главную. */
export default function LaborRemovedPage() {
  redirect("/");
}
