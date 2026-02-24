import { createClient } from './supabase-js';

export function createMiddlewareClient() {
  return createClient();
}

export function createServerComponentClient() {
  return createClient();
}

export function createRouteHandlerClient() {
  return createClient();
}
