/**
 * 场景模板类型。
 *
 * 一个场景描述「在某个业务问题下，组合哪些标准 + 走什么流程」。
 * 平台内置 5 个离散制造场景（库存/设备/质检/排产/来料）。
 */

import type { DeliveryStandard } from './types.js';

export type ScenarioIndustry = 'discrete-manufacturing' | 'process-manufacturing';

export interface ScenarioTrigger {
  /** 触发源 */
  source: 'ontology_event' | 'schedule' | 'manual';
  /** ontology_event 时：监听哪个对象属性 */
  watch_field?: string;
  /** schedule 时：cron */
  cron?: string;
}

export interface ScenarioFlowStep {
  id: string;
  /** 引用哪个标准 */
  standard_key: string;
  /** 步骤描述 */
  description: string;
  /** 下一步（可省略） */
  next?: string | null;
  /** 失败时跳转 */
  on_failure?: string;
}

export interface Scenario {
  key: string;
  name: string;
  industry: ScenarioIndustry;
  description: string;
  /** 默认加载的标准 key 列表 */
  default_standard_keys: string[];
  /** 触发器 */
  trigger: ScenarioTrigger;
  /** 流程步骤 DAG */
  flow_template: ScenarioFlowStep[];
  /** 是否平台内置 */
  built_in: boolean;
}

/** 校验场景模板引用了已知标准（避免悬挂引用）。 */
export function validateScenarioReferences(
  scenario: Scenario,
  knownStandardKeys: Set<string>
): { valid: boolean; dangling: string[] } {
  const dangling: string[] = [];
  for (const step of scenario.flow_template) {
    if (!knownStandardKeys.has(step.standard_key)) {
      dangling.push(step.standard_key);
    }
  }
  return { valid: dangling.length === 0, dangling };
}

export type { DeliveryStandard };