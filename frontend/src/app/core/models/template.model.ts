export interface TemplateFieldSchema {
  name: string;
  label?: string;
  required?: boolean;
  type?: string;
}

export interface Template {
  id: string;
  code: string;
  name: string;
  document_type: string;
  description?: string | null;
  fields_schema: TemplateFieldSchema[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}
