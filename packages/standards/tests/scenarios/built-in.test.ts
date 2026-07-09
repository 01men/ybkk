import { describe, it, expect } from 'vitest';
import {
  BUILT_IN_SCENARIOS,
  BUILT_IN_STANDARDS,
} from '../src/scenarios';
import { validateScenarioReferences } from '../src/dsl/scenario';
import { parseStandardYaml, validateStandard } from '../src/dsl/standard';

describe('BUILT_IN_SCENARIOS', () => {
  it('contains exactly 5 scenarios', () => {
    expect(BUILT_IN_SCENARIOS).toHaveLength(5);
  });

  it('all belong to discrete-manufacturing industry', () => {
    for (const s of BUILT_IN_SCENARIOS) {
      expect(s.industry).toBe('discrete-manufacturing');
    }
  });

  it('all have built_in=true', () => {
    for (const s of BUILT_IN_SCENARIOS) {
      expect(s.built_in).toBe(true);
    }
  });

  it('all have unique keys', () => {
    const keys = BUILT_IN_SCENARIOS.map((s) => s.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('all flow templates form a valid DAG', () => {
    for (const s of BUILT_IN_SCENARIOS) {
      const stepIds = new Set(s.flow_template.map((st) => st.id));
      for (const step of s.flow_template) {
        if (step.next && step.next !== null) {
          expect(stepIds.has(step.next)).toBe(true);
        }
      }
    }
  });
});

describe('BUILT_IN_STANDARDS', () => {
  it('all pass schema validation', () => {
    for (const std of BUILT_IN_STANDARDS) {
      const { validation } = validateStandard(std);
      expect(validation.valid).toBe(true);
      expect(validation.errors).toEqual([]);
    }
  });

  it('all have unique keys', () => {
    const keys = BUILT_IN_STANDARDS.map((s) => s.key);
    expect(new Set(keys).size).toBe(keys.length);
  });

  it('all are built_in', () => {
    for (const s of BUILT_IN_STANDARDS) {
      expect(s.built_in).toBe(true);
    }
  });
});

describe('scenario references', () => {
  it('all standard_key refs in scenarios resolve to known standards', () => {
    const knownKeys = new Set([
      ...BUILT_IN_STANDARDS.map((s) => s.key),
      // 模板里引用的 notify / create_ticket 等动作标准（在 DB 里存）
      'notify_purchase',
      'create_replenish_ticket',
      'create_maintenance_ticket',
      'notify_maintenance',
      'quality_judge_pass',
      'tag_quality_result',
      'production_collect_constraints',
      'notify_schedule',
      'inbound_quality_anomaly',
      'create_8d_report',
      'notify_supplier',
    ]);

    for (const s of BUILT_IN_SCENARIOS) {
      const result = validateScenarioReferences(s, knownKeys);
      expect(result.dangling).toEqual([]);
    }
  });
});

describe('5 specific scenarios', () => {
  it('inventory_alert triggers on material.current_stock change', () => {
    const s = BUILT_IN_SCENARIOS.find((x) => x.key === 'inventory_alert')!;
    expect(s.trigger.source).toBe('ontology_event');
    expect(s.trigger.watch_field).toBe('material.current_stock');
  });

  it('equipment_maintenance runs on schedule', () => {
    const s = BUILT_IN_SCENARIOS.find((x) => x.key === 'equipment_maintenance')!;
    expect(s.trigger.source).toBe('schedule');
    expect(s.trigger.cron).toBe('0 8 * * *');
  });

  it('production_scheduling only runs on weekdays', () => {
    const s = BUILT_IN_SCENARIOS.find((x) => x.key === 'production_scheduling')!;
    expect(s.trigger.cron).toContain('1-5');
  });
});