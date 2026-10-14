# 脱敏 Few-shot 与模板

以下按本人提交中的结构重写为虚构的内容目录、推荐和发放业务。不是原项目代码的逐字复制，也不是可直接对生产数据库执行的完整功能。示例中的模型、表、状态和错误码须替换为项目真实定义。

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

## B. 可选展示失败与关键写入失败

依据：展示模块允许受控降级且保留结构化异常上下文；本人曾移除支付执行中 catch 后返回 false 的处理，让必要失败继续向上层传播。

下例的 callable 是现有业务适配器；可选读取只捕获已定义的可用性异常。不要把它扩展成“所有异常均降级”的全局规则。

```php
<?php

namespace App\Services\Business\Example;

use Illuminate\Support\Facades\Log;
use RuntimeException;
use Throwable;

class OptionalDataUnavailableException extends RuntimeException
{
}

class Recommendation
{
    public function optionalList(callable $read, int $userId): array
    {
        try {
            return $read($userId);
        } catch (OptionalDataUnavailableException $exception) {
            try {
                Log::warning('recommendation cache unavailable', [
                    'user_id'   => $userId,
                    'exception' => get_class($exception),
                ]);
            } catch (Throwable $logException) {
                // 可选展示的降级结果不依赖日志可用性。
            }

            return [];
        }
    }
}

class Settlement
{
    /** commit 必须在自身事务成功提交后才返回；异常交由调用方现有边界处理。 */
    public function settle(callable $commit, int $paymentId): array
    {
        return $commit($paymentId);
    }
}
```

Settlement 的例子只表达错误边界，不是完整结算实现；不要用“已调用 commit”冒充真实事务提交。日志由现有异常处理层记录时，无需各层重复记录。

## C. 同连接、锁后复查和幂等重放

依据：复杂写入模块使用明确的连接、主库读取、用户锁和锁后幂等检查；重复请求返回已保存结果。

假设：调用方已经完成鉴权；users 表含 id/app_id；reward_requests 已有 app_id/user_id/request_id 联合唯一约束和 fingerprint/result 字段。fingerprint 由当前业务的确定性参数规范化生成，不能直接 hash 未规范化的 request 全量数据。此示例不会创建 schema。

```php
<?php

namespace App\Services\Business\Example;

use Illuminate\Database\Connection;
use InvalidArgumentException;
use LogicException;
use RuntimeException;

class RewardGrant
{
    private Connection $write;

    public function __construct(Connection $write)
    {
        $this->write = $write;
    }

    /** apply 只执行同一连接内的数据库写入，不发送外部通知。 */
    public function grantOnce(int $appId, int $userId, string $requestId, string $fingerprint, callable $apply): array
    {
        if ($appId <= 0 || $userId <= 0 || $requestId === '' || $fingerprint === '') {
            throw new InvalidArgumentException('发放参数不完整');
        }

        return $this->write->transaction(function () use ($appId, $userId, $requestId, $fingerprint, $apply) {
            $user = $this->write->table('users')
                ->where('app_id', $appId)
                ->where('id', $userId)
                ->lockForUpdate()
                ->first();
            if (!$user) {
                throw new InvalidArgumentException('用户不存在');
            }

            $scope = [ 'app_id' => $appId, 'user_id' => $userId, 'request_id' => $requestId ];
            // 锁后复查，不能依赖事务前的查询结果。
            $existing = $this->write->table('reward_requests')->where($scope)->first();
            if ($existing) {
                if (!hash_equals((string)$existing->fingerprint, $fingerprint)) {
                    throw new InvalidArgumentException('同一请求不能使用不同参数');
                }
                $result = json_decode($existing->result, true, 512, JSON_THROW_ON_ERROR);
                if (!is_array($result)) {
                    throw new RuntimeException('发放记录损坏');
                }

                return $result;
            }

            $result = $apply($this->write, $userId);
            if (!is_array($result)) {
                throw new LogicException('发放结果必须为数组');
            }
            $saved = $this->write->table('reward_requests')->insert($scope + [
                'fingerprint' => $fingerprint,
                'result'      => json_encode($result, JSON_THROW_ON_ERROR),
            ]);
            if (!$saved) {
                throw new RuntimeException('发放记录写入失败');
            }

            return $result;
        });
    }
}
```

锁和唯一约束须与所有写入方一致；不能仅靠这个片段防御绕过用户锁的其他服务。回调必须遵守上述同连接条件。事务重试、外部通知、队列和补偿沿用项目真实机制，不复制固定重试次数。
