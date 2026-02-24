export type User = Record<string, unknown>;
export type Session = Record<string, unknown>;

const queryBuilder = {
  select: () => queryBuilder,
  eq: () => queryBuilder,
  gte: () => queryBuilder,
  order: () => queryBuilder,
  limit: async () => ({ data: [], count: 0, error: null }),
};

export function createClient() {
  return {
    from: () => queryBuilder,
    auth: {
      getSession: async () => ({ data: { session: null }, error: null }),
      getUser: async () => ({ data: { user: null }, error: null }),
      onAuthStateChange: () => ({
        data: {
          subscription: {
            unsubscribe: () => {},
          },
        },
      }),
    },
  };
}
