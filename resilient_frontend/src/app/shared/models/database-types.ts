export interface User {
  id: string;
  username: string;
  role: string;
  updated_at: string;
  created_at: string;
}

export interface Users {
  users: User[];
}
