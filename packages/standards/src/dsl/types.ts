/**
 * 交付标准 DSL 类型定义。
 *
 * 一个标准描述「在什么场景下、满足什么条件、做什么动作」。
 * 平台内置标准覆盖 5 个常见离散制造场景（库存/设备/质检/排产/来料）。
 */

export type StandardKind =
  | 'threshold'    // 阈值型（库存量 < 安全库存）
  | 'pattern'      // 模式型（出现特定模式 → 触发）
  | 'temporal'     // 时间型（超时未处理）
  | 'aggregation'; // 聚合型（连续 N 次达标）

export type StandardAction =
  | 'notify'        // 发钉钉 / 飞书
  | 'create_ticket' // 创建工单
  | 'webhook'       // 出站 webhook
  | 'tag'           // 在本体图打标签
  | 'block';        // 阻止下一步

export interface StandardExpression {
  /** 表达式 DSL（如 {field: 'inventory.qty', op: '<', value: '$safety_stock'}）*/
  kind: StandardKind;
  condition: ThresholdCondition | PatternCondition | TemporalCondition | AggregationCondition;
  action: StandardAction;
  action_payload: Record<string, unknown>;
}

export interface ThresholdCondition {
  type: 'threshold';
  field: string;
  op: '<' | '<=' | '==' | '!=' | '>=' | '>';
  value: string | number | boolean;
  /** value 可以是字段引用（如 '$safety_stock'）*/
  is_ref?: boolean;
}

export interface PatternCondition {
  type: 'pattern';
  pattern: string;
  window_minutes?: number;
}

export interface TemporalCondition {
  type: 'temporal';
  since_field: string;
  exceed_minutes: number;
}

export interface AggregationCondition {
  type: 'aggregation';
  count: number;
  within_minutes: number;
  match: ThresholdCondition | PatternCondition;
}

export interface DeliveryStandard {
  /** 标准唯一 key（如 'inventory_low_stock'）*/
  key: string;
  /** 中文名 */
  name: string;
  /** 类型 */
  kind: StandardKind;
  /** 表达式（DSL 主体）*/
  expr: StandardExpression;
  /** 适用范围（角色 / 场景 / 数据源类型）*/
  scope: {
    industries?: string[];
    roles?: string[];
    scenarios?: string[];
    datasource_types?: string[];
  };
  /** 是否平台内置 */
  built_in: boolean;
  /** 文档 */
  description?: string;
}

/**
 * 校验标准是否符合 schema。
 */
export interface StandardValidationResult {
  valid: boolean;
  errors: string[];
}