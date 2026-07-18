/** UI is Russian-only for now. `t` stays as an identity helper so call sites don't need a mass rewrite. */
export function translate(value: string, _lang?: string) {
  return value;
}
