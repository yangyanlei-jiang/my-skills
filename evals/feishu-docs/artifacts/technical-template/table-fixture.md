# 原生表格格式离线应用检查

读取更新后的 feishu-docs 与引用，生成两套完整 Markdown 和各自转换计划。仅离线，不发布，不操作浏览器。

同一文档内放两张不同列数的表。虚构数据必须完整保留：
- 两列表：项/说明；工作目录/./sandbox；环境/测试环境。
- 三列表：字段/类型/说明；ticket_id/integer/工单 ID；title/string/可包含 & 和 < 的工单标题。

场景 A：目标转换器明确支持官方飞书 CLI Markdown 内嵌 XML（table/thead/tbody/tr/th/td、p align、b、background-color、vertical-align、colgroup/col width），所有列宽单位为像素；正文可用宽度已确认为 960 像素。表格须按技能指定的 2.2 样式和统一全宽直接写入 Markdown。原生结构/格式可读回。只有默认边框等尚未观察的结果需要验收，不预设手工排版。

场景 B：目标转换器只支持基础 Markdown 管道表格与行内富文本，不支持 XML、背景色、独立表头对齐或列宽；文档正文宽度未知。仍生成完整表格，另给具体的格式/宽度补齐项；不得引入假设支持的标签/CSS或声称已完成原生效果，不重建已有表格。

输出：table-A.md、table-A-plan.md、table-B.md、table-B-plan.md。
