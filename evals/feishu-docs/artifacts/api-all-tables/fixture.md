# 接口小表全宽离线场景

只生成 Markdown 与简短转换计划，不登录、不联网、不发布。

虚构接口 get_ticket，GET /v3/tickets/{id}，X-Client-Key 认证，无版本门槛。仅一个入参：路径 id，integer，必填。项目响应契约为 {"ok":true,"result":{"title":"Test ticket"}}；需要说明的 result 业务对象只有 title:string，含义为工单标题；无分页，本次不描述错误分支。正文末尾另放一个两列责任表：事项/负责人；联调/测试团队。

目标转换器已明确支持官方飞书 Markdown 内嵌 XML：table、colgroup/col width（像素）、thead/tbody、tr/th/td、p align、b、background-color、vertical-align。正文可用宽度已确认为 1020 像素。结构和格式可以读回。按所读技能自然组织，不添加未给定契约或无关章节。

输出 draft.md 与 plan.md；输出文件只放正式正文，不把转换说明混入正文。
