/**
 * Brazilian input masks and strict validation utilities.
 */

export function formatCpf(raw: string): string {
  const digits = (raw || '').replace(/\D/g, '').slice(0, 11);
  if (digits.length <= 3) return digits;
  if (digits.length <= 6) return `${digits.slice(0, 3)}.${digits.slice(3)}`;
  if (digits.length <= 9) return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6)}`;
  return `${digits.slice(0, 3)}.${digits.slice(3, 6)}.${digits.slice(6, 9)}-${digits.slice(9, 11)}`;
}

export function validateCpf(cpf: string): boolean {
  if (!cpf) return true; // Optional field, if empty it's considered valid
  const clean = cpf.replace(/\D/g, '');
  if (clean.length !== 11) return false;

  // Reject known invalid all-same-digit CPFs (e.g. 000.000.000-00, 111.111.111-11)
  if (/^(\d)\1{10}$/.test(clean)) return false;

  // First check digit
  let sum = 0;
  for (let i = 0; i < 9; i++) {
    sum += parseInt(clean.charAt(i), 10) * (10 - i);
  }
  let firstRemainder = (sum * 10) % 11;
  if (firstRemainder === 10 || firstRemainder === 11) firstRemainder = 0;
  if (firstRemainder !== parseInt(clean.charAt(9), 10)) return false;

  // Second check digit
  sum = 0;
  for (let i = 0; i < 10; i++) {
    sum += parseInt(clean.charAt(i), 10) * (11 - i);
  }
  let secondRemainder = (sum * 10) % 11;
  if (secondRemainder === 10 || secondRemainder === 11) secondRemainder = 0;
  return secondRemainder === parseInt(clean.charAt(10), 10);
}

export function formatPhone(raw: string): string {
  const digits = (raw || '').replace(/\D/g, '').slice(0, 11);
  if (!digits) return '';
  if (digits.length <= 2) return `(${digits}`;
  if (digits.length <= 6) return `(${digits.slice(0, 2)}) ${digits.slice(2)}`;
  if (digits.length <= 10) {
    return `(${digits.slice(0, 2)}) ${digits.slice(2, 6)}-${digits.slice(6)}`;
  }
  return `(${digits.slice(0, 2)}) ${digits.slice(2, 7)}-${digits.slice(7, 11)}`;
}

export function validatePhone(phone: string): boolean {
  if (!phone) return true; // Optional field
  const clean = phone.replace(/\D/g, '');
  return clean.length >= 10 && clean.length <= 11;
}

export function validateEmail(email: string): boolean {
  if (!email) return true; // Optional field
  const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
  return regex.test(email.trim());
}
