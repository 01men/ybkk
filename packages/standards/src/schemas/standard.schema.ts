/**
 * JSON Schema for DeliveryStandard（参见 TASK-040）。
 * 启动时所有内置标准都会通过 ajv 校验。
 */

export const standardSchema = {
  $schema: 'http://json-schema.org/draft-07/schema#',
  $id: 'https://aios.com/schemas/standard.schema.json',
  type: 'object',
  required: ['key', 'name', 'kind', 'expr', 'scope', 'built_in'],
  properties: {
    key: { type: 'string', pattern: '^[a-z][a-z0-9_]{2,63}$' },
    name: { type: 'string', minLength: 1, maxLength: 256 },
    kind: { type: 'string', enum: ['threshold', 'pattern', 'temporal', 'aggregation'] },
    expr: {
      type: 'object',
      required: ['kind', 'condition', 'action', 'action_payload'],
      properties: {
        kind: { type: 'string', enum: ['threshold', 'pattern', 'temporal', 'aggregation'] },
        condition: {
          oneOf: [
            {
              type: 'object',
              required: ['type', 'field', 'op', 'value'],
              properties: {
                type: { const: 'threshold' },
                field: { type: 'string', minLength: 1 },
                op: { enum: ['<', '<=', '==', '!=', '>=', '>'] },
                value: {},
                is_ref: { type: 'boolean' },
              },
            },
            {
              type: 'object',
              required: ['type', 'pattern'],
              properties: {
                type: { const: 'pattern' },
                pattern: { type: 'string', minLength: 1 },
                window_minutes: { type: 'integer', minimum: 1 },
              },
            },
            {
              type: 'object',
              required: ['type', 'since_field', 'exceed_minutes'],
              properties: {
                type: { const: 'temporal' },
                since_field: { type: 'string', minLength: 1 },
                exceed_minutes: { type: 'integer', minimum: 1 },
              },
            },
            {
              type: 'object',
              required: ['type', 'count', 'within_minutes', 'match'],
              properties: {
                type: { const: 'aggregation' },
                count: { type: 'integer', minimum: 1 },
                within_minutes: { type: 'integer', minimum: 1 },
                match: { type: 'object' },
              },
            },
          ],
        },
        action: {
          enum: ['notify', 'create_ticket', 'webhook', 'tag', 'block'],
        },
        action_payload: { type: 'object' },
      },
    },
    scope: {
      type: 'object',
      properties: {
        industries: { type: 'array', items: { type: 'string' } },
        roles: { type: 'array', items: { type: 'string' } },
        scenarios: { type: 'array', items: { type: 'string' } },
        datasource_types: { type: 'array', items: { type: 'string' } },
      },
    },
    built_in: { type: 'boolean' },
    description: { type: 'string' },
  },
  additionalProperties: false,
} as const;