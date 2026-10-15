# 错误、日志与副作用

用于错误处理、关键写入、缓存或并发任务；纯读接口不因此添加事务、锁或幂等表。下列模板仍是虚构业务的抽象改写，不能直接当成生产实现。

## 先确定失败边界

- 可选展示只有在业务明确允许且故障类型已知时，才返回约定的 `[]`、`null` 或默认结构；正常的空结果不等于异常。
- 支付、资产、库存和必要持久化失败，交给当前调用链的错误边界。复用业务异常/系统异常区分，不统一 catch 后返回成功或 `false`。
- 使用可检索事件名和结构化上下文，保留必要 ID、操作和异常类型；减少正常守卫和成功路径噪声，已有上层记录时不重复记录。
- 只在明确可选的降级路径中容忍日志自身不可用；其他路径沿用项目日志策略。

## 写入与缓存的不变量

1. 从真实调用方确认状态来源、幂等范围、重复请求应返回的结果；同 key 不同参数按业务冲突处理。复用已有约束和锁，Redis 锁不替代数据库幂等。
2. 原子业务单元使用同一真实写连接；读写分离时核对主库读取。保持锁顺序，在锁后复查状态和幂等记录。
3. 外部不可回滚调用、通知和重试不可重复的副作用使用项目已有提交后或补偿机制；数据库事务不能撤销外部调用。
4. 缓存键沿用集中定义/缓存类；跨键计数、频控或缓存提交核对原子性；锁主动释放须校验持有者 token。
5. TTL、日界线、时区、重试次数和运营分支由当前需求确定，不从历史代码或模板复制阈值。

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
