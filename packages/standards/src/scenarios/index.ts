/**
 * 5 个内置离散制造场景模板（参见 TASK-041）。
 *
 * 每个场景配 1~3 个内置交付标准；用户可在 UI 上覆盖标准参数。
 */

import type { DeliveryStandard } from '../dsl/types.js';
import type { Scenario } from '../dsl/scenario.js';

// =============================================================================
// 场景 1：库存预警
// =============================================================================

export const inventoryAlertScenario: Scenario = {
  key: 'inventory_alert',
  name: '库存预警',
  industry: 'discrete-manufacturing',
  description: '当物料库存低于安全库存阈值时，自动通知采购 + 创建补货工单',
  default_standard_keys: ['inventory_low_stock'],
  trigger: {
    source: 'ontology_event',
    watch_field: 'material.current_stock',
  },
  flow_template: [
    {
      id: 'check',
      standard_key: 'inventory_low_stock',
      description: '检测库存量是否低于安全库存',
      next: 'notify',
    },
    {
      id: 'notify',
      standard_key: 'notify_purchase',
      description: '通知采购负责人',
      next: 'create_ticket',
    },
    {
      id: 'create_ticket',
      standard_key: 'create_replenish_ticket',
      description: '创建补货工单',
      next: null,
    },
  ],
  built_in: true,
};

// =============================================================================
// 场景 2：设备保养
// =============================================================================

export const equipmentMaintenanceScenario: Scenario = {
  key: 'equipment_maintenance',
  name: '设备保养',
  industry: 'discrete-manufacturing',
  description: '基于运行时长 / 上次保养时间，自动生成设备保养工单',
  default_standard_keys: ['equipment_maintenance_due'],
  trigger: {
    source: 'schedule',
    cron: '0 8 * * *', // 每天 8 点扫描
  },
  flow_template: [
    {
      id: 'scan',
      standard_key: 'equipment_maintenance_due',
      description: '扫描所有设备是否到保养周期',
      next: 'create_ticket',
      on_failure: null,
    },
    {
      id: 'create_ticket',
      standard_key: 'create_maintenance_ticket',
      description: '为到期设备创建保养工单',
      next: 'notify',
    },
    {
      id: 'notify',
      standard_key: 'notify_maintenance',
      description: '通知设备负责人',
      next: null,
    },
  ],
  built_in: true,
};

// =============================================================================
// 场景 3：质检抽检
// =============================================================================

export const qualityInspectionScenario: Scenario = {
  key: 'quality_inspection',
  name: '质检抽检',
  industry: 'discrete-manufacturing',
  description: '基于生产批次自动抽样检验，不合格自动触发返工',
  default_standard_keys: ['quality_inspection_sample'],
  trigger: {
    source: 'ontology_event',
    watch_field: 'batch.completed',
  },
  flow_template: [
    {
      id: 'sample',
      standard_key: 'quality_inspection_sample',
      description: '按 AQL 标准抽样',
      next: 'judge',
    },
    {
      id: 'judge',
      standard_key: 'quality_judge_pass',
      description: '判定是否合格',
      next: 'tag',
    },
    {
      id: 'tag',
      standard_key: 'tag_quality_result',
      description: '在本体图上标记批次质量等级',
      next: null,
    },
  ],
  built_in: true,
};

// =============================================================================
// 场景 4：排产优化
// =============================================================================

export const productionSchedulingScenario: Scenario = {
  key: 'production_scheduling',
  name: '排产优化',
  industry: 'discrete-manufacturing',
  description: '基于订单交期 / 设备产能 / 物料齐套性自动排产',
  default_standard_keys: ['production_schedule_optimize'],
  trigger: {
    source: 'schedule',
    cron: '0 6 * * 1-5', // 工作日 6 点
  },
  flow_template: [
    {
      id: 'collect',
      standard_key: 'production_collect_constraints',
      description: '收集订单 / 设备 / 物料约束',
      next: 'optimize',
    },
    {
      id: 'optimize',
      standard_key: 'production_schedule_optimize',
      description: '排产优化求解',
      next: 'notify',
    },
    {
      id: 'notify',
      standard_key: 'notify_schedule',
      description: '下发排产结果到车间',
      next: null,
    },
  ],
  built_in: true,
};

// =============================================================================
// 场景 5：来料异常
// =============================================================================

export const inboundAnomalyScenario: Scenario = {
  key: 'inbound_anomaly',
  name: '来料异常',
  industry: 'discrete-manufacturing',
  description: '供应商来料数量 / 质量异常时，自动触发 8D 报告',
  default_standard_keys: ['inbound_qty_anomaly', 'inbound_quality_anomaly'],
  trigger: {
    source: 'ontology_event',
    watch_field: 'inbound.received',
  },
  flow_template: [
    {
      id: 'check_qty',
      standard_key: 'inbound_qty_anomaly',
      description: '数量异常检测',
      next: 'check_quality',
    },
    {
      id: 'check_quality',
      standard_key: 'inbound_quality_anomaly',
      description: '质量异常检测',
      next: 'create_8d',
    },
    {
      id: 'create_8d',
      standard_key: 'create_8d_report',
      description: '创建 8D 报告',
      next: 'notify_supplier',
    },
    {
      id: 'notify_supplier',
      standard_key: 'notify_supplier',
      description: '通知供应商质量整改',
      next: null,
    },
  ],
  built_in: true,
};

// =============================================================================
// 内置标准（5 个场景涉及的关键标准；其它标准在 delivery_standards 表里存）
// =============================================================================

export const inventoryLowStockStandard: DeliveryStandard = {
  key: 'inventory_low_stock',
  name: '库存低于安全库存',
  kind: 'threshold',
  expr: {
    kind: 'threshold',
    condition: {
      type: 'threshold',
      field: 'material.current_stock',
      op: '<',
      value: '$material.safety_stock',
      is_ref: true,
    },
    action: 'create_ticket',
    action_payload: { ticket_type: 'replenish' },
  },
  scope: {
    industries: ['discrete-manufacturing'],
    scenarios: ['inventory_alert'],
    datasource_types: ['mysql', 'postgres', 'sqlserver', 'oracle'],
  },
  built_in: true,
  description: '物料库存量小于安全库存时触发补货流程',
};

export const equipmentMaintenanceDueStandard: DeliveryStandard = {
  key: 'equipment_maintenance_due',
  name: '设备保养到期',
  kind: 'temporal',
  expr: {
    kind: 'temporal',
    condition: {
      type: 'temporal',
      since_field: 'equipment.last_maintenance_at',
      exceed_minutes: 60 * 24 * 30, // 30 天
    },
    action: 'create_ticket',
    action_payload: { ticket_type: 'maintenance' },
  },
  scope: { industries: ['discrete-manufacturing'], scenarios: ['equipment_maintenance'] },
  built_in: true,
};

// 其余标准简化定义（同结构）
export const qualityInspectionSampleStandard: DeliveryStandard = {
  key: 'quality_inspection_sample',
  name: '按 AQL 抽样',
  kind: 'pattern',
  expr: {
    kind: 'pattern',
    condition: { type: 'pattern', pattern: 'AQL-2.5', window_minutes: 60 },
    action: 'create_ticket',
    action_payload: { ticket_type: 'inspection' },
  },
  scope: { industries: ['discrete-manufacturing'], scenarios: ['quality_inspection'] },
  built_in: true,
};

export const productionScheduleOptimizeStandard: DeliveryStandard = {
  key: 'production_schedule_optimize',
  name: '排产优化',
  kind: 'aggregation',
  expr: {
    kind: 'aggregation',
    condition: {
      type: 'aggregation',
      count: 10,
      within_minutes: 60 * 8,
      match: {
        type: 'threshold',
        field: 'order.due_days',
        op: '<=',
        value: 7,
      },
    },
    action: 'tag',
    action_payload: { tag: 'urgent' },
  },
  scope: { industries: ['discrete-manufacturing'], scenarios: ['production_scheduling'] },
  built_in: true,
};

export const inboundQtyAnomalyStandard: DeliveryStandard = {
  key: 'inbound_qty_anomaly',
  name: '来料数量异常',
  kind: 'threshold',
  expr: {
    kind: 'threshold',
    condition: {
      type: 'threshold',
      field: 'inbound.received_qty',
      op: '<',
      value: '$inbound.ordered_qty',
      is_ref: true,
    },
    action: 'create_ticket',
    action_payload: { ticket_type: '8d' },
  },
  scope: { industries: ['discrete-manufacturing'], scenarios: ['inbound_anomaly'] },
  built_in: true,
};

// =============================================================================
// 索引
// =============================================================================

export const BUILT_IN_SCENARIOS: Scenario[] = [
  inventoryAlertScenario,
  equipmentMaintenanceScenario,
  qualityInspectionScenario,
  productionSchedulingScenario,
  inboundAnomalyScenario,
];

export const BUILT_IN_STANDARDS: DeliveryStandard[] = [
  inventoryLowStockStandard,
  equipmentMaintenanceDueStandard,
  qualityInspectionSampleStandard,
  productionScheduleOptimizeStandard,
  inboundQtyAnomalyStandard,
];