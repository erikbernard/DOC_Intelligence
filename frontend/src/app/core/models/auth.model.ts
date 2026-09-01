export type UserRole = 'ADMIN' | 'REVIEWER' | 'COMMON_USER';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string; // email
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}
