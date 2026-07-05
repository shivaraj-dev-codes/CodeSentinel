import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "./client";
import type { User } from "../store/authStore";

interface AuthResponse {
  success: boolean;
  data: { user: User; access: string; refresh: string };
}

export const authApi = {
  register: (email: string, password: string, passwordConfirm: string, fullName: string) =>
    api.post<AuthResponse>("/auth/register/", { email, password, password_confirm: passwordConfirm, full_name: fullName }),

  login: (email: string, password: string) =>
    api.post<AuthResponse>("/auth/login/", { email, password }),

  logout: (refresh: string) =>
    api.post("/auth/logout/", { refresh }),

  me: () =>
    api.get<{ success: boolean; data: User }>("/auth/me/"),

  connectGitHub: (code: string) =>
    api.post<{ success: boolean; data: User }>("/auth/github/", { code }),
};

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: () => authApi.me().then((r) => r.data.data),
    staleTime: 1000 * 60 * 5,
  });
}

export function useLogin() {
  return useMutation({
    mutationFn: ({ email, password }: { email: string; password: string }) =>
      authApi.login(email, password).then((r) => r.data),
  });
}

export function useRegister() {
  return useMutation({
    mutationFn: ({ email, password, passwordConfirm, fullName }: {
      email: string; password: string; passwordConfirm: string; fullName: string;
    }) => authApi.register(email, password, passwordConfirm, fullName).then((r) => r.data),
  });
}
