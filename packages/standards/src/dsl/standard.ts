/**
 * 交付标准 DSL：解析 / 校验 / 序列化。
 */

import Ajv, { ValidateFunction } from 'ajv';
import addFormats from 'ajv-formats';
import YAML from 'yaml';
import { standardSchema } from '../schemas/standard.schema.js';
import type { DeliveryStandard, StandardValidationResult } from './types.js';

const ajv = new Ajv({ allErrors: true, strict: false });
addFormats(ajv);
const validateFn: ValidateFunction = ajv.compile(standardSchema as object);

/** 把 YAML 字符串解析成 DeliveryStandard，并校验。 */
export function parseStandardYaml(yamlText: string): {
  standard: DeliveryStandard;
  validation: StandardValidationResult;
} {
  const parsed = YAML.parse(yamlText) as unknown;
  return validateStandard(parsed);
}

/** 校验任意对象是否符合标准 schema。 */
export function validateStandard(input: unknown): {
  standard: DeliveryStandard;
  validation: StandardValidationResult;
} {
  const valid = validateFn(input);
  const errors =
    validateFn.errors?.map(
      (e) => `${e.instancePath || '/'} ${e.message ?? 'invalid'}`
    ) ?? [];
  return {
    standard: input as DeliveryStandard,
    validation: { valid: !!valid, errors },
  };
}

/** 标准对象 → YAML。 */
export function serializeStandardYaml(standard: DeliveryStandard): string {
  return YAML.stringify(standard, { indent: 2, lineWidth: 100 });
}

/** 把用户的覆盖项合并到基线标准（字段级 merge）。 */
export function applyStandardOverrides(
  baseline: DeliveryStandard,
  overrides: Partial<DeliveryStandard>
): DeliveryStandard {
  return {
    ...baseline,
    ...overrides,
    expr: {
      ...baseline.expr,
      ...(overrides.expr ?? {}),
      condition: { ...baseline.expr.condition, ...(overrides.expr?.condition ?? {}) },
      action_payload: { ...baseline.expr.action_payload, ...(overrides.expr?.action_payload ?? {}) },
    },
    scope: { ...baseline.scope, ...(overrides.scope ?? {}) },
  };
}