export type PersonaStatus =
  | 'PENDING'
  | 'DOCUMENTS_RECEIVED'
  | 'IN_REVIEW'
  | 'ONBOARDING_COMPLETED';

export interface Persona {
  id: string;
  name: string;
  email: string | null;
  cpf: string | null;
  phone: string | null;
  status: PersonaStatus;
  required_document_types: string[];
  metadata_info: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export type PersonaCreate = Pick<Persona, 'name'> &
  Partial<Pick<Persona, 'email' | 'cpf' | 'phone' | 'required_document_types' | 'metadata_info'>>;

export interface PersonaFilterParams {
  status?: PersonaStatus;
  search?: string;
  skip?: number;
  limit?: number;
}
