// ============================================================
// Token 存储与管理
// ============================================================

const TOKEN_KEY = "aixue_access_token";
const USER_KEY = "aixue_user";

/** 保存 Token */
export function saveToken(token: string): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

/** 获取 Token */
export function getToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem(TOKEN_KEY);
  }
  return null;
}

/** 移除 Token */
export function removeToken(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

/** 保存用户信息缓存 */
export function saveUserCache(user: object): void {
  if (typeof window !== "undefined") {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

/** 获取用户信息缓存 */
export function getUserCache<T>(): T | null {
  if (typeof window !== "undefined") {
    const raw = localStorage.getItem(USER_KEY);
    if (raw) {
      try {
        return JSON.parse(raw) as T;
      } catch {
        return null;
      }
    }
  }
  return null;
}

/** 判断是否已登录 */
export function isAuthenticated(): boolean {
  return !!getToken();
}
