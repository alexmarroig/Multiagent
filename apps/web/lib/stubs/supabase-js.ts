export type User = Record<string, unknown>;
export type Session = Record<string, unknown>;

const queryBuilder = {
  select: () => queryBuilder,
  eq: () => queryBuilder,
  gte: () => queryBuilder,
  order: () => queryBuilder,
  single: async () => ({ data: null, error: null }),
  upsert: async () => ({ data: null, error: null }),
  limit: async () => ({ data: [], count: 0, error: null }),
};

export function createClient() {
  return {
    from: () => queryBuilder,
    auth: {
      getSession: async () => ({ data: { session: null }, error: null }),
      getUser: async () => ({ data: { user: null }, error: null }),
      signUp: async () => ({ data: { user: null, session: null }, error: null }),
      signInWithPassword: async () => ({ data: { user: null, session: null }, error: null }),
      signOut: async () => ({ error: null }),
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
