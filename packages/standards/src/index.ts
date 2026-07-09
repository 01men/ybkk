/**
 * aios_standards —— 场景模板 DSL 与内置交付标准（参见 TASK-040/041）。
 *
 * 设计原则：
 *  - DSL 是声明式 YAML，不是代码（业务配置人员可读可改）
 *  - 每个标准有 JSON Schema 校验（启动时加载 5 个内置模板）
 *  - 标准覆盖 = 在基线标准上做字段级覆盖（merge 而非替换）
 */

export * from './dsl/standard.js';
export * from './dsl/scenario.js';
export * from './scenarios/index.js';
export { BUILT_IN_SCENARIOS } from './scenarios/index.js';