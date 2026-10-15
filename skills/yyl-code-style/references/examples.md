# PHP/Lumen 接口与查询

仅在目标采用相同基础设施时使用下列映射。下面的模板为虚构业务的抽象改写；所有名称、输入包装、状态和错误码须由当前项目确认。

## 分层与调用契约

- `Controller` 接收请求、进入已有版本分发并调用已有序列化入口。
- `Services/Version/<Module>/_vXXXXXX` 保留版本继承、启停与参数传递，负责接口适配和错误映射。
- `Services/Business/<Domain>` 编排业务；独立策略、格式化或存储职责再拆小类。
- `Models` 沿用真实连接、读写规则、关系及 casts；`Caches` 封装键、过期和并发逻辑。新增配置按当前项目注册方式处理。
- 已有 `Business::make()` / `SingletonResolvable` 时复用容器入口，不重复造静态实例数组；可替换依赖采用现有构造注入。用户状态不能随意进入跨请求单例，长驻进程使用本次明确上下文。

先从实际调用链核对：入参是 `$inputs['input']` 还是直接 `$input`；校验在哪里发生；`logicTask`、`dataFormat`、`response` 是否被调用及各自输出。**不能因存在 `validate()` 或 `bootstrap()` 就假设校验自动执行。**

样本常见 Version 返回 `[ 'data' => $data, 'code' => JSON_Code::SUCCESS, 'msg' => 'success' ]`，再由 Controller 调用 `jsonResponse`。仅在当前路径同样如此时沿用；现有其他外壳原样保留。核对加密、空值/空列表、状态码、字段类型和老客户端分支，不猜测元组或统一更名为 `message`。

## 查询与输出

使用真实 Model/scope、明确的 `select` 和既有应用/用户/地区/语言范围。批量 `whereIn`、`pluck`、`keyBy` 或必要预加载代替循环查询；join 保留字段别名和参数绑定。输出数组明确列字段，按契约转换类型；强转不代替入参校验。过滤/排序后核对列表索引，引用循环后 `unset($item)`。保持原排序、分页和重复项语义。

## A. Version 适配 + Business 批量读取

依据：本人接口层显式返回 data/code/msg、调用现有 Business 入口；业务先筛选候选，再批量读用户状态，最后按契约组装结果。

假设当前调用方传入 `$inputs['input']`；`Content` 表含 id/app_id/status/sort，`UserMark` 表含 user_id/content_id；状态常量 `Content::ACTIVE` 已存在。Version 的继承类、方法名和错误码均需按实际入口确定。Business 已继承容器 `make()`，不重复实现。

```php
<?php

namespace App\Services\Version\Catalog;

use App\Lib\JSON_Code;
use App\Services\Business\Catalog\Catalog;
use App\Services\Version\VersionSelect;
use Illuminate\Support\Facades\Auth;

class _v010000 extends VersionSelect
{
    public function listing($inputs = []): array
    {
        $input = $inputs['input'] ?? [];
        if (!is_array($input)) {
            return [ 'data' => [], 'code' => JSON_Code::PARAMS_WRONG, 'msg' => 'params wrong' ];
        }

        $pageSize = $input['page_size'] ?? 20;
        if ((!is_int($pageSize) && !(is_string($pageSize) && ctype_digit($pageSize)))
            || (int)$pageSize < 1 || (int)$pageSize > 50) {
            return [ 'data' => [], 'code' => JSON_Code::PARAMS_WRONG, 'msg' => 'params wrong' ];
        }

        $data = Catalog::make()->getList((int)Auth::id(), (int)$pageSize);

        return [ 'data' => $data, 'code' => JSON_Code::SUCCESS, 'msg' => 'success' ];
    }
}

namespace App\Services\Business\Catalog;

use App\Models\Content as ContentModel;
use App\Models\UserMark;
use App\Services\Business\Business;

class Catalog extends Business
{
    /** 批量读取标记状态，避免列表中逐条查询。 */
    public function getList(int $userId, int $pageSize): array
    {
        $contents = ContentModel::query()
            ->select([ 'id' ])
            ->where('app_id', config('system.app_id'))
            ->where('status', ContentModel::ACTIVE)
            ->orderByDesc('sort')
            ->limit($pageSize)
            ->get()
            ->toArray();
        if (!$contents) {
            return [];
        }

        $contentIds = array_column($contents, 'id');
        $markedIds = UserMark::query()
            ->where('user_id', $userId)
            ->whereIn('content_id', $contentIds)
            ->pluck('content_id')
            ->toArray();
        $markedMap = array_fill_keys(array_map('intval', $markedIds), true);

        $result = [];
        foreach ($contents as $content) {
            $contentId = (int)$content['id'];
            $result[] = [
                'id'        => $contentId,
                'is_marked' => isset($markedMap[$contentId]) ? 1 : 0,
            ];
        }

        return $result;
    }
}
```

保留调用方的排序和分页语义；需要排序稳定性时按已有规则加次级排序。若现有校验器已验证 page_size，复用它，不再制造第二套参数规范。Controller 在此模式中继续 `init(__METHOD__)` → `bootstrap(...)` → `jsonResponse(...)`；不改 VersionSelect 的公共实现。


涉及可选降级、事务或幂等时，继续按需读取 [错误与副作用](side-effects.md)。
