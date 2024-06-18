export interface User {
  id: string;
  username: string;
  role: string;
  updated_at: string;
  created_at: string;
  active: boolean;
}

export interface Users {
  users: User[];
}
