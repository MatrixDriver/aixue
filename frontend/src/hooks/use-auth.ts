"use client";

// ============================================================
// 认证状态 Hook
// ============================================================

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  getToken,
  saveToken,
  removeToken,
  saveUserCache,
  getUserCache,
} from "@/lib/auth";
import { login as apiLogin, register as apiRegister, getMe } from "@/lib/api";
import type { User, LoginRequest, RegisterRequest } from "@/lib/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  error: string | null;
}

export function useAuth() {
  const router = useRouter();
  const [state, setState] = useState<AuthState>({
    user: null,
    loading: true,
    error: null,
  });

  // 初始化：检查 Token 并加载用户信息
  useEffect(() => {
    const token = getToken();
    if (!token) {
      setState({ user: null, loading: false, error: null });
      return;
    }

    // 先尝试从缓存读取
    const cached = getUserCache<User>();
    if (cached) {
      setState({ user: cached, loading: false, error: null });
    }

    // 后台刷新用户信息
    getMe()
      .then((user) => {
        saveUserCache(user);
        setState({ user, loading: false, error: null });
      })
      .catch(() => {
        removeToken();
        setState({ user: null, loading: false, error: null });
      });
  }, []);

  // 登录
  const login = useCallback(
    async (data: LoginRequest) => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const tokenRes = await apiLogin(data);
        saveToken(tokenRes.access_token);
        const user = await getMe();
        saveUserCache(user);
        setState({ user, loading: false, error: null });
        router.push("/solve");
      } catch (err: unknown) {
        const message =
          (err as { response?: { data?: { detail?: string } } })?.response
            ?.data?.detail || "登录失败，请检查用户名和密码";
        setState({ user: null, loading: false, error: message });
        throw err;
      }
    },
    [router]
  );

  // 注册
  const registerUser = useCallback(
    async (data: RegisterRequest) => {
      setState((prev) => ({ ...prev, loading: true, error: null }));
      try {
        const tokenRes = await apiRegister(data);
        saveToken(tokenRes.access_token);
        const user = await getMe();
        saveUserCache(user);
        setState({ user, loading: false, error: null });
        router.push("/solve");
      } catch (err: unknown) {
        const message =
          (err as { response?: { data?: { detail?: string } } })?.response
            ?.data?.detail || "注册失败，请稍后重试";
        setState({ user: null, loading: false, error: message });
        throw err;
      }
    },
    [router]
  );

  // 登出
  const logout = useCallback(() => {
    removeToken();
    setState({ user: null, loading: false, error: null });
    router.push("/login");
  }, [router]);

  // 刷新用户信息
  const refreshUser = useCallback(async () => {
    try {
      const user = await getMe();
      saveUserCache(user);
      setState((prev) => ({ ...prev, user }));
    } catch {
      // 忽略刷新失败
    }
  }, []);

  return {
    user: state.user,
    loading: state.loading,
    error: state.error,
    login,
    register: registerUser,
    logout,
    refreshUser,
    isAuthenticated: !!state.user,
  };
}
