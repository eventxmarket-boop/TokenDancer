// Deprecated: use keyStore directly
export const keyService = {
  getAll() { return [] },
  create(_name: string, _group: string) { return Promise.resolve({ id: 0 }) },
  delete(_id: string) { return Promise.resolve() },
  toggleStatus(_id: string) { return Promise.resolve() },
  setSearch(_v: string) {},
  setGroup(_v: string) {},
  setStatus(_v: string) {},
}
