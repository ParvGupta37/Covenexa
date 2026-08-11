export type UserRole = "ADMIN" | "MANAGER" | "ANALYST";

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  industry: string;
  created_at: string;
}

export interface RiskRating {
  level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  score: number;
}

export interface Borrower {
  id: string;
  organization_id: string;
  company_name: string;
  sector: string;
  country: string;
  risk_rating: RiskRating;
}

export interface Money {
  amount: number;
  currency: string;
}

export interface Loan {
  id: string;
  borrower_id: string;
  agreement_id?: string | null;
  principal_amount: Money;
  interest_rate: number;
  start_date: string;
  maturity_date: string;
  status: "ACTIVE" | "CLOSED" | "DEFAULTED";
}

export interface UploadedDocument {
  agreement_id: string;
  loan_id: string;
  file_name: string;
  file_path: string;
  file_type: string;
  upload_date: string;
  status: string;
}
