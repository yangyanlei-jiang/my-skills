---
name: yyl-code-style
description: Use when writing, refactoring, or reviewing code in Yang Yanlei's personal style (杨艳磊 / YYL), especially PHP and Lumen services resembling video_api. For other languages, apply the transferable style while retaining their framework and API contracts. Not for changing repository-wide formatting or migrating architecture without a task requirement.
---

# YYL Code Style

目标：生成能自然融入杨艳磊现有代码的实现。**当前任务要求、仓库规范和既有契约优先于本技能；个人风格决定新增代码的表达方式，不改变业务语义。**

先查看改动位置附近的类、调用方、响应格式和格式化配置。不要以文件被本人提交过为依据，把整个文件都归为个人创作。风格依据与限制见 [风格画像](references/style-profile.md)。

## 1. 代码风格

- 类和命名空间用 `PascalCase`，方法、局部变量和属性用 `camelCase`；表名、字段、配置键及 API 数据键沿用 `snake_case`。`is/has/can` 表示布尔判断，`get/build/format/validate` 表达明确职责。
- 使用四空格缩进、短数组 `[]`、英文标识符和中文业务注释。没有 formatter 或邻近规范时，PHP 单行数组采用 `[ 'key' => $value ]`，多行关联数组适度对齐 `=>`。已有文件的括号、强转空格和尾逗号规则优先，避免无关格式差异。
- 多段业务使用空行分组；优先前置校验、提前 `return` 和循环中的 `continue`。先收集、批量读取，再构建明确的结果数组。
- 注释解释条件、时间边界、兼容原因和数据不变量。接口职责不清或存在非显然边界时补 PHPDoc；不生成作者日期头、不逐行翻译代码、不保留调试代码或大段注释掉的旧实现。
- 新增内部方法尽量声明明确参数、返回值及属性类型；旧方法的可见性、签名、nullable、弱类型调用兼容性以真实调用方为准。不要为统一外观给全文件添加 `strict_types`，或擅自收紧旧接口。
- 新常量使用语义明确的 `UPPER_SNAKE_CASE`；复用已有业务常量、配置和枚举映射，不借风格修改重命名旧常量或批量升级原生 enum。

## 2. 分层与实例获取

在采用相同基础设施的 Lumen 项目中：

1. `Controller` 接收请求、进入既有版本分发并调用已有序列化入口；不承担复杂查询和业务编排。
2. `Services/Version/<Module>/_vXXXXXX` 保留版本继承、启停与参数传递方式，完成接口适配和业务错误映射。
3. `Services/Business/<Domain>` 负责业务条件与编排；需要独立策略、格式化、快照或存储职责时拆成小类，不为简单功能强制引入 Repository/Factory。
4. `Models` 保留真实连接、读写规则、关系和 casts；`Caches` 封装缓存键、过期与并发逻辑；常量、helper 和配置沿用项目已有位置。

存在 `Business::make()` / `SingletonResolvable` 时复用容器入口；需要替换的依赖采用现有构造注入方式，不另造静态实例数组。先核对实例生命周期：携带用户状态的对象不能随意扩展成跨请求单例，队列/长驻进程不要从上一次请求的静态状态取上下文。

其他框架保留其原生目录、依赖注入与类生命周期；只迁移命名、业务拆分、提前返回和契约意识，不创建一套 Lumen 基类。

## 3. 接口、查询与错误处理

- 在 `video_api` 同类 Version 接口中，常见结果为 `[ 'data' => $data, 'code' => JSON_Code::SUCCESS, 'msg' => 'success' ]`，Controller 再调用既有 `jsonResponse`。核对实际入口：可能接收 `$inputs['input']`，也可能接收直接 `$input`。禁止猜测成 `[code, data]` 元组、改成 `message` 或新套响应外壳。
- 核对当前校验、`logicTask`、`dataFormat` 和 `response` 各自真实执行位置；流水线名称不证明基类自动执行 `validate`。保留已有加密、空值/空列表表示、状态码、字段类型和老客户端分支。
- Eloquent 优先使用真实 Model/现有 scope、`query()`、明确 `select`，并沿用应用、用户、地区、语言等已有范围。批量 `whereIn` / `pluck` / `keyBy` 或必要的预加载优于循环查询；新增 join 时保留字段别名和参数绑定。
- 输出数组显式列字段并按契约强转；过滤、排序和引用循环后注意列表索引及 `unset($item)`。强转不替代入参合法性检查，不因补默认值隐藏错误。
- 可选展示业务在明确允许的故障范围内降级为 `[]`、`null` 或既有默认结构；支付、资产、库存及必要持久化失败继续失败并交给真实错误边界。业务异常与系统异常分开，不统一 catch 后返回成功或 `false`。
- 日志采用可检索事件名和结构化上下文，记录必要 ID、操作和异常类型；减少成功路径及每个守卫分支的噪声。仅在明确的可选降级路径中允许日志自身失败不影响响应，不全局吞掉日志错误。

## 4. 有副作用时的行为规范

- 状态、金额、次数和展示资格修改先确认来源、幂等键及重复请求结果。复用现有约束/锁；Redis 锁不是数据库幂等和事务的替代品。
- 一个原子业务单元内使用同一真实写连接，锁顺序一致，锁后复查状态与幂等记录；读写分离时核对主库读取。外部不可回滚调用及重试不可重复的副作用按项目已有提交后/补偿机制处理。
- Redis 键复用集中定义或现有缓存类。跨多个键的频控、计数、缓存提交需确认原子性；只有本人 token 的锁才能主动释放。TTL、日界线、时区和重试次数来自当前需求，不复制历史示例值。
- 功能、版本、实验、地区或语言分支以当前产品规则为准；保留兼容逻辑，不把某次运营条件写成通用风格要求。

## 5. 范例与自查

涉及具体写法时阅读 [脱敏 Few-shot 与模板](references/examples.md)：含版本接口、批量查询、可选降级及同连接幂等事务。示例依赖已注明，实际使用必须换成项目真实模型和常量。

完成后检查：

- [ ] 命名、缩进、数组和注释与邻近文件一致，差异仅覆盖任务范围。
- [ ] Controller/Version/Business/Model/Cache 的职责与实例入口正确，没有多余层或重复 `make()`。
- [ ] 入参、版本分发、鉴权、应用/用户范围、响应外壳及字段类型保留；已查看校验的真实执行位置。
- [ ] 条件和查询集中处理，没有 N+1；选择字段、排序、分页、空值与列表索引符合契约。
- [ ] 可选降级与必要写入失败分开，日志足够定位且不暴露敏感内容。
- [ ] 涉及写入时已检查连接、幂等、重放、锁所有权、时间边界和提交后副作用。
- [ ] 只使用目标 PHP/框架支持的语法及现有工具；至少对实际修改的 PHP 执行 `php -l`，行为验证按项目惯例进行，不擅自新建测试框架或执行 schema/migration。
- [ ] 若某项风格与任务或仓库规则冲突，采用后者并简短说明取舍；没有为“像本人”复制历史缺陷或私有业务规则。
